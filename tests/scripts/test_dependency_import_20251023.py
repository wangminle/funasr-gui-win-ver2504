#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V3 依赖导入测试脚本（重写版）

测试目标：
1. import 阶段不解析 CLI 参数、不抛 SystemExit
2. 运行阶段缺依赖时提示友好
3. websocket_compat.connect_websocket 兼容逻辑存在
4. GUI 启动时依赖检查功能

日期: 2026-01-27 (重写)
"""

import os
import subprocess
import sys
import time
import unittest

# 获取项目根目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
SRC_DIR = os.path.join(PROJECT_ROOT, "src", "python-gui-client")
CLIENT_SCRIPT = os.path.join(SRC_DIR, "simple_funasr_client.py")
GUI_SCRIPT = os.path.join(SRC_DIR, "funasr_gui_client_v3.py")
WEBSOCKET_COMPAT_SCRIPT = os.path.join(SRC_DIR, "websocket_compat.py")


class TestImportWithoutCLIParsing(unittest.TestCase):
    """测试1: import 阶段不解析 CLI 参数"""

    def test_import_simple_client_no_sysexit(self):
        """测试 import simple_funasr_client 不会触发 SystemExit"""
        # 使用子进程测试，避免污染当前进程
        test_code = """
import sys
sys.path.insert(0, r'{src_dir}')
try:
    import simple_funasr_client
    print('IMPORT_SUCCESS')
except SystemExit as e:
    print(f'SYSEXIT: {{e.code}}')
except Exception as e:
    print(f'ERROR: {{e}}')
""".format(src_dir=SRC_DIR)

        result = subprocess.run(
            [sys.executable, "-c", test_code],
            capture_output=True,
            text=True,
            timeout=30,
        )

        self.assertIn("IMPORT_SUCCESS", result.stdout,
                      f"import 应成功，实际输出: {result.stdout}\n{result.stderr}")
        self.assertNotIn("SYSEXIT", result.stdout,
                         "import 阶段不应触发 SystemExit")

    def test_import_gui_client_no_sysexit(self):
        """测试 import funasr_gui_client_v3 不会触发 SystemExit"""
        test_code = """
import sys
sys.path.insert(0, r'{src_dir}')
try:
    # 仅导入模块，不运行主函数
    import funasr_gui_client_v3
    print('IMPORT_SUCCESS')
except SystemExit as e:
    print(f'SYSEXIT: {{e.code}}')
except Exception as e:
    print(f'ERROR: {{e}}')
""".format(src_dir=SRC_DIR)

        result = subprocess.run(
            [sys.executable, "-c", test_code],
            capture_output=True,
            text=True,
            timeout=30,
        )

        self.assertIn("IMPORT_SUCCESS", result.stdout,
                      f"import 应成功，实际输出: {result.stdout}\n{result.stderr}")
        self.assertNotIn("SYSEXIT", result.stdout,
                         "import 阶段不应触发 SystemExit")


class TestSyntaxCheck(unittest.TestCase):
    """测试2: 语法检查"""

    def test_simple_client_syntax(self):
        """测试 simple_funasr_client.py 语法正确"""
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", CLIENT_SCRIPT],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0,
                         f"语法检查失败: {result.stderr}")

    def test_gui_client_syntax(self):
        """测试 funasr_gui_client_v3.py 语法正确"""
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", GUI_SCRIPT],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0,
                         f"语法检查失败: {result.stderr}")

    def test_websocket_compat_syntax(self):
        """测试 websocket_compat.py 语法正确"""
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", WEBSOCKET_COMPAT_SCRIPT],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0,
                         f"语法检查失败: {result.stderr}")


class TestWebsocketCompatModule(unittest.TestCase):
    """测试3: websocket_compat 兼容层"""

    def test_connect_websocket_exists(self):
        """测试 connect_websocket 函数存在"""
        sys.path.insert(0, SRC_DIR)
        try:
            from websocket_compat import connect_websocket
            self.assertTrue(callable(connect_websocket),
                            "connect_websocket 应该是可调用的")
        finally:
            sys.path.remove(SRC_DIR)

    def test_websocket_compat_has_proxy_handling(self):
        """测试 websocket_compat 包含 proxy 参数处理逻辑"""
        with open(WEBSOCKET_COMPAT_SCRIPT, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查是否包含 proxy 相关处理
        self.assertIn("proxy", content.lower(),
                      "websocket_compat 应包含 proxy 参数处理")
        self.assertIn("disable_proxy", content,
                      "websocket_compat 应包含 disable_proxy 参数")

    def test_websocket_compat_handles_old_websockets(self):
        """测试 websocket_compat 处理旧版 websockets 的兼容逻辑"""
        with open(WEBSOCKET_COMPAT_SCRIPT, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查是否包含 TypeError 捕获（用于旧版 websockets 不支持 proxy）
        self.assertIn("TypeError", content,
                      "websocket_compat 应捕获 TypeError 以兼容旧版")

    def test_websocket_compat_async_context_wrapper(self):
        """测试 websocket_compat 包含异步上下文管理器包装"""
        with open(WEBSOCKET_COMPAT_SCRIPT, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查是否包含异步上下文管理器相关代码
        self.assertIn("__aenter__", content,
                      "websocket_compat 应处理 __aenter__ 方法")
        self.assertIn("__aexit__", content,
                      "websocket_compat 应处理 __aexit__ 方法")


class TestGUIDependencyCheck(unittest.TestCase):
    """测试4: GUI 依赖检查功能"""

    def test_gui_has_check_dependencies_method(self):
        """测试 GUI 包含 check_dependencies 方法或相关逻辑"""
        with open(GUI_SCRIPT, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查是否包含依赖检查相关代码
        has_check = (
            "check_dependencies" in content or
            "import_module" in content or
            "check_module" in content or
            "missing" in content.lower()
        )
        self.assertTrue(has_check,
                        "GUI 应包含依赖检查功能")

    def test_gui_checks_websockets(self):
        """测试 GUI 检查 websockets 依赖"""
        with open(GUI_SCRIPT, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn("websockets", content,
                      "GUI 应检查 websockets 依赖")

    def test_gui_checks_mutagen(self):
        """测试 GUI 检查 mutagen 依赖"""
        with open(GUI_SCRIPT, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn("mutagen", content,
                      "GUI 应检查 mutagen 依赖")


class TestErrorMessages(unittest.TestCase):
    """测试5: 错误提示友好性"""

    def test_simple_client_has_install_hint(self):
        """测试 simple_funasr_client 包含安装提示"""
        with open(CLIENT_SCRIPT, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查是否包含安装指导
        has_hint = (
            "pip install" in content or
            "安装" in content or
            "install" in content.lower()
        )
        self.assertTrue(has_hint,
                        "simple_funasr_client 应包含依赖安装提示")

    def test_gui_has_error_dialog(self):
        """测试 GUI 包含错误对话框"""
        with open(GUI_SCRIPT, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查是否包含错误对话框
        has_dialog = (
            "messagebox.showerror" in content or
            "messagebox.showwarning" in content or
            "错误" in content
        )
        self.assertTrue(has_dialog,
                        "GUI 应包含错误提示对话框")


class TestDelayedImport(unittest.TestCase):
    """测试6: 延迟导入机制"""

    def test_simple_client_delayed_websockets_import(self):
        """测试 simple_funasr_client 延迟导入 websockets"""
        with open(CLIENT_SCRIPT, 'r', encoding='utf-8') as f:
            content = f.read()

        # 顶层导入部分（文件开头的 import 语句）
        lines = content.split('\n')
        toplevel_imports = []

        for line in lines[:100]:  # 检查前100行
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            if stripped.startswith('import ') or stripped.startswith('from '):
                if 'websockets' in stripped:
                    toplevel_imports.append(line)
            elif (not stripped.startswith('import') and
                  not stripped.startswith('from') and
                  not stripped.startswith('"""') and
                  not stripped.startswith("'''")):
                # 遇到非导入语句（排除多行字符串）
                if (stripped and
                    not stripped.startswith('#') and
                    '=' not in stripped[:20] and
                    not stripped.startswith('if ')):
                    break

        # 顶层不应直接 import websockets（应通过 websocket_compat）
        self.assertEqual(len(toplevel_imports), 0,
                         f"顶层不应直接导入 websockets: {toplevel_imports}")

    def test_uses_websocket_compat(self):
        """测试 simple_funasr_client 使用 websocket_compat"""
        with open(CLIENT_SCRIPT, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn("websocket_compat", content,
                      "应使用 websocket_compat 模块")
        self.assertIn("connect_websocket", content,
                      "应使用 connect_websocket 函数")


class TestProtocolAdapterImport(unittest.TestCase):
    """测试7: 协议适配层导入"""

    def test_protocol_adapter_fallback_import(self):
        """测试 protocol_adapter 的降级导入机制"""
        with open(CLIENT_SCRIPT, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查是否包含 ImportError 降级处理
        self.assertIn("ImportError", content,
                      "应包含 ImportError 降级处理")
        self.assertIn("importlib", content,
                      "应包含 importlib 动态导入机制")

    def test_protocol_adapter_module_exists(self):
        """测试 protocol_adapter.py 模块存在"""
        protocol_adapter_path = os.path.join(SRC_DIR, "protocol_adapter.py")
        self.assertTrue(os.path.exists(protocol_adapter_path),
                        "protocol_adapter.py 应存在")


class TestCLIArgsNotParsedOnImport(unittest.TestCase):
    """测试8: CLI 参数解析延迟"""

    def test_args_is_none_after_import(self):
        """测试 import 后 args 为 None"""
        test_code = """
import sys
sys.path.insert(0, r'{src_dir}')
import simple_funasr_client
print(f'ARGS_IS_NONE: {{simple_funasr_client.args is None}}')
""".format(src_dir=SRC_DIR)

        result = subprocess.run(
            [sys.executable, "-c", test_code],
            capture_output=True,
            text=True,
            timeout=30,
        )

        self.assertIn("ARGS_IS_NONE: True", result.stdout,
                      f"import 后 args 应为 None，实际输出: {result.stdout}")

    def test_parser_defined_but_not_called(self):
        """测试 parser 定义但未在 import 时调用 parse_args"""
        with open(CLIENT_SCRIPT, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查 args 初始化
        self.assertIn("args: Any = None", content,
                      "args 应初始化为 None")

        # parse_args 应只在函数内调用，不在模块级别
        lines = content.split('\n')
        module_level_parse = False
        in_function = False

        for line in lines:
            stripped = line.strip()
            if stripped.startswith('def ') or stripped.startswith('async def '):
                in_function = True
            if not in_function and 'parse_args()' in stripped:
                module_level_parse = True
                break

        self.assertFalse(module_level_parse,
                         "parse_args() 不应在模块级别调用")


def run_tests():
    """运行所有测试"""
    print("=" * 70)
    print("V3 依赖导入测试（重写版）")
    print("=" * 70)
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python版本: {sys.version}")
    print(f"项目根目录: {PROJECT_ROOT}")
    print(f"源码目录: {SRC_DIR}")
    print("=" * 70)
    print()

    # 检查文件是否存在
    if not os.path.exists(CLIENT_SCRIPT):
        print(f"✗ 错误: 找不到脚本文件: {CLIENT_SCRIPT}")
        return None

    if not os.path.exists(GUI_SCRIPT):
        print(f"✗ 错误: 找不到脚本文件: {GUI_SCRIPT}")
        return None

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    test_classes = [
        TestImportWithoutCLIParsing,
        TestSyntaxCheck,
        TestWebsocketCompatModule,
        TestGUIDependencyCheck,
        TestErrorMessages,
        TestDelayedImport,
        TestProtocolAdapterImport,
        TestCLIArgsNotParsedOnImport,
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

    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"  - {test}")

    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"  - {test}")

    print("=" * 70)

    return result


if __name__ == "__main__":
    result = run_tests()
    if result:
        sys.exit(0 if result.wasSuccessful() else 1)
    else:
        sys.exit(1)
