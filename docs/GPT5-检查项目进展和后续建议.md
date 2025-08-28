我先快速浏览关键代码与文档，核对目录/注释/命名是否符合`.cursorrules`，并检查测试脚本的预期，以便给出精准的开发建议与合规评估。随后我会根据阅读结果总结现有功能与进度，并提出下一步开发方案。
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool

我已快速通读核心代码与四类文档，并抽查了关键测试脚本；下面给出“功能/进度评估”“.cursorrules合规性评估”“发现的不一致点/风险”“下一步开发建议”。

### 现有功能与开发进度（基于代码与文档交叉验证）
- 已实现（稳定）
  - 多语言UI与资源管理、结果/日志分离、配置持久化（`dev/config/config.json`）、文件/日志/输出路径统一（`dev/logs` 与 `dev/output`）、日志轮转（5MB×3）、WebSocket连接测试（含SSL/超时与异常分支）、调用子进程识别（`simple_funasr_client.py`）、基础错误处理与弹窗提示。
  - 智能时长预估（mutagen获取媒体时长 + 测速结果动态估算 + 动态通信超时 + 兜底20分钟）。
  - 速度测试（两文件串行，记录上传/转写时间，计算上传MB/s与转写倍速，UI提示与弹窗结果；测速结果回填到时长管理器）。
- 已具备但需打磨
  - 速度测试依赖 `dev/demo/tv-report-1.mp4/.wav`，当前仓库未包含样例，实际运行会报“测试文件不存在”；建议补齐或降级为“引导下载/自动生成小样例”。
  - 翻译资源中有重复键（如“trying_websocket_connection”和“websocket_connected”等成对重复），不影响运行但应清理，减少维护成本。
- 未实现（文档中列为后续/可选）
  - 热词UI/传参（`--hotword`）、Online/2Pass模式选择与参数配置（`--mode`、`--chunk_size`、`--chunk_interval`）、可选自定义输出目录、并发参数（`--thread_num`）、打包（nuitka/pyinstaller）等。

### 与.cursorrules规范的遵从度
- 目录与职责
  - 主目录含 `dev/docs/tests/ref`，开发主目录为 `dev`，代码全在 `dev/src`，输出在 `dev/output`，日志在 `dev/logs`，配置在 `dev/config`。符合。
- 注释与风格
  - 全面中文注释；类名驼峰、函数名下划线，符合。
- 文档管理
  - 四大文档均在 `docs/` 且为markdown，命名带前缀，符合；但存在少量内容与实现不一致（见下文“不一致点”）。
- 测试标准
  - 有较完整测试脚本与测试总结（多日期），覆盖正常/边界/异常；基本符合。  
- 结论
  - 结论：基本严格遵守.cursorrules；主要改进点集中在“文档与实现一致性”和“demo资源补齐”。

### 发现的不一致点/风险（需优先处理）
- 文档与实现不一致（取消功能）
  - 架构文档明确“移除取消功能”（引用）：
```126:140:docs/funasr-python-gui-client-v2-架构设计.md
#### 4.1.2 架构简化要点
# 移除的复杂功能（基于v0.2.0对齐）
- recognition_running 状态变量
- cancel_event 取消事件
- 复杂的取消识别功能
- 过度的异步处理逻辑
```
  - 但UI文档仍包含“取消识别功能系统”（引用）：
```251:268:docs/funasr-python-gui-client-v2-UI定义.md
## 10. 取消识别功能系统
*   **核心机制**: 
    *   **状态管理**: 使用 `self.recognition_running` ...
    *   **取消信号**: 使用 `self.cancel_event` ...
...
```
  - 建议：统一口径（倾向沿用架构简化：不提供取消），UI文档改为“待办/可选”或删除本节。
- 文档中“结果输出目录”与实现不一致
  - 代码输出到 `dev/output`；架构文档个别处仍提“dev/release/results”。建议统一为 `dev/output`，与.cursorrules一致。
- 速度测试依赖资源缺失
  - 代码硬编码期望 `dev/demo/tv-report-1.mp4/.wav`；当前仓库无样例（引用）：
```2323:2337:dev/src/python-gui-client/funasr_gui_client_v2.py
demo_dir = os.path.join(self.dev_dir, 'demo')
mp4_file = os.path.join(demo_dir, 'tv-report-1.mp4')
wav_file = os.path.join(demo_dir, 'tv-report-1.wav')
if not os.path.exists(mp4_file) or not os.path.exists(wav_file):
    ... 测试文件不存在 ...
```
  - 建议：引入小体积demo或提供“自动生成1~2秒WAV”作为兜底。
- 细节瑕疵
  - `LanguageManager.translations` 有重复键；建议去重。
  - 文档中零星历史路径/示例（如Windows本地路径）与现结构不符，建议清理。

### 下一步开发建议（按“每次只做一个任务”的原则）
- 建议当前任务（P0，小而关键）：对齐文档与资源
  1) 修订两处文档不一致：  
     - UI文档移除“取消识别功能系统”或标注“未来可选”。  
     - 架构文档将“dev/release/results”统一为“dev/output”。  
  2) 为速度测试补齐demo资源方案（二选一）：  
     - 放入极小样例 `dev/demo/tv-report-1.wav/mp4`；或  
     - 在GUI中检测缺失后，自动生成1~2秒纯音WAV到 `dev/demo` 再执行测速。  
  3) 清理重复翻译键。
  4) 按测试标准新增或更新一份“测试总结”到 `tests/`（命名 `test_[功能名称]_summary_[日期].md`），说明修订点与验证结论。
- 下两个迭代任务（排期建议）
  - 任务A（P1）：热词UI与传参  
    - UI增加“选择热词文件”与预览；调用时传 `--hotword`；更新需求/架构/UI文档与测试脚本。
  - 任务B（P2）：Online/2Pass模式选择  
    - UI增加模式单选及参数（`chunk_size/chunk_interval`），完善结果显示与日志；新增集成测试。

如果你同意，我先执行“文档对齐+demo兜底+翻译去重”的小迭代，并补充测试总结；随后进入“热词UI与传参”。

- 已完成：通读代码/文档/测试，给出功能与进度评估、.cursorrules合规模拟审计、差异点清单与修复优先级、单一下一步任务建议（文档/资源对齐），并给出后续两期任务建议（热词与模式选择）。