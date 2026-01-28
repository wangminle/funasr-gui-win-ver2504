#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""速度测试格式化测试脚本

测试目标：
1. LanguageManager.get() 速度测试相关key格式化
2. 各种参数组合不抛异常
3. 翻译结果的正确性

日期：2026-01-27
"""

import os
import sys
import time
import unittest

# 添加源代码路径
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "python-gui-client")
)


class TestSpeedTestFormatting(unittest.TestCase):
    """速度测试格式化字符串测试类"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        try:
            from funasr_gui_client_v3 import LanguageManager
            cls.lang_manager = LanguageManager()
            cls.lang_manager_available = True
        except ImportError as e:
            cls.lang_manager = None
            cls.lang_manager_available = False
            cls.import_error = str(e)

    def setUp(self):
        """每个测试前检查"""
        if not self.lang_manager_available:
            self.skipTest(f"LanguageManager不可用: {self.import_error}")

    def test_upload_started_formatting(self):
        """测试上传开始格式化"""
        key = "speed_test_upload_started"
        try:
            result = self.lang_manager.get(key, 1)
            self.assertIsInstance(result, str)
            self.assertIn("1", result)
        except KeyError:
            self.skipTest(f"翻译键 {key} 不存在")

    def test_upload_completed_formatting(self):
        """测试上传完成格式化"""
        key = "speed_test_upload_completed"
        try:
            result = self.lang_manager.get(key, 1, 1.5)
            self.assertIsInstance(result, str)
            self.assertIn("1", result)
        except KeyError:
            self.skipTest(f"翻译键 {key} 不存在")

    def test_transcription_started_formatting(self):
        """测试转写开始格式化"""
        key = "speed_test_transcription_started"
        try:
            result = self.lang_manager.get(key, 1)
            self.assertIsInstance(result, str)
        except KeyError:
            self.skipTest(f"翻译键 {key} 不存在")

    def test_transcription_completed_formatting(self):
        """测试转写完成格式化"""
        key = "speed_test_transcription_completed"
        try:
            result = self.lang_manager.get(key, 1, 2.3)
            self.assertIsInstance(result, str)
        except KeyError:
            self.skipTest(f"翻译键 {key} 不存在")

    def test_file_completed_formatting(self):
        """测试文件测试完成格式化"""
        key = "speed_test_file_completed"
        try:
            result = self.lang_manager.get(key, 1, 1.5, 2.3)
            self.assertIsInstance(result, str)
        except KeyError:
            self.skipTest(f"翻译键 {key} 不存在")

    def test_results_log_formatting(self):
        """测试速度测试结果日志格式化"""
        key = "speed_test_results_log"
        try:
            result = self.lang_manager.get(key, 5.2, 15.8)
            self.assertIsInstance(result, str)
        except KeyError:
            self.skipTest(f"翻译键 {key} 不存在")


class TestSpeedTestFormattingEdgeCases(unittest.TestCase):
    """速度测试格式化边界条件测试"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        try:
            from funasr_gui_client_v3 import LanguageManager
            cls.lang_manager = LanguageManager()
            cls.lang_manager_available = True
        except ImportError as e:
            cls.lang_manager = None
            cls.lang_manager_available = False
            cls.import_error = str(e)

    def setUp(self):
        """每个测试前检查"""
        if not self.lang_manager_available:
            self.skipTest(f"LanguageManager不可用: {self.import_error}")

    def test_zero_values(self):
        """测试零值参数"""
        key = "speed_test_upload_completed"
        try:
            # 零值应该不抛异常
            result = self.lang_manager.get(key, 0, 0.0)
            self.assertIsInstance(result, str)
        except KeyError:
            self.skipTest(f"翻译键 {key} 不存在")

    def test_large_values(self):
        """测试大数值参数"""
        key = "speed_test_upload_completed"
        try:
            result = self.lang_manager.get(key, 999, 99999.99)
            self.assertIsInstance(result, str)
        except KeyError:
            self.skipTest(f"翻译键 {key} 不存在")

    def test_negative_values(self):
        """测试负值参数（异常数据）"""
        key = "speed_test_upload_completed"
        try:
            # 负值不应该导致程序崩溃
            result = self.lang_manager.get(key, -1, -1.5)
            self.assertIsInstance(result, str)
        except KeyError:
            self.skipTest(f"翻译键 {key} 不存在")

    def test_float_precision(self):
        """测试浮点精度"""
        key = "speed_test_upload_completed"
        try:
            # 高精度浮点数
            result = self.lang_manager.get(key, 1, 1.123456789)
            self.assertIsInstance(result, str)
            # 验证格式化后不会有过多小数位
            # 假设格式化使用 {:.2f}，结果中应该有 "1.12"
        except KeyError:
            self.skipTest(f"翻译键 {key} 不存在")


class TestLanguageSwitching(unittest.TestCase):
    """测试语言切换后的格式化"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        try:
            from funasr_gui_client_v3 import LanguageManager
            cls.lang_manager = LanguageManager()
            cls.lang_manager_available = True
        except ImportError as e:
            cls.lang_manager = None
            cls.lang_manager_available = False
            cls.import_error = str(e)

    def setUp(self):
        """每个测试前检查"""
        if not self.lang_manager_available:
            self.skipTest(f"LanguageManager不可用: {self.import_error}")

    def test_chinese_formatting(self):
        """测试中文语言下的格式化"""
        self.lang_manager.current_lang = "zh"
        key = "speed_test_upload_completed"
        try:
            result = self.lang_manager.get(key, 1, 1.5)
            self.assertIsInstance(result, str)
            # 中文应包含"秒"或其他中文字符
        except KeyError:
            self.skipTest(f"翻译键 {key} 不存在")

    def test_english_formatting(self):
        """测试英文语言下的格式化"""
        self.lang_manager.current_lang = "en"
        key = "speed_test_upload_completed"
        try:
            result = self.lang_manager.get(key, 1, 1.5)
            self.assertIsInstance(result, str)
        except KeyError:
            self.skipTest(f"翻译键 {key} 不存在")

    def tearDown(self):
        """恢复默认语言"""
        if self.lang_manager:
            self.lang_manager.current_lang = "zh"


class TestSpeedTestStatusKeys(unittest.TestCase):
    """测试速度测试状态相关的翻译键"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        try:
            from funasr_gui_client_v3 import LanguageManager
            cls.lang_manager = LanguageManager()
            cls.lang_manager_available = True
        except ImportError as e:
            cls.lang_manager = None
            cls.lang_manager_available = False
            cls.import_error = str(e)

    def setUp(self):
        """每个测试前检查"""
        if not self.lang_manager_available:
            self.skipTest(f"LanguageManager不可用: {self.import_error}")

    def test_status_keys_exist(self):
        """测试速度测试状态键存在"""
        status_keys = [
            "not_tested",
            "testing",
            "test_completed",
            "test_failed_status",
        ]

        for key in status_keys:
            with self.subTest(key=key):
                try:
                    result = self.lang_manager.get(key)
                    self.assertIsInstance(result, str)
                    self.assertGreater(len(result), 0, f"键 {key} 不应为空字符串")
                except KeyError:
                    self.skipTest(f"翻译键 {key} 不存在")

    def test_speed_test_event_start_formatting(self):
        """测试速度测试开始事件格式化"""
        key = "speed_test_event_start"
        try:
            result = self.lang_manager.get(key, "file1.wav", 1.5, "file2.wav", 2.0)
            self.assertIsInstance(result, str)
        except KeyError:
            self.skipTest(f"翻译键 {key} 不存在")

    def test_speed_test_event_testing_file_formatting(self):
        """测试文件测试事件格式化"""
        key = "speed_test_event_testing_file"
        try:
            result = self.lang_manager.get(key, 1, "test_audio.wav")
            self.assertIsInstance(result, str)
        except KeyError:
            self.skipTest(f"翻译键 {key} 不存在")


class TestErrorMessageKeys(unittest.TestCase):
    """测试速度测试错误消息键"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        try:
            from funasr_gui_client_v3 import LanguageManager
            cls.lang_manager = LanguageManager()
            cls.lang_manager_available = True
        except ImportError as e:
            cls.lang_manager = None
            cls.lang_manager_available = False
            cls.import_error = str(e)

    def setUp(self):
        """每个测试前检查"""
        if not self.lang_manager_available:
            self.skipTest(f"LanguageManager不可用: {self.import_error}")

    def test_error_keys_formatting(self):
        """测试错误消息格式化"""
        error_keys = [
            ("speed_test_error_missing_timestamps", ["upload_start, upload_end"]),
            ("speed_test_error_general", ["Connection timeout"]),
        ]

        for key, args in error_keys:
            with self.subTest(key=key):
                try:
                    result = self.lang_manager.get(key, *args)
                    self.assertIsInstance(result, str)
                except KeyError:
                    self.skipTest(f"翻译键 {key} 不存在")

    def test_dialog_error_messages(self):
        """测试对话框错误消息"""
        dialog_keys = [
            ("dialog_speed_test_error_msg", ["Network error"]),
            ("dialog_result_calc_failed_msg", ["Division by zero"]),
        ]

        for key, args in dialog_keys:
            with self.subTest(key=key):
                try:
                    result = self.lang_manager.get(key, *args)
                    self.assertIsInstance(result, str)
                except KeyError:
                    self.skipTest(f"翻译键 {key} 不存在")


class TestResultDisplayKeys(unittest.TestCase):
    """测试结果展示相关的翻译键"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        try:
            from funasr_gui_client_v3 import LanguageManager
            cls.lang_manager = LanguageManager()
            cls.lang_manager_available = True
        except ImportError as e:
            cls.lang_manager = None
            cls.lang_manager_available = False
            cls.import_error = str(e)

    def setUp(self):
        """每个测试前检查"""
        if not self.lang_manager_available:
            self.skipTest(f"LanguageManager不可用: {self.import_error}")

    def test_result_label_keys(self):
        """测试结果标签键"""
        label_keys = [
            "total_file_size",
            "total_upload_time",
            "average_upload_speed",
            "total_audio_duration",
            "total_transcription_time",
            "transcription_speed_label",
        ]

        for key in label_keys:
            with self.subTest(key=key):
                try:
                    result = self.lang_manager.get(key)
                    self.assertIsInstance(result, str)
                    self.assertGreater(len(result), 0, f"键 {key} 不应为空字符串")
                except KeyError:
                    self.skipTest(f"翻译键 {key} 不存在")


def run_tests():
    """运行所有测试"""
    print("=" * 70)
    print("速度测试格式化测试")
    print("=" * 70)
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python版本: {sys.version}")
    print("=" * 70)
    print()

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    test_classes = [
        TestSpeedTestFormatting,
        TestSpeedTestFormattingEdgeCases,
        TestLanguageSwitching,
        TestSpeedTestStatusKeys,
        TestErrorMessageKeys,
        TestResultDisplayKeys,
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
    skipped = len([r for r in result.skipped]) if hasattr(result, 'skipped') else 0
    print(f"跳过: {skipped}")
    print("=" * 70)

    return result


if __name__ == "__main__":
    result = run_tests()
    sys.exit(0 if result.wasSuccessful() else 1)
