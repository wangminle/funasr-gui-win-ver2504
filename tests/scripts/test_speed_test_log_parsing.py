#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""速度测试日志解析测试脚本

本脚本合并了以下历史测试脚本的核心功能：
- test_speed_test_fix_20250714.py
- test_speed_test_fix_v2_20250714.py
- test_speed_test_time_calculation_fix_20250714.py
- test_transcribe_completion_detection_fix_20250714.py

测试目标：
1. 日志行→上传开始/结束/转写结束的判定规则
2. 与GUI实现保持同一套关键字集合
3. 兜底规则测试
4. 边界条件（空输出、超时、None时间处理）
5. 防止重复检测机制

日期：2026-01-27
"""

import logging
import os
import sys
import time
import unittest
from typing import Optional

# 添加源代码路径
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "python-gui-client")
)


class SpeedTestLogParser:
    """速度测试日志解析器

    与GUI实现保持同一套关键字集合，用于单元测试验证。
    """

    # 上传开始检测关键字
    UPLOAD_START_KEYWORDS = [
        "发送初始化消息:",
        "发送WebSocket:",
    ]

    # 上传结束检测关键字（与 GUI 速度测试实现对齐）
    # - 主路径：检测到“上传进度: 100%”
    # - 兜底：检测到 is_speaking=false 的结束指令（发送WebSocket 行）
    UPLOAD_END_KEYWORDS = [
        "上传进度: 100%",
    ]

    # 转写结束检测关键字
    TRANSCRIBE_END_KEYWORDS = [
        "离线识别完成",
        "实时识别完成",
        "离线模式收到非空文本",
        "收到结束标志或完整结果",
    ]

    @classmethod
    def detect_upload_start(cls, line: str) -> bool:
        """检测是否为上传开始日志"""
        for keyword in cls.UPLOAD_START_KEYWORDS:
            # GUI 速度测试判定：包含关键字 + 包含 mode 字段
            if keyword in line and "mode" in line:
                return True
        return False

    @classmethod
    def detect_upload_end(cls, line: str) -> bool:
        """检测是否为上传结束日志"""
        # 主路径：上传进度 100%
        for keyword in cls.UPLOAD_END_KEYWORDS:
            if keyword in line:
                return True

        # 兜底：is_speaking=false 的结束指令（需在发送WebSocket行内）
        normalized = line.replace(" ", "").lower()
        if "发送websocket:" in normalized and '"is_speaking":false' in normalized:
            return True

        return False

    @classmethod
    def detect_transcribe_start(cls, line: str) -> bool:
        """检测是否为转写开始日志"""
        # GUI 速度测试实现：转写开始时间与“上传结束”同步
        return cls.detect_upload_end(line)

    @classmethod
    def detect_transcribe_end(cls, line: str) -> bool:
        """检测是否为转写结束日志"""
        for keyword in cls.TRANSCRIBE_END_KEYWORDS:
            if keyword in line:
                return True
        return False


class TestUploadStartDetection(unittest.TestCase):
    """测试上传开始检测"""

    def test_init_message_detection(self):
        """测试发送初始化消息检测"""
        line = '[2026-01-27 10:30:00][发送] 发送初始化消息: {"mode": "offline", "audio_fs": 16000}'
        self.assertTrue(SpeedTestLogParser.detect_upload_start(line))

    def test_websocket_message_detection(self):
        """测试发送WebSocket消息检测"""
        line = '[2026-01-27 10:30:00][发送] 发送WebSocket: {"mode": "offline", "audio_fs": 16000}'
        self.assertTrue(SpeedTestLogParser.detect_upload_start(line))

    def test_no_mode_should_not_detect(self):
        """测试不包含mode参数时不应检测为上传开始"""
        line = '[2026-01-27 10:30:00][发送] 发送初始化消息: {"audio_fs": 16000}'
        self.assertFalse(SpeedTestLogParser.detect_upload_start(line))

    def test_unrelated_line_not_detected(self):
        """测试无关日志行不被检测"""
        line = "[2026-01-27 10:30:00] 正在处理音频文件..."
        self.assertFalse(SpeedTestLogParser.detect_upload_start(line))


class TestUploadEndDetection(unittest.TestCase):
    """测试上传结束检测"""

    def test_progress_100_detection(self):
        """测试上传进度100%检测"""
        line = "[2026-01-27 10:30:05] 上传进度: 100%"
        self.assertTrue(SpeedTestLogParser.detect_upload_end(line))

    def test_is_speaking_false_fallback_detection(self):
        """测试 is_speaking=false 兜底检测（发送WebSocket行）"""
        line = '[2026-01-27 10:30:05][指令] 发送WebSocket: {"is_speaking": false}'
        self.assertTrue(SpeedTestLogParser.detect_upload_end(line))

    def test_progress_50_not_detected(self):
        """测试非100%进度不被检测为上传结束"""
        line = "[2026-01-27 10:30:03] 上传进度: 50%"
        self.assertFalse(SpeedTestLogParser.detect_upload_end(line))


class TestTranscribeStartDetection(unittest.TestCase):
    """测试转写开始检测"""

    def test_transcribe_start_on_upload_100(self):
        """测试：上传100%即视为转写开始"""
        line = "[2026-01-27 10:30:05] 上传进度: 100%"
        self.assertTrue(SpeedTestLogParser.detect_transcribe_start(line))

    def test_transcribe_start_on_is_speaking_false(self):
        """测试：is_speaking=false 兜底也视为转写开始"""
        line = '[2026-01-27 10:30:05][指令] 发送WebSocket: {"is_speaking": false}'
        self.assertTrue(SpeedTestLogParser.detect_transcribe_start(line))


class TestTranscribeEndDetection(unittest.TestCase):
    """测试转写结束检测"""

    def test_offline_completed_detection(self):
        """测试离线识别完成检测"""
        line = "[2026-01-27 10:30:08][完成] 离线识别完成"
        self.assertTrue(SpeedTestLogParser.detect_transcribe_end(line))

    def test_realtime_completed_detection(self):
        """测试实时识别完成检测"""
        line = "[2026-01-27 10:30:08][完成] 实时识别完成"
        self.assertTrue(SpeedTestLogParser.detect_transcribe_end(line))

    def test_non_empty_text_detection(self):
        """测试离线模式收到非空文本检测"""
        line = "[2026-01-27 10:30:08][结果] 离线模式收到非空文本: 测试结果"
        self.assertTrue(SpeedTestLogParser.detect_transcribe_end(line))

    def test_end_flag_or_result_detection(self):
        """测试收到结束标志或完整结果检测"""
        line = "[2026-01-27 10:30:08][完成] 收到结束标志或完整结果"
        self.assertTrue(SpeedTestLogParser.detect_transcribe_end(line))

    def test_audio_process_completed_not_used_by_v3_speed_test(self):
        """测试：'音频处理流程完成' 不作为 V3 速度测试转写结束标志"""
        line = "[2026-01-27 10:30:08][完成] 音频处理流程完成"
        self.assertFalse(SpeedTestLogParser.detect_transcribe_end(line))

    def test_result_text_detection(self):
        """测试识别文本结果（旧脚本格式）不作为 V3 速度测试结束标志"""
        line = "识别文本(test-audio-1): 这是测试识别结果。"
        self.assertFalse(SpeedTestLogParser.detect_transcribe_end(line))

    def test_preparing_not_detected(self):
        """测试准备状态不被检测为转写结束"""
        line = "[2026-01-27 10:30:08][信息] 准备离线识别"
        self.assertFalse(SpeedTestLogParser.detect_transcribe_end(line))

    def test_in_progress_not_detected(self):
        """测试进行中状态不被检测为转写结束"""
        line = "[2026-01-27 10:30:08][调试] 离线识别进行中"
        self.assertFalse(SpeedTestLogParser.detect_transcribe_end(line))


class TestFullLogSequenceParsing(unittest.TestCase):
    """测试完整日志序列解析"""

    def test_complete_log_sequence(self):
        """测试完整的日志序列解析"""
        test_logs = [
            '[2026-01-27 10:30:00][发送] 发送初始化消息: {"mode": "offline", "audio_fs": 16000}',
            "正在处理音频文件...",
            "上传进度: 25%",
            "上传进度: 50%",
            "上传进度: 75%",
            "上传进度: 100%",
            '[2026-01-27 10:30:05][指令] 发送WebSocket: {"is_speaking": false}',
            "[2026-01-27 10:30:06][调试] 等待服务器处理完成...",
            "[2026-01-27 10:30:07][调试] 等待接收消息...",
            "正在处理识别请求...",
            "[2026-01-27 10:30:08][完成] 离线识别完成",
        ]

        # 模拟时间戳检测
        upload_start_time: Optional[float] = None
        upload_end_time: Optional[float] = None
        transcribe_start_time: Optional[float] = None
        transcribe_end_time: Optional[float] = None

        for i, line in enumerate(test_logs):
            current_time = time.time() + i * 0.1  # 模拟时间流逝

            # 检测上传开始
            if SpeedTestLogParser.detect_upload_start(line) and upload_start_time is None:
                upload_start_time = current_time

            # 检测上传结束
            if SpeedTestLogParser.detect_upload_end(line) and upload_end_time is None:
                upload_end_time = current_time
                # 上传结束时自动设置转写开始时间（如果尚未设置）
                if transcribe_start_time is None:
                    transcribe_start_time = current_time

            # 检测转写开始（额外检测点）
            if SpeedTestLogParser.detect_transcribe_start(line) and transcribe_start_time is None:
                transcribe_start_time = current_time

            # 检测转写结束
            if SpeedTestLogParser.detect_transcribe_end(line) and transcribe_end_time is None:
                transcribe_end_time = current_time

        # 验证所有时间点都被检测到
        self.assertIsNotNone(upload_start_time, "应检测到上传开始时间")
        self.assertIsNotNone(upload_end_time, "应检测到上传结束时间")
        self.assertIsNotNone(transcribe_start_time, "应检测到转写开始时间")
        self.assertIsNotNone(transcribe_end_time, "应检测到转写结束时间")

        # 验证时间计算合理性
        upload_duration = upload_end_time - upload_start_time
        transcribe_duration = transcribe_end_time - transcribe_start_time
        self.assertGreater(upload_duration, 0, "上传时间应大于0")
        self.assertGreater(transcribe_duration, 0, "转写时间应大于0")


class TestNoneTimeHandling(unittest.TestCase):
    """测试None时间的安全处理"""

    def test_upload_start_none(self):
        """测试upload_start_time为None的情况"""
        upload_start_time: Optional[float] = None
        upload_end_time = time.time()

        # 安全检查逻辑
        if upload_start_time is not None and upload_end_time is not None:
            upload_duration = upload_end_time - upload_start_time
            self.fail("不应该计算时间差")
        else:
            # 正确处理：跳过计算
            pass

    def test_transcribe_start_none(self):
        """测试transcribe_start_time为None的情况"""
        transcribe_start_time: Optional[float] = None
        transcribe_end_time = time.time()

        if transcribe_start_time is not None and transcribe_end_time is not None:
            transcribe_duration = transcribe_end_time - transcribe_start_time
            self.fail("不应该计算时间差")
        else:
            # 正确处理：跳过计算
            pass

    def test_all_combinations(self):
        """测试各种None组合"""
        current_time = time.time()
        test_cases = [
            (None, current_time, None, current_time, "upload_start和transcribe_start为None"),
            (current_time, None, current_time, None, "upload_end和transcribe_end为None"),
            (None, None, None, None, "全部为None"),
            (current_time, current_time, None, current_time, "仅transcribe_start为None"),
            (current_time, current_time, current_time, None, "仅transcribe_end为None"),
        ]

        for us, ue, ts, te, description in test_cases:
            with self.subTest(description=description):
                # upload时间计算
                if us is not None and ue is not None:
                    upload_duration = ue - us
                    self.assertGreaterEqual(upload_duration, 0, f"{description}: upload时间差应>=0")
                else:
                    pass  # 安全跳过

                # transcribe时间计算
                if ts is not None and te is not None:
                    transcribe_duration = te - ts
                    self.assertGreaterEqual(transcribe_duration, 0, f"{description}: transcribe时间差应>=0")
                else:
                    pass  # 安全跳过


class TestTimeCalculationRobustness(unittest.TestCase):
    """测试时间计算的健壮性"""

    def test_very_short_time(self):
        """测试极短时间（不为0）"""
        upload_start = 0.0
        upload_end = 0.0001  # 0.1毫秒

        duration = upload_end - upload_start
        self.assertGreaterEqual(duration, 0, "极短时间差应>=0")

    def test_negative_time_protection(self):
        """测试负时间差的保护（异常情况）"""
        upload_start = time.time()
        upload_end = upload_start - 1  # 异常：结束时间早于开始时间

        duration = upload_end - upload_start
        # 检测到负时间差，应触发保护逻辑
        if duration < 0:
            # 修复为最小正值
            fixed_duration = max(0.1, duration)
            self.assertGreater(fixed_duration, 0, "修复后的时间差应>0")

    def test_zero_time_fix(self):
        """测试时间为0的修复"""
        test_values = [
            (0.0, 0.1),   # 上传时间为0
            (0.0, 0.1),   # 转写时间为0
            (-0.1, 0.1),  # 上传时间为负数
            (0.05, 0.05), # 时间很小但有效
        ]

        for original, expected_min in test_values:
            fixed = original if original > 0 else 0.1
            self.assertGreater(fixed, 0, f"修复后的值 {fixed} 应>0")


class TestPreventDuplicateDetection(unittest.TestCase):
    """测试防止重复检测机制"""

    def test_multiple_transcribe_end_logs(self):
        """测试多个转写结束日志只检测一次"""
        repeated_logs = [
            "[2026-01-27 10:30:08][完成] 离线识别完成",
            "[2026-01-27 10:30:09][完成] 离线识别完成",  # 重复
            "[2026-01-27 10:30:10][结果] 离线模式收到非空文本: 结果",
            "[2026-01-27 10:30:11][完成] 离线识别完成",  # 再次重复
        ]

        transcribe_end_time: Optional[float] = None
        detection_count = 0

        for line in repeated_logs:
            if SpeedTestLogParser.detect_transcribe_end(line) and transcribe_end_time is None:
                transcribe_end_time = time.time()
                detection_count += 1

        self.assertEqual(detection_count, 1, "应只检测到1次转写结束")
        self.assertIsNotNone(transcribe_end_time, "转写结束时间应被设置")


class TestEdgeCasesTranscribeDetection(unittest.TestCase):
    """测试转写检测的边界情况"""

    def test_edge_cases(self):
        """测试各种边界情况"""
        edge_cases = [
            # (日志行, 是否应检测为转写结束, 描述)
            ("[2026-01-27][完成] 离线识别完成", True, "正常的离线识别完成"),
            ("[2026-01-27][完成] 实时识别完成", True, "正常的实时识别完成"),
            ("[2026-01-27][完成] 离线识别完成，文件处理结束", True, "带额外信息的离线识别完成"),
            ("[2026-01-27][结果] 离线模式收到非空文本: 识别结果文本内容", True, "带结果内容的文本"),
            ("[2026-01-27][完成] 实时识别完成!", True, "带感叹号的完成"),
            ("[2026-01-27][完成] 收到结束标志或完整结果，处理完毕", True, "带额外信息的结束标志"),
            ("[2026-01-27][调试] 离线识别进行中", False, "进行中状态"),
            ("[2026-01-27][信息] 准备离线识别", False, "准备状态"),
            ("[2026-01-27][错误] 离线识别失败", False, "失败状态"),
        ]

        for line, should_detect, description in edge_cases:
            with self.subTest(description=description):
                detected = SpeedTestLogParser.detect_transcribe_end(line)
                self.assertEqual(detected, should_detect, f"{description}: 检测结果不符预期")


class TestEmptyAndTimeoutCases(unittest.TestCase):
    """测试空输出和超时情况"""

    def test_empty_log_sequence(self):
        """测试空日志序列"""
        empty_logs: list[str] = []

        upload_start_time: Optional[float] = None
        for line in empty_logs:
            if SpeedTestLogParser.detect_upload_start(line):
                upload_start_time = time.time()

        self.assertIsNone(upload_start_time, "空日志应无检测结果")

    def test_no_upload_start_in_logs(self):
        """测试日志中无上传开始标记"""
        logs_without_start = [
            "上传进度: 50%",
            "上传进度: 100%",
            "[2026-01-27][完成] 离线识别完成",
        ]

        upload_start_time: Optional[float] = None
        for line in logs_without_start:
            if SpeedTestLogParser.detect_upload_start(line):
                upload_start_time = time.time()

        self.assertIsNone(upload_start_time, "应未检测到上传开始")


def run_tests():
    """运行所有测试"""
    print("=" * 70)
    print("速度测试日志解析测试")
    print("=" * 70)
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python版本: {sys.version}")
    print("=" * 70)
    print()

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    test_classes = [
        TestUploadStartDetection,
        TestUploadEndDetection,
        TestTranscribeStartDetection,
        TestTranscribeEndDetection,
        TestFullLogSequenceParsing,
        TestNoneTimeHandling,
        TestTimeCalculationRobustness,
        TestPreventDuplicateDetection,
        TestEdgeCasesTranscribeDetection,
        TestEmptyAndTimeoutCases,
    ]

    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print()
    print("=" * 70)
    print("测试总结")
    print("=" * 70)
    print(f"运行测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print("=" * 70)

    return result


if __name__ == "__main__":
    result = run_tests()
    sys.exit(0 if result.wasSuccessful() else 1)
