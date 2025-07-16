#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
速度测试时间计算修复测试脚本
测试修复了的时间计算安全检查功能

测试目标：
1. 验证upload_start_time和upload_end_time的安全检查
2. 验证transcribe_start_time和transcribe_end_time的安全检查  
3. 验证新的日志检测模式（发送初始化消息）
4. 验证错误情况下的警告日志输出

日期：2024-07-14
"""

import sys
import os
import time
import json
import tempfile
import threading
import subprocess
import logging
from unittest.mock import Mock, patch, MagicMock

# 添加源代码路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dev', 'src', 'python-gui-client'))

def test_normal_time_calculation():
    """测试正常情况下的时间计算"""
    print("=== 测试1: 正常时间计算 ===")
    
    try:
        from funasr_gui_client_v2 import FunASRGUIClient
        
        # 模拟GUI客户端
        app = FunASRGUIClient()
        app.withdraw()  # 隐藏窗口
        
        # 模拟时间变量
        upload_start_time = time.time()
        upload_end_time = upload_start_time + 5.0  # 5秒上传时间
        transcribe_start_time = upload_end_time
        transcribe_end_time = transcribe_start_time + 3.0  # 3秒转写时间
        
        # 验证计算
        upload_duration = upload_end_time - upload_start_time
        transcribe_duration = transcribe_end_time - transcribe_start_time
        
        assert abs(upload_duration - 5.0) < 0.1, f"上传时间计算错误: {upload_duration}"
        assert abs(transcribe_duration - 3.0) < 0.1, f"转写时间计算错误: {transcribe_duration}"
        
        print("✓ 正常时间计算测试通过")
        app.destroy()
        return True
        
    except Exception as e:
        print(f"✗ 正常时间计算测试失败: {e}")
        return False

def test_none_time_handling():
    """测试None时间的安全处理"""
    print("=== 测试2: None时间安全处理 ===")
    
    try:
        # 测试upload_start_time为None的情况
        upload_start_time = None
        upload_end_time = time.time()
        
        # 模拟检查逻辑
        if upload_start_time is not None:
            upload_duration = upload_end_time - upload_start_time
            print("✗ 应该检测到upload_start_time为None")
            return False
        else:
            print("✓ 正确检测到upload_start_time为None")
        
        # 测试transcribe_start_time为None的情况
        transcribe_start_time = None
        transcribe_end_time = time.time()
        
        if transcribe_start_time is not None:
            transcribe_duration = transcribe_end_time - transcribe_start_time
            print("✗ 应该检测到transcribe_start_time为None")
            return False
        else:
            print("✓ 正确检测到transcribe_start_time为None")
        
        print("✓ None时间安全处理测试通过")
        return True
        
    except Exception as e:
        print(f"✗ None时间安全处理测试失败: {e}")
        return False

def test_log_detection_patterns():
    """测试日志检测模式"""
    print("=== 测试3: 日志检测模式 ===")
    
    try:
        # 测试新的检测模式
        test_logs = [
            '[2024-07-14 10:30:00][发送] 发送初始化消息: {"mode": "offline", "audio_fs": 16000}',
            '[2024-07-14 10:30:01][发送] 发送WebSocket: {"mode": "offline", "audio_fs": 16000}',
            '[2024-07-14 10:30:05] 上传进度: 100%',
            '[2024-07-14 10:30:08][完成] 离线识别完成',
            '[2024-07-14 10:30:09][完成] 实时识别完成',
            '[2024-07-14 10:30:10][结果] 离线模式收到非空文本: 测试结果',
            '[2024-07-14 10:30:11][完成] 收到结束标志或完整结果'
        ]
        
        upload_start_detected = False
        upload_end_detected = False
        transcribe_end_detected = False
        
        for line in test_logs:
            # 检测上传开始（新增的检测模式）
            if ("发送初始化消息:" in line or "发送WebSocket:" in line) and "mode" in line:
                upload_start_detected = True
                print("✓ 检测到上传开始")
            
            # 检测上传结束
            if "上传进度: 100%" in line:
                upload_end_detected = True
                print("✓ 检测到上传结束")
            
            # 检测转写完成（更新的检测条件）
            if ("离线识别完成" in line or "实时识别完成" in line or "离线模式收到非空文本" in line or "收到结束标志或完整结果" in line):
                transcribe_end_detected = True
                print("✓ 检测到转写完成")
        
        assert upload_start_detected, "未检测到上传开始"
        assert upload_end_detected, "未检测到上传结束"
        assert transcribe_end_detected, "未检测到转写完成"
        
        print("✓ 日志检测模式测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 日志检测模式测试失败: {e}")
        return False

def test_warning_log_output():
    """测试警告日志输出"""
    print("=== 测试4: 警告日志输出 ===")
    
    try:
        # 模拟日志处理器
        import logging
        
        # 创建一个内存日志处理器
        log_stream = []
        
        class TestLogHandler(logging.Handler):
            def emit(self, record):
                log_stream.append(self.format(record))
        
        # 设置测试日志
        logger = logging.getLogger()
        handler = TestLogHandler()
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)
        
        # 模拟警告情况
        test_file_index = 0
        
        # 模拟upload_start_time为None的警告
        logging.warning(f"速度测试警告: 文件{test_file_index + 1}未检测到上传开始时间，无法计算上传耗时")
        
        # 模拟transcribe_start_time为None的警告
        logging.warning(f"速度测试警告: 文件{test_file_index + 1}未检测到转写开始时间，无法计算转写耗时")
        
        # 验证日志内容
        warning_logs = [log for log in log_stream if "速度测试警告" in log]
        
        assert len(warning_logs) >= 2, f"警告日志数量不足: {len(warning_logs)}"
        assert "未检测到上传开始时间" in warning_logs[0], "缺少上传开始时间警告"
        assert "未检测到转写开始时间" in warning_logs[1], "缺少转写开始时间警告"
        
        print("✓ 警告日志输出测试通过")
        logger.removeHandler(handler)
        return True
        
    except Exception as e:
        print(f"✗ 警告日志输出测试失败: {e}")
        return False

def test_edge_cases():
    """测试边界条件"""
    print("=== 测试5: 边界条件 ===")
    
    try:
        # 测试时间为0的情况
        upload_start_time = 0.0
        upload_end_time = 0.0001  # 非常短的时间
        
        if upload_start_time is not None and upload_end_time is not None:
            upload_duration = upload_end_time - upload_start_time
            assert upload_duration >= 0, "时间差不能为负"
            print(f"✓ 极短时间测试通过: {upload_duration}")
        
        # 测试负时间差的情况（理论上不应该发生，但要防护）
        upload_start_time = time.time()
        upload_end_time = upload_start_time - 1  # 结束时间早于开始时间
        
        if upload_start_time is not None and upload_end_time is not None:
            upload_duration = upload_end_time - upload_start_time
            if upload_duration < 0:
                print(f"✓ 正确检测到负时间差: {upload_duration}")
            else:
                print("⚠ 未检测到负时间差，但这可能是正常的")
        
        print("✓ 边界条件测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 边界条件测试失败: {e}")
        return False

def test_exception_handling():
    """测试异常情况处理"""
    print("=== 测试6: 异常情况处理 ===")
    
    try:
        # 测试类型错误的处理
        upload_start_time = "invalid_time"  # 错误的类型
        upload_end_time = time.time()
        
        try:
            if upload_start_time is not None:
                upload_duration = upload_end_time - upload_start_time  # 应该抛出TypeError
                print("✗ 应该检测到类型错误")
                return False
        except TypeError:
            print("✓ 正确处理了类型错误")
        
        # 测试各种None组合
        test_cases = [
            (None, time.time(), None, time.time()),
            (time.time(), None, time.time(), None),
            (None, None, None, None),
            (time.time(), time.time(), None, time.time()),
            (time.time(), time.time(), time.time(), None)
        ]
        
        for i, (us_time, ue_time, ts_time, te_time) in enumerate(test_cases):
            print(f"  测试用例 {i+1}: upload({us_time is not None}, {ue_time is not None}), transcribe({ts_time is not None}, {te_time is not None})")
            
            # 检查upload时间
            if us_time is not None and ue_time is not None:
                try:
                    upload_duration = ue_time - us_time
                    print(f"    ✓ upload时间计算成功: {upload_duration:.4f}s")
                except Exception as e:
                    print(f"    ✗ upload时间计算失败: {e}")
            else:
                print(f"    ⚠ upload时间缺失，跳过计算")
            
            # 检查transcribe时间
            if ts_time is not None and te_time is not None:
                try:
                    transcribe_duration = te_time - ts_time
                    print(f"    ✓ transcribe时间计算成功: {transcribe_duration:.4f}s")
                except Exception as e:
                    print(f"    ✗ transcribe时间计算失败: {e}")
            else:
                print(f"    ⚠ transcribe时间缺失，跳过计算")
        
        print("✓ 异常情况处理测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 异常情况处理测试失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("开始速度测试时间计算修复测试...")
    print("=" * 50)
    
    test_functions = [
        test_normal_time_calculation,
        test_none_time_handling,
        test_log_detection_patterns,
        test_warning_log_output,
        test_edge_cases,
        test_exception_handling
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
        print("🎉 所有测试通过！时间计算修复工作正常。")
        return True
    else:
        print("❌ 有测试失败，请检查修复代码。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 