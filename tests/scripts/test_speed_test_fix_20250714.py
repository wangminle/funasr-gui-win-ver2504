#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
速度测试修复验证脚本
测试日期：2025-01-14
目标：验证修复后的速度测试功能
"""

import logging
import os
import subprocess
import sys
import time


def setup_test_environment():
    """设置测试环境"""
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # 确保在项目根目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    os.chdir(project_root)
    
    logging.info(f"测试环境设置完成，项目根目录: {project_root}")

def test_gui_client_import():
    """测试GUI客户端是否能正常导入"""
    try:
        sys.path.insert(0, 'src/python-gui-client')
        import funasr_gui_client_v3
        logging.info("✓ GUI客户端模块导入成功")
        return True
    except Exception as e:
        logging.error(f"✗ GUI客户端模块导入失败: {e}")
        return False

def test_simple_client_syntax():
    """测试simple_funasr_client.py语法"""
    try:
        result = subprocess.run([
            sys.executable, '-m', 'py_compile', 
            'src/python-gui-client/simple_funasr_client.py'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logging.info("✓ simple_funasr_client.py 语法检查通过")
            return True
        else:
            logging.error(f"✗ simple_funasr_client.py 语法错误: {result.stderr}")
            return False
    except Exception as e:
        logging.error(f"✗ 语法检查异常: {e}")
        return False

def test_log_format_strings():
    """测试日志格式化字符串是否正确"""
    try:
        sys.path.insert(0, 'src/python-gui-client')
        from funasr_gui_client_v3 import LanguageManager
        
        lang_manager = LanguageManager()
        
        # 测试可能有问题的格式化字符串
        test_cases = [
            ("speed_test_upload_completed", [1, 10.5]),
            ("speed_test_transcription_completed", [1, 15.2]),
            ("speed_test_file_completed", [1, 10.5, 15.2]),
        ]
        
        all_passed = True
        for key, args in test_cases:
            try:
                result = lang_manager.get(key, *args)
                logging.info(f"✓ 格式化测试通过: {key} -> {result}")
            except Exception as e:
                logging.error(f"✗ 格式化测试失败: {key} -> {e}")
                all_passed = False
        
        return all_passed
    except Exception as e:
        logging.error(f"✗ 日志格式化测试异常: {e}")
        return False

def test_timestamp_detection_logic():
    """测试时间戳检测逻辑（模拟）"""
    try:
        # 模拟输出行
        test_lines = [
            "[2025-01-14 15:12:11][发送] 发送初始化消息: {\"mode\": \"offline\", \"audio_fs\": 16000}",
            "上传进度: 50%",
            "上传进度: 100%",
            "[2025-01-14 15:12:12][发送] 发送结束标志: {\"is_speaking\": false}",
            "[2025-01-14 15:12:13][等待] 等待服务器处理...",
            "[2025-01-14 15:12:14][接收] 等待服务器消息...",
            "识别文本(tv-report-1): 这是测试识别结果",
            "[2025-01-14 15:12:15][完成] 离线识别完成",
            "[2025-01-14 15:12:16][完成] 音频处理流程完成"
        ]
        
        # 模拟时间戳检测
        upload_start_time = None
        upload_end_time = None
        transcribe_start_time = None
        transcribe_end_time = None
        
        for line in test_lines:
            # 检测上传开始
            if "发送初始化消息:" in line and upload_start_time is None:
                upload_start_time = time.time()
                logging.info(f"✓ 检测到上传开始: {line[:50]}...")
            
            # 检测上传结束
            if ("上传进度: 100%" in line or "发送结束标志:" in line) and upload_end_time is None:
                upload_end_time = time.time()
                logging.info(f"✓ 检测到上传结束: {line[:50]}...")
            
            # 检测转写开始
            if ("等待服务器处理..." in line or "等待服务器消息..." in line) and transcribe_start_time is None:
                transcribe_start_time = time.time()
                logging.info(f"✓ 检测到转写开始: {line[:50]}...")
            
            # 检测转写结束
            if ("识别文本(" in line or "离线识别完成" in line or "音频处理流程完成" in line) and transcribe_end_time is None:
                transcribe_end_time = time.time()
                logging.info(f"✓ 检测到转写结束: {line[:50]}...")
        
        # 检查是否都检测到了
        missing = []
        if upload_start_time is None: missing.append("上传开始时间")
        if upload_end_time is None: missing.append("上传结束时间")
        if transcribe_start_time is None: missing.append("转写开始时间")
        if transcribe_end_time is None: missing.append("转写结束时间")
        
        if missing:
            logging.error(f"✗ 时间戳检测失败，缺失: {', '.join(missing)}")
            return False
        else:
            logging.info("✓ 所有时间戳都能正确检测")
            return True
            
    except Exception as e:
        logging.error(f"✗ 时间戳检测逻辑测试异常: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    logging.info("开始速度测试修复验证...")
    logging.info("=" * 50)
    
    tests = [
        ("GUI客户端导入测试", test_gui_client_import),
        ("simple_funasr_client语法测试", test_simple_client_syntax),
        ("日志格式化字符串测试", test_log_format_strings),
        ("时间戳检测逻辑测试", test_timestamp_detection_logic),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logging.info(f"\n运行测试: {test_name}")
        if test_func():
            passed += 1
        else:
            logging.error(f"测试失败: {test_name}")
    
    logging.info("=" * 50)
    logging.info(f"测试完成: {passed}/{total} 通过")
    
    if passed == total:
        logging.info("✓ 所有测试通过，速度测试修复验证成功！")
        return True
    else:
        logging.error("✗ 部分测试失败，需要进一步检查")
        return False

if __name__ == "__main__":
    setup_test_environment()
    success = run_all_tests()
    
    if success:
        print("\n🎉 速度测试修复验证通过！可以进行实际测试。")
        sys.exit(0)
    else:
        print("\n❌ 速度测试修复验证失败！需要进一步修复。")
        sys.exit(1) 
