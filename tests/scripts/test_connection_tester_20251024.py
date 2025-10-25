#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ConnectionTester类测试脚本

测试目标：
1. 类初始化和配置
2. URI构建逻辑
3. SSL上下文创建
4. 错误类型解析
5. 用户友好消息生成
6. 连接测试基本流程（模拟）

创建时间：2025-10-24
"""

import sys
import os
import unittest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock

# 添加 src 目录到路径
sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/python-gui-client"))
)

# 导入被测试的模块
from connection_tester import (
    ConnectionTester,
    ConnectionTestResult,
    ErrorType,
    test_connection,
)


class TestConnectionTester(unittest.TestCase):
    """ConnectionTester类测试"""
    
    def setUp(self):
        """设置测试环境"""
        self.tester = ConnectionTester(timeout=5)
    
    def test_01_initialization(self):
        """测试1: 初始化"""
        print("\n测试1: ConnectionTester初始化")
        
        # 默认参数
        tester1 = ConnectionTester()
        self.assertEqual(tester1.timeout, 10)
        self.assertIsNotNone(tester1.init_message)
        self.assertEqual(tester1.init_message.get("mode"), "offline")
        print("  ✓ 默认参数正确")
        
        # 自定义参数
        custom_message = {"mode": "online", "test": True}
        tester2 = ConnectionTester(timeout=5, init_message=custom_message)
        self.assertEqual(tester2.timeout, 5)
        self.assertEqual(tester2.init_message, custom_message)
        print("  ✓ 自定义参数正确")
    
    def test_02_build_uri(self):
        """测试2: URI构建"""
        print("\n测试2: URI构建")
        
        # WebSocket URI
        uri_ws = self.tester._build_uri("127.0.0.1", 10095, False)
        self.assertEqual(uri_ws, "ws://127.0.0.1:10095")
        print(f"  ✓ WebSocket URI: {uri_ws}")
        
        # WebSocket Secure URI
        uri_wss = self.tester._build_uri("127.0.0.1", 10095, True)
        self.assertEqual(uri_wss, "wss://127.0.0.1:10095")
        print(f"  ✓ WebSocket Secure URI: {uri_wss}")
        
        # 其他主机
        uri_remote = self.tester._build_uri("example.com", 8080, False)
        self.assertEqual(uri_remote, "ws://example.com:8080")
        print(f"  ✓ 远程URI: {uri_remote}")
    
    def test_03_ssl_context(self):
        """测试3: SSL上下文创建"""
        print("\n测试3: SSL上下文创建")
        
        # 不使用SSL
        ssl_ctx_none = self.tester._create_ssl_context(False)
        self.assertIsNone(ssl_ctx_none)
        print("  ✓ 不使用SSL时返回None")
        
        # 使用SSL
        ssl_ctx = self.tester._create_ssl_context(True)
        self.assertIsNotNone(ssl_ctx)
        import ssl
        self.assertIsInstance(ssl_ctx, ssl.SSLContext)
        self.assertFalse(ssl_ctx.check_hostname)
        self.assertEqual(ssl_ctx.verify_mode, ssl.CERT_NONE)
        print("  ✓ SSL上下文创建成功")
        print(f"    - check_hostname: {ssl_ctx.check_hostname}")
        print(f"    - verify_mode: {ssl_ctx.verify_mode}")
    
    def test_04_parse_error_types(self):
        """测试4: 错误类型解析"""
        print("\n测试4: 错误类型解析")
        
        # 先导入websockets以便测试
        self.tester._import_websockets()
        
        # 网络错误
        error_network = ConnectionRefusedError("Connection refused")
        error_type = self.tester._parse_error(error_network)
        self.assertEqual(error_type, ErrorType.NETWORK)
        print("  ✓ ConnectionRefusedError -> NETWORK")
        
        # 超时错误
        error_timeout = asyncio.TimeoutError()
        error_type = self.tester._parse_error(error_timeout)
        self.assertEqual(error_type, ErrorType.TIMEOUT)
        print("  ✓ TimeoutError -> TIMEOUT")
        
        # SSL错误
        import ssl
        error_ssl = ssl.SSLError("SSL error")
        error_type = self.tester._parse_error(error_ssl)
        self.assertEqual(error_type, ErrorType.SSL)
        print("  ✓ SSLError -> SSL")
        
        # 未知错误
        error_unknown = ValueError("Unknown error")
        error_type = self.tester._parse_error(error_unknown)
        self.assertEqual(error_type, ErrorType.UNKNOWN)
        print("  ✓ ValueError -> UNKNOWN")
    
    def test_05_user_friendly_messages(self):
        """测试5: 用户友好消息"""
        print("\n测试5: 用户友好消息")
        
        # 网络错误消息
        msg = self.tester._get_user_friendly_message(
            ErrorType.NETWORK, ConnectionRefusedError()
        )
        self.assertIn("无法连接", msg)
        print(f"  ✓ NETWORK: {msg}")
        
        # 超时错误消息
        msg = self.tester._get_user_friendly_message(
            ErrorType.TIMEOUT, asyncio.TimeoutError()
        )
        self.assertIn("超时", msg)
        print(f"  ✓ TIMEOUT: {msg}")
        
        # SSL错误消息
        import ssl
        msg = self.tester._get_user_friendly_message(
            ErrorType.SSL, ssl.SSLError()
        )
        self.assertIn("SSL", msg)
        print(f"  ✓ SSL: {msg}")
    
    def test_06_connection_test_result(self):
        """测试6: 连接测试结果数据类"""
        print("\n测试6: ConnectionTestResult数据类")
        
        # 成功结果
        result_success = ConnectionTestResult(
            success=True,
            error_type=None,
            error_message="连接成功",
            technical_details="测试详情",
            response_received=True,
            response_data="{\"test\": true}",
        )
        self.assertTrue(result_success.success)
        self.assertIsNone(result_success.error_type)
        self.assertTrue(result_success.response_received)
        print("  ✓ 成功结果创建正确")
        
        # 失败结果
        result_failure = ConnectionTestResult(
            success=False,
            error_type=ErrorType.NETWORK,
            error_message="连接失败",
            technical_details="详细错误信息",
        )
        self.assertFalse(result_failure.success)
        self.assertEqual(result_failure.error_type, ErrorType.NETWORK)
        print("  ✓ 失败结果创建正确")
        
        # 部分成功结果
        result_partial = ConnectionTestResult(
            success=True,
            error_type=None,
            error_message="连接成功（无响应）",
            technical_details="建链成功但未收到响应",
            partial_success=True,
            response_received=False,
        )
        self.assertTrue(result_partial.success)
        self.assertTrue(result_partial.partial_success)
        self.assertFalse(result_partial.response_received)
        print("  ✓ 部分成功结果创建正确")
    
    def test_07_setters(self):
        """测试7: 配置方法"""
        print("\n测试7: 配置方法")
        
        # 设置超时
        self.tester.set_timeout(15)
        self.assertEqual(self.tester.timeout, 15)
        print("  ✓ set_timeout 正常工作")
        
        # 设置初始化消息
        new_message = {"mode": "2pass", "test": "value"}
        self.tester.set_init_message(new_message)
        self.assertEqual(self.tester.init_message, new_message)
        print("  ✓ set_init_message 正常工作")
    
    async def test_08_connection_refused(self):
        """测试8: 连接被拒绝场景（实际测试）"""
        print("\n测试8: 连接被拒绝场景")
        
        # 测试连接到不存在的端口（实际会被拒绝）
        result = await self.tester.test_connection("127.0.0.1", 65535, False)
        
        # 应该失败
        self.assertFalse(result.success)
        # 错误类型应该是网络错误或超时
        self.assertIn(result.error_type, [ErrorType.NETWORK, ErrorType.TIMEOUT])
        print(f"  ✓ 错误类型: {result.error_type.value}")
        print(f"  ✓ 错误消息: {result.error_message}")
        print(f"  ✓ 技术详情: {result.technical_details}")
    
    async def test_09_invalid_host(self):
        """测试9: 无效主机场景"""
        print("\n测试9: 无效主机场景")
        
        # 测试无效的主机名
        result = await self.tester.test_connection("invalid.host.test", 10095, False)
        
        # 应该失败
        self.assertFalse(result.success)
        # 应该是网络错误或超时
        self.assertIn(result.error_type, [ErrorType.NETWORK, ErrorType.TIMEOUT])
        print(f"  ✓ 错误类型: {result.error_type.value}")
        print(f"  ✓ 错误消息: {result.error_message}")
    
    def test_10_convenience_function(self):
        """测试10: 便捷函数"""
        print("\n测试10: 便捷函数test_connection")
        
        # 这只是一个语法测试，实际连接会在集成测试中验证
        self.assertIsNotNone(test_connection)
        print("  ✓ test_connection函数存在")
        print("  ℹ️  实际连接测试需要在集成测试中进行")


def run_sync_tests():
    """运行同步测试"""
    print("=" * 70)
    print("ConnectionTester 类测试")
    print("=" * 70)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加同步测试
    suite.addTests(loader.loadTestsFromName('__main__.TestConnectionTester.test_01_initialization'))
    suite.addTests(loader.loadTestsFromName('__main__.TestConnectionTester.test_02_build_uri'))
    suite.addTests(loader.loadTestsFromName('__main__.TestConnectionTester.test_03_ssl_context'))
    suite.addTests(loader.loadTestsFromName('__main__.TestConnectionTester.test_04_parse_error_types'))
    suite.addTests(loader.loadTestsFromName('__main__.TestConnectionTester.test_05_user_friendly_messages'))
    suite.addTests(loader.loadTestsFromName('__main__.TestConnectionTester.test_06_connection_test_result'))
    suite.addTests(loader.loadTestsFromName('__main__.TestConnectionTester.test_07_setters'))
    suite.addTests(loader.loadTestsFromName('__main__.TestConnectionTester.test_10_convenience_function'))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


async def run_async_tests():
    """运行异步测试"""
    print("\n" + "=" * 70)
    print("ConnectionTester 异步测试（需要网络访问）")
    print("=" * 70)
    
    test_case = TestConnectionTester()
    test_case.setUp()
    
    passed = 0
    failed = 0
    
    try:
        print("\n执行异步测试...")
        await test_case.test_08_connection_refused()
        print("✓ test_08_connection_refused 通过")
        passed += 1
    except Exception as e:
        print(f"✗ test_08_connection_refused 失败: {e}")
        failed += 1
    
    try:
        await test_case.test_09_invalid_host()
        print("✓ test_09_invalid_host 通过")
        passed += 1
    except Exception as e:
        print(f"✗ test_09_invalid_host 失败: {e}")
        failed += 1
    
    print(f"\n异步测试完成: {passed}通过, {failed}失败")
    return failed == 0


def main():
    """主函数"""
    # 运行同步测试
    sync_result = run_sync_tests()
    
    # 运行异步测试
    async_success = asyncio.run(run_async_tests())
    
    # 打印总结
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)
    
    total_tests = sync_result.testsRun + 2  # 加上2个异步测试
    failed_tests = len(sync_result.failures) + len(sync_result.errors)
    if not async_success:
        failed_tests += 2
    
    success_tests = total_tests - failed_tests
    
    print(f"总测试数: {total_tests}")
    print(f"成功: {success_tests}")
    print(f"失败: {failed_tests}")
    
    if failed_tests == 0:
        print("\n✅ 所有测试通过！")
        return 0
    else:
        print(f"\n❌ 有 {failed_tests} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())

