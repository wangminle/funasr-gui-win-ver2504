"""协议适配层单元测试

测试 protocol_adapter.py 的核心功能：
1. 消息构建测试
2. 结果解析测试
3. 结束判定测试（核心！）

版本: 3.0
日期: 2026-01-26
"""

import json
import os
import sys
import unittest

# 添加源码目录到路径
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "../../src/python-gui-client")
)

from protocol_adapter import (
    MessageProfile,
    ParsedResult,
    ProtocolAdapter,
    RecognitionMode,
    ServerType,
    create_adapter,
    create_message_profile,
)


class TestServerTypeEnum(unittest.TestCase):
    """测试 ServerType 枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        self.assertEqual(ServerType.AUTO.value, "auto")
        self.assertEqual(ServerType.LEGACY.value, "legacy")
        self.assertEqual(ServerType.FUNASR_MAIN.value, "funasr_main")

    def test_enum_from_string(self):
        """测试从字符串创建枚举"""
        self.assertEqual(ServerType("auto"), ServerType.AUTO)
        self.assertEqual(ServerType("legacy"), ServerType.LEGACY)
        self.assertEqual(ServerType("funasr_main"), ServerType.FUNASR_MAIN)

    def test_invalid_enum_value(self):
        """测试无效枚举值"""
        with self.assertRaises(ValueError):
            ServerType("invalid")


class TestRecognitionModeEnum(unittest.TestCase):
    """测试 RecognitionMode 枚举"""

    def test_enum_values(self):
        """测试枚举值"""
        self.assertEqual(RecognitionMode.OFFLINE.value, "offline")
        self.assertEqual(RecognitionMode.ONLINE.value, "online")
        self.assertEqual(RecognitionMode.TWOPASS.value, "2pass")


class TestMessageProfile(unittest.TestCase):
    """测试 MessageProfile 数据类"""

    def test_default_values(self):
        """测试默认值"""
        profile = MessageProfile(
            server_type=ServerType.AUTO,
            mode=RecognitionMode.OFFLINE,
            wav_name="test.wav",
        )

        self.assertEqual(profile.wav_format, "pcm")
        self.assertEqual(profile.audio_fs, 16000)
        self.assertTrue(profile.use_itn)
        self.assertTrue(profile.use_ssl)
        self.assertEqual(profile.hotwords, "")
        self.assertFalse(profile.enable_svs_params)
        self.assertEqual(profile.svs_lang, "auto")
        self.assertTrue(profile.svs_itn)
        self.assertEqual(profile.chunk_size, [5, 10, 5])
        self.assertEqual(profile.chunk_interval, 10)

    def test_custom_values(self):
        """测试自定义值"""
        profile = MessageProfile(
            server_type=ServerType.FUNASR_MAIN,
            mode=RecognitionMode.TWOPASS,
            wav_name="custom.wav",
            wav_format="wav",
            audio_fs=8000,
            use_itn=False,
            hotwords='{"热词": 10}',
            enable_svs_params=True,
            svs_lang="zh",
            chunk_size=[10, 20, 10],
        )

        self.assertEqual(profile.wav_format, "wav")
        self.assertEqual(profile.audio_fs, 8000)
        self.assertFalse(profile.use_itn)
        self.assertEqual(profile.hotwords, '{"热词": 10}')
        self.assertTrue(profile.enable_svs_params)
        self.assertEqual(profile.svs_lang, "zh")
        self.assertEqual(profile.chunk_size, [10, 20, 10])


class TestProtocolAdapterMessageBuild(unittest.TestCase):
    """测试协议适配器消息构建功能"""

    def setUp(self):
        """测试前准备"""
        self.adapter = ProtocolAdapter(ServerType.AUTO)

    def test_build_offline_message_auto(self):
        """测试构建离线模式消息（AUTO类型）"""
        profile = MessageProfile(
            server_type=ServerType.AUTO,
            mode=RecognitionMode.OFFLINE,
            wav_name="test.wav",
        )

        msg = self.adapter.build_start_message(profile)
        data = json.loads(msg)

        self.assertEqual(data["mode"], "offline")
        self.assertEqual(data["wav_name"], "test.wav")
        self.assertEqual(data["wav_format"], "pcm")
        self.assertEqual(data["audio_fs"], 16000)
        self.assertTrue(data["is_speaking"])
        self.assertTrue(data["itn"])
        # AUTO 模式默认不下发 SVS 参数
        self.assertNotIn("svs_lang", data)
        self.assertNotIn("svs_itn", data)
        # 离线模式不包含 chunk 参数
        self.assertNotIn("chunk_size", data)

    def test_build_offline_message_funasr_main(self):
        """测试构建离线模式消息（FUNASR_MAIN类型）"""
        adapter = ProtocolAdapter(ServerType.FUNASR_MAIN)
        profile = MessageProfile(
            server_type=ServerType.FUNASR_MAIN,
            mode=RecognitionMode.OFFLINE,
            wav_name="test.wav",
            svs_lang="zh",
        )

        msg = adapter.build_start_message(profile)
        data = json.loads(msg)

        # FUNASR_MAIN 模式下发 SVS 参数
        self.assertEqual(data["svs_lang"], "zh")
        self.assertTrue(data["svs_itn"])

    def test_build_twopass_message(self):
        """测试构建 2pass 模式消息"""
        profile = MessageProfile(
            server_type=ServerType.AUTO,
            mode=RecognitionMode.TWOPASS,
            wav_name="test.wav",
            chunk_size=[5, 10, 5],
            chunk_interval=10,
        )

        msg = self.adapter.build_start_message(profile)
        data = json.loads(msg)

        self.assertEqual(data["mode"], "2pass")
        self.assertEqual(data["chunk_size"], [5, 10, 5])
        self.assertEqual(data["chunk_interval"], 10)
        self.assertIn("encoder_chunk_look_back", data)
        self.assertIn("decoder_chunk_look_back", data)

    def test_build_message_with_hotwords(self):
        """测试构建带热词的消息"""
        profile = MessageProfile(
            server_type=ServerType.AUTO,
            mode=RecognitionMode.OFFLINE,
            wav_name="test.wav",
            hotwords='{"阿里巴巴": 20, "腾讯": 10}',
        )

        msg = self.adapter.build_start_message(profile)
        data = json.loads(msg)

        self.assertEqual(data["hotwords"], '{"阿里巴巴": 20, "腾讯": 10}')

    def test_build_end_message(self):
        """测试构建结束消息"""
        msg = self.adapter.build_end_message()
        data = json.loads(msg)

        self.assertFalse(data["is_speaking"])


class TestProtocolAdapterResultParse(unittest.TestCase):
    """测试协议适配器结果解析功能"""

    def setUp(self):
        """测试前准备"""
        self.adapter = ProtocolAdapter(ServerType.AUTO)

    def test_parse_basic_result(self):
        """测试解析基本结果"""
        raw_msg = json.dumps(
            {
                "mode": "offline",
                "wav_name": "test.wav",
                "text": "这是识别结果",
                "is_final": True,
            }
        )

        result = self.adapter.parse_result(raw_msg)

        self.assertEqual(result.text, "这是识别结果")
        self.assertEqual(result.mode, "offline")
        self.assertEqual(result.wav_name, "test.wav")
        self.assertTrue(result.is_final)
        self.assertTrue(result.is_complete)  # is_final=True 应该导致 is_complete=True
        self.assertIsNone(result.error)

    def test_parse_is_final_string_coercion(self):
        """测试 is_final 字段为字符串时的宽容解析"""
        raw_msg_false = json.dumps(
            {
                "mode": "offline",
                "wav_name": "test.wav",
                "text": "这是识别结果",
                "is_final": "false",
            }
        )
        result_false = self.adapter.parse_result(raw_msg_false)
        self.assertFalse(result_false.is_final)
        # offline 收到回包也应结束（避免新版服务端 is_final 恒 false 导致卡死）
        self.assertTrue(result_false.is_complete)

        raw_msg_true = json.dumps(
            {
                "mode": "offline",
                "wav_name": "test.wav",
                "text": "这是识别结果",
                "is_final": "true",
            }
        )
        result_true = self.adapter.parse_result(raw_msg_true)
        self.assertTrue(result_true.is_final)
        self.assertTrue(result_true.is_complete)

    def test_parse_stamp_sents_result(self):
        """测试解析 stamp_sents 格式结果"""
        raw_msg = json.dumps(
            {
                "mode": "offline",
                "wav_name": "test.wav",
                "stamp_sents": [
                    {"text_seg": "这是", "punc": ""},
                    {"text_seg": "识别", "punc": ""},
                    {"text_seg": "结果", "punc": "。"},
                ],
                "is_final": False,
            }
        )

        result = self.adapter.parse_result(raw_msg)

        self.assertEqual(result.text, "这是识别结果")
        self.assertIsNotNone(result.stamp_sents)
        self.assertEqual(len(result.stamp_sents), 3)

    def test_parse_2pass_offline_result(self):
        """测试解析 2pass-offline 结果"""
        raw_msg = json.dumps(
            {
                "mode": "2pass-offline",
                "wav_name": "test.wav",
                "text": "最终纠错结果",
                "is_final": False,
            }
        )

        result = self.adapter.parse_result(raw_msg)

        self.assertEqual(result.mode, "2pass-offline")
        self.assertEqual(result.text, "最终纠错结果")
        self.assertFalse(result.is_final)
        # 2pass-offline 应该导致 is_complete=True（即使 is_final=False）
        self.assertTrue(result.is_complete)

    def test_parse_invalid_json(self):
        """测试解析无效 JSON"""
        raw_msg = "invalid json {"

        result = self.adapter.parse_result(raw_msg)

        self.assertIsNotNone(result.error)
        self.assertIn("JSON解析失败", result.error)
        self.assertEqual(result.text, "")
        self.assertFalse(result.is_complete)

    def test_parse_empty_text(self):
        """测试解析空文本结果"""
        raw_msg = json.dumps(
            {"mode": "offline", "wav_name": "test.wav", "text": "", "is_final": False}
        )

        result = self.adapter.parse_result(raw_msg)

        self.assertEqual(result.text, "")
        # offline 模式收到回包应该结束（即使文本为空）
        self.assertTrue(result.is_complete)


class TestShouldComplete(unittest.TestCase):
    """测试结束判定逻辑（核心！）"""

    def setUp(self):
        """测试前准备"""
        self.adapter = ProtocolAdapter(ServerType.AUTO)

    def test_is_final_true(self):
        """测试 is_final=True 的情况"""
        raw_msg = json.dumps(
            {"mode": "offline", "text": "识别结果", "is_final": True}
        )

        result = self.adapter.parse_result(raw_msg)

        self.assertTrue(result.is_complete)

    def test_offline_mode_always_complete(self):
        """🔴 核心测试：离线模式收到任何回包都应结束"""
        # 场景1：正常文本，is_final=False（新版服务端特征）
        raw_msg1 = json.dumps(
            {"mode": "offline", "text": "识别结果", "is_final": False}
        )
        result1 = self.adapter.parse_result(raw_msg1)
        self.assertTrue(
            result1.is_complete, "离线模式收到文本回包应该结束（即使 is_final=False）"
        )

        # 场景2：空文本（静音场景）
        raw_msg2 = json.dumps({"mode": "offline", "text": "", "is_final": False})
        result2 = self.adapter.parse_result(raw_msg2)
        self.assertTrue(result2.is_complete, "离线模式收到空文本回包也应该结束（静音场景）")

    def test_2pass_offline_complete(self):
        """测试 2pass-offline 模式结束判定"""
        raw_msg = json.dumps(
            {"mode": "2pass-offline", "text": "最终结果", "is_final": False}
        )

        result = self.adapter.parse_result(raw_msg)

        self.assertTrue(
            result.is_complete, "2pass-offline 模式收到回包应该结束（最终纠错结果）"
        )

    def test_2pass_online_not_complete(self):
        """测试 2pass-online 模式不应该结束"""
        raw_msg = json.dumps(
            {"mode": "2pass-online", "text": "中间结果", "is_final": False}
        )

        result = self.adapter.parse_result(raw_msg)

        self.assertFalse(
            result.is_complete, "2pass-online 模式中间结果不应该结束"
        )

    def test_stamp_sents_complete(self):
        """测试有 stamp_sents 的情况"""
        raw_msg = json.dumps(
            {
                "mode": "2pass-online",
                "text": "",
                "stamp_sents": [{"text_seg": "结果", "punc": ""}],
                "is_final": False,
            }
        )

        result = self.adapter.parse_result(raw_msg)

        self.assertTrue(
            result.is_complete, "收到 stamp_sents 应该可以结束"
        )


class TestConvenienceFunctions(unittest.TestCase):
    """测试便捷函数"""

    def test_create_adapter(self):
        """测试 create_adapter 函数"""
        adapter = create_adapter("auto")
        self.assertEqual(adapter.server_type, ServerType.AUTO)

        adapter = create_adapter("legacy")
        self.assertEqual(adapter.server_type, ServerType.LEGACY)

        adapter = create_adapter("funasr_main")
        self.assertEqual(adapter.server_type, ServerType.FUNASR_MAIN)

        # 无效值应该使用默认值
        adapter = create_adapter("invalid")
        self.assertEqual(adapter.server_type, ServerType.AUTO)

    def test_create_message_profile(self):
        """测试 create_message_profile 函数"""
        profile = create_message_profile(
            mode="offline", wav_name="test.wav", server_type="auto"
        )

        self.assertEqual(profile.mode, RecognitionMode.OFFLINE)
        self.assertEqual(profile.wav_name, "test.wav")
        self.assertEqual(profile.server_type, ServerType.AUTO)

        # 测试 2pass 模式
        profile = create_message_profile(mode="2pass", wav_name="test.wav")
        self.assertEqual(profile.mode, RecognitionMode.TWOPASS)


class TestIsFinalSemantics(unittest.TestCase):
    """测试 is_final 语义记录功能"""

    def setUp(self):
        """测试前准备"""
        self.adapter = ProtocolAdapter(ServerType.AUTO)

    def test_record_legacy_semantics(self):
        """测试记录旧版语义"""
        self.adapter.record_is_final_semantics(is_final_value=True, mode="offline")

        self.assertEqual(self.adapter.get_is_final_semantics(), "legacy_true")

    def test_record_new_semantics(self):
        """测试记录新版语义"""
        self.adapter.record_is_final_semantics(is_final_value=False, mode="offline")

        self.assertEqual(self.adapter.get_is_final_semantics(), "always_false")


class TestEdgeCases(unittest.TestCase):
    """测试边界情况"""

    def setUp(self):
        """测试前准备"""
        self.adapter = ProtocolAdapter(ServerType.AUTO)

    def test_missing_fields(self):
        """测试缺少字段的情况"""
        raw_msg = json.dumps({"text": "只有文本"})

        result = self.adapter.parse_result(raw_msg)

        self.assertEqual(result.text, "只有文本")
        self.assertEqual(result.mode, "unknown")
        self.assertEqual(result.wav_name, "")

    def test_unicode_text(self):
        """测试 Unicode 文本"""
        raw_msg = json.dumps(
            {
                "mode": "offline",
                "text": "中文识别结果🎉",
                "is_final": True,
            }
        )

        result = self.adapter.parse_result(raw_msg)

        self.assertEqual(result.text, "中文识别结果🎉")

    def test_large_timestamp(self):
        """测试大型时间戳数据"""
        raw_msg = json.dumps(
            {
                "mode": "offline",
                "text": "测试",
                "timestamp": [[0, 100], [100, 200], [200, 300]],
                "is_final": True,
            }
        )

        result = self.adapter.parse_result(raw_msg)

        self.assertEqual(result.timestamp, [[0, 100], [100, 200], [200, 300]])


if __name__ == "__main__":
    # 设置详细输出
    unittest.main(verbosity=2)
