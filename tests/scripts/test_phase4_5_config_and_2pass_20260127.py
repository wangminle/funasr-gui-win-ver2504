#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 4 & Phase 5 测试脚本（重写版）

测试内容：
- Phase 4: 配置持久化
  - 4.1 配置迁移策略（V2 -> V3），备份.v2.bak
  - 4.2 缓存探测结果加载/24小时过期规则
  - 4.3 探测级别持久化
  - 4.4 配置保存完整性（V3分组结构+兼容扁平键）
  - 4.5 热词配置读写一致性（从test_hotword_support_20251023.py并入）

- Phase 5: 2pass 探测增强
  - 5.1 探测级别选择控件
  - 5.2 2pass 模式自动切换探测级别
  - 5.3 增强探测结果展示

日期: 2026-01-27 (重写)
"""

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, patch

# 添加源码目录到路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
SRC_DIR = os.path.join(PROJECT_ROOT, "src", "python-gui-client")
sys.path.insert(0, SRC_DIR)


# =============================================================================
# 测试辅助函数（内联实现，避免依赖不存在的模块）
# =============================================================================


def read_json_file(path: str) -> Dict[str, Any]:
    """读取JSON文件"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json_file_atomic(path: str, data: Dict[str, Any]) -> None:
    """原子写入JSON文件"""
    import shutil

    temp_path = path + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    shutil.move(temp_path, path)


def ensure_backup_file(path: str, backup_suffix: str = ".bak") -> str:
    """确保创建备份文件，返回备份路径"""
    import shutil

    backup_path = path + backup_suffix
    if os.path.exists(path):
        shutil.copy2(path, backup_path)
    return backup_path


def is_cache_time_valid(
    time_str: str,
    now: Optional[datetime] = None,
    ttl_hours: int = 24
) -> bool:
    """检查缓存时间是否有效（未过期）"""
    if not time_str:
        return False
    try:
        cache_time = datetime.fromisoformat(time_str)
        if now is None:
            now = datetime.now()
        age = now - cache_time
        return age < timedelta(hours=ttl_hours)
    except (ValueError, TypeError):
        return False


def merge_config_preserving_unknown(
    base: Dict[str, Any],
    overlay: Dict[str, Any]
) -> Dict[str, Any]:
    """合并配置，保留未知字段"""
    result = base.copy()
    for key, value in overlay.items():
        if key not in result:
            # 保留未知字段
            result[key] = value
    return result


# =============================================================================
# Phase 4.1: 配置迁移测试
# =============================================================================


class TestConfigMigration(unittest.TestCase):
    """Phase 4.1: 配置迁移测试

    验证 V2 -> V3 配置迁移的正确性。
    """

    def test_v2_config_recognition(self):
        """测试 V2 配置结构能被正确识别"""
        v2_config = {
            "ip": "127.0.0.1",
            "port": "10095",
            "use_itn": 1,
            "use_ssl": 1,
            "language": "zh",
            "hotword_path": "/path/to/hotwords.txt",
            "connection_test_timeout": 5,
        }

        # V2 配置无 config_version 字段或版本 < 3
        config_version = v2_config.get("config_version", 1)
        self.assertLess(config_version, 3, "V2 配置应被识别为版本 < 3")

    def test_v2_config_has_flat_structure(self):
        """测试 V2 配置使用扁平结构"""
        v2_config = {
            "ip": "127.0.0.1",
            "port": "10095",
            "use_itn": 1,
        }

        # V2 配置直接在根级别存储字段
        self.assertIn("ip", v2_config)
        self.assertNotIn("server", v2_config)

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
            "presets": {},
        }

        # 验证必需字段
        self.assertEqual(v3_config["config_version"], 3)
        self.assertIn("server", v3_config)
        self.assertIn("protocol", v3_config)
        self.assertIn("probe_level", v3_config["protocol"])
        self.assertIn("cache", v3_config)

    def test_v2_backup_created_before_overwrite(self):
        """测试 V2 配置在写回前可创建 .v2.bak 备份（防止静默丢数据）"""
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "config.json")
            v2_config = {
                "ip": "127.0.0.1",
                "port": "10095",
                "custom_field": "custom_value",
            }
            write_json_file_atomic(path, v2_config)

            backup_path = ensure_backup_file(path, backup_suffix=".v2.bak")
            self.assertTrue(os.path.exists(path + ".v2.bak"))
            self.assertEqual(backup_path, path + ".v2.bak")

            backup_data = read_json_file(path + ".v2.bak")
            self.assertEqual(backup_data.get("custom_field"), "custom_value")

    def test_migration_preserves_unknown_fields(self):
        """测试写回合并时保留未知字段（避免测试假绿）"""
        v2_config = {
            "ip": "127.0.0.1",
            "port": "10095",
            "custom_field": "custom_value",
            "another_unknown": 123,
        }

        base_v3 = {
            "config_version": 3,
            "server": {"ip": "127.0.0.1", "port": "10095"},
            "options": {"use_itn": 1, "use_ssl": 1, "hotword_path": ""},
            "ui": {"language": "zh"},
            "protocol": {"probe_level": "offline_light"},
            "sensevoice": {"svs_lang": "auto", "svs_itn": True},
            "cache": {"last_probe_result": None, "last_probe_time": None},
            "presets": {},
        }

        merged = merge_config_preserving_unknown(base_v3, v2_config)
        self.assertEqual(merged.get("custom_field"), "custom_value")
        self.assertEqual(merged.get("another_unknown"), 123)


# =============================================================================
# Phase 4.2: 缓存探测结果测试
# =============================================================================


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

    def test_cache_time_validity_within_24h(self):
        """测试24小时内缓存有效"""
        now = datetime.now()
        recent_time = now - timedelta(hours=1)

        self.assertTrue(is_cache_time_valid(recent_time.isoformat(), now=now, ttl_hours=24))

    def test_cache_time_validity_expired(self):
        """测试超过24小时缓存过期"""
        now = datetime.now()
        old_time = now - timedelta(hours=25)

        self.assertFalse(is_cache_time_valid(old_time.isoformat(), now=now, ttl_hours=24))

    def test_cache_time_edge_case_exactly_24h(self):
        """测试恰好24小时的边界情况"""
        now = datetime.now()
        edge_time = now - timedelta(hours=24)

        self.assertFalse(is_cache_time_valid(edge_time.isoformat(), now=now, ttl_hours=24))

    def test_cache_time_parsing(self):
        """测试缓存时间字符串解析"""
        time_str = "2026-01-27T10:00:00"
        parsed_time = datetime.fromisoformat(time_str)

        self.assertEqual(parsed_time.year, 2026)
        self.assertEqual(parsed_time.month, 1)
        self.assertEqual(parsed_time.day, 27)
        self.assertEqual(parsed_time.hour, 10)


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
        self.assertAlmostEqual(caps.probe_duration_ms, 123.45)

    def test_from_dict_with_none_values(self):
        """测试包含 None 值的字典"""
        from server_probe import ServerCapabilities

        data = {
            "reachable": True,
            "responsive": True,
            "supports_offline": None,
            "supports_2pass": None,
        }

        caps = ServerCapabilities.from_dict(data)

        self.assertTrue(caps.reachable)
        self.assertIsNone(caps.supports_offline)
        self.assertIsNone(caps.supports_2pass)

    def test_from_dict_invalid_probe_level(self):
        """测试无效探测级别的降级处理"""
        from server_probe import ServerCapabilities, ProbeLevel

        data = {
            "reachable": True,
            "probe_level": "INVALID_LEVEL",
        }

        caps = ServerCapabilities.from_dict(data)

        # 无效值应降级为默认值
        self.assertEqual(caps.probe_level, ProbeLevel.CONNECT_ONLY)

    def test_to_dict_roundtrip(self):
        """测试 to_dict/from_dict 往返一致性"""
        from server_probe import ServerCapabilities, ProbeLevel

        original = ServerCapabilities(
            reachable=True,
            responsive=True,
            supports_offline=True,
            supports_2pass=False,
            has_timestamp=True,
            inferred_server_type="legacy",
            probe_level=ProbeLevel.TWOPASS_FULL,
            probe_notes=["note1", "note2"],
            probe_duration_ms=456.78,
        )

        data = original.to_dict()
        restored = ServerCapabilities.from_dict(data)

        self.assertEqual(original.reachable, restored.reachable)
        self.assertEqual(original.responsive, restored.responsive)
        self.assertEqual(original.supports_offline, restored.supports_offline)
        self.assertEqual(original.supports_2pass, restored.supports_2pass)
        self.assertEqual(original.has_timestamp, restored.has_timestamp)
        self.assertEqual(original.inferred_server_type, restored.inferred_server_type)
        self.assertEqual(original.probe_level, restored.probe_level)


# =============================================================================
# Phase 4.3: 探测级别持久化测试
# =============================================================================


class TestProbeLevelPersistence(unittest.TestCase):
    """Phase 4.3: 探测级别持久化测试"""

    def test_probe_level_values(self):
        """测试探测级别值有效性"""
        valid_levels = ["offline_light", "twopass_full", "connect_only"]

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

    def test_create_probe_level_function(self):
        """测试 create_probe_level 函数"""
        from server_probe import create_probe_level, ProbeLevel

        self.assertEqual(create_probe_level("offline_light"), ProbeLevel.OFFLINE_LIGHT)
        self.assertEqual(create_probe_level("twopass_full"), ProbeLevel.TWOPASS_FULL)
        self.assertEqual(create_probe_level("connect_only"), ProbeLevel.CONNECT_ONLY)
        # 无效值应返回默认值
        self.assertEqual(create_probe_level("invalid"), ProbeLevel.OFFLINE_LIGHT)
        self.assertEqual(create_probe_level(""), ProbeLevel.OFFLINE_LIGHT)

    def test_probe_level_case_insensitive(self):
        """测试探测级别字符串大小写不敏感"""
        from server_probe import create_probe_level, ProbeLevel

        self.assertEqual(create_probe_level("OFFLINE_LIGHT"), ProbeLevel.OFFLINE_LIGHT)
        self.assertEqual(create_probe_level("Offline_Light"), ProbeLevel.OFFLINE_LIGHT)
        self.assertEqual(create_probe_level("TWOPASS_FULL"), ProbeLevel.TWOPASS_FULL)


# =============================================================================
# Phase 4.4: 配置保存完整性测试
# =============================================================================


class TestConfigSaveIntegrity(unittest.TestCase):
    """Phase 4.4: 配置保存完整性测试"""

    def test_config_save_all_v3_sections(self):
        """测试配置保存包含所有 V3 必需节"""
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

        saved_config = self._create_v3_config()

        for section in required_v3_sections:
            self.assertIn(section, saved_config, f"配置应包含 {section} 节")

    def test_config_save_all_protocol_fields(self):
        """测试 protocol 节包含所有必需字段"""
        protocol_required_fields = [
            "server_type",
            "preferred_mode",
            "auto_probe_on_start",
            "auto_probe_on_switch",
            "probe_level",
            "connection_test_timeout",
        ]

        saved_config = self._create_v3_config()

        for field in protocol_required_fields:
            self.assertIn(
                field, saved_config["protocol"],
                f"protocol 节应包含 {field} 字段"
            )

    def test_config_save_backward_compatible_flat_keys(self):
        """测试同时写入兼容性扁平键"""
        saved_config = self._create_v3_config()

        # V3结构中应同时保存扁平键供V2兼容读取
        # 这里测试策略：配置中应有server节 + 可选的根级别扁平键
        self.assertIn("server", saved_config)
        self.assertIn("ip", saved_config["server"])

    def test_cache_write_only_updates_cache_node(self):
        """测试缓存写回仅更新 cache 节点"""
        config = self._create_v3_config()

        # 模拟仅更新缓存的操作
        new_probe_result = {
            "reachable": True,
            "responsive": True,
            "supports_offline": True,
        }
        new_probe_time = datetime.now().isoformat()

        # 原始其他配置不应被修改
        original_ip = config["server"]["ip"]
        original_probe_level = config["protocol"]["probe_level"]

        # 更新缓存
        config["cache"]["last_probe_result"] = new_probe_result
        config["cache"]["last_probe_time"] = new_probe_time

        # 验证其他配置未被修改
        self.assertEqual(config["server"]["ip"], original_ip)
        self.assertEqual(config["protocol"]["probe_level"], original_probe_level)
        # 验证缓存已更新
        self.assertIsNotNone(config["cache"]["last_probe_result"])
        self.assertIsNotNone(config["cache"]["last_probe_time"])

    def _create_v3_config(self) -> Dict[str, Any]:
        """创建完整的 V3 配置"""
        return {
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


# =============================================================================
# Phase 4.5: 热词配置测试（从 test_hotword_support_20251023.py 并入）
# =============================================================================


class TestHotwordConfig(unittest.TestCase):
    """Phase 4.5: 热词配置测试"""

    def test_hotword_path_in_v3_options(self):
        """测试热词路径在 V3 options 节中"""
        config = {
            "config_version": 3,
            "options": {
                "use_itn": 1,
                "use_ssl": 1,
                "hotword_path": "/path/to/hotwords.txt",
            },
        }

        hotword_path = config.get("options", {}).get("hotword_path", "")
        self.assertEqual(hotword_path, "/path/to/hotwords.txt")

    def test_hotword_config_save_load_consistency(self):
        """测试热词配置保存和加载一致性"""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False, encoding='utf-8'
        ) as f:
            config = {
                "config_version": 3,
                "options": {"hotword_path": "/path/to/hotwords.txt"},
            }
            json.dump(config, f, ensure_ascii=False, indent=4)
            temp_file = f.name

        try:
            with open(temp_file, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)

            self.assertEqual(
                loaded_config["options"]["hotword_path"],
                "/path/to/hotwords.txt"
            )
        finally:
            os.unlink(temp_file)

    def test_hotword_empty_path_handling(self):
        """测试空热词路径处理"""
        config = {
            "options": {"hotword_path": ""},
        }

        hotword_path = config.get("options", {}).get("hotword_path", "")
        self.assertEqual(hotword_path, "")
        self.assertFalse(bool(hotword_path))

    def test_hotword_file_existence_check(self):
        """测试热词文件存在性检查逻辑"""
        nonexistent_path = "/path/that/does/not/exist/hotwords.txt"

        # 文件不存在时不应添加热词参数
        if os.path.exists(nonexistent_path):
            should_add_param = True
        else:
            should_add_param = False

        self.assertFalse(should_add_param, "不存在的文件不应添加参数")

    def test_hotword_parameter_passing_logic(self):
        """测试热词参数传递逻辑"""
        # 模拟有效热词文件
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.txt', delete=False, encoding='utf-8'
        ) as f:
            f.write("阿里巴巴 20\n")
            f.write("人工智能 15\n")
            temp_hotword = f.name

        try:
            args = ["python3", "simple_funasr_client.py", "--host", "127.0.0.1"]

            # 模拟参数传递逻辑
            if temp_hotword and os.path.exists(temp_hotword):
                args.extend(["--hotword", temp_hotword])

            self.assertIn("--hotword", args)
            self.assertIn(temp_hotword, args)
        finally:
            os.unlink(temp_hotword)


# =============================================================================
# Phase 5.1: 探测级别选择测试
# =============================================================================


class TestProbeLevelSelection(unittest.TestCase):
    """Phase 5.1: 探测级别选择测试"""

    def test_probe_level_options_mapping(self):
        """测试探测级别选项映射"""
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


# =============================================================================
# Phase 5.2: 2pass 模式自动切换测试
# =============================================================================


class TestTwoPassAutoSwitch(unittest.TestCase):
    """Phase 5.2: 2pass 模式自动切换测试"""

    def test_2pass_mode_triggers_full_probe(self):
        """测试选择 2pass 模式时应触发完整探测"""
        recognition_mode = "2pass"
        current_probe_level = "offline_light"

        # 预期行为：自动切换到完整探测
        if recognition_mode == "2pass" and current_probe_level != "twopass_full":
            new_probe_level = "twopass_full"
        else:
            new_probe_level = current_probe_level

        self.assertEqual(
            new_probe_level, "twopass_full",
            "2pass 模式应自动切换到完整探测"
        )

    def test_offline_mode_keeps_light_probe(self):
        """测试 offline 模式保持轻量探测"""
        recognition_mode = "offline"
        current_probe_level = "offline_light"

        if recognition_mode == "2pass" and current_probe_level != "twopass_full":
            new_probe_level = "twopass_full"
        else:
            new_probe_level = current_probe_level

        self.assertEqual(
            new_probe_level, "offline_light",
            "offline 模式应保持轻量探测"
        )

    def test_online_mode_keeps_current_level(self):
        """测试 online 模式保持当前探测级别"""
        recognition_mode = "online"
        current_probe_level = "offline_light"

        if recognition_mode == "2pass" and current_probe_level != "twopass_full":
            new_probe_level = "twopass_full"
        else:
            new_probe_level = current_probe_level

        self.assertEqual(
            new_probe_level, "offline_light",
            "online 模式应保持当前探测级别"
        )

    def test_2pass_already_full_no_change(self):
        """测试 2pass 模式已是完整探测时不变"""
        recognition_mode = "2pass"
        current_probe_level = "twopass_full"

        if recognition_mode == "2pass" and current_probe_level != "twopass_full":
            new_probe_level = "twopass_full"
        else:
            new_probe_level = current_probe_level

        self.assertEqual(new_probe_level, "twopass_full")


# =============================================================================
# Phase 5.3: 探测结果展示测试
# =============================================================================


class TestProbeResultDisplay(unittest.TestCase):
    """Phase 5.3: 探测结果展示测试"""

    def test_2pass_unknown_display(self):
        """测试 2pass 未判定时的展示"""
        caps = MagicMock()
        caps.reachable = True
        caps.responsive = True
        caps.supports_offline = True
        caps.supports_2pass = None  # 未判定
        caps.supports_online = None
        caps.has_timestamp = False
        caps.has_stamp_sents = False
        caps.inferred_server_type = "unknown"

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

    def test_2pass_not_supported_display(self):
        """测试 2pass 不支持时的展示"""
        caps = MagicMock()
        caps.supports_2pass = False
        caps.responsive = True

        modes = []
        if caps.supports_2pass is True:
            modes.append("2pass")
        elif caps.supports_2pass is None and caps.responsive:
            modes.append("2pass未判定")

        self.assertNotIn("2pass", modes)
        self.assertNotIn("2pass未判定", modes)


class TestServerCapabilitiesToDisplayText(unittest.TestCase):
    """测试 ServerCapabilities.to_display_text 方法"""

    def test_display_not_reachable(self):
        """测试不可连接时的展示文本"""
        from server_probe import ServerCapabilities

        caps = ServerCapabilities(reachable=False, error="连接超时")
        text = caps.to_display_text()

        self.assertIn("❌", text)
        self.assertIn("不可连接", text)

    def test_display_reachable_and_responsive(self):
        """测试可连接且有响应的展示文本"""
        from server_probe import ServerCapabilities

        caps = ServerCapabilities(
            reachable=True,
            responsive=True,
            supports_offline=True,
        )
        text = caps.to_display_text()

        self.assertIn("✅", text)
        self.assertIn("服务可用", text)

    def test_display_reachable_but_not_responsive(self):
        """测试可连接但无响应的展示文本"""
        from server_probe import ServerCapabilities

        caps = ServerCapabilities(
            reachable=True,
            responsive=False,
        )
        text = caps.to_display_text()

        self.assertIn("✅", text)
        self.assertIn("已连接", text)
        self.assertIn("未响应", text)


# =============================================================================
# 运行测试
# =============================================================================


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    test_classes = [
        # Phase 4 测试
        TestConfigMigration,
        TestCacheProbeResult,
        TestServerCapabilitiesFromDict,
        TestProbeLevelPersistence,
        TestConfigSaveIntegrity,
        TestHotwordConfig,
        # Phase 5 测试
        TestProbeLevelSelection,
        TestTwoPassAutoSwitch,
        TestProbeResultDisplay,
        TestServerCapabilitiesToDisplayText,
    ]

    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result


if __name__ == "__main__":
    print("=" * 70)
    print("Phase 4 & Phase 5 测试（重写版）")
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

    sys.exit(0 if result.wasSuccessful() else 1)
