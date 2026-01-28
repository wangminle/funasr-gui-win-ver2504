#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V3 子进程参数传递测试

测试 GUI 调用 simple_funasr_client.py 时的参数传递规则：
1. --server_type 参数传递
2. --mode 参数传递
3. SenseVoice 参数规则（AUTO vs FUNASR_MAIN）
4. 热词参数（仅文件存在时传 --hotword）

日期: 2026-01-27
"""

import argparse
import os
import sys
import tempfile
import time
import unittest
from typing import Any, Dict, List, Optional

# 添加源码目录到路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
SRC_DIR = os.path.join(PROJECT_ROOT, "src", "python-gui-client")
sys.path.insert(0, SRC_DIR)


class SubprocessArgsBuilder:
    """模拟 GUI 构建子进程参数的逻辑

    这个类模拟 FunASRGUIClient 中构建 simple_funasr_client.py 调用参数的逻辑。
    """

    def __init__(self):
        self.python_exe = sys.executable
        self.script_path = os.path.join(SRC_DIR, "simple_funasr_client.py")

    def build_args(
        self,
        host: str,
        port: str,
        audio_file: str,
        mode: str = "offline",
        use_itn: bool = True,
        use_ssl: bool = True,
        server_type: str = "auto",
        hotword_path: Optional[str] = None,
        svs_lang: str = "auto",
        svs_itn: int = 1,
        output_dir: str = "dev/output",
        transcribe_timeout: int = 600,
    ) -> List[str]:
        """构建子进程调用参数

        Args:
            host: 服务器地址
            port: 服务器端口
            audio_file: 音频文件路径
            mode: 识别模式 (offline/online/2pass)
            use_itn: 是否启用 ITN（False 时传 --no-itn）
            use_ssl: 是否启用 SSL（False 时传 --no-ssl）
            server_type: 服务端类型 (auto/legacy/funasr_main/public_cloud)
            hotword_path: 热词文件路径
            svs_lang: SenseVoice 语种
            svs_itn: SenseVoice ITN（0/1）
            output_dir: 输出目录
            transcribe_timeout: 离线识别超时（秒）

        Returns:
            命令行参数列表
        """
        args = [
            self.python_exe,
            self.script_path,
            "--host", host,
            "--port", port,
            "--audio_in", audio_file,
            "--mode", mode,
            "--output_dir", output_dir,
            "--transcribe_timeout", str(transcribe_timeout),
        ]

        # GUI 行为：use_itn/use_ssl 通过 “--no-itn/--no-ssl” 传递
        if not use_itn:
            args.append("--no-itn")
        if not use_ssl:
            args.append("--no-ssl")

        # GUI 行为：public_cloud 不传 --server_type（由预设 IP/端口体现）
        if server_type and server_type != "public_cloud":
            args.extend(["--server_type", server_type])

        # 添加热词参数（仅当文件存在时）
        if hotword_path and os.path.exists(hotword_path):
            args.extend(["--hotword", hotword_path])

        # GUI 行为：SenseVoice 参数规则
        # - server_type in ("funasr_main", "auto") 时传 --svs_lang/--svs_itn
        # - 仅 server_type == "funasr_main" 时额外传 --enable_svs_params=1
        if server_type in ("funasr_main", "auto"):
            args.extend(["--svs_lang", svs_lang])
            args.extend(["--svs_itn", str(int(svs_itn))])
            if server_type == "funasr_main":
                args.extend(["--enable_svs_params", "1"])

        return args


# =============================================================================
# 测试1: --server_type 参数传递
# =============================================================================


class TestServerTypeParameter(unittest.TestCase):
    """测试 --server_type 参数传递"""

    def setUp(self):
        self.builder = SubprocessArgsBuilder()

    def test_server_type_auto(self):
        """测试 server_type=auto 参数传递"""
        args = self.builder.build_args(
            host="127.0.0.1",
            port="10095",
            audio_file="test.wav",
            server_type="auto",
        )

        self.assertIn("--server_type", args)
        idx = args.index("--server_type")
        self.assertEqual(args[idx + 1], "auto")

    def test_server_type_legacy(self):
        """测试 server_type=legacy 参数传递"""
        args = self.builder.build_args(
            host="127.0.0.1",
            port="10095",
            audio_file="test.wav",
            server_type="legacy",
        )

        idx = args.index("--server_type")
        self.assertEqual(args[idx + 1], "legacy")

    def test_server_type_funasr_main(self):
        """测试 server_type=funasr_main 参数传递"""
        args = self.builder.build_args(
            host="127.0.0.1",
            port="10095",
            audio_file="test.wav",
            server_type="funasr_main",
        )

        idx = args.index("--server_type")
        self.assertEqual(args[idx + 1], "funasr_main")


# =============================================================================
# 测试2: --mode 参数传递
# =============================================================================


class TestModeParameter(unittest.TestCase):
    """测试 --mode 参数传递"""

    def setUp(self):
        self.builder = SubprocessArgsBuilder()

    def test_mode_offline(self):
        """测试 mode=offline 参数传递"""
        args = self.builder.build_args(
            host="127.0.0.1",
            port="10095",
            audio_file="test.wav",
            mode="offline",
        )

        self.assertIn("--mode", args)
        idx = args.index("--mode")
        self.assertEqual(args[idx + 1], "offline")

    def test_mode_online(self):
        """测试 mode=online 参数传递"""
        args = self.builder.build_args(
            host="127.0.0.1",
            port="10095",
            audio_file="test.wav",
            mode="online",
        )

        idx = args.index("--mode")
        self.assertEqual(args[idx + 1], "online")

    def test_mode_2pass(self):
        """测试 mode=2pass 参数传递"""
        args = self.builder.build_args(
            host="127.0.0.1",
            port="10095",
            audio_file="test.wav",
            mode="2pass",
        )

        idx = args.index("--mode")
        self.assertEqual(args[idx + 1], "2pass")


# =============================================================================
# 测试3: SenseVoice 参数规则
# =============================================================================


class TestSenseVoiceParameters(unittest.TestCase):
    """测试 SenseVoice 参数传递规则"""

    def setUp(self):
        self.builder = SubprocessArgsBuilder()

    def test_auto_mode_no_svs_params(self):
        """测试 AUTO 模式下：传 svs_lang/svs_itn，但不传 enable_svs_params"""
        args = self.builder.build_args(
            host="127.0.0.1",
            port="10095",
            audio_file="test.wav",
            server_type="auto",
            svs_lang="auto",
            svs_itn=1,
        )

        self.assertIn("--svs_lang", args)
        self.assertIn("--svs_itn", args)
        self.assertNotIn("--enable_svs_params", args)

    def test_funasr_main_with_svs_params(self):
        """测试 FUNASR_MAIN 模式下传 SenseVoice 参数"""
        args = self.builder.build_args(
            host="127.0.0.1",
            port="10095",
            audio_file="test.wav",
            server_type="funasr_main",
            svs_lang="zh",
            svs_itn=1,
        )

        self.assertIn("--enable_svs_params", args)
        self.assertIn("--svs_lang", args)
        self.assertIn("--svs_itn", args)

        # 验证具体值
        idx = args.index("--enable_svs_params")
        self.assertEqual(args[idx + 1], "1")

        idx = args.index("--svs_lang")
        self.assertEqual(args[idx + 1], "zh")

        idx = args.index("--svs_itn")
        self.assertEqual(args[idx + 1], "1")

    def test_svs_lang_variants(self):
        """测试 SenseVoice 语种变体"""
        for lang in ["auto", "zh", "en", "ja", "ko", "yue"]:
            with self.subTest(lang=lang):
                args = self.builder.build_args(
                    host="127.0.0.1",
                    port="10095",
                    audio_file="test.wav",
                    server_type="auto",
                    svs_lang=lang,
                )

                idx = args.index("--svs_lang")
                self.assertEqual(args[idx + 1], lang)

    def test_svs_itn_true(self):
        """测试 SenseVoice ITN 启用"""
        args = self.builder.build_args(
            host="127.0.0.1",
            port="10095",
            audio_file="test.wav",
            server_type="auto",
            svs_itn=1,
        )

        idx = args.index("--svs_itn")
        self.assertEqual(args[idx + 1], "1")

    def test_svs_itn_false(self):
        """测试 SenseVoice ITN 禁用"""
        args = self.builder.build_args(
            host="127.0.0.1",
            port="10095",
            audio_file="test.wav",
            server_type="auto",
            svs_itn=0,
        )

        idx = args.index("--svs_itn")
        self.assertEqual(args[idx + 1], "0")


# =============================================================================
# 测试4: 热词参数
# =============================================================================


class TestHotwordParameter(unittest.TestCase):
    """测试热词参数传递"""

    def setUp(self):
        self.builder = SubprocessArgsBuilder()

    def test_hotword_with_existing_file(self):
        """测试热词文件存在时传递参数"""
        # 创建临时热词文件
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.txt', delete=False, encoding='utf-8'
        ) as f:
            f.write("阿里巴巴 20\n")
            f.write("人工智能 15\n")
            temp_hotword = f.name

        try:
            args = self.builder.build_args(
                host="127.0.0.1",
                port="10095",
                audio_file="test.wav",
                hotword_path=temp_hotword,
            )

            self.assertIn("--hotword", args)
            idx = args.index("--hotword")
            self.assertEqual(args[idx + 1], temp_hotword)
        finally:
            os.unlink(temp_hotword)

    def test_hotword_with_nonexistent_file(self):
        """测试热词文件不存在时不传递参数"""
        nonexistent_path = "/path/that/does/not/exist/hotwords.txt"

        args = self.builder.build_args(
            host="127.0.0.1",
            port="10095",
            audio_file="test.wav",
            hotword_path=nonexistent_path,
        )

        self.assertNotIn("--hotword", args)

    def test_hotword_with_empty_path(self):
        """测试热词路径为空时不传递参数"""
        args = self.builder.build_args(
            host="127.0.0.1",
            port="10095",
            audio_file="test.wav",
            hotword_path="",
        )

        self.assertNotIn("--hotword", args)

    def test_hotword_with_none(self):
        """测试热词路径为 None 时不传递参数"""
        args = self.builder.build_args(
            host="127.0.0.1",
            port="10095",
            audio_file="test.wav",
            hotword_path=None,
        )

        self.assertNotIn("--hotword", args)


# =============================================================================
# 测试5: 基础参数
# =============================================================================


class TestBasicParameters(unittest.TestCase):
    """测试基础参数传递"""

    def setUp(self):
        self.builder = SubprocessArgsBuilder()

    def test_host_and_port(self):
        """测试主机和端口参数"""
        args = self.builder.build_args(
            host="192.168.1.100",
            port="10096",
            audio_file="test.wav",
        )

        self.assertIn("--host", args)
        self.assertIn("--port", args)

        idx = args.index("--host")
        self.assertEqual(args[idx + 1], "192.168.1.100")

        idx = args.index("--port")
        self.assertEqual(args[idx + 1], "10096")

    def test_audio_file(self):
        """测试音频文件参数"""
        args = self.builder.build_args(
            host="127.0.0.1",
            port="10095",
            audio_file="/path/to/audio.wav",
        )

        self.assertIn("--audio_in", args)
        idx = args.index("--audio_in")
        self.assertEqual(args[idx + 1], "/path/to/audio.wav")

    def test_use_itn_enabled(self):
        """测试 ITN 启用"""
        args = self.builder.build_args(
            host="127.0.0.1",
            port="10095",
            audio_file="test.wav",
            use_itn=True,
        )

        self.assertNotIn("--no-itn", args)

    def test_use_itn_disabled(self):
        """测试 ITN 禁用"""
        args = self.builder.build_args(
            host="127.0.0.1",
            port="10095",
            audio_file="test.wav",
            use_itn=False,
        )

        self.assertIn("--no-itn", args)

    def test_ssl_enabled(self):
        """测试 SSL 启用"""
        args = self.builder.build_args(
            host="127.0.0.1",
            port="10095",
            audio_file="test.wav",
            use_ssl=True,
        )

        self.assertNotIn("--no-ssl", args)

    def test_ssl_disabled(self):
        """测试 SSL 禁用"""
        args = self.builder.build_args(
            host="127.0.0.1",
            port="10095",
            audio_file="test.wav",
            use_ssl=False,
        )

        self.assertIn("--no-ssl", args)


# =============================================================================
# 测试6: 参数组合
# =============================================================================


class TestParameterCombinations(unittest.TestCase):
    """测试参数组合"""

    def setUp(self):
        self.builder = SubprocessArgsBuilder()

    def test_full_parameters_combination(self):
        """测试完整参数组合"""
        # 创建临时热词文件
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.txt', delete=False, encoding='utf-8'
        ) as f:
            f.write("测试热词 10\n")
            temp_hotword = f.name

        try:
            args = self.builder.build_args(
                host="192.168.1.100",
                port="10096",
                audio_file="/path/to/audio.wav",
                mode="2pass",
                use_itn=True,
                use_ssl=True,
                server_type="funasr_main",
                hotword_path=temp_hotword,
                svs_lang="zh",
                svs_itn=1,
            )

            # 验证所有参数都存在
            self.assertIn("--host", args)
            self.assertIn("--port", args)
            self.assertIn("--audio_in", args)
            self.assertIn("--mode", args)
            self.assertIn("--server_type", args)
            self.assertIn("--hotword", args)
            self.assertIn("--enable_svs_params", args)
            self.assertIn("--svs_lang", args)
            self.assertIn("--svs_itn", args)

            # 验证具体值
            idx = args.index("--mode")
            self.assertEqual(args[idx + 1], "2pass")

            idx = args.index("--server_type")
            self.assertEqual(args[idx + 1], "funasr_main")

        finally:
            os.unlink(temp_hotword)

    def test_minimal_parameters(self):
        """测试最小参数组合"""
        args = self.builder.build_args(
            host="127.0.0.1",
            port="10095",
            audio_file="test.wav",
        )

        # 必需参数
        self.assertIn("--host", args)
        self.assertIn("--port", args)
        self.assertIn("--audio_in", args)

        # 默认参数
        self.assertIn("--mode", args)
        self.assertIn("--server_type", args)

        # 默认不传 SenseVoice 参数
        self.assertNotIn("--enable_svs_params", args)


# =============================================================================
# 测试7: 参数解析验证
# =============================================================================


class TestArgumentParserValidation(unittest.TestCase):
    """测试参数能被 simple_funasr_client 正确解析"""

    def test_parser_accepts_server_type(self):
        """测试解析器接受 --server_type 参数"""
        # 模拟解析器
        parser = argparse.ArgumentParser()
        parser.add_argument("--server_type", choices=["auto", "legacy", "funasr_main"])

        # 测试各种值
        for value in ["auto", "legacy", "funasr_main"]:
            args = parser.parse_args(["--server_type", value])
            self.assertEqual(args.server_type, value)

    def test_parser_accepts_mode(self):
        """测试解析器接受 --mode 参数"""
        parser = argparse.ArgumentParser()
        parser.add_argument("--mode", choices=["offline", "online", "2pass"])

        for value in ["offline", "online", "2pass"]:
            args = parser.parse_args(["--mode", value])
            self.assertEqual(args.mode, value)

    def test_parser_accepts_svs_params(self):
        """测试解析器接受 SenseVoice 参数"""
        parser = argparse.ArgumentParser()
        parser.add_argument("--enable_svs_params", type=int)
        parser.add_argument("--svs_lang", choices=["auto", "zh", "en", "ja", "ko", "yue"])
        parser.add_argument("--svs_itn", type=int)

        args = parser.parse_args([
            "--enable_svs_params", "1",
            "--svs_lang", "zh",
            "--svs_itn", "1"
        ])

        self.assertEqual(args.enable_svs_params, 1)
        self.assertEqual(args.svs_lang, "zh")
        self.assertEqual(args.svs_itn, 1)


# =============================================================================
# 运行测试
# =============================================================================


def run_tests():
    """运行所有测试"""
    print("=" * 70)
    print("V3 子进程参数传递测试")
    print("=" * 70)
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python版本: {sys.version}")
    print("=" * 70)
    print()

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    test_classes = [
        TestServerTypeParameter,
        TestModeParameter,
        TestSenseVoiceParameters,
        TestHotwordParameter,
        TestBasicParameters,
        TestParameterCombinations,
        TestArgumentParserValidation,
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
