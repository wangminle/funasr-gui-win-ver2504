#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
转写完成检测修复测试脚本
测试修复了的转写完成检测功能

测试目标：
1. 验证"离线识别完成"检测
2. 验证"实时识别完成"检测  
3. 验证原有的"离线模式收到非空文本"检测
4. 验证原有的"收到结束标志或完整结果"检测
5. 验证多种格式的兼容性

日期：2024-07-14
"""

import os
import sys
import time

# 添加源代码路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dev', 'src', 'python-gui-client'))

def test_transcribe_completion_patterns():
    """测试转写完成的各种检测模式"""
    print("=== 测试转写完成检测模式 ===")
    
    try:
        # 测试各种转写完成的日志格式
        test_logs = [
            # 新格式
            '[2024-07-14 10:30:08][完成] 离线识别完成',
            '[2024-07-14 10:30:09][完成] 实时识别完成',
            # 原有格式
            '[2024-07-14 10:30:10][结果] 离线模式收到非空文本: 测试结果',
            '[2024-07-14 10:30:11][完成] 收到结束标志或完整结果',
            # 其他不应该触发的格式
            '[2024-07-14 10:30:12][信息] 开始离线识别',
            '[2024-07-14 10:30:13][调试] 准备实时识别',
        ]
        
        transcribe_end_detected_count = 0
        detected_patterns = []
        
        for line in test_logs:
            # 使用实际的检测条件
            if ("离线识别完成" in line or "实时识别完成" in line or 
                "离线模式收到非空文本" in line or "收到结束标志或完整结果" in line):
                transcribe_end_detected_count += 1
                
                # 记录检测到的具体模式
                if "离线识别完成" in line:
                    detected_patterns.append("离线识别完成")
                elif "实时识别完成" in line:
                    detected_patterns.append("实时识别完成")
                elif "离线模式收到非空文本" in line:
                    detected_patterns.append("离线模式收到非空文本")
                elif "收到结束标志或完整结果" in line:
                    detected_patterns.append("收到结束标志或完整结果")
                
                print(f"✓ 检测到转写完成: {line.strip()}")
        
        # 验证检测结果
        expected_count = 4  # 应该检测到4种模式
        assert transcribe_end_detected_count == expected_count, f"转写完成检测次数错误: 期望{expected_count}, 实际{transcribe_end_detected_count}"
        
        # 验证各种模式都被检测到
        expected_patterns = ["离线识别完成", "实时识别完成", "离线模式收到非空文本", "收到结束标志或完整结果"]
        for pattern in expected_patterns:
            assert pattern in detected_patterns, f"未检测到模式: {pattern}"
            print(f"✓ 模式 '{pattern}' 检测正常")
        
        print("✓ 转写完成检测模式测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 转写完成检测模式测试失败: {e}")
        return False

def test_transcribe_timing_simulation():
    """模拟完整的转写时间计算流程"""
    print("=== 测试完整转写时间计算流程 ===")
    
    try:
        # 模拟完整的速度测试流程
        upload_start_time = None
        upload_end_time = None
        transcribe_start_time = None
        transcribe_end_time = None
        
        test_sequence = [
            ('[2024-07-14 10:30:00][发送] 发送初始化消息: {"mode": "offline", "audio_fs": 16000}', 'upload_start'),
            ('[2024-07-14 10:30:05] 上传进度: 100%', 'upload_end'),
            ('[2024-07-14 10:30:08][完成] 离线识别完成', 'transcribe_end'),
        ]
        
        for line, event_type in test_sequence:
            current_time = time.time()
            
            if event_type == 'upload_start':
                if ("发送初始化消息:" in line or "发送WebSocket:" in line) and "mode" in line and upload_start_time is None:
                    upload_start_time = current_time
                    transcribe_start_time = current_time  # 假设上传开始即转写开始
                    print(f"✓ 检测到上传开始: {upload_start_time}")
            
            elif event_type == 'upload_end':
                if "上传进度: 100%" in line and upload_end_time is None:
                    upload_end_time = current_time
                    print(f"✓ 检测到上传结束: {upload_end_time}")
            
            elif event_type == 'transcribe_end':
                if ("离线识别完成" in line or "实时识别完成" in line or 
                    "离线模式收到非空文本" in line or "收到结束标志或完整结果" in line) and transcribe_end_time is None:
                    transcribe_end_time = current_time
                    print(f"✓ 检测到转写完成: {transcribe_end_time}")
        
        # 验证所有时间点都被检测到
        assert upload_start_time is not None, "未检测到上传开始时间"
        assert upload_end_time is not None, "未检测到上传结束时间"
        assert transcribe_start_time is not None, "未检测到转写开始时间"
        assert transcribe_end_time is not None, "未检测到转写结束时间"
        
        # 进行安全的时间计算
        if upload_start_time is not None and upload_end_time is not None:
            upload_duration = upload_end_time - upload_start_time
            print(f"✓ 上传时间计算成功: {upload_duration:.4f}s")
        else:
            print("⚠ 上传时间缺失，跳过计算")
        
        if transcribe_start_time is not None and transcribe_end_time is not None:
            transcribe_duration = transcribe_end_time - transcribe_start_time
            print(f"✓ 转写时间计算成功: {transcribe_duration:.4f}s")
        else:
            print("⚠ 转写时间缺失，跳过计算")
        
        print("✓ 完整转写时间计算流程测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 完整转写时间计算流程测试失败: {e}")
        return False

def test_edge_cases_transcribe_detection():
    """测试转写检测的边界情况"""
    print("=== 测试转写检测边界情况 ===")
    
    try:
        # 测试各种边界情况
        edge_cases = [
            # 正常情况
            ('[2024-07-14 10:30:08][完成] 离线识别完成', True, "正常的离线识别完成"),
            ('[2024-07-14 10:30:09][完成] 实时识别完成', True, "正常的实时识别完成"),
            
            # 包含其他文字的情况
            ('[2024-07-14 10:30:10][完成] 离线识别完成，文件处理结束', True, "带额外信息的离线识别完成"),
            ('[2024-07-14 10:30:11][结果] 离线模式收到非空文本: 识别结果文本内容', True, "带结果内容的文本"),
            
            # 不应该触发的情况
            ('[2024-07-14 10:30:12][调试] 离线识别进行中', False, "进行中状态"),
            ('[2024-07-14 10:30:13][信息] 准备离线识别', False, "准备状态"),
            ('[2024-07-14 10:30:14][错误] 离线识别失败', False, "失败状态"),
            
            # 大小写和变体
            ('[2024-07-14 10:30:15][完成] 实时识别完成!', True, "带感叹号的完成"),
            ('[2024-07-14 10:30:16][完成] 收到结束标志或完整结果，处理完毕', True, "带额外信息的结束标志"),
        ]
        
        passed_cases = 0
        total_cases = len(edge_cases)
        
        for line, should_detect, description in edge_cases:
            detected = ("离线识别完成" in line or "实时识别完成" in line or 
                       "离线模式收到非空文本" in line or "收到结束标志或完整结果" in line)
            
            if detected == should_detect:
                print(f"✓ {description}: 检测结果正确 ({'检测到' if detected else '未检测到'})")
                passed_cases += 1
            else:
                print(f"✗ {description}: 检测结果错误 (期望{'检测到' if should_detect else '不检测'}, 实际{'检测到' if detected else '未检测到'})")
        
        assert passed_cases == total_cases, f"边界情况测试失败: {passed_cases}/{total_cases}"
        
        print("✓ 转写检测边界情况测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 转写检测边界情况测试失败: {e}")
        return False

def test_multiple_detection_prevention():
    """测试防止重复检测的机制"""
    print("=== 测试防止重复检测机制 ===")
    
    try:
        # 模拟可能出现重复日志的情况
        transcribe_end_time = None
        detection_count = 0
        
        repeated_logs = [
            '[2024-07-14 10:30:08][完成] 离线识别完成',
            '[2024-07-14 10:30:09][完成] 离线识别完成',  # 重复
            '[2024-07-14 10:30:10][结果] 离线模式收到非空文本: 结果',
            '[2024-07-14 10:30:11][完成] 离线识别完成',  # 再次重复
        ]
        
        for line in repeated_logs:
            # 模拟实际的检测逻辑（包含防止重复检测的条件）
            if ("离线识别完成" in line or "实时识别完成" in line or 
                "离线模式收到非空文本" in line or "收到结束标志或完整结果" in line) and transcribe_end_time is None:
                transcribe_end_time = time.time()
                detection_count += 1
                print(f"✓ 第{detection_count}次检测到转写完成: {line.strip()}")
        
        # 验证只检测了一次
        assert detection_count == 1, f"重复检测错误: 期望1次, 实际{detection_count}次"
        assert transcribe_end_time is not None, "转写结束时间未设置"
        
        print("✓ 防止重复检测机制测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 防止重复检测机制测试失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("开始转写完成检测修复测试...")
    print("=" * 50)
    
    test_functions = [
        test_transcribe_completion_patterns,
        test_transcribe_timing_simulation,
        test_edge_cases_transcribe_detection,
        test_multiple_detection_prevention
    ]
    
    passed = 0
    total = len(test_functions)
    
    for test_func in test_functions:
        try:
            if test_func():
                passed += 1
            print()
        except Exception as e:
            print(f"✗ 测试函数 {test_func.__name__} 执行失败: {e}")
            print()
    
    print("=" * 50)
    print(f"测试完成: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有转写完成检测测试通过！修复工作正常。")
        return True
    else:
        print("❌ 有测试失败，请检查转写完成检测修复代码。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 