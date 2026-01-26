#!/usr/bin/env python3
"""
测试脚本：验证StatusManager的两个关键修复

测试目标：
1. P0修复：验证临时状态不会覆盖持久状态
2. P1修复：验证连接测试线程中的UI更新使用主线程调度

测试场景：
1. 临时状态恢复：设置持久状态 -> 设置临时状态 -> 验证恢复到持久状态
2. 线程安全：检查_async_test_connection中所有UI更新都使用after()包装
3. 边界情况：临时状态持续时间为0时的行为

创建日期：2025-10-23
"""

import os
import sys
import time
import re
import unittest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import tkinter as tk
from tkinter import ttk

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src" / "python-gui-client"
sys.path.insert(0, str(src_path))


class TestStatusManagerPersistentStateFix(unittest.TestCase):
    """测试临时状态不覆盖持久状态的修复"""

    def setUp(self):
        """测试前准备"""
        # 使用Mock对象代替真实的Tkinter组件（避免在无头环境中出现问题）
        self._current_status = ""
        
        def set_status(value):
            self._current_status = value
        
        def get_status():
            return self._current_status
        
        self.status_var = Mock()
        self.status_var.get = Mock(side_effect=get_status)
        self.status_var.set = Mock(side_effect=set_status)
        
        self.status_bar = Mock()
        self.status_bar.config = Mock()
        # after不立即执行回调，只是返回一个timer ID
        self._timer_id_counter = 0
        def mock_after(delay, func):
            self._timer_id_counter += 1
            return self._timer_id_counter
        self.status_bar.after = Mock(side_effect=mock_after)
        self.status_bar.after_cancel = Mock()

        # 创建模拟的LanguageManager
        self.lang_manager = Mock()
        self.lang_manager.get = Mock(side_effect=lambda key, *args: f"[{key}]")

        # 延迟导入StatusManager类
        from funasr_gui_client_v3 import StatusManager

        # 创建StatusManager实例
        self.status_manager = StatusManager(
            self.status_var, self.status_bar, self.lang_manager
        )

        print(f"\n[setUp] StatusManager实例创建成功")

    def tearDown(self):
        """测试后清理"""
        print(f"[tearDown] 清理完成")

    def test_01_persistent_status_not_overwritten_by_temp(self):
        """
        测试1：临时状态不应覆盖持久状态
        
        这是P0优先级的核心修复测试
        """
        print("\n" + "=" * 70)
        print("测试1：临时状态不应覆盖持久状态（P0修复）")
        print("=" * 70)

        # 步骤1：设置一个持久状态
        self.status_manager.set_success("准备就绪", temp_duration=0)
        print(f"[步骤1] 设置持久状态：'准备就绪'")
        print(f"  - 当前状态文本：{self.status_var.get()}")
        print(f"  - 持久状态记录：{self.status_manager.persistent_status}")

        # 验证持久状态被保存
        self.assertEqual(
            self.status_manager.persistent_status, "准备就绪", "持久状态应该被保存"
        )
        self.assertEqual(
            self.status_manager.persistent_status_type,
            self.status_manager.STATUS_SUCCESS,
            "持久状态类型应该是SUCCESS",
        )

        # 步骤2：设置一个临时状态（3秒）
        temp_message = "文件复制成功"
        self.status_manager.set_success(temp_message, temp_duration=3)
        print(f"\n[步骤2] 设置临时状态：'{temp_message}' (3秒)")
        print(f"  - 当前状态文本：{self.status_var.get()}")
        print(f"  - 持久状态记录：{self.status_manager.persistent_status}")

        # 验证关键修复：临时状态不应覆盖持久状态
        self.assertEqual(
            self.status_manager.persistent_status,
            "准备就绪",
            "临时状态不应该覆盖持久状态（这是修复的核心）",
        )
        
        # 验证当前显示的是临时状态
        self.assertEqual(self.status_var.get(), temp_message, "当前显示的应该是临时状态文本")

        # 步骤3：手动触发恢复（模拟定时器触发）
        print(f"\n[步骤3] 手动触发状态恢复")
        self.status_manager._restore_persistent_status()
        print(f"  - 恢复后状态文本：{self.status_var.get()}")
        print(f"  - 持久状态记录：{self.status_manager.persistent_status}")

        # 验证恢复到正确的持久状态
        self.assertEqual(
            self.status_var.get(), "准备就绪", "应该恢复到之前的持久状态"
        )

        print("\n✓ 测试通过：临时状态不会覆盖持久状态")

    def test_02_temp_duration_zero_updates_persistent(self):
        """
        测试2：temp_duration=0时应该更新持久状态
        
        验证边界条件
        """
        print("\n" + "=" * 70)
        print("测试2：temp_duration=0时应该更新持久状态")
        print("=" * 70)

        # 设置第一个持久状态
        self.status_manager.set_info("状态1", temp_duration=0)
        print(f"[步骤1] 设置状态1：持久状态 = {self.status_manager.persistent_status}")

        # 设置第二个持久状态（temp_duration=0）
        self.status_manager.set_info("状态2", temp_duration=0)
        print(f"[步骤2] 设置状态2：持久状态 = {self.status_manager.persistent_status}")

        # 验证持久状态被更新
        self.assertEqual(
            self.status_manager.persistent_status,
            "状态2",
            "temp_duration=0时应该更新持久状态",
        )

        print("✓ 测试通过：temp_duration=0时正确更新持久状态")

    def test_03_multiple_temp_states_sequence(self):
        """
        测试3：连续多个临时状态的处理
        
        验证复杂场景
        """
        print("\n" + "=" * 70)
        print("测试3：连续多个临时状态的处理")
        print("=" * 70)

        # 设置持久状态
        self.status_manager.set_success("系统就绪", temp_duration=0)
        original_persistent = self.status_manager.persistent_status
        print(f"[初始] 持久状态：{original_persistent}")

        # 连续设置多个临时状态
        self.status_manager.set_info("操作1进行中", temp_duration=1)
        print(f"[临时1] 持久状态：{self.status_manager.persistent_status}")
        self.assertEqual(
            self.status_manager.persistent_status, original_persistent, "持久状态不变"
        )

        self.status_manager.set_info("操作2进行中", temp_duration=2)
        print(f"[临时2] 持久状态：{self.status_manager.persistent_status}")
        self.assertEqual(
            self.status_manager.persistent_status, original_persistent, "持久状态不变"
        )

        # 手动触发恢复
        self.status_manager._restore_persistent_status()
        print(f"[恢复后] 当前状态：{self.status_var.get()}")

        # 验证恢复到原始持久状态
        self.assertEqual(
            self.status_var.get(), original_persistent, "应该恢复到最初的持久状态"
        )

        print("✓ 测试通过：多个临时状态不影响持久状态恢复")

    def test_04_different_status_types(self):
        """
        测试4：不同类型状态的持久化处理
        
        验证SUCCESS/INFO/WARNING/ERROR/PROCESSING类型
        """
        print("\n" + "=" * 70)
        print("测试4：不同类型状态的持久化处理")
        print("=" * 70)

        test_cases = [
            ("set_success", "成功消息", self.status_manager.STATUS_SUCCESS),
            ("set_info", "信息消息", self.status_manager.STATUS_INFO),
            ("set_warning", "警告消息", self.status_manager.STATUS_WARNING),
            ("set_error", "错误消息", self.status_manager.STATUS_ERROR),
            ("set_processing", "处理中消息", self.status_manager.STATUS_PROCESSING),
        ]

        for method_name, message, expected_type in test_cases:
            print(f"\n测试 {method_name}:")

            # 设置持久状态
            method = getattr(self.status_manager, method_name)
            method(f"{message}_持久", temp_duration=0)
            print(f"  - 持久状态：{self.status_manager.persistent_status}")
            self.assertEqual(self.status_manager.persistent_status, f"{message}_持久")
            self.assertEqual(self.status_manager.persistent_status_type, expected_type)

            # 设置临时状态
            method(f"{message}_临时", temp_duration=1)
            print(f"  - 设置临时状态后持久状态：{self.status_manager.persistent_status}")
            self.assertEqual(
                self.status_manager.persistent_status,
                f"{message}_持久",
                f"{method_name}的临时状态不应覆盖持久状态",
            )

        print("\n✓ 测试通过：所有状态类型都正确处理持久化")


class TestThreadSafetyFix(unittest.TestCase):
    """测试线程安全UI更新的修复"""

    def test_01_async_test_connection_uses_after(self):
        """
        测试1：_async_test_connection中所有UI更新都使用after()包装
        
        这是P1优先级的核心修复测试
        """
        print("\n" + "=" * 70)
        print("测试1：检查_async_test_connection的线程安全性（P1修复）")
        print("=" * 70)

        # 读取源代码文件
        source_file = src_path / "funasr_gui_client_v3.py"
        with open(source_file, "r", encoding="utf-8") as f:
            content = f.read()

        # 找到_async_test_connection方法
        async_method_pattern = r"async def _async_test_connection\(.*?\):(.*?)(?=\n    def |\n    async def |\nclass |\Z)"
        match = re.search(async_method_pattern, content, re.DOTALL)

        if not match:
            self.fail("未找到_async_test_connection方法")

        method_content = match.group(1)
        print(f"[检查] 方法内容长度：{len(method_content)} 字符")

        # 检查所有status_manager调用
        status_manager_calls = re.findall(
            r"self\.status_manager\.(set_\w+)\(", method_content
        )
        print(f"\n[检查] 找到 {len(status_manager_calls)} 个 status_manager 调用")

        # 检查所有_update_connection_indicator调用
        indicator_calls = re.findall(
            r"self\._update_connection_indicator\(", method_content
        )
        print(f"[检查] 找到 {len(indicator_calls)} 个 _update_connection_indicator 调用")

        # 检查是否都使用了after()包装
        # 正确模式：self.status_bar.after(0, lambda: self.status_manager.set_xxx(...))
        after_wrapped_status = re.findall(
            r"self\.status_bar\.after\(0,\s*lambda[^:]*:\s*self\.status_manager\.set_\w+",
            method_content,
        )
        after_wrapped_indicator = re.findall(
            r"self\.status_bar\.after\(0,\s*lambda[^:]*:\s*self\._update_connection_indicator",
            method_content,
        )

        print(
            f"\n[检查] 使用after()包装的status_manager调用：{len(after_wrapped_status)}"
        )
        print(
            f"[检查] 使用after()包装的indicator调用：{len(after_wrapped_indicator)}"
        )

        # 验证所有调用都被包装
        self.assertEqual(
            len(status_manager_calls),
            len(after_wrapped_status),
            f"所有status_manager调用都应该使用after()包装。"
            f"找到{len(status_manager_calls)}个调用，但只有{len(after_wrapped_status)}个被包装",
        )

        self.assertEqual(
            len(indicator_calls),
            len(after_wrapped_indicator),
            f"所有_update_connection_indicator调用都应该使用after()包装。"
            f"找到{len(indicator_calls)}个调用，但只有{len(after_wrapped_indicator)}个被包装",
        )

        # 检查是否有直接调用（不通过after）的情况
        # 反向检查：查找不在after中的调用
        lines = method_content.split("\n")
        direct_calls = []

        for i, line in enumerate(lines, 1):
            # 检查是否包含status_manager或_update_connection_indicator调用
            if (
                "self.status_manager.set_" in line
                or "self._update_connection_indicator(" in line
            ):
                # 检查该行或前一行是否有after包装
                context = "\n".join(lines[max(0, i - 3) : i + 1])
                if "self.status_bar.after(0," not in context:
                    direct_calls.append((i, line.strip()))

        if direct_calls:
            print(f"\n[警告] 发现 {len(direct_calls)} 个可能的直接调用：")
            for line_num, line_content in direct_calls:
                print(f"  行 {line_num}: {line_content}")
            self.fail(
                f"发现 {len(direct_calls)} 个UI更新调用未使用after()包装，违反线程安全规则"
            )

        print("\n✓ 测试通过：所有UI更新都使用after()包装，符合线程安全要求")

    def test_02_after_usage_pattern_correct(self):
        """
        测试2：验证after()调用的模式正确性
        
        检查lambda表达式是否正确捕获变量
        """
        print("\n" + "=" * 70)
        print("测试2：验证after()调用的模式正确性")
        print("=" * 70)

        # 读取源代码文件
        source_file = src_path / "funasr_gui_client_v3.py"
        with open(source_file, "r", encoding="utf-8") as f:
            content = f.read()

        # 找到_async_test_connection方法
        async_method_pattern = r"async def _async_test_connection\(.*?\):(.*?)(?=\n    def |\n    async def |\nclass |\Z)"
        match = re.search(async_method_pattern, content, re.DOTALL)

        if not match:
            self.fail("未找到_async_test_connection方法")

        method_content = match.group(1)

        # 检查带变量捕获的lambda（应该有显式参数如 lambda ip=ip, port=port）
        # 这些调用使用了f-string格式化，需要捕获变量
        variable_capture_patterns = [
            r"lambda\s+ip=ip,\s*port=port:",  # 正确的变量捕获模式
            r"lambda\s+error_type=error_type:",  # 错误类型捕获
        ]

        found_captures = 0
        for pattern in variable_capture_patterns:
            matches = re.findall(pattern, method_content)
            found_captures += len(matches)
            if matches:
                print(f"[检查] 找到 {len(matches)} 个变量捕获lambda：{pattern}")

        print(f"\n[统计] 总共找到 {found_captures} 个带变量捕获的lambda表达式")

        # 验证：应该至少有一些使用变量捕获的lambda
        # （因为有些调用包含ip、port等变量）
        self.assertGreater(
            found_captures, 0, "应该有使用变量捕获的lambda表达式（如 lambda ip=ip, port=port:）"
        )

        print("✓ 测试通过：after()调用模式正确，正确捕获了变量")


def run_tests():
    """运行所有测试"""
    print("\n" + "=" * 70)
    print("开始测试：验证StatusManager的关键修复")
    print("测试日期：2025-10-23")
    print("=" * 70)

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestStatusManagerPersistentStateFix))
    suite.addTests(loader.loadTestsFromTestCase(TestThreadSafetyFix))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 输出测试总结
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)
    print(f"总测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n✓ 所有测试通过！StatusManager修复有效。")
        print("\n修复总结：")
        print("  P0修复 ✓ 临时状态不覆盖持久状态")
        print("  P1修复 ✓ 连接测试中的UI更新使用主线程调度")
        return 0
    else:
        print("\n✗ 存在失败的测试，请检查修复代码。")
        return 1


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
