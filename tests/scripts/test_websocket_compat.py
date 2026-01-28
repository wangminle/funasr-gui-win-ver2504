#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WebSocket 兼容层单元测试

测试 websocket_compat.py 的核心功能：
1. proxy 参数兼容降级（新版 websockets 支持 vs 旧版不支持）
2. AsyncMock 包装的 async-with 行为
3. open_timeout 参数传递
4. disable_proxy 选项行为

日期: 2026-01-27
"""

import asyncio
import inspect
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# 添加源码目录到路径
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "../../src/python-gui-client")
)


class TestConnectWebsocketBasic(unittest.TestCase):
    """测试 connect_websocket 基础功能"""

    def test_function_exists(self):
        """测试 connect_websocket 函数存在"""
        from websocket_compat import connect_websocket

        self.assertTrue(callable(connect_websocket))

    def test_function_signature(self):
        """测试 connect_websocket 函数签名"""
        from websocket_compat import connect_websocket

        sig = inspect.signature(connect_websocket)
        params = list(sig.parameters.keys())

        self.assertIn("uri", params)
        self.assertIn("disable_proxy", params)

    def test_disable_proxy_default_true(self):
        """测试 disable_proxy 参数默认值为 True"""
        from websocket_compat import connect_websocket

        sig = inspect.signature(connect_websocket)
        disable_proxy_param = sig.parameters.get("disable_proxy")

        self.assertIsNotNone(disable_proxy_param)
        self.assertEqual(disable_proxy_param.default, True)


class TestProxyParameterCompatibility(unittest.TestCase):
    """测试 proxy 参数兼容性"""

    def test_new_websockets_with_proxy_support(self):
        """测试新版 websockets 支持 proxy 参数"""

        async def run_test():
            # 模拟新版 websockets（支持 proxy 参数）
            mock_ws_instance = AsyncMock()

            mock_websockets = MagicMock()
            mock_connect = MagicMock()
            mock_connect.__aenter__ = AsyncMock(return_value=mock_ws_instance)
            mock_connect.__aexit__ = AsyncMock(return_value=None)
            mock_websockets.connect.return_value = mock_connect

            with patch.dict("sys.modules", {"websockets": mock_websockets}):
                # 重新导入以应用 patch
                import importlib
                import websocket_compat
                importlib.reload(websocket_compat)

                result = websocket_compat.connect_websocket("wss://localhost:10095")

                # 验证 websockets.connect 被调用且传递了 proxy=None
                mock_websockets.connect.assert_called_once()
                call_kwargs = mock_websockets.connect.call_args[1]
                self.assertIn("proxy", call_kwargs)
                self.assertIsNone(call_kwargs["proxy"])

        asyncio.run(run_test())

    def test_old_websockets_proxy_fallback(self):
        """测试旧版 websockets 不支持 proxy 参数时的降级处理"""

        async def run_test():
            # 模拟旧版 websockets（不支持 proxy 参数，抛出 TypeError）
            mock_ws_instance = AsyncMock()

            def connect_side_effect(*args, **kwargs):
                if "proxy" in kwargs:
                    raise TypeError("connect() got an unexpected keyword argument 'proxy'")
                # 返回一个模拟的连接对象
                mock_connect = MagicMock()
                mock_connect.__aenter__ = AsyncMock(return_value=mock_ws_instance)
                mock_connect.__aexit__ = AsyncMock(return_value=None)
                return mock_connect

            mock_websockets = MagicMock()
            mock_websockets.connect.side_effect = connect_side_effect

            with patch.dict("sys.modules", {"websockets": mock_websockets}):
                import importlib
                import websocket_compat
                importlib.reload(websocket_compat)

                # 应该不会抛出异常，而是降级处理
                result = websocket_compat.connect_websocket("wss://localhost:10095")

                # 验证被调用了两次：第一次带 proxy，第二次不带
                self.assertEqual(mock_websockets.connect.call_count, 2)

        asyncio.run(run_test())

    def test_disable_proxy_false_no_proxy_param(self):
        """测试 disable_proxy=False 时不添加 proxy 参数"""

        async def run_test():
            mock_ws_instance = AsyncMock()

            mock_websockets = MagicMock()
            mock_connect = MagicMock()
            mock_connect.__aenter__ = AsyncMock(return_value=mock_ws_instance)
            mock_connect.__aexit__ = AsyncMock(return_value=None)
            mock_websockets.connect.return_value = mock_connect

            with patch.dict("sys.modules", {"websockets": mock_websockets}):
                import importlib
                import websocket_compat
                importlib.reload(websocket_compat)

                result = websocket_compat.connect_websocket(
                    "wss://localhost:10095",
                    disable_proxy=False
                )

                # 验证 websockets.connect 被调用但不带 proxy 参数
                mock_websockets.connect.assert_called_once()
                call_kwargs = mock_websockets.connect.call_args[1]
                self.assertNotIn("proxy", call_kwargs)

        asyncio.run(run_test())


class TestAsyncContextManagerWrapping(unittest.TestCase):
    """测试异步上下文管理器包装"""

    def test_normal_async_context_manager(self):
        """测试正常的异步上下文管理器不需要包装"""

        async def run_test():
            mock_ws_instance = AsyncMock()

            mock_websockets = MagicMock()
            mock_connect = MagicMock()
            mock_connect.__aenter__ = AsyncMock(return_value=mock_ws_instance)
            mock_connect.__aexit__ = AsyncMock(return_value=None)
            mock_websockets.connect.return_value = mock_connect

            with patch.dict("sys.modules", {"websockets": mock_websockets}):
                import importlib
                import websocket_compat
                importlib.reload(websocket_compat)

                conn = websocket_compat.connect_websocket("wss://localhost:10095")

                # 应该可以作为异步上下文管理器使用
                self.assertTrue(
                    hasattr(conn, "__aenter__") or inspect.isawaitable(conn)
                )

        asyncio.run(run_test())

    def test_awaitable_wrapped_to_context_manager(self):
        """测试纯 awaitable 对象被包装为异步上下文管理器"""

        async def run_test():
            mock_ws_instance = AsyncMock()
            mock_ws_instance.close = AsyncMock()

            # 模拟返回纯 coroutine 而非上下文管理器
            async def mock_coroutine():
                return mock_ws_instance

            mock_websockets = MagicMock()
            mock_websockets.connect.return_value = mock_coroutine()

            with patch.dict("sys.modules", {"websockets": mock_websockets}):
                import importlib
                import websocket_compat
                importlib.reload(websocket_compat)

                conn = websocket_compat.connect_websocket("wss://localhost:10095")

                # 包装后应该可以作为异步上下文管理器使用
                async with conn as ws:
                    self.assertIsNotNone(ws)

        asyncio.run(run_test())


class TestOpenTimeoutParameter(unittest.TestCase):
    """测试 open_timeout 参数传递"""

    def test_open_timeout_passed_through(self):
        """测试 open_timeout 参数被正确传递"""

        async def run_test():
            mock_ws_instance = AsyncMock()

            mock_websockets = MagicMock()
            mock_connect = MagicMock()
            mock_connect.__aenter__ = AsyncMock(return_value=mock_ws_instance)
            mock_connect.__aexit__ = AsyncMock(return_value=None)
            mock_websockets.connect.return_value = mock_connect

            with patch.dict("sys.modules", {"websockets": mock_websockets}):
                import importlib
                import websocket_compat
                importlib.reload(websocket_compat)

                result = websocket_compat.connect_websocket(
                    "wss://localhost:10095",
                    open_timeout=10.0
                )

                # 验证 open_timeout 被传递
                call_kwargs = mock_websockets.connect.call_args[1]
                self.assertIn("open_timeout", call_kwargs)
                self.assertEqual(call_kwargs["open_timeout"], 10.0)

        asyncio.run(run_test())

    def test_ssl_parameter_passed_through(self):
        """测试 ssl 参数被正确传递"""

        async def run_test():
            import ssl
            ssl_context = ssl.create_default_context()

            mock_ws_instance = AsyncMock()

            mock_websockets = MagicMock()
            mock_connect = MagicMock()
            mock_connect.__aenter__ = AsyncMock(return_value=mock_ws_instance)
            mock_connect.__aexit__ = AsyncMock(return_value=None)
            mock_websockets.connect.return_value = mock_connect

            with patch.dict("sys.modules", {"websockets": mock_websockets}):
                import importlib
                import websocket_compat
                importlib.reload(websocket_compat)

                result = websocket_compat.connect_websocket(
                    "wss://localhost:10095",
                    ssl=ssl_context
                )

                # 验证 ssl 被传递
                call_kwargs = mock_websockets.connect.call_args[1]
                self.assertIn("ssl", call_kwargs)
                self.assertEqual(call_kwargs["ssl"], ssl_context)

        asyncio.run(run_test())

    def test_subprotocols_parameter_passed_through(self):
        """测试 subprotocols 参数被正确传递"""

        async def run_test():
            mock_ws_instance = AsyncMock()

            mock_websockets = MagicMock()
            mock_connect = MagicMock()
            mock_connect.__aenter__ = AsyncMock(return_value=mock_ws_instance)
            mock_connect.__aexit__ = AsyncMock(return_value=None)
            mock_websockets.connect.return_value = mock_connect

            with patch.dict("sys.modules", {"websockets": mock_websockets}):
                import importlib
                import websocket_compat
                importlib.reload(websocket_compat)

                result = websocket_compat.connect_websocket(
                    "wss://localhost:10095",
                    subprotocols=["binary"]
                )

                # 验证 subprotocols 被传递
                call_kwargs = mock_websockets.connect.call_args[1]
                self.assertIn("subprotocols", call_kwargs)
                self.assertEqual(call_kwargs["subprotocols"], ["binary"])

        asyncio.run(run_test())


class TestErrorHandling(unittest.TestCase):
    """测试错误处理"""

    def test_non_proxy_typeerror_propagates(self):
        """测试非 proxy 相关的 TypeError 能正常抛出"""

        async def run_test():
            mock_websockets = MagicMock()
            mock_websockets.connect.side_effect = TypeError("unrelated error")

            with patch.dict("sys.modules", {"websockets": mock_websockets}):
                import importlib
                import websocket_compat
                importlib.reload(websocket_compat)

                with self.assertRaises(TypeError) as context:
                    websocket_compat.connect_websocket("wss://localhost:10095")

                self.assertIn("unrelated error", str(context.exception))

        asyncio.run(run_test())

    def test_other_exceptions_propagate(self):
        """测试其他异常能正常抛出"""

        async def run_test():
            mock_websockets = MagicMock()
            mock_websockets.connect.side_effect = ConnectionRefusedError("Connection refused")

            with patch.dict("sys.modules", {"websockets": mock_websockets}):
                import importlib
                import websocket_compat
                importlib.reload(websocket_compat)

                with self.assertRaises(ConnectionRefusedError):
                    websocket_compat.connect_websocket("wss://localhost:10095")

        asyncio.run(run_test())


class TestCodeQuality(unittest.TestCase):
    """测试代码质量"""

    def test_module_has_docstring(self):
        """测试模块有文档字符串"""
        import websocket_compat

        self.assertIsNotNone(websocket_compat.__doc__)
        self.assertGreater(len(websocket_compat.__doc__), 0)

    def test_connect_websocket_has_docstring(self):
        """测试 connect_websocket 函数有文档字符串"""
        from websocket_compat import connect_websocket

        self.assertIsNotNone(connect_websocket.__doc__)
        self.assertGreater(len(connect_websocket.__doc__), 0)

    def test_source_file_syntax(self):
        """测试源文件语法正确"""
        import subprocess
        import sys

        src_path = os.path.join(
            os.path.dirname(__file__),
            "../../src/python-gui-client/websocket_compat.py"
        )

        result = subprocess.run(
            [sys.executable, "-m", "py_compile", src_path],
            capture_output=True,
            text=True
        )

        self.assertEqual(result.returncode, 0, f"语法检查失败: {result.stderr}")


class TestIntegrationWithServerProbe(unittest.TestCase):
    """测试与 server_probe 的集成"""

    def test_server_probe_uses_connect_websocket(self):
        """测试 server_probe 使用 connect_websocket"""
        src_path = os.path.join(
            os.path.dirname(__file__),
            "../../src/python-gui-client/server_probe.py"
        )

        with open(src_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn("connect_websocket", content)
        self.assertIn("websocket_compat", content)

    def test_simple_funasr_client_uses_connect_websocket(self):
        """测试 simple_funasr_client 使用 connect_websocket"""
        src_path = os.path.join(
            os.path.dirname(__file__),
            "../../src/python-gui-client/simple_funasr_client.py"
        )

        with open(src_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn("connect_websocket", content)
        self.assertIn("websocket_compat", content)


def run_tests():
    """运行所有测试"""
    import time

    print("=" * 70)
    print("WebSocket 兼容层单元测试")
    print("=" * 70)
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python版本: {sys.version}")
    print("=" * 70)
    print()

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    test_classes = [
        TestConnectWebsocketBasic,
        TestProxyParameterCompatibility,
        TestAsyncContextManagerWrapping,
        TestOpenTimeoutParameter,
        TestErrorHandling,
        TestCodeQuality,
        TestIntegrationWithServerProbe,
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
