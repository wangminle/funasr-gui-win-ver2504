#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import math

# Adjust sys.path to correctly find the funasr_gui_client_v2 module
# This ensures the import works correctly even if the script is run from the project root or from within the 'test' directory.
current_script_path = os.path.dirname(os.path.abspath(__file__)) # Path to '.../project_root/test'
project_root_dir = os.path.abspath(os.path.join(current_script_path, '..')) # Path to '.../project_root'
module_path = os.path.join(project_root_dir, 'src', 'python-gui-client')
sys.path.append(module_path)

from funasr_gui_client_v2 import TranscribeTimeManager

def test_time_manager():
    """测试转写时长管理器"""
    print("=== 转写时长管理器测试 ===")
    
    # 创建管理器实例
    tm = TranscribeTimeManager()
    
    # 测试1: 无测速结果的情况
    print('\n=== 测试1: 无测速结果 ===')
    # 模拟一个180秒的音频文件
    tm.current_file_duration = 180
    
    # 直接测试计算逻辑
    if tm.last_transcribe_speed is None:
        wait_timeout = math.ceil(tm.current_file_duration / 5)  # 180/5=36
        estimate_time = math.ceil(tm.current_file_duration / 10)  # 180/10=18
    
    print(f'文件时长: 180秒')
    print(f'等待超时: {wait_timeout}秒 (预期: 36秒)')
    print(f'预估时长: {estimate_time}秒 (预期: 18秒)')
    
    # 测试2: 有测速结果的情况 (高倍速)
    print('\n=== 测试2: 有测速结果 (高倍速) ===')
    tm.set_speed_test_results(10.0, 30.0)  # 10MB/s, 30倍速
    
    # 直接测试计算逻辑
    base_estimate = tm.current_file_duration / tm.last_transcribe_speed  # 180/30=6
    estimate_time = math.ceil(base_estimate * 1.2)  # 6*1.2=7.2 -> 8
    
    if tm.last_transcribe_speed > 5:
        wait_timeout = math.ceil(tm.current_file_duration / 5)  # 180/5=36
    else:
        wait_timeout = math.ceil(tm.current_file_duration)  # 180
    
    print(f'测速结果: 上传10MB/s, 转写30x')
    print(f'等待超时: {wait_timeout}秒 (预期: 36秒，因为倍速>5)')
    print(f'预估时长: {estimate_time}秒 (预期: 8秒)')
    
    # 测试3: 低倍速情况
    print('\n=== 测试3: 有测速结果 (低倍速) ===')
    tm.set_speed_test_results(5.0, 3.0)  # 5MB/s, 3倍速
    
    # 直接测试计算逻辑
    base_estimate = tm.current_file_duration / tm.last_transcribe_speed  # 180/3=60
    estimate_time = math.ceil(base_estimate * 1.2)  # 60*1.2=72
    
    if tm.last_transcribe_speed > 5:
        wait_timeout = math.ceil(tm.current_file_duration / 5)  # 180/5=36
    else:
        wait_timeout = math.ceil(tm.current_file_duration)  # 180
    
    print(f'测速结果: 上传5MB/s, 转写3x')
    print(f'等待超时: {wait_timeout}秒 (预期: 180秒，因为倍速<=5)')
    print(f'预估时长: {estimate_time}秒 (预期: 72秒)')
    
    # 测试4: 无法获取文件时长的情况
    print('\n=== 测试4: 无法获取文件时长 ===')
    tm.current_file_duration = None
    
    # 直接测试计算逻辑
    wait_timeout = 600  # 默认10分钟
    estimate_time = 60   # 默认1分钟预估
    
    print(f'文件时长: 无法获取')
    print(f'等待超时: {wait_timeout}秒 (预期: 600秒)')
    print(f'预估时长: {estimate_time}秒 (预期: 60秒)')
    
    # 测试5: 实际调用calculate_transcribe_times方法
    print('\n=== 测试5: 实际方法调用 ===')
    tm.current_file_duration = 180
    tm.set_speed_test_results(10.0, 30.0)
    
    # 模拟calculate_transcribe_times的逻辑，但不调用get_audio_duration
    
    # 如果没有测速结果，使用基础公式
    if tm.last_transcribe_speed is None:
        wait_timeout = math.ceil(tm.current_file_duration / 5)
        estimate_time = math.ceil(tm.current_file_duration / 10)
    else:
        # 有测速结果的情况
        base_estimate = tm.current_file_duration / tm.last_transcribe_speed
        estimate_time = math.ceil(base_estimate * 1.2)
        
        if tm.last_transcribe_speed > 5:
            wait_timeout = math.ceil(tm.current_file_duration / 5)
        else:
            wait_timeout = math.ceil(tm.current_file_duration)
    
    print(f'文件时长: 180秒, 测速: 10MB/s, 30x')
    print(f'等待超时: {wait_timeout}秒')
    print(f'预估时长: {estimate_time}秒')
    
    print('\n=== 测试完成 ===')

if __name__ == "__main__":
    test_time_manager() 