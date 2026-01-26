"""服务探测层单元测试

测试 server_probe.py 的核心功能：
1. ProbeLevel 枚举测试
2. ServerCapabilities 数据类测试
3. ServerProbe 类测试（包括模拟测试）

版本: 3.0
日期: 2026-01-26
"""

import asyncio
import json
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# 添加源码目录到路径
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "../../src/python-gui-client")
)

from server_probe import (
    ProbeLevel,
    ServerCapabilities,
    ServerProbe,
    create_probe_level,
    probe_server,
    probe_server_sync,
)


class TestProbeLevelEnum(unittest.TestCase):
    """测试 ProbeLevel 枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        self.assertEqual(ProbeLevel.CONNECT_ONLY.value, 0)
        self.assertEqual(ProbeLevel.OFFLINE_LIGHT.value, 1)
        self.assertEqual(ProbeLevel.TWOPASS_FULL.value, 2)

    def test_enum_names(self):
        """测试枚举名称"""
        self.assertEqual(ProbeLevel.CONNECT_ONLY.name, "CONNECT_ONLY")
        self.assertEqual(ProbeLevel.OFFLINE_LIGHT.name, "OFFLINE_LIGHT")
        self.assertEqual(ProbeLevel.TWOPASS_FULL.name, "TWOPASS_FULL")

    def test_create_probe_level(self):
        """测试从字符串创建探测级别"""
        self.assertEqual(create_probe_level("connect_only"), ProbeLevel.CONNECT_ONLY)
        self.assertEqual(create_probe_level("offline_light"), ProbeLevel.OFFLINE_LIGHT)
        self.assertEqual(create_probe_level("twopass_full"), ProbeLevel.TWOPASS_FULL)
        # 大小写不敏感
        self.assertEqual(create_probe_level("CONNECT_ONLY"), ProbeLevel.CONNECT_ONLY)
        self.assertEqual(create_probe_level("Offline_Light"), ProbeLevel.OFFLINE_LIGHT)
        # 无效值返回默认
        self.assertEqual(create_probe_level("invalid"), ProbeLevel.OFFLINE_LIGHT)


class TestServerCapabilities(unittest.TestCase):
    """测试 ServerCapabilities 数据类"""

    def test_default_values(self):
        """测试默认值"""
        caps = ServerCapabilities()

        self.assertFalse(caps.reachable)
        self.assertFalse(caps.responsive)
        self.assertIsNone(caps.error)
        self.assertIsNone(caps.supports_offline)
        self.assertIsNone(caps.supports_online)
        self.assertIsNone(caps.supports_2pass)
        self.assertFalse(caps.has_timestamp)
        self.assertFalse(caps.has_stamp_sents)
        self.assertEqual(caps.is_final_semantics, "unknown")
        self.assertEqual(caps.inferred_server_type, "unknown")
        self.assertEqual(caps.probe_level, ProbeLevel.CONNECT_ONLY)
        self.assertEqual(caps.probe_notes, [])

    def test_to_display_text_not_reachable(self):
        """测试不可连接时的显示文本"""
        caps = ServerCapabilities(reachable=False, error="连接超时")
        display = caps.to_display_text()

        self.assertIn("❌", display)
        self.assertIn("不可连接", display)
        self.assertIn("连接超时", display)

    def test_to_display_text_reachable_responsive(self):
        """测试可连接且有响应时的显示文本"""
        caps = ServerCapabilities(
            reachable=True,
            responsive=True,
            supports_offline=True,
            supports_2pass=True,
            has_timestamp=True,
            inferred_server_type="funasr_main",
        )
        display = caps.to_display_text()

        self.assertIn("✅", display)
        self.assertIn("服务可用", display)
        self.assertIn("离线", display)
        self.assertIn("2pass", display)
        self.assertIn("时间戳", display)
        self.assertIn("可能新版", display)

    def test_to_display_text_reachable_no_response(self):
        """测试可连接但无响应时的显示文本"""
        caps = ServerCapabilities(reachable=True, responsive=False)
        display = caps.to_display_text()

        self.assertIn("✅", display)
        self.assertIn("已连接", display)
        self.assertIn("未响应", display)
        self.assertIn("未判定", display)

    def test_to_display_text_legacy_server(self):
        """测试旧版服务端的显示文本"""
        caps = ServerCapabilities(
            reachable=True,
            responsive=True,
            supports_offline=True,
            inferred_server_type="legacy",
        )
        display = caps.to_display_text()

        self.assertIn("可能旧版", display)

    def test_to_dict(self):
        """测试转换为字典"""
        caps = ServerCapabilities(
            reachable=True,
            responsive=True,
            error=None,
            supports_offline=True,
            supports_2pass=False,
            has_timestamp=True,
            is_final_semantics="always_false",
            inferred_server_type="funasr_main",
            probe_level=ProbeLevel.OFFLINE_LIGHT,
            probe_notes=["测试笔记"],
            probe_duration_ms=123.45,
        )

        data = caps.to_dict()

        self.assertTrue(data["reachable"])
        self.assertTrue(data["responsive"])
        self.assertIsNone(data["error"])
        self.assertTrue(data["supports_offline"])
        self.assertFalse(data["supports_2pass"])
        self.assertTrue(data["has_timestamp"])
        self.assertEqual(data["is_final_semantics"], "always_false")
        self.assertEqual(data["inferred_server_type"], "funasr_main")
        self.assertEqual(data["probe_level"], "OFFLINE_LIGHT")
        self.assertEqual(data["probe_notes"], ["测试笔记"])
        self.assertEqual(data["probe_duration_ms"], 123.45)

    def test_from_dict(self):
        """测试从字典创建实例"""
        data = {
            "reachable": True,
            "responsive": True,
            "error": None,
            "supports_offline": True,
            "supports_2pass": None,
            "has_timestamp": True,
            "is_final_semantics": "legacy_true",
            "inferred_server_type": "legacy",
            "probe_level": "OFFLINE_LIGHT",
            "probe_notes": ["恢复的笔记"],
            "probe_duration_ms": 200.0,
        }

        caps = ServerCapabilities.from_dict(data)

        self.assertTrue(caps.reachable)
        self.assertTrue(caps.responsive)
        self.assertIsNone(caps.error)
        self.assertTrue(caps.supports_offline)
        self.assertIsNone(caps.supports_2pass)
        self.assertTrue(caps.has_timestamp)
        self.assertEqual(caps.is_final_semantics, "legacy_true")
        self.assertEqual(caps.inferred_server_type, "legacy")
        self.assertEqual(caps.probe_level, ProbeLevel.OFFLINE_LIGHT)
        self.assertEqual(caps.probe_notes, ["恢复的笔记"])
        self.assertEqual(caps.probe_duration_ms, 200.0)

    def test_from_dict_with_invalid_probe_level(self):
        """测试从字典创建实例时处理无效的probe_level"""
        data = {"probe_level": "INVALID_LEVEL"}

        caps = ServerCapabilities.from_dict(data)

        # 无效的probe_level应该回退到默认值
        self.assertEqual(caps.probe_level, ProbeLevel.CONNECT_ONLY)

    def test_roundtrip_dict_conversion(self):
        """测试字典转换的往返一致性"""
        original = ServerCapabilities(
            reachable=True,
            responsive=True,
            supports_offline=True,
            supports_2pass=True,
            has_timestamp=True,
            has_stamp_sents=True,
            is_final_semantics="always_false",
            inferred_server_type="funasr_main",
            probe_level=ProbeLevel.TWOPASS_FULL,
            probe_notes=["note1", "note2"],
            probe_duration_ms=150.5,
        )

        # 转换为字典再转回
        data = original.to_dict()
        restored = ServerCapabilities.from_dict(data)

        # 验证关键字段一致
        self.assertEqual(original.reachable, restored.reachable)
        self.assertEqual(original.responsive, restored.responsive)
        self.assertEqual(original.supports_offline, restored.supports_offline)
        self.assertEqual(original.supports_2pass, restored.supports_2pass)
        self.assertEqual(original.has_timestamp, restored.has_timestamp)
        self.assertEqual(original.is_final_semantics, restored.is_final_semantics)
        self.assertEqual(original.inferred_server_type, restored.inferred_server_type)
        self.assertEqual(original.probe_level, restored.probe_level)
        self.assertEqual(original.probe_notes, restored.probe_notes)


class TestServerProbeInit(unittest.TestCase):
    """测试 ServerProbe 初始化"""

    def test_init_with_string_port(self):
        """测试使用字符串端口初始化"""
        probe = ServerProbe("localhost", "10095", use_ssl=True)

        self.assertEqual(probe.host, "localhost")
        self.assertEqual(probe.port, "10095")
        self.assertTrue(probe.use_ssl)

    def test_init_with_int_port(self):
        """测试使用整数端口初始化"""
        probe = ServerProbe("127.0.0.1", 10095, use_ssl=False)

        self.assertEqual(probe.host, "127.0.0.1")
        self.assertEqual(probe.port, "10095")  # 应该转换为字符串
        self.assertFalse(probe.use_ssl)


class TestServerProbeInferType(unittest.TestCase):
    """测试服务端类型推断"""

    def test_infer_funasr_main(self):
        """测试推断为新版服务端"""
        probe = ServerProbe("localhost", "10095")
        caps = ServerCapabilities(is_final_semantics="always_false")

        probe._infer_server_type(caps)

        self.assertEqual(caps.inferred_server_type, "funasr_main")

    def test_infer_legacy(self):
        """测试推断为旧版服务端"""
        probe = ServerProbe("localhost", "10095")
        caps = ServerCapabilities(is_final_semantics="legacy_true")

        probe._infer_server_type(caps)

        self.assertEqual(caps.inferred_server_type, "legacy")

    def test_infer_unknown(self):
        """测试推断为未知类型"""
        probe = ServerProbe("localhost", "10095")
        caps = ServerCapabilities(is_final_semantics="unknown")

        probe._infer_server_type(caps)

        self.assertEqual(caps.inferred_server_type, "unknown")


class TestCoerceBool(unittest.TestCase):
    """测试宽容布尔解析方法"""

    def test_coerce_bool_with_bool(self):
        """测试布尔输入"""
        self.assertTrue(ServerProbe._coerce_bool(True))
        self.assertFalse(ServerProbe._coerce_bool(False))

    def test_coerce_bool_with_none(self):
        """测试 None 输入"""
        self.assertIsNone(ServerProbe._coerce_bool(None))

    def test_coerce_bool_with_int(self):
        """测试整数输入"""
        self.assertTrue(ServerProbe._coerce_bool(1))
        self.assertFalse(ServerProbe._coerce_bool(0))
        self.assertTrue(ServerProbe._coerce_bool(42))
        self.assertTrue(ServerProbe._coerce_bool(-1))

    def test_coerce_bool_with_string_true(self):
        """测试字符串 true 变体"""
        self.assertTrue(ServerProbe._coerce_bool("true"))
        self.assertTrue(ServerProbe._coerce_bool("True"))
        self.assertTrue(ServerProbe._coerce_bool("TRUE"))
        self.assertTrue(ServerProbe._coerce_bool("1"))
        self.assertTrue(ServerProbe._coerce_bool("yes"))
        self.assertTrue(ServerProbe._coerce_bool("on"))

    def test_coerce_bool_with_string_false(self):
        """测试字符串 false 变体"""
        self.assertFalse(ServerProbe._coerce_bool("false"))
        self.assertFalse(ServerProbe._coerce_bool("False"))
        self.assertFalse(ServerProbe._coerce_bool("FALSE"))
        self.assertFalse(ServerProbe._coerce_bool("0"))
        self.assertFalse(ServerProbe._coerce_bool("no"))
        self.assertFalse(ServerProbe._coerce_bool("off"))
        self.assertFalse(ServerProbe._coerce_bool(""))

    def test_coerce_bool_with_whitespace(self):
        """测试带空格的字符串"""
        self.assertTrue(ServerProbe._coerce_bool("  true  "))
        self.assertFalse(ServerProbe._coerce_bool("  false  "))


class TestServerProbeWithMock(unittest.TestCase):
    """使用Mock测试ServerProbe的探测功能

    注意：由于 websockets 是在函数内部动态导入的，
    需要使用 patch.dict 来模拟 sys.modules
    """

    def test_probe_connection_timeout(self):
        """测试连接超时情况 - 通过错误信息验证"""
        # 注意：实际网络连接测试需要真实服务器
        # 这里我们测试 ServerCapabilities 的错误状态设置
        caps = ServerCapabilities(reachable=False, error="连接超时")

        self.assertFalse(caps.reachable)
        self.assertEqual(caps.error, "连接超时")
        self.assertIn("不可连接", caps.to_display_text())

    def test_probe_connection_refused(self):
        """测试连接被拒绝情况 - 通过错误信息验证"""
        caps = ServerCapabilities(reachable=False, error="连接被拒绝")

        self.assertFalse(caps.reachable)
        self.assertEqual(caps.error, "连接被拒绝")
        self.assertIn("不可连接", caps.to_display_text())

    def test_probe_connect_only_success(self):
        """测试仅连接探测成功"""

        async def run_test():
            # 创建模拟的WebSocket连接（异步上下文管理器）
            mock_ws_instance = AsyncMock()

            mock_websockets = MagicMock()
            mock_connect = AsyncMock()
            mock_connect.__aenter__.return_value = mock_ws_instance
            mock_connect.__aexit__.return_value = None
            mock_websockets.connect.return_value = mock_connect

            with patch.dict("sys.modules", {"websockets": mock_websockets}):
                probe = ServerProbe("localhost", "10095")
                caps = await probe.probe(level=ProbeLevel.CONNECT_ONLY, timeout=5.0)

                self.assertTrue(caps.reachable)
                self.assertIn("WebSocket连接成功", caps.probe_notes)

        asyncio.run(run_test())

    def test_probe_offline_success_with_response(self):
        """测试离线探测成功且有响应"""

        async def run_test():
            # 模拟服务端响应
            mock_response = json.dumps(
                {
                    "mode": "offline",
                    "text": "",
                    "is_final": False,
                    "timestamp": [[0, 100]],
                }
            )

            mock_ws_instance = AsyncMock()
            mock_ws_instance.recv.return_value = mock_response

            mock_websockets = MagicMock()
            mock_connect = AsyncMock()
            mock_connect.__aenter__.return_value = mock_ws_instance
            mock_connect.__aexit__.return_value = None
            mock_websockets.connect.return_value = mock_connect

            with patch.dict("sys.modules", {"websockets": mock_websockets}):
                probe = ServerProbe("localhost", "10095")
                caps = await probe.probe(level=ProbeLevel.OFFLINE_LIGHT, timeout=5.0)

                self.assertTrue(caps.reachable)
                self.assertTrue(caps.responsive)
                self.assertTrue(caps.supports_offline)
                self.assertTrue(caps.has_timestamp)
                self.assertEqual(caps.is_final_semantics, "always_false")

        asyncio.run(run_test())

    def test_probe_offline_success_legacy_response(self):
        """测试离线探测成功且响应为旧版特征"""

        async def run_test():
            # 模拟旧版服务端响应（is_final=True）
            mock_response = json.dumps(
                {"mode": "offline", "text": "测试", "is_final": True}
            )

            mock_ws_instance = AsyncMock()
            mock_ws_instance.recv.return_value = mock_response

            mock_websockets = MagicMock()
            mock_connect = AsyncMock()
            mock_connect.__aenter__.return_value = mock_ws_instance
            mock_connect.__aexit__.return_value = None
            mock_websockets.connect.return_value = mock_connect

            with patch.dict("sys.modules", {"websockets": mock_websockets}):
                probe = ServerProbe("localhost", "10095")
                caps = await probe.probe(level=ProbeLevel.OFFLINE_LIGHT, timeout=5.0)

                self.assertTrue(caps.responsive)
                self.assertEqual(caps.is_final_semantics, "legacy_true")
                self.assertEqual(caps.inferred_server_type, "legacy")

        asyncio.run(run_test())

    def test_probe_offline_no_response(self):
        """测试离线探测无响应"""

        async def run_test():
            mock_ws_instance = AsyncMock()
            # 模拟接收超时
            mock_ws_instance.recv.side_effect = asyncio.TimeoutError()

            mock_websockets = MagicMock()
            mock_connect = AsyncMock()
            mock_connect.__aenter__.return_value = mock_ws_instance
            mock_connect.__aexit__.return_value = None
            mock_websockets.connect.return_value = mock_connect

            with patch.dict("sys.modules", {"websockets": mock_websockets}):
                probe = ServerProbe("localhost", "10095")
                caps = await probe.probe(level=ProbeLevel.OFFLINE_LIGHT, timeout=5.0)

                self.assertTrue(caps.reachable)
                self.assertFalse(caps.responsive)
                self.assertIsNone(caps.supports_offline)  # 未判定
                self.assertIn("离线探测无响应", " ".join(caps.probe_notes))

        asyncio.run(run_test())


class TestConvenienceFunctions(unittest.TestCase):
    """测试便捷函数"""

    def test_probe_server_async(self):
        """测试异步便捷函数"""

        async def run_test():
            mock_websockets = MagicMock()
            mock_websockets.connect = AsyncMock(side_effect=ConnectionRefusedError())

            with patch.dict("sys.modules", {"websockets": mock_websockets}):
                caps = await probe_server(
                    "localhost", "10095", use_ssl=True, level=ProbeLevel.CONNECT_ONLY
                )

                self.assertFalse(caps.reachable)

        asyncio.run(run_test())

    def test_probe_server_sync_function_exists(self):
        """测试同步便捷函数存在且可调用"""
        # 验证函数签名
        import inspect

        sig = inspect.signature(probe_server_sync)
        params = list(sig.parameters.keys())

        self.assertIn("host", params)
        self.assertIn("port", params)
        self.assertIn("use_ssl", params)
        self.assertIn("level", params)
        self.assertIn("timeout", params)


class TestEdgeCases(unittest.TestCase):
    """测试边界情况"""

    def test_empty_probe_notes(self):
        """测试空探测笔记"""
        caps = ServerCapabilities()
        self.assertEqual(caps.probe_notes, [])

    def test_probe_notes_append(self):
        """测试探测笔记追加"""
        caps = ServerCapabilities()
        caps.probe_notes.append("笔记1")
        caps.probe_notes.append("笔记2")

        self.assertEqual(len(caps.probe_notes), 2)
        self.assertIn("笔记1", caps.probe_notes)
        self.assertIn("笔记2", caps.probe_notes)

    def test_probe_duration_tracking(self):
        """测试探测时长追踪"""

        async def run_test():
            mock_websockets = MagicMock()
            mock_websockets.connect = AsyncMock(side_effect=ConnectionRefusedError())

            with patch.dict("sys.modules", {"websockets": mock_websockets}):
                probe = ServerProbe("localhost", "10095")
                caps = await probe.probe(level=ProbeLevel.CONNECT_ONLY, timeout=1.0)

                # 探测时长应该被记录
                self.assertGreater(caps.probe_duration_ms, 0)

        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main(verbosity=2)
