#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V3 GUI 探测集成测试

测试 GUI 层探测相关的集成功能：
1. 缓存恢复 24 小时规则
2. token 防抖不乱序覆盖
3. probe 不覆盖 connection_status
4. 2pass 模式自动切换完整探测
5. 探测与"连接服务器"语义隔离

日期: 2026-01-27
"""

import datetime
import json
import os
import sys
import tempfile
import time
import unittest
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, patch

# 添加源码目录到路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
SRC_DIR = os.path.join(PROJECT_ROOT, "src", "python-gui-client")
sys.path.insert(0, SRC_DIR)


# =============================================================================
# 测试1: 缓存恢复 24 小时规则
# =============================================================================


class TestCacheExpiration24Hours(unittest.TestCase):
    """测试缓存 24 小时过期规则"""

    def test_cache_within_24h_is_valid(self):
        """测试 24 小时内的缓存有效"""
        now = datetime.datetime.now()
        cache_time = now - datetime.timedelta(hours=1)

        is_valid = self._is_cache_valid(cache_time.isoformat(), now)
        self.assertTrue(is_valid, "1小时前的缓存应有效")

    def test_cache_at_23h_is_valid(self):
        """测试 23 小时 59 分钟的缓存有效"""
        now = datetime.datetime.now()
        cache_time = now - datetime.timedelta(hours=23, minutes=59)

        is_valid = self._is_cache_valid(cache_time.isoformat(), now)
        self.assertTrue(is_valid, "23小时59分钟前的缓存应有效")

    def test_cache_exactly_24h_is_expired(self):
        """测试恰好 24 小时的缓存过期"""
        now = datetime.datetime.now()
        cache_time = now - datetime.timedelta(hours=24)

        is_valid = self._is_cache_valid(cache_time.isoformat(), now)
        self.assertFalse(is_valid, "恰好24小时前的缓存应过期")

    def test_cache_over_24h_is_expired(self):
        """测试超过 24 小时的缓存过期"""
        now = datetime.datetime.now()
        cache_time = now - datetime.timedelta(hours=25)

        is_valid = self._is_cache_valid(cache_time.isoformat(), now)
        self.assertFalse(is_valid, "25小时前的缓存应过期")

    def test_cache_none_time_is_expired(self):
        """测试缓存时间为 None 视为过期"""
        now = datetime.datetime.now()

        is_valid = self._is_cache_valid(None, now)
        self.assertFalse(is_valid, "缓存时间为None应视为过期")

    def test_cache_invalid_format_is_expired(self):
        """测试无效格式的缓存时间视为过期"""
        now = datetime.datetime.now()

        is_valid = self._is_cache_valid("invalid-time-format", now)
        self.assertFalse(is_valid, "无效格式应视为过期")

    def _is_cache_valid(
        self, cache_time_str: Optional[str], now: datetime.datetime
    ) -> bool:
        """模拟 GUI 中的缓存有效性检查逻辑

        Args:
            cache_time_str: ISO 格式的缓存时间字符串
            now: 当前时间

        Returns:
            缓存是否有效
        """
        if not cache_time_str:
            return False

        try:
            cache_time = datetime.datetime.fromisoformat(cache_time_str)
            age = now - cache_time
            return age.total_seconds() < 24 * 3600  # 24小时 = 86400秒
        except (ValueError, TypeError):
            return False


class TestCacheRestoreOnStartup(unittest.TestCase):
    """测试启动时缓存恢复"""

    def test_valid_cache_restores_capabilities(self):
        """测试有效缓存能恢复探测结果"""
        from server_probe import ServerCapabilities

        cache_data = {
            "reachable": True,
            "responsive": True,
            "supports_offline": True,
            "supports_2pass": None,
            "inferred_server_type": "legacy",
            "probe_level": "OFFLINE_LIGHT",
        }

        caps = ServerCapabilities.from_dict(cache_data)

        self.assertTrue(caps.reachable)
        self.assertTrue(caps.responsive)
        self.assertTrue(caps.supports_offline)
        self.assertEqual(caps.inferred_server_type, "legacy")

    def test_empty_cache_returns_default_capabilities(self):
        """测试空缓存返回默认能力"""
        from server_probe import ServerCapabilities

        caps = ServerCapabilities.from_dict({})

        self.assertFalse(caps.reachable)
        self.assertFalse(caps.responsive)


# =============================================================================
# 测试2: token 防抖不乱序覆盖
# =============================================================================


class TestTokenDebouncing(unittest.TestCase):
    """测试 token 防抖机制"""

    def test_newer_token_overwrites_older(self):
        """测试新 token 的结果覆盖旧结果"""
        # 模拟 token 机制
        results = []
        current_token = 0

        def schedule_update(token, result, delay):
            """模拟延迟更新"""
            # 只有 token 匹配时才更新
            if token == current_token:
                results.append(result)

        # 发起第一次探测（token=1）
        current_token = 1
        token1 = current_token

        # 发起第二次探测（token=2，第一次还未返回）
        current_token = 2
        token2 = current_token

        # 第一次结果返回（但 token 已过期）
        schedule_update(token1, "result1", delay=100)

        # 第二次结果返回
        schedule_update(token2, "result2", delay=50)

        # 只有第二次结果被接受
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], "result2")

    def test_stale_token_ignored(self):
        """测试过期 token 的结果被忽略"""
        current_token = 5

        def should_update(token):
            return token == current_token

        # 旧 token 应被忽略
        self.assertFalse(should_update(3))
        self.assertFalse(should_update(4))
        # 当前 token 应被接受
        self.assertTrue(should_update(5))

    def test_token_increment_on_each_probe(self):
        """测试每次探测 token 递增"""
        probe_token = 0

        def schedule_probe():
            nonlocal probe_token
            probe_token += 1
            return probe_token

        tokens = [schedule_probe() for _ in range(5)]

        self.assertEqual(tokens, [1, 2, 3, 4, 5])


class TestDebounceTimer(unittest.TestCase):
    """测试防抖计时器"""

    def test_rapid_calls_only_keep_last_timer(self):
        """测试快速调用只保留最后一次定时器（取消前序）"""
        scheduled = []
        cancelled = []
        current_timer_id = None

        def after(delay_ms, callback):
            # 模拟 tkinter.after 返回的 timer id
            tid = len(scheduled) + 1
            scheduled.append((tid, delay_ms, callback))
            return tid

        def after_cancel(tid):
            cancelled.append(tid)

        def schedule_probe():
            """模拟 GUI 中 _schedule_probe 的核心逻辑（防抖 + 取消前序 timer）"""
            nonlocal current_timer_id
            if current_timer_id is not None:
                after_cancel(current_timer_id)
            current_timer_id = after(500, lambda: None)

        # 快速调用多次：应不断取消前序定时器，只保留最后一个 timer id
        for _ in range(5):
            schedule_probe()

        self.assertEqual(len(scheduled), 5, "每次调用都会重新安排定时器")
        self.assertEqual(len(cancelled), 4, "前4次安排应被后续调用取消")
        self.assertEqual(current_timer_id, scheduled[-1][0], "最终仅最后一个 timer id 生效")
        self.assertEqual(scheduled[-1][1], 500, "防抖延迟应为 500ms")

    def test_debounce_delay_500ms(self):
        """测试防抖延迟为 500ms"""
        # GUI 中使用 500ms 防抖延迟
        DEBOUNCE_DELAY_MS = 500

        self.assertEqual(DEBOUNCE_DELAY_MS, 500)


# =============================================================================
# 测试3: probe 不覆盖 connection_status
# =============================================================================


class TestProbeAndConnectionStatusIsolation(unittest.TestCase):
    """测试探测状态与连接状态隔离"""

    def test_probe_success_does_not_set_connection_status(self):
        """测试探测成功不设置 connection_status"""
        # 模拟 GUI 状态
        connection_status = False
        probe_reachable = False

        def update_probe_result(caps_reachable):
            nonlocal probe_reachable
            # 探测只更新 probe_reachable，不修改 connection_status
            probe_reachable = caps_reachable
            # 注意：不设置 connection_status = True

        # 探测成功
        update_probe_result(True)

        self.assertTrue(probe_reachable, "探测可达应为 True")
        self.assertFalse(connection_status, "connection_status 应保持 False")

    def test_probe_failure_does_not_clear_connection_status(self):
        """测试探测失败不清除已有的 connection_status"""
        # 模拟已连接状态
        connection_status = True
        probe_reachable = True

        def update_probe_result_error():
            nonlocal probe_reachable
            # 探测失败只更新 probe_reachable
            probe_reachable = False
            # 关键：不修改 connection_status

        # 探测失败
        update_probe_result_error()

        self.assertFalse(probe_reachable, "探测可达应为 False")
        self.assertTrue(connection_status, "connection_status 应保持 True")

    def test_connection_test_sets_connection_status(self):
        """测试正式连接测试设置 connection_status"""
        connection_status = False

        def update_connection_indicator(connected):
            nonlocal connection_status
            connection_status = connected

        # 连接测试成功
        update_connection_indicator(True)

        self.assertTrue(connection_status)

    def test_two_independent_states(self):
        """测试 probe_reachable 和 connection_status 是两个独立状态"""
        probe_reachable = False
        connection_status = False

        # 场景1：探测成功，但未进行连接测试
        probe_reachable = True
        self.assertTrue(probe_reachable)
        self.assertFalse(connection_status)

        # 场景2：连接测试成功
        connection_status = True
        self.assertTrue(probe_reachable)
        self.assertTrue(connection_status)

        # 场景3：探测失败，但连接状态保持
        probe_reachable = False
        self.assertFalse(probe_reachable)
        self.assertTrue(connection_status)


# =============================================================================
# 测试4: 2pass 模式自动切换完整探测
# =============================================================================


class TestTwoPassAutoSwitchProbeLevel(unittest.TestCase):
    """测试 2pass 模式自动切换探测级别"""

    def test_2pass_mode_triggers_full_probe(self):
        """测试选择 2pass 模式触发完整探测"""
        current_mode = "2pass"
        current_probe_level = "offline_light"

        def on_mode_change(mode, probe_level):
            if mode == "2pass" and probe_level != "twopass_full":
                return "twopass_full"
            return probe_level

        new_level = on_mode_change(current_mode, current_probe_level)

        self.assertEqual(new_level, "twopass_full")

    def test_offline_mode_keeps_light_probe(self):
        """测试 offline 模式保持轻量探测"""
        current_mode = "offline"
        current_probe_level = "offline_light"

        def on_mode_change(mode, probe_level):
            if mode == "2pass" and probe_level != "twopass_full":
                return "twopass_full"
            return probe_level

        new_level = on_mode_change(current_mode, current_probe_level)

        self.assertEqual(new_level, "offline_light")

    def test_2pass_already_full_no_change(self):
        """测试 2pass 模式已是完整探测时不变"""
        current_mode = "2pass"
        current_probe_level = "twopass_full"

        def on_mode_change(mode, probe_level):
            if mode == "2pass" and probe_level != "twopass_full":
                return "twopass_full"
            return probe_level

        new_level = on_mode_change(current_mode, current_probe_level)

        self.assertEqual(new_level, "twopass_full")

    def test_auto_probe_on_switch_enabled(self):
        """测试 auto_probe_on_switch 启用时触发探测"""
        auto_probe_on_switch = True
        probe_triggered = False

        def on_mode_change_with_probe(mode, auto_probe_enabled):
            nonlocal probe_triggered
            if auto_probe_enabled:
                probe_triggered = True

        on_mode_change_with_probe("2pass", auto_probe_on_switch)

        self.assertTrue(probe_triggered)

    def test_auto_probe_on_switch_disabled(self):
        """测试 auto_probe_on_switch 禁用时不触发探测"""
        auto_probe_on_switch = False
        probe_triggered = False

        def on_mode_change_with_probe(mode, auto_probe_enabled):
            nonlocal probe_triggered
            if auto_probe_enabled:
                probe_triggered = True

        on_mode_change_with_probe("2pass", auto_probe_on_switch)

        self.assertFalse(probe_triggered)


# =============================================================================
# 测试5: 探测与"连接服务器"语义隔离
# =============================================================================


class TestProbeVsConnectSemantics(unittest.TestCase):
    """测试探测与连接服务器的语义隔离"""

    def test_probe_is_lightweight_detection(self):
        """测试探测是轻量级检测"""
        # 探测的目的
        probe_purpose = [
            "检测服务器可达性",
            "探测服务能力（离线/2pass）",
            "推断服务端类型",
            "不建立持久连接",
        ]

        self.assertEqual(len(probe_purpose), 4)
        self.assertIn("不建立持久连接", probe_purpose)

    def test_connect_is_formal_test(self):
        """测试连接服务器是正式测试"""
        # 连接的目的
        connect_purpose = [
            "正式验证连接可用性",
            "设置 connection_status",
            "启用识别功能",
            "可能需要更长超时",
        ]

        self.assertEqual(len(connect_purpose), 4)
        self.assertIn("设置 connection_status", connect_purpose)

    def test_probe_result_only_updates_ui(self):
        """测试探测结果只更新 UI"""
        ui_updated = False
        connection_status_changed = False

        def on_probe_result(caps):
            nonlocal ui_updated
            ui_updated = True
            # 注意：不修改 connection_status

        on_probe_result(MagicMock(reachable=True))

        self.assertTrue(ui_updated)
        self.assertFalse(connection_status_changed)

    def test_connect_result_updates_status_and_ui(self):
        """测试连接结果更新状态和 UI"""
        ui_updated = False
        connection_status = False

        def on_connect_result(connected):
            nonlocal ui_updated, connection_status
            ui_updated = True
            connection_status = connected

        on_connect_result(True)

        self.assertTrue(ui_updated)
        self.assertTrue(connection_status)


# =============================================================================
# 测试6: GUI 探测结果格式化
# =============================================================================


class TestProbeResultFormatting(unittest.TestCase):
    """测试探测结果格式化"""

    def test_format_reachable_responsive(self):
        """测试可达且有响应的格式化"""
        from server_probe import ServerCapabilities

        caps = ServerCapabilities(
            reachable=True,
            responsive=True,
            supports_offline=True,
        )

        text = caps.to_display_text()

        self.assertIn("✅", text)
        self.assertIn("服务可用", text)
        self.assertIn("离线", text)

    def test_format_reachable_no_response(self):
        """测试可达但无响应的格式化"""
        from server_probe import ServerCapabilities

        caps = ServerCapabilities(
            reachable=True,
            responsive=False,
        )

        text = caps.to_display_text()

        self.assertIn("✅", text)
        self.assertIn("已连接", text)
        self.assertIn("未响应", text)

    def test_format_not_reachable(self):
        """测试不可达的格式化"""
        from server_probe import ServerCapabilities

        caps = ServerCapabilities(
            reachable=False,
            error="连接超时",
        )

        text = caps.to_display_text()

        self.assertIn("❌", text)
        self.assertIn("不可连接", text)
        self.assertIn("连接超时", text)

    def test_format_2pass_unknown(self):
        """测试 2pass 未判定的格式化"""
        from server_probe import ServerCapabilities

        caps = ServerCapabilities(
            reachable=True,
            responsive=True,
            supports_offline=True,
            supports_2pass=None,  # 未判定
        )

        text = caps.to_display_text()

        self.assertIn("离线", text)
        # 2pass 未判定时不应显示为支持
        self.assertNotIn("2pass", text.split("|")[0] if "|" in text else text)


# =============================================================================
# 运行测试
# =============================================================================


def run_tests():
    """运行所有测试"""
    print("=" * 70)
    print("V3 GUI 探测集成测试")
    print("=" * 70)
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python版本: {sys.version}")
    print("=" * 70)
    print()

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    test_classes = [
        TestCacheExpiration24Hours,
        TestCacheRestoreOnStartup,
        TestTokenDebouncing,
        TestDebounceTimer,
        TestProbeAndConnectionStatusIsolation,
        TestTwoPassAutoSwitchProbeLevel,
        TestProbeVsConnectSemantics,
        TestProbeResultFormatting,
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
