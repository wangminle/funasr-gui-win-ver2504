#!/usr/bin/env python3
"""Phase 3 GUI 集成测试脚本

测试目标：验证 Phase 3 GUI 集成功能
- 服务端配置区域控件
- 探测控制区域控件
- SenseVoice 设置区域控件
- 配置加载/保存
- 翻译文本完整性

日期: 2026-01-26
版本: 3.0
"""

import json
import os
import sys
import unittest

# 添加项目路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
src_path = os.path.join(project_root, "src", "python-gui-client")
sys.path.insert(0, src_path)


class TestPhase3TranslationKeys(unittest.TestCase):
    """测试 Phase 3 新增的翻译键是否完整"""

    def setUp(self):
        """设置测试环境"""
        # 导入语言管理器
        from funasr_gui_client_v3 import LanguageManager
        self.lang_manager = LanguageManager()

    def test_server_config_translations(self):
        """测试服务端配置区域翻译键"""
        required_keys = [
            "server_config_section",
            "server_type_label",
            "server_type_auto",
            "server_type_legacy",
            "server_type_funasr_main",
            "server_type_public_cloud",
            "recognition_mode_label",
            "mode_offline",
            "mode_2pass",
        ]
        
        for key in required_keys:
            with self.subTest(key=key):
                # 测试中文
                self.lang_manager.current_lang = "zh"
                zh_text = self.lang_manager.get(key)
                self.assertNotIn("[Missing:", zh_text, f"缺少中文翻译: {key}")
                
                # 测试英文
                self.lang_manager.current_lang = "en"
                en_text = self.lang_manager.get(key)
                self.assertNotIn("[Missing:", en_text, f"缺少英文翻译: {key}")

    def test_probe_control_translations(self):
        """测试探测控制区域翻译键"""
        required_keys = [
            "auto_probe_on_start",
            "auto_probe_on_switch",
            "probe_now",
            "probe_status_waiting",
            "probe_status_probing",
            "probe_status_success",
            "probe_status_connected",
            "probe_status_failed",
            "probe_error_check_ip_port_ssl",
            "probe_result_frame_title",  # Bug fix: 探测结果框架标题
            # Bug fix: 探测模式短名称（避免硬替换）
            "probe_mode_offline_short",
            "probe_mode_2pass_short",
            "probe_mode_realtime_short",
            "probe_capability_timestamp",
        ]
        
        for key in required_keys:
            with self.subTest(key=key):
                self.lang_manager.current_lang = "zh"
                zh_text = self.lang_manager.get(key)
                self.assertNotIn("[Missing:", zh_text, f"缺少中文翻译: {key}")
                
                self.lang_manager.current_lang = "en"
                en_text = self.lang_manager.get(key)
                self.assertNotIn("[Missing:", en_text, f"缺少英文翻译: {key}")

    def test_sensevoice_translations(self):
        """测试 SenseVoice 设置区域翻译键"""
        required_keys = [
            "sensevoice_settings",
            "svs_lang_label",
            "svs_itn_enable",
            "svs_note",
        ]
        
        for key in required_keys:
            with self.subTest(key=key):
                self.lang_manager.current_lang = "zh"
                zh_text = self.lang_manager.get(key)
                self.assertNotIn("[Missing:", zh_text, f"缺少中文翻译: {key}")
                
                self.lang_manager.current_lang = "en"
                en_text = self.lang_manager.get(key)
                self.assertNotIn("[Missing:", en_text, f"缺少英文翻译: {key}")

    def test_log_message_translations(self):
        """测试日志消息翻译键"""
        required_keys = [
            "probe_started",
            "probe_completed",
            "probe_failed_log",
            "server_type_changed",
            "recognition_mode_changed",
            "auto_probe_startup",
        ]
        
        for key in required_keys:
            with self.subTest(key=key):
                self.lang_manager.current_lang = "zh"
                zh_text = self.lang_manager.get(key)
                self.assertNotIn("[Missing:", zh_text, f"缺少中文翻译: {key}")


class TestPhase3ConfigStructure(unittest.TestCase):
    """测试 V3 配置结构"""

    def test_v3_config_structure(self):
        """测试 V3 配置文件结构完整性"""
        config_path = os.path.join(project_root, "dev", "config", "config.json")
        
        self.assertTrue(os.path.exists(config_path), "配置文件不存在")
        
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        # 检查必需的顶级键
        self.assertEqual(config.get("config_version"), 3, "配置版本应为 3")
        
        # 检查 server 结构
        self.assertIn("server", config, "缺少 server 配置节")
        self.assertIn("ip", config["server"], "缺少 server.ip")
        self.assertIn("port", config["server"], "缺少 server.port")
        
        # 检查 options 结构
        self.assertIn("options", config, "缺少 options 配置节")
        self.assertIn("use_itn", config["options"], "缺少 options.use_itn")
        self.assertIn("use_ssl", config["options"], "缺少 options.use_ssl")
        
        # 检查 protocol 结构（Phase 3 新增）
        self.assertIn("protocol", config, "缺少 protocol 配置节")
        protocol = config["protocol"]
        self.assertIn("server_type", protocol, "缺少 protocol.server_type")
        self.assertIn("preferred_mode", protocol, "缺少 protocol.preferred_mode")
        self.assertIn("auto_probe_on_start", protocol, "缺少 protocol.auto_probe_on_start")
        self.assertIn("auto_probe_on_switch", protocol, "缺少 protocol.auto_probe_on_switch")
        
        # 检查 sensevoice 结构（Phase 3 新增）
        self.assertIn("sensevoice", config, "缺少 sensevoice 配置节")
        sensevoice = config["sensevoice"]
        self.assertIn("svs_lang", sensevoice, "缺少 sensevoice.svs_lang")
        self.assertIn("svs_itn", sensevoice, "缺少 sensevoice.svs_itn")
        
        # 检查 cache 结构
        self.assertIn("cache", config, "缺少 cache 配置节")

    def test_backward_compatibility_keys(self):
        """测试向后兼容的扁平键"""
        config_path = os.path.join(project_root, "dev", "config", "config.json")
        
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        # 检查向后兼容的扁平键
        compat_keys = ["ip", "port", "use_itn", "use_ssl", "language"]
        for key in compat_keys:
            self.assertIn(key, config, f"缺少向后兼容键: {key}")


class TestServerProbeIntegration(unittest.TestCase):
    """测试服务探测器集成"""

    def test_server_probe_import(self):
        """测试 server_probe 模块导入"""
        try:
            from server_probe import ServerProbe, ServerCapabilities, ProbeLevel
            self.assertTrue(True, "server_probe 模块导入成功")
        except ImportError as e:
            self.fail(f"server_probe 模块导入失败: {e}")

    def test_server_capabilities_to_display_text(self):
        """测试 ServerCapabilities.to_display_text() 方法"""
        from server_probe import ServerCapabilities, ProbeLevel
        
        # 测试不可连接状态
        caps = ServerCapabilities(
            reachable=False,
            error="连接被拒绝"
        )
        display = caps.to_display_text()
        self.assertIn("❌", display, "不可连接状态应包含 ❌")
        
        # 测试可连接但无响应状态
        caps = ServerCapabilities(
            reachable=True,
            responsive=False
        )
        display = caps.to_display_text()
        self.assertIn("✅", display, "已连接状态应包含 ✅")
        
        # 测试完全可用状态
        caps = ServerCapabilities(
            reachable=True,
            responsive=True,
            supports_offline=True,
            has_timestamp=True,
            inferred_server_type="funasr_main"
        )
        display = caps.to_display_text()
        self.assertIn("✅", display, "可用状态应包含 ✅")
        self.assertIn("离线", display, "应显示支持的模式")

    def test_server_capabilities_to_dict(self):
        """测试 ServerCapabilities.to_dict() 方法"""
        from server_probe import ServerCapabilities, ProbeLevel
        
        caps = ServerCapabilities(
            reachable=True,
            responsive=True,
            supports_offline=True,
            is_final_semantics="always_false",
            inferred_server_type="funasr_main",
            probe_level=ProbeLevel.OFFLINE_LIGHT
        )
        
        data = caps.to_dict()
        
        self.assertTrue(data["reachable"], "reachable 应为 True")
        self.assertTrue(data["responsive"], "responsive 应为 True")
        self.assertTrue(data["supports_offline"], "supports_offline 应为 True")
        self.assertEqual(data["is_final_semantics"], "always_false")
        self.assertEqual(data["inferred_server_type"], "funasr_main")


class TestProtocolAdapterIntegration(unittest.TestCase):
    """测试协议适配器集成"""

    def test_protocol_adapter_import(self):
        """测试 protocol_adapter 模块导入"""
        try:
            from protocol_adapter import (
                ProtocolAdapter,
                ServerType,
                RecognitionMode,
                MessageProfile,
                ParsedResult,
            )
            self.assertTrue(True, "protocol_adapter 模块导入成功")
        except ImportError as e:
            self.fail(f"protocol_adapter 模块导入失败: {e}")

    def test_server_type_enum(self):
        """测试 ServerType 枚举值"""
        from protocol_adapter import ServerType
        
        self.assertEqual(ServerType.AUTO.value, "auto")
        self.assertEqual(ServerType.LEGACY.value, "legacy")
        self.assertEqual(ServerType.FUNASR_MAIN.value, "funasr_main")

    def test_recognition_mode_enum(self):
        """测试 RecognitionMode 枚举值"""
        from protocol_adapter import RecognitionMode
        
        self.assertEqual(RecognitionMode.OFFLINE.value, "offline")
        self.assertEqual(RecognitionMode.ONLINE.value, "online")
        self.assertEqual(RecognitionMode.TWOPASS.value, "2pass")

    def test_message_profile_creation(self):
        """测试 MessageProfile 创建"""
        from protocol_adapter import MessageProfile, ServerType, RecognitionMode
        
        profile = MessageProfile(
            server_type=ServerType.AUTO,
            mode=RecognitionMode.OFFLINE,
            wav_name="test.wav"
        )
        
        self.assertEqual(profile.server_type, ServerType.AUTO)
        self.assertEqual(profile.mode, RecognitionMode.OFFLINE)
        self.assertEqual(profile.wav_name, "test.wav")
        self.assertEqual(profile.wav_format, "pcm")
        self.assertEqual(profile.audio_fs, 16000)

    def test_protocol_adapter_build_start_message(self):
        """测试构建开始消息"""
        from protocol_adapter import (
            ProtocolAdapter,
            MessageProfile,
            ServerType,
            RecognitionMode,
        )
        
        adapter = ProtocolAdapter(ServerType.AUTO)
        profile = MessageProfile(
            server_type=ServerType.AUTO,
            mode=RecognitionMode.OFFLINE,
            wav_name="test.wav"
        )
        
        msg = adapter.build_start_message(profile)
        data = json.loads(msg)
        
        self.assertEqual(data["mode"], "offline")
        self.assertEqual(data["wav_name"], "test.wav")
        self.assertEqual(data["wav_format"], "pcm")
        self.assertTrue(data["is_speaking"])

    def test_protocol_adapter_parse_result(self):
        """测试解析结果消息"""
        from protocol_adapter import ProtocolAdapter, ServerType
        
        adapter = ProtocolAdapter(ServerType.AUTO)
        
        # 测试离线模式结果
        raw_msg = json.dumps({
            "mode": "offline",
            "text": "测试文本",
            "is_final": False,
            "wav_name": "test.wav"
        })
        
        result = adapter.parse_result(raw_msg)
        
        self.assertEqual(result.text, "测试文本")
        self.assertEqual(result.mode, "offline")
        self.assertFalse(result.is_final)
        self.assertTrue(result.is_complete, "离线模式收到回包应视为完成")


class TestGUIControlsExistence(unittest.TestCase):
    """测试 GUI 控件是否正确定义（无需实际创建 Tkinter 窗口）"""

    def test_gui_client_import(self):
        """测试 GUI 客户端模块导入"""
        try:
            from funasr_gui_client_v3 import FunASRGUIClient, LanguageManager
            self.assertTrue(True, "funasr_gui_client_v3 模块导入成功")
        except ImportError as e:
            self.fail(f"funasr_gui_client_v3 模块导入失败: {e}")

    def test_language_manager_methods(self):
        """测试 LanguageManager 方法"""
        from funasr_gui_client_v3 import LanguageManager
        
        lm = LanguageManager()
        
        # 测试获取翻译
        self.assertIsInstance(lm.get("app_title"), str)
        
        # 测试语言切换
        original_lang = lm.current_lang
        new_lang = lm.switch_language()
        self.assertNotEqual(original_lang, new_lang)


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestPhase3TranslationKeys))
    suite.addTests(loader.loadTestsFromTestCase(TestPhase3ConfigStructure))
    suite.addTests(loader.loadTestsFromTestCase(TestServerProbeIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestProtocolAdapterIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestGUIControlsExistence))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回测试结果
    return result.wasSuccessful()


if __name__ == "__main__":
    print("=" * 60)
    print("Phase 3 GUI 集成测试")
    print("=" * 60)
    print()
    
    success = run_tests()
    
    print()
    print("=" * 60)
    if success:
        print("✅ 所有测试通过！")
    else:
        print("❌ 部分测试失败，请检查上述错误信息。")
    print("=" * 60)
    
    sys.exit(0 if success else 1)
