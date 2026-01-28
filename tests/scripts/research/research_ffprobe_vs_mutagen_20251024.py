#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ffprobe vs mutagen 预研脚本

目标：对比两种媒体时长检测方案的效果
测试文件：
- resources/demo/tv-report-1.wav
- resources/demo/tv-report-1.mp4

对比维度：
1. 准确性：检测的时长是否准确
2. 覆盖率：支持的文件格式
3. 性能：检测耗时
4. 依赖性：安装难度
5. 容错性：失败时的行为

创建时间：2025-10-24
"""

import os
import sys
import time
import json
import subprocess
from typing import Optional, Dict, Any
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class MutagenDetector:
    """mutagen时长检测器"""
    
    def __init__(self):
        self.name = "mutagen"
        self.available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """检查mutagen是否可用"""
        try:
            import mutagen
            return True
        except ImportError:
            return False
    
    def detect_duration(self, file_path: str) -> Optional[float]:
        """检测文件时长"""
        if not self.available:
            return None
        
        try:
            from mutagen import File
            
            audio_file = File(file_path)
            if (
                audio_file is not None
                and hasattr(audio_file, "info")
                and hasattr(audio_file.info, "length")
            ):
                return audio_file.info.length
            else:
                return None
        except Exception as e:
            print(f"  ⚠️  mutagen检测失败: {e}")
            return None


class FFprobeDetector:
    """ffprobe时长检测器"""
    
    def __init__(self):
        self.name = "ffprobe"
        self.available = self._check_availability()
        self.ffprobe_path = self._find_ffprobe()
    
    def _check_availability(self) -> bool:
        """检查ffprobe是否可用"""
        return self._find_ffprobe() is not None
    
    def _find_ffprobe(self) -> Optional[str]:
        """查找ffprobe可执行文件"""
        # 尝试直接调用
        try:
            result = subprocess.run(
                ["ffprobe", "-version"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                return "ffprobe"
        except Exception:
            pass
        
        # 尝试常见路径
        common_paths = [
            "/usr/bin/ffprobe",
            "/usr/local/bin/ffprobe",
            "/opt/homebrew/bin/ffprobe",  # macOS Homebrew
        ]
        
        for path in common_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                return path
        
        return None
    
    def detect_duration(self, file_path: str) -> Optional[float]:
        """检测文件时长"""
        if not self.available:
            return None
        
        try:
            # 使用ffprobe检测
            cmd = [
                self.ffprobe_path,
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                file_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                if "format" in data and "duration" in data["format"]:
                    return float(data["format"]["duration"])
            
            return None
        except Exception as e:
            print(f"  ⚠️  ffprobe检测失败: {e}")
            return None


class MediaFileInfo:
    """媒体文件信息"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)
        self.file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        self.file_ext = os.path.splitext(file_path)[1]
        self.exists = os.path.exists(file_path)


def test_detector(detector, file_path: str) -> Dict[str, Any]:
    """测试单个检测器"""
    result = {
        "detector": detector.name,
        "available": detector.available,
        "duration": None,
        "time_cost": None,
        "success": False,
        "error": None
    }
    
    if not detector.available:
        result["error"] = f"{detector.name}不可用"
        return result
    
    try:
        start_time = time.time()
        duration = detector.detect_duration(file_path)
        end_time = time.time()
        
        result["duration"] = duration
        result["time_cost"] = end_time - start_time
        result["success"] = duration is not None
        
        if not result["success"]:
            result["error"] = "检测返回None"
    
    except Exception as e:
        result["error"] = str(e)
    
    return result


def format_duration(seconds: Optional[float]) -> str:
    """格式化时长显示"""
    if seconds is None:
        return "None"
    
    if seconds < 60:
        return f"{seconds:.2f}秒"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}分{secs:.2f}秒"


def format_time_cost(seconds: Optional[float]) -> str:
    """格式化耗时显示"""
    if seconds is None:
        return "N/A"
    return f"{seconds*1000:.2f}ms"


def print_test_result(result: Dict[str, Any]):
    """打印测试结果"""
    detector = result["detector"]
    
    if not result["available"]:
        print(f"  ❌ {detector}: 不可用")
        return
    
    if result["success"]:
        print(f"  ✅ {detector}: {format_duration(result['duration'])} (耗时: {format_time_cost(result['time_cost'])})")
    else:
        print(f"  ❌ {detector}: 失败 - {result['error']}")


def compare_results(mutagen_result: Dict[str, Any], ffprobe_result: Dict[str, Any]):
    """对比两个检测器的结果"""
    print("\n" + "=" * 70)
    print("📊 对比分析")
    print("=" * 70)
    
    # 1. 可用性对比
    print("\n【1. 可用性】")
    print(f"  mutagen: {'✅ 可用' if mutagen_result['available'] else '❌ 不可用'}")
    print(f"  ffprobe: {'✅ 可用' if ffprobe_result['available'] else '❌ 不可用'}")
    
    # 2. 准确性对比
    print("\n【2. 准确性】")
    if mutagen_result['success'] and ffprobe_result['success']:
        mutagen_dur = mutagen_result['duration']
        ffprobe_dur = ffprobe_result['duration']
        diff = abs(mutagen_dur - ffprobe_dur)
        
        print(f"  mutagen: {format_duration(mutagen_dur)}")
        print(f"  ffprobe: {format_duration(ffprobe_dur)}")
        print(f"  差异: {diff:.4f}秒")
        
        if diff < 0.1:
            print(f"  结论: ✅ 两者结果一致（差异<0.1秒）")
        else:
            print(f"  结论: ⚠️  存在差异（差异={diff:.4f}秒）")
    else:
        print("  无法对比（至少有一个检测器失败）")
    
    # 3. 性能对比
    print("\n【3. 性能】")
    if mutagen_result['success'] and ffprobe_result['success']:
        mutagen_time = mutagen_result['time_cost']
        ffprobe_time = ffprobe_result['time_cost']
        
        print(f"  mutagen: {format_time_cost(mutagen_time)}")
        print(f"  ffprobe: {format_time_cost(ffprobe_time)}")
        
        if mutagen_time < ffprobe_time:
            ratio = ffprobe_time / mutagen_time
            print(f"  结论: ✅ mutagen更快（快{ratio:.1f}倍）")
        else:
            ratio = mutagen_time / ffprobe_time
            print(f"  结论: ✅ ffprobe更快（快{ratio:.1f}倍）")
    else:
        if mutagen_result['success']:
            print(f"  mutagen: {format_time_cost(mutagen_result['time_cost'])}")
        if ffprobe_result['success']:
            print(f"  ffprobe: {format_time_cost(ffprobe_result['time_cost'])}")
    
    # 4. 成功率对比
    print("\n【4. 成功率】")
    print(f"  mutagen: {'✅ 成功' if mutagen_result['success'] else '❌ 失败'}")
    print(f"  ffprobe: {'✅ 成功' if ffprobe_result['success'] else '❌ 失败'}")


def run_research():
    """执行预研"""
    print("=" * 70)
    print("🔬 ffprobe vs mutagen 预研")
    print("=" * 70)
    print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 初始化检测器
    mutagen_detector = MutagenDetector()
    ffprobe_detector = FFprobeDetector()
    
    # 测试文件列表
    test_files = [
        "resources/demo/tv-report-1.wav",
        "resources/demo/tv-report-1.mp4",
    ]
    
    # 转换为绝对路径
    test_files = [str(project_root / f) for f in test_files]
    
    all_results = []
    
    # 对每个文件进行测试
    for file_path in test_files:
        print("\n" + "=" * 70)
        
        # 获取文件信息
        file_info = MediaFileInfo(file_path)
        
        print(f"📁 测试文件: {file_info.file_name}")
        print(f"   路径: {file_path}")
        print(f"   大小: {file_info.file_size / 1024 / 1024:.2f} MB")
        print(f"   格式: {file_info.file_ext}")
        print(f"   存在: {'✅' if file_info.exists else '❌'}")
        print()
        
        if not file_info.exists:
            print("  ⚠️  文件不存在，跳过测试")
            continue
        
        # 测试mutagen
        print("🔍 测试mutagen...")
        mutagen_result = test_detector(mutagen_detector, file_path)
        print_test_result(mutagen_result)
        
        # 测试ffprobe
        print("\n🔍 测试ffprobe...")
        ffprobe_result = test_detector(ffprobe_detector, file_path)
        print_test_result(ffprobe_result)
        
        # 对比结果
        compare_results(mutagen_result, ffprobe_result)
        
        # 保存结果
        all_results.append({
            "file": file_info.file_name,
            "file_path": file_path,
            "mutagen": mutagen_result,
            "ffprobe": ffprobe_result
        })
    
    # 总结
    print("\n" + "=" * 70)
    print("📊 总体总结")
    print("=" * 70)
    
    print("\n【检测器可用性】")
    print(f"  mutagen: {'✅ 可用' if mutagen_detector.available else '❌ 不可用（需要安装: pip install mutagen）'}")
    print(f"  ffprobe: {'✅ 可用' if ffprobe_detector.available else '❌ 不可用（需要安装: brew install ffmpeg 或 apt install ffmpeg）'}")
    
    # 统计成功率
    mutagen_success_count = sum(1 for r in all_results if r['mutagen']['success'])
    ffprobe_success_count = sum(1 for r in all_results if r['ffprobe']['success'])
    total_files = len(all_results)
    
    print(f"\n【检测成功率】")
    print(f"  mutagen: {mutagen_success_count}/{total_files} ({mutagen_success_count/total_files*100:.0f}%)")
    print(f"  ffprobe: {ffprobe_success_count}/{total_files} ({ffprobe_success_count/total_files*100:.0f}%)")
    
    # 推荐方案
    print(f"\n【推荐方案】")
    if mutagen_success_count == total_files and ffprobe_success_count == total_files:
        print("  ✅ 两者都能成功检测所有文件")
        print("  💡 建议: 优先使用mutagen（无外部依赖），ffprobe作为备选")
    elif mutagen_success_count == total_files:
        print("  ✅ mutagen能成功检测所有文件")
        print("  💡 建议: 使用mutagen即可")
    elif ffprobe_success_count == total_files:
        print("  ✅ ffprobe能成功检测所有文件")
        print("  💡 建议: 使用ffprobe，但需要确保ffmpeg已安装")
    else:
        print("  ⚠️  两者都无法100%成功")
        print("  💡 建议: 组合使用，先mutagen后ffprobe，最后兜底策略")
    
    print("\n" + "=" * 70)
    print("✅ 预研完成")
    print("=" * 70)
    
    return all_results


if __name__ == "__main__":
    results = run_research()
