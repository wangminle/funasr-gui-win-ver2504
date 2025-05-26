# FunASR GUI 客户端 - V2 UI 布局详细定义

**版本**: 2.1 (基于实际代码 `funasr_gui_client_v2.py` 更新)

## 1. 前端方案概述

*   **开发语言**: Python (当前开发环境版本 3.12)
*   **GUI 框架**: Tkinter (`tkinter` 和 `tkinter.ttk`)
    *   **选用理由**: Python 内置标准库，无需额外安装，轻量级，跨平台兼容性好，能够满足本项目简洁高效的需求。
*   **基础字体**: 默认使用系统字体，部分特殊标签（如连接状态指示器）指定为 Arial。
    *   **基础字号**: 遵循系统默认控件字号（通常为 9pt 或 10pt），特殊标签可单独指定。
*   **配色方案**: 主要采用系统默认主题颜色（浅色模式），通过前景颜色（`foreground`）区分状态（如连接状态的红色/绿色）。
*   **布局管理**: 混合使用 `pack()` 和 `grid()` 进行布局。
    *   `pack()` 用于整体框架的垂直排列和填充。
    *   `grid()` 用于框架内部控件的精确对齐和行列管理。
*   **国际化支持**: 使用字符串资源文件和语言切换机制。
    *   **语言选项**: 支持中文和英文界面切换。
    *   **实现方式**: 所有UI文本使用变量引用，根据当前语言设置动态加载。

## 2. 主窗口

*   **代码实例**: `app = FunASRGUIClient()`
*   **标题**: "FunASR GUI Client V2"
*   **初始大小**: 800x600 (`self.geometry("800x600")`)

## 3. 服务器连接配置

*   **框架变量名**: `server_frame`
*   **文本**: "服务器连接配置" / "Server Connection"
*   **布局**: `pack(padx=10, pady=5, fill=tk.X)` (顶部横向填充)

    *   **服务器 IP 标签 (`ttk.Label`)**
        *   **文本**: "服务器 IP:" / "Server IP:"
        *   **位置**: `grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)`
    *   **服务器 IP 输入框 (`ttk.Entry`)**
        *   **控件变量名**: `self.ip_entry`
        *   **关联变量**: `self.ip_var` (tk.StringVar, 默认值 "127.0.0.1")
        *   **大小**: `width=30`
        *   **位置**: `grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)`
        *   **操作**: 用户输入 FunASR WebSocket 服务器的 IP 地址。
        *   **映射**: 对应 `--host` 参数。
    *   **端口 标签 (`ttk.Label`)**
        *   **文本**: "端口:" / "Port:"
        *   **位置**: `grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)`
    *   **端口 输入框 (`ttk.Entry`)**
        *   **控件变量名**: `self.port_entry`
        *   **关联变量**: `self.port_var` (tk.StringVar, 默认值 "10095")
        *   **大小**: `width=10`
        *   **位置**: `grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)`
        *   **操作**: 用户输入 FunASR WebSocket 服务器的端口号。
        *   **映射**: 对应 `--port` 参数。
    *   **连接服务器 按钮 (`ttk.Button`)**
        *   **控件变量名**: `self.connect_button`
        *   **文本**: "连接服务器" / "Connect Server"
        *   **位置**: `grid(row=0, column=4, padx=15, pady=5, sticky=tk.E)`
        *   **操作**: 点击后调用 `self.connect_server` 方法，在后台线程尝试连接服务器并测试 WebSocket 可用性。
        *   **效果**: 点击后按钮变为禁用状态，直到连接尝试结束（成功、失败或超时）后恢复可用。状态栏和输出区域会显示连接过程信息。连接状态指示器会更新。
    *   **连接状态指示器 (`ttk.Label`)**
        *   **控件变量名**: `self.connection_indicator`
        *   **初始文本**: "未连接" / "Disconnected"
        *   **初始颜色**: 红色
        *   **字体**: `("Arial", 9, "bold")`
        *   **位置**: `grid(row=0, column=5, padx=5, pady=5, sticky=tk.E)`
        *   **效果**: `self._update_connection_indicator()` 方法根据连接测试结果更新其文本和颜色（成功时为 "已连接"/"Connected"，绿色，失败时为 "未连接"/"Disconnected"，红色）。

## 4. 文件选择与执行

*   **框架变量名**: `file_frame`
*   **文本**: "文件选择与执行" / "File Selection and Execution"
*   **布局**: `pack(padx=10, pady=5, fill=tk.X)`

    *   **选择文件 按钮 (`ttk.Button`)**
        *   **控件变量名**: `self.select_button`
        *   **文本**: "选择音/视频文件" / "Select Audio/Video File"
        *   **位置**: `grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)`
        *   **操作**: 点击后调用 `self.select_file` 方法，弹出文件选择对话框。
        *   **对话框设置**: `filetypes = (("音频/视频/脚本文件", "*.wav *.mp3 *.pcm *.mp4 *.mkv *.avi *.flv *.scp"), ("所有文件", "*.*"))`
        *   **效果**: 选择文件后，文件路径显示框更新；状态栏更新；输出区域清空并显示已选择文件信息。识别过程中此按钮禁用。
    *   **文件路径 显示框 (`ttk.Entry`)**
        *   **控件变量名**: `self.file_path_entry`
        *   **关联变量**: `self.file_path_var` (tk.StringVar)
        *   **大小**: `width=60`, 水平可扩展 (`columnconfigure(1, weight=1)`)
        *   **状态**: 只读 (`state='readonly'`)
        *   **位置**: `grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)`
        *   **效果**: 显示 `self.select_file` 方法中选择的文件路径。
    *   **开始识别 按钮 (`ttk.Button`)**
        *   **控件变量名**: `self.start_button`
        *   **文本**: "开始识别" / "Start Recognition"
        *   **位置**: `grid(row=0, column=4, padx=15, pady=5, sticky=tk.E)`
        *   **操作**: 点击后调用 `self.start_recognition` 方法，在后台线程运行 `_run_script`。
        *   **效果**: 读取 IP、端口、文件路径和高级选项，构造命令调用 `simple_funasr_client.py`。点击后按钮变为禁用状态，直到识别过程结束（成功或失败）后恢复可用。状态栏和输出区域会显示识别过程信息。选择文件按钮也同时禁用。
        *   **映射**: 固定传递 `--mode offline`。根据高级选项传递 `--use_itn` 和 `--ssl`。传递 `--audio_in` (选择的文件路径), `--host`, `--port`, `--output_dir`。

## 5. 高级选项

*   **框架变量名**: `options_frame`
*   **文本**: "高级选项" / "Advanced Options"
*   **布局**: `pack(padx=10, pady=5, fill=tk.X)`

    *   **启用 ITN 复选框 (`ttk.Checkbutton`)**
        *   **控件变量名**: `self.itn_check`
        *   **文本**: "启用 ITN" / "Enable ITN"
        *   **关联变量**: `self.use_itn_var` (tk.IntVar, 默认值 1)
        *   **位置**: `grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)`
        *   **操作**: 用户勾选/取消勾选。
        *   **映射**: 勾选时传递 `--use_itn 1`，不勾选时传递 `--use_itn 0`。
    *   **启用 SSL 复选框 (`ttk.Checkbutton`)**
        *   **控件变量名**: `self.ssl_check`
        *   **文本**: "启用 SSL" / "Enable SSL"
        *   **关联变量**: `self.use_ssl_var` (tk.IntVar, 默认值 1)
        *   **位置**: `grid(row=0, column=1, padx=5, pady=2, sticky=tk.W)`
        *   **操作**: 用户勾选/取消勾选。
        *   **映射**: 勾选时传递 `--ssl 1`，不勾选时传递 `--ssl 0`。
    *   **打开日志文件 按钮 (`ttk.Button`)**
        *   **控件变量名**: `self.open_log_button`
        *   **文本**: "打开日志文件" / "Open Log File"
        *   **位置**: `grid(row=0, column=2, padx=15, pady=2, sticky=tk.W)`
        *   **操作**: 点击后调用 `self.open_log_file` 方法。
        *   **效果**: 根据操作系统尝试打开日志文件 (`release/logs/funasr_gui_client.log`) 或其所在目录。
    *   **打开结果目录 按钮 (`ttk.Button`)**
        *   **控件变量名**: `self.open_results_button`
        *   **文本**: "打开结果目录" / "Open Results Directory"
        *   **位置**: `grid(row=0, column=3, padx=15, pady=2, sticky=tk.W)`
        *   **操作**: 点击后调用 `self.open_results_folder` 方法。
        *   **效果**: 根据操作系统尝试打开识别结果保存目录 (`release/results`) 或其所在目录。
    *   **语言选择 下拉框 (`ttk.Combobox`)**
        *   **控件变量名**: `self.language_combo`
        *   **文本标签**: "界面语言:" / "UI Language:"
        *   **选项值**: ["中文", "English"]
        *   **关联变量**: `self.language_var` (tk.StringVar, 默认值 "中文")
        *   **位置**: `grid(row=0, column=4, padx=15, pady=2, sticky=tk.W)`
        *   **操作**: 用户选择界面语言。
        *   **效果**: 选择后调用 `self.change_language` 方法，动态更新所有UI文本。

## 6. 速度测试区域

*   **框架变量名**: `speed_test_frame`
*   **文本**: "速度测试" / "Speed Test"
*   **布局**: `pack(padx=10, pady=5, fill=tk.X)`

    *   **速度测试 按钮 (`ttk.Button`)**
        *   **控件变量名**: `self.speed_test_button`
        *   **文本**: "速度测试" / "Speed Test"
        *   **位置**: `grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)`
        *   **操作**: 点击后调用 `self.start_speed_test` 方法，在后台线程执行测试。
        *   **效果**: 使用demo目录中的测试文件依次进行识别，记录上传时间和转写时间，计算并显示上传速度和转写速度。点击后按钮变为禁用状态，直到测试完成后恢复可用。状态栏和状态显示标签会显示测试进度。
    
    *   **测试状态 标签 (`ttk.Label`)**
        *   **控件变量名**: `self.speed_test_status`
        *   **关联变量**: `self.speed_test_status_var` (tk.StringVar, 默认值 "未测试" / "Not Tested")
        *   **字体**: `("Arial", 9, "bold")`
        *   **位置**: `grid(row=0, column=1, padx=15, pady=5, sticky=tk.W)`
        *   **效果**: 显示当前测试状态，包括"未测试"/"Not Tested"、"测试1进行中..."/"Test 1 in progress..."、"测试2进行中..."/"Test 2 in progress..."、"测试完成"/"Test Complete"。
    
    *   **结果显示区域 (嵌套 `ttk.Frame`)**
        *   **框架变量名**: `result_frame`
        *   **位置**: `grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)`
        
        *   **上传速度 标签 (`ttk.Label`)**
            *   **文本**: "上传速度:" / "Upload Speed:"
            *   **位置**: `grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)`
        
        *   **上传速度 值标签 (`ttk.Label`)**
            *   **关联变量**: `self.upload_speed_var` (tk.StringVar, 默认值 "--")
            *   **位置**: `grid(row=0, column=1, padx=5, pady=2, sticky=tk.W)`
            *   **效果**: 显示测试后计算的上传速度，格式为 "x.xx MB/s"。
        
        *   **转写速度 标签 (`ttk.Label`)**
            *   **文本**: "转写速度:" / "Transcription Speed:"
            *   **位置**: `grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)`
        
        *   **转写速度 值标签 (`ttk.Label`)**
            *   **关联变量**: `self.transcribe_speed_var` (tk.StringVar, 默认值 "--")
            *   **位置**: `grid(row=1, column=1, padx=5, pady=2, sticky=tk.W)`
            *   **效果**: 显示测试后计算的转写速度，格式为 "x.xx倍速" / "x.xx RTF"。

## 7. 运行日志与结果

*   **框架变量名**: `log_frame` (原 `result_frame`)
*   **文本**: "运行日志与结果" / "Logs and Results"
*   **布局**: `pack(padx=10, pady=5, fill=tk.BOTH, expand=True)` (填充剩余空间)

    *   **日志/输出 文本框 (`scrolledtext.ScrolledText`)**
        *   **控件变量名**: `self.log_text` (原 `self.output_text`)
        *   **大小**: `height=15`, 自动换行 (`wrap=tk.WORD`), 可垂直和水平扩展 (`pack(fill=tk.BOTH, expand=True, padx=5, pady=5)`)。
        *   **状态**: 初始和大部分时间为禁用 (`state='disabled'`)，由 `GuiLogHandler` 在更新内容时临时启用。
        *   **操作**: 显示程序运行日志（所有级别）、依赖检查信息、连接状态、识别过程中的标准输出/错误（标记为脚本输出/错误），以及最终的识别结果文本（特殊标记）。
        *   **效果**: 文本会自动滚动到最底部 (`self.log_text.see(tk.END)`)。

## 8. 状态栏

*   **控件变量名**: `self.status_bar`
*   **关联变量**: `self.status_var` (tk.StringVar, 初始值 "准备就绪" / "Ready")
*   **外观**: `relief=tk.SUNKEN`, `anchor=tk.W`
*   **布局**: `pack(side=tk.BOTTOM, fill=tk.X)` (固定在窗口底部并横向填充)
*   **效果**: 通过更新 `self.status_var.set(...)` 来显示当前操作的简短状态，如 "正在连接..."/"Connecting...", "识别完成"/"Recognition Complete", "错误："/"Error:" 等。

## 9. 国际化实现

*   **语言资源管理**: 
    *   **资源文件**: `language_resources.py` 或类似文件包含中英文字符串映射。
    *   **动态加载**: 根据当前语言设置加载相应的字符串资源。
    *   **语言切换**: `change_language` 方法在语言变更时遍历所有UI组件，更新文本。
    
*   **UI变更处理**:
    *   所有UI文本使用 `self.text_resources[key]` 或类似方式获取，而非硬编码。
    *   包括标签文本、按钮文本、状态消息、对话框内容等。
    *   文件选择对话框和消息框也需根据语言设置动态更新文本。

*   **配置持久化**:
    *   语言设置作为用户配置的一部分保存，下次启动时自动加载。
    *   配置保存在 `release/config/config.json` 文件中。

这样的布局将核心功能（服务器、文件、开始）放在最显眼的位置，同时考虑了高级参数的可配置性和国际化支持，并强调了状态反馈和结果位置的重要性。

