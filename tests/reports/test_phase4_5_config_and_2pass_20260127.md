# Phase 4 & Phase 5 测试报告

**测试日期**: 2026-01-27  
**测试人员**: 开发团队  
**测试环境**: macOS Darwin 25.3.0 / Python 3.12

---

## 1. 测试概述

### 1.1 测试目标

验证 FunASR GUI 客户端 V3 的 Phase 4（配置持久化）和 Phase 5（2pass 探测增强）功能实现的正确性。

### 1.2 测试范围

| 阶段 | 功能模块 | 测试项 |
|------|----------|--------|
| Phase 4.1 | 配置迁移策略 | V2 -> V3 配置自动升级 |
| Phase 4.2 | 缓存探测结果 | 启动时加载缓存、24小时有效期 |
| Phase 4.3 | 探测级别持久化 | 探测级别保存/加载 |
| Phase 4.4 | 配置保存完整性 | V3 所有字段正确持久化 |
| Phase 5.1 | 探测级别控件 | GUI 选择器功能 |
| Phase 5.2 | 2pass 自动切换 | 模式联动探测级别 |
| Phase 5.3 | 探测结果展示 | 2pass 状态显示增强 |

---

## 2. 测试执行

### 2.1 测试脚本

- **脚本路径**: `tests/scripts/test_phase4_5_config_and_2pass_20260127.py`
- **测试框架**: Python unittest
- **测试用例数**: 14

### 2.2 测试结果

```
======================================================================
测试总结
======================================================================
运行测试数: 14
成功: 14
失败: 0
错误: 0
======================================================================
```

### 2.3 测试用例详情

| 序号 | 测试类 | 测试方法 | 描述 | 结果 |
|------|--------|----------|------|------|
| 1 | TestConfigMigration | test_v2_to_v3_migration_structure | V2 配置识别与迁移 | ✅ 通过 |
| 2 | TestConfigMigration | test_v3_config_structure | V3 配置结构完整性 | ✅ 通过 |
| 3 | TestProbeLevelPersistence | test_probe_level_values | 探测级别值有效性 | ✅ 通过 |
| 4 | TestProbeLevelPersistence | test_probe_level_in_config | 探测级别配置位置 | ✅ 通过 |
| 5 | TestCacheProbeResult | test_cache_structure | 缓存结构验证 | ✅ 通过 |
| 6 | TestCacheProbeResult | test_cache_time_validity | 缓存时间有效期（24小时） | ✅ 通过 |
| 7 | TestServerCapabilitiesFromDict | test_from_dict_basic | ServerCapabilities 字典创建 | ✅ 通过 |
| 8 | TestProbeLevelSelection | test_probe_level_options | 探测级别选项映射 | ✅ 通过 |
| 9 | TestTwoPassAutoSwitch | test_2pass_mode_triggers_full_probe | 2pass 模式触发完整探测 | ✅ 通过 |
| 10 | TestTwoPassAutoSwitch | test_offline_mode_keeps_light_probe | offline 模式保持轻量探测 | ✅ 通过 |
| 11 | TestProbeResultDisplay | test_2pass_unknown_display | 2pass 未判定展示 | ✅ 通过 |
| 12 | TestProbeResultDisplay | test_2pass_supported_display | 2pass 支持展示 | ✅ 通过 |
| 13 | TestProtocolAdapterIntegration | test_create_probe_level | create_probe_level 函数 | ✅ 通过 |
| 14 | TestConfigSaveIntegrity | test_config_save_all_v3_fields | 配置保存完整性 | ✅ 通过 |

---

## 3. 功能实现说明

### 3.1 Phase 4: 配置持久化

#### 3.1.1 配置迁移策略 (Phase 4.1)

**实现位置**: `funasr_gui_client_v3.py` - `load_config()` 和 `_migrate_config_to_v3()` 方法

**功能说明**:
- 启动时检测配置版本（`config_version` 字段）
- 如果版本 < 3，自动执行 V2 -> V3 迁移
- 迁移后自动保存新格式配置

**迁移映射**:
```
V2 扁平结构          →  V3 分组结构
─────────────────────────────────────
ip, port             →  server.ip, server.port
use_itn, use_ssl     →  options.use_itn, options.use_ssl
language             →  ui.language
(新增)               →  protocol.* (探测相关配置)
(新增)               →  sensevoice.* (SenseVoice 配置)
(新增)               →  cache.* (探测结果缓存)
```

#### 3.1.2 缓存探测结果 (Phase 4.2)

**实现位置**: `funasr_gui_client_v3.py` - `_restore_cached_probe_result()` 方法

**功能说明**:
- 启动时优先从 `cache.last_probe_result` 恢复探测结果
- 检查缓存有效期（24小时内有效）
- 过期缓存自动忽略，触发新探测

**缓存结构**:
```json
{
  "cache": {
    "last_probe_result": {
      "reachable": true,
      "responsive": true,
      "supports_offline": true,
      "supports_2pass": null,
      "inferred_server_type": "unknown"
    },
    "last_probe_time": "2026-01-27T10:00:00"
  }
}
```

#### 3.1.3 探测级别持久化 (Phase 4.3)

**实现位置**: 
- `_get_current_probe_level()` - 读取探测级别
- `save_config()` - 保存探测级别

**支持的探测级别**:
| 配置值 | 显示名称 | 说明 |
|--------|----------|------|
| `offline_light` | 轻量探测 | 仅离线模式探测，快速（1-3s） |
| `twopass_full` | 完整探测 | 包含 2pass 模式探测（3-5s） |

#### 3.1.4 配置保存完整性 (Phase 4.4)

**实现位置**: `save_config()` 方法

**V3 配置必需节**:
- `config_version`: 配置版本号（3）
- `server`: 服务器连接配置
- `options`: 功能选项
- `ui`: 界面配置
- `protocol`: 协议相关配置（含探测级别）
- `sensevoice`: SenseVoice 参数
- `cache`: 探测结果缓存
- `presets`: 预设配置

### 3.2 Phase 5: 2pass 探测增强

#### 3.2.1 探测级别选择控件 (Phase 5.1)

**实现位置**: `funasr_gui_client_v3.py` - 服务端配置区域

**UI 元素**:
- 探测级别标签：`probe_level_label`
- 探测级别下拉框：`probe_level_combo`
- 显示变量：`probe_level_display_var`
- 配置变量：`probe_level_var`

**选项映射**:
```python
PROBE_LEVEL_OPTIONS = [
    ("轻量探测", "offline_light"),
    ("完整探测", "twopass_full"),
]
```

#### 3.2.2 2pass 模式自动切换 (Phase 5.2)

**实现位置**: `_on_recognition_mode_changed()` 方法

**功能逻辑**:
```python
# 当识别模式切换到 2pass 时
if mode_value == "2pass":
    if probe_level_var.get() != "twopass_full":
        # 自动切换到完整探测级别
        probe_level_var.set("twopass_full")
        # 触发自动探测（如果启用）
```

**触发条件**:
- 用户选择 2pass 识别模式
- 当前探测级别不是完整探测

#### 3.2.3 增强探测结果展示 (Phase 5.3)

**实现位置**: `_format_probe_result_text()` 方法

**展示增强**:
1. **2pass 状态显示**:
   - 支持：显示 "2pass"
   - 未判定：显示 "2pass未判定"
   
2. **警告提示**:
   - 当用户选择 2pass 模式但探测未判定 2pass 能力时
   - 显示：⚠️ 2pass能力未判定，建议使用完整探测

**新增翻译键**:
```python
"probe_mode_2pass_unknown": {"zh": "2pass未判定", "en": "2pass Unknown"},
"probe_2pass_warning": {
    "zh": "⚠️ 2pass能力未判定，建议使用完整探测",
    "en": "⚠️ 2pass capability unknown, suggest full probe",
}
```

---

## 4. 修改文件清单

| 文件路径 | 修改内容 |
|----------|----------|
| `src/python-gui-client/funasr_gui_client_v3.py` | Phase 4 & 5 全部功能实现 |

### 4.1 主要修改点

1. **配置加载/保存** (`load_config`, `save_config`, `_migrate_config_to_v3`)
2. **缓存恢复** (`_restore_cached_probe_result`)
3. **探测级别** (`_get_current_probe_level`, `_on_probe_level_changed`)
4. **2pass 联动** (`_on_recognition_mode_changed`)
5. **结果展示** (`_format_probe_result_text`)
6. **UI 控件** (探测级别标签、下拉框)
7. **翻译文本** (探测级别、2pass 相关)
8. **语言切换** (`update_ui_language` 中的探测级别控件更新)

---

## 5. 测试结论

### 5.1 测试结果

**✅ 全部通过**

所有 14 个测试用例均通过，Phase 4 和 Phase 5 的功能实现符合设计要求。

### 5.2 功能验收

| 功能点 | 验收状态 |
|--------|----------|
| V2 配置自动迁移到 V3 | ✅ 通过 |
| 缓存探测结果加载与有效期检查 | ✅ 通过 |
| 探测级别保存与加载 | ✅ 通过 |
| 探测级别 UI 选择器 | ✅ 通过 |
| 2pass 模式自动切换探测级别 | ✅ 通过 |
| 2pass 状态增强展示 | ✅ 通过 |

### 5.3 后续建议

1. **集成测试**: 建议在实际服务器环境下进行端到端测试
2. **用户测试**: 建议进行 UI 可用性测试，验证探测级别切换的用户体验
3. **性能监控**: 建议监控完整探测（twopass_full）的执行时间

---

## 6. 附录

### 6.1 配置示例

```json
{
    "config_version": 3,
    "server": {
        "ip": "127.0.0.1",
        "port": "10095"
    },
    "protocol": {
        "server_type": "auto",
        "preferred_mode": "offline",
        "auto_probe_on_start": true,
        "auto_probe_on_switch": true,
        "probe_level": "offline_light",
        "connection_test_timeout": 5
    },
    "cache": {
        "last_probe_result": {
            "reachable": true,
            "responsive": true,
            "supports_offline": true,
            "supports_2pass": true
        },
        "last_probe_time": "2026-01-27T10:00:00"
    }
}
```

### 6.2 探测级别说明

| 级别 | 配置值 | 探测内容 | 预计耗时 |
|------|--------|----------|----------|
| 轻量探测 | `offline_light` | 连接测试 + 离线模式探测 | 1-3秒 |
| 完整探测 | `twopass_full` | 连接测试 + 离线模式 + 2pass模式 | 3-5秒 |

---

---

## 7. Bug 修复记录（追加）

**修复日期**: 2026-01-27 10:25

根据代码审查反馈，修复了以下问题：

### 7.1 P0 级别修复

| 问题 | 修复内容 | 修改文件 |
|------|----------|----------|
| twopass_full 超时时间不足 | 完整探测自动使用 12s 超时（原 5s），拆分离线/2pass 超时 | `server_probe.py` |
| twopass_full 在离线无响应时跳过 2pass | 移除响应前置条件，即使离线无响应也尝试 2pass 探测 | `server_probe.py` |

### 7.2 P1 级别修复

| 问题 | 修复内容 | 修改文件 |
|------|----------|----------|
| 缓存前缀 `[缓存]` 未国际化 | 添加 `probe_cached_prefix` 翻译键，支持中英文 | `funasr_gui_client_v3.py` |
| 缓存恢复不更新 `probe_reachable` 和指示器 | 缓存恢复时同步更新状态变量和 UI 指示器 | `funasr_gui_client_v3.py` |
| V2→V3 迁移丢弃用户自定义字段 | 迁移前备份原配置（`.v2.bak`），保留未知字段和自定义预设 | `funasr_gui_client_v3.py` |

### 7.3 P2 级别修复

| 问题 | 修复内容 | 修改文件 |
|------|----------|----------|
| 探测级别变更未立即保存 | 在 `_on_probe_level_changed()` 末尾调用 `save_config()` | `funasr_gui_client_v3.py` |
| "2pass未判定" 显示过于频繁 | 仅在用户选择 2pass 模式时才显示该提示 | `funasr_gui_client_v3.py` |

### 7.4 P3 级别修复

| 问题 | 修复内容 | 修改文件 |
|------|----------|----------|
| 测试脚本 CRLF 换行符 | 转换为 LF 换行符 | `test_phase4_5_config_and_2pass_20260127.py` |

### 7.5 关键代码变更

**server_probe.py - 超时优化**:
```python
# 根据探测级别调整超时时间
if level == ProbeLevel.TWOPASS_FULL:
    effective_timeout = max(timeout, 12.0)  # 完整探测至少 12 秒
else:
    effective_timeout = timeout
```

**server_probe.py - 2pass 探测条件修改**:
```python
# P0修复：即使离线无响应也尝试 2pass（存在"离线不回包但 2pass 回包"的服务端）
if level == ProbeLevel.TWOPASS_FULL and caps.reachable:
    if not caps.responsive:
        caps.probe_notes.append("离线探测无响应，仍尝试2pass探测")
    await self._probe_2pass_with_new_connection(...)
```

**funasr_gui_client_v3.py - 缓存前缀国际化**:
```python
cached_prefix = self.lang_manager.get("probe_cached_prefix")  # "[缓存]" / "[Cached]"
self.probe_result_var.set(f"{cached_prefix} {display_text}")
```

---

**报告生成时间**: 2026-01-27 09:55:04  
**Bug 修复更新时间**: 2026-01-27 10:25
