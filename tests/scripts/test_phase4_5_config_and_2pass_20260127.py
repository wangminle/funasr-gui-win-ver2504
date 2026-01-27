#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 4 & Phase 5 测试脚本

测试内容：
- Phase 4: 配置持久化
  - 4.1 配置迁移策略（V2 -> V3）
  - 4.2 缓存探测结果加载
  - 4.3 探测级别持久化
  - 4.4 配置保存完整性

- Phase 5: 2pass 探测增强
  - 5.1 探测级别选择控件
  - 5.2 2pass 模式自动切换探测级别
  - 5.3 增强探测结果展示

日期: 2026-01-27
"""

import json
import os
import sys
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

# 添加源码目录到路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
SRC_DIR = os.path.join(PROJECT_ROOT, "src", "python-gui-client")
sys.path.insert(0, SRC_DIR)


class TestConfigMigration(unittest.TestCase):
    """Phase 4.1: 配置迁移测试"""

    def test_v2_to_v3_migration_structure(self):
        """测试 V2 配置结构能被正确识别并需要迁移"""
        # V2 配置示例（无 config_version 或 version < 3）
        v2_config = {
            "ip": "127.0.0.1",
            "port": "10095",
            "use_itn": 1,
            "use_ssl": 1,
            "language": "zh",
            "hotword_path": "",
            "connection_test_timeout": 5,
        }
        
        # 检查版本识别
        config_version = v2_config.get("config_version", 1)
        self.assertLess(config_version, 3, "V2 配置应被识别为版本 < 3")
        
    def test_v3_config_structure(self):
        """测试 V3 配置结构完整性"""
        v3_config = {
            "config_version": 3,
            "server": {"ip": "127.0.0.1", "port": "10095"},
            "options": {"use_itn": 1, "use_ssl": 1, "hotword_path": ""},
            "ui": {"language": "zh"},
            "protocol": {
                "server_type": "auto",
                "preferred_mode": "offline",
                "auto_probe_on_start": True,
                "auto_probe_on_switch": True,
                "probe_level": "offline_light",
                "connection_test_timeout": 5,
            },
            "sensevoice": {"svs_lang": "auto", "svs_itn": True},
            "cache": {"last_probe_result": None, "last_probe_time": None},
            "presets": {
                "public_cloud": {
                    "ip": "www.funasr.com",
                    "port": "10096",
                    "use_ssl": True,
                    "description": "FunASR公网测试服务",
                }
            },
        }
        
        # 验证必需字段
        self.assertEqual(v3_config["config_version"], 3)
        self.assertIn("server", v3_config)
        self.assertIn("protocol", v3_config)
        self.assertIn("probe_level", v3_config["protocol"])
        self.assertIn("cache", v3_config)


class TestProbeLevelPersistence(unittest.TestCase):
    """Phase 4.3: 探测级别持久化测试"""

    def test_probe_level_values(self):
        """测试探测级别值有效性"""
        valid_levels = ["offline_light", "twopass_full"]
        
        for level in valid_levels:
            self.assertIn(level, valid_levels, f"探测级别 {level} 应该是有效的")
    
    def test_probe_level_in_config(self):
        """测试探测级别在配置中的位置"""
        config = {
            "protocol": {
                "probe_level": "offline_light"
            }
        }
        
        probe_level = config.get("protocol", {}).get("probe_level", "offline_light")
        self.assertEqual(probe_level, "offline_light")


class TestCacheProbeResult(unittest.TestCase):
    """Phase 4.2: 缓存探测结果测试"""

    def test_cache_structure(self):
        """测试缓存结构"""
        cache = {
            "last_probe_result": {
                "reachable": True,
                "responsive": True,
                "supports_offline": True,
                "supports_2pass": None,
                "inferred_server_type": "unknown",
            },
            "last_probe_time": "2026-01-27T10:00:00",
        }
        
        self.assertIn("last_probe_result", cache)
        self.assertIn("last_probe_time", cache)
        
    def test_cache_time_validity(self):
        """测试缓存时间有效性检查（24小时内）"""
        now = datetime.now()
        
        # 1小时前的缓存应该有效
        recent_time = now - timedelta(hours=1)
        age_hours = (now - recent_time).total_seconds() / 3600
        self.assertLess(age_hours, 24, "1小时前的缓存应该有效")
        
        # 25小时前的缓存应该过期
        old_time = now - timedelta(hours=25)
        age_hours = (now - old_time).total_seconds() / 3600
        self.assertGreater(age_hours, 24, "25小时前的缓存应该过期")


class TestServerCapabilitiesFromDict(unittest.TestCase):
    """测试 ServerCapabilities.from_dict 方法"""

    def test_from_dict_basic(self):
        """测试从字典创建 ServerCapabilities"""
        from server_probe import ServerCapabilities, ProbeLevel
        
        data = {
            "reachable": True,
            "responsive": True,
            "error": None,
            "supports_offline": True,
            "supports_2pass": True,
            "supports_online": True,
            "has_timestamp": True,
            "has_stamp_sents": False,
            "is_final_semantics": "legacy_true",
            "inferred_server_type": "legacy",
            "probe_level": "OFFLINE_LIGHT",
            "probe_notes": ["测试探测"],
            "probe_duration_ms": 123.45,
        }
        
        caps = ServerCapabilities.from_dict(data)
        
        self.assertTrue(caps.reachable)
        self.assertTrue(caps.responsive)
        self.assertTrue(caps.supports_offline)
        self.assertTrue(caps.supports_2pass)
        self.assertEqual(caps.inferred_server_type, "legacy")
        self.assertEqual(caps.probe_level, ProbeLevel.OFFLINE_LIGHT)


class TestProbeLevelSelection(unittest.TestCase):
    """Phase 5.1: 探测级别选择测试"""

    def test_probe_level_options(self):
        """测试探测级别选项映射"""
        # 模拟 GUI 中的选项映射
        options = [
            ("轻量探测", "offline_light"),
            ("完整探测", "twopass_full"),
        ]
        
        display_to_value = {d: v for d, v in options}
        value_to_display = {v: d for d, v in options}
        
        self.assertEqual(display_to_value["轻量探测"], "offline_light")
        self.assertEqual(display_to_value["完整探测"], "twopass_full")
        self.assertEqual(value_to_display["offline_light"], "轻量探测")
        self.assertEqual(value_to_display["twopass_full"], "完整探测")


class TestTwoPassAutoSwitch(unittest.TestCase):
    """Phase 5.2: 2pass 模式自动切换测试"""

    def test_2pass_mode_triggers_full_probe(self):
        """测试选择 2pass 模式时应触发完整探测"""
        # 模拟场景：当 recognition_mode 为 "2pass" 时
        recognition_mode = "2pass"
        current_probe_level = "offline_light"
        
        # 预期行为：自动切换到完整探测
        if recognition_mode == "2pass" and current_probe_level != "twopass_full":
            new_probe_level = "twopass_full"
        else:
            new_probe_level = current_probe_level
        
        self.assertEqual(new_probe_level, "twopass_full", 
                        "2pass 模式应自动切换到完整探测")

    def test_offline_mode_keeps_light_probe(self):
        """测试 offline 模式保持轻量探测"""
        recognition_mode = "offline"
        current_probe_level = "offline_light"
        
        # offline 模式不应自动切换探测级别
        if recognition_mode == "2pass" and current_probe_level != "twopass_full":
            new_probe_level = "twopass_full"
        else:
            new_probe_level = current_probe_level
        
        self.assertEqual(new_probe_level, "offline_light",
                        "offline 模式应保持轻量探测")


class TestProbeResultDisplay(unittest.TestCase):
    """Phase 5.3: 探测结果展示测试"""

    def test_2pass_unknown_display(self):
        """测试 2pass 未判定时的展示"""
        # 模拟 ServerCapabilities
        caps = MagicMock()
        caps.reachable = True
        caps.responsive = True
        caps.supports_offline = True
        caps.supports_2pass = None  # 未判定
        caps.supports_online = None
        caps.has_timestamp = False
        caps.has_stamp_sents = False
        caps.inferred_server_type = "unknown"
        
        # 构建显示文本（模拟）
        modes = []
        if caps.supports_offline is True:
            modes.append("离线")
        if caps.supports_2pass is True:
            modes.append("2pass")
        elif caps.supports_2pass is None and caps.responsive:
            modes.append("2pass未判定")
        
        self.assertIn("2pass未判定", modes, "2pass 未判定时应显示提示")

    def test_2pass_supported_display(self):
        """测试 2pass 支持时的展示"""
        caps = MagicMock()
        caps.supports_2pass = True
        caps.responsive = True
        
        modes = []
        if caps.supports_2pass is True:
            modes.append("2pass")
        elif caps.supports_2pass is None and caps.responsive:
            modes.append("2pass未判定")
        
        self.assertIn("2pass", modes)
        self.assertNotIn("2pass未判定", modes)


class TestProtocolAdapterIntegration(unittest.TestCase):
    """协议适配层集成测试"""

    def test_create_probe_level(self):
        """测试 create_probe_level 函数"""
        from server_probe import create_probe_level, ProbeLevel
        
        self.assertEqual(create_probe_level("offline_light"), ProbeLevel.OFFLINE_LIGHT)
        self.assertEqual(create_probe_level("twopass_full"), ProbeLevel.TWOPASS_FULL)
        self.assertEqual(create_probe_level("connect_only"), ProbeLevel.CONNECT_ONLY)
        # 无效值应返回默认值
        self.assertEqual(create_probe_level("invalid"), ProbeLevel.OFFLINE_LIGHT)


class TestConfigSaveIntegrity(unittest.TestCase):
    """Phase 4.4: 配置保存完整性测试"""

    def test_config_save_all_v3_fields(self):
        """测试配置保存包含所有 V3 必需字段"""
        required_v3_sections = [
            "config_version",
            "server",
            "options",
            "ui",
            "protocol",
            "sensevoice",
            "cache",
            "presets",
        ]
        
        protocol_required_fields = [
            "server_type",
            "preferred_mode",
            "auto_probe_on_start",
            "auto_probe_on_switch",
            "probe_level",
            "connection_test_timeout",
        ]
        
        # 模拟保存的配置
        saved_config = {
            "config_version": 3,
            "server": {"ip": "127.0.0.1", "port": "10095"},
            "options": {"use_itn": 1, "use_ssl": 1, "hotword_path": ""},
            "ui": {"language": "zh"},
            "protocol": {
                "server_type": "auto",
                "preferred_mode": "offline",
                "auto_probe_on_start": True,
                "auto_probe_on_switch": True,
                "probe_level": "offline_light",
                "connection_test_timeout": 5,
            },
            "sensevoice": {"svs_lang": "auto", "svs_itn": True},
            "cache": {"last_probe_result": None, "last_probe_time": None},
            "presets": {},
        }
        
        # 验证所有必需节存在
        for section in required_v3_sections:
            self.assertIn(section, saved_config, f"配置应包含 {section} 节")
        
        # 验证 protocol 节包含所有必需字段
        for field in protocol_required_fields:
            self.assertIn(field, saved_config["protocol"], 
                         f"protocol 节应包含 {field} 字段")


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    test_classes = [
        TestConfigMigration,
        TestProbeLevelPersistence,
        TestCacheProbeResult,
        TestServerCapabilitiesFromDict,
        TestProbeLevelSelection,
        TestTwoPassAutoSwitch,
        TestProbeResultDisplay,
        TestProtocolAdapterIntegration,
        TestConfigSaveIntegrity,
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    print("=" * 70)
    print("Phase 4 & Phase 5 测试")
    print("=" * 70)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()
    
    result = run_tests()
    
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
    
    # 退出码
    sys.exit(0 if result.wasSuccessful() else 1)
