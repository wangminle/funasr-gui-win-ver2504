# FunASR GUI Client V2

这是一个基于 Tkinter 的图形用户界面 (GUI) 客户端，用于与 FunASR (FunASR ASR) WebSocket 服务进行交互，实现语音识别功能。

## ✨ 功能特性

*   **服务器连接配置**: 允许用户输入 FunASR WebSocket 服务器的 IP 地址和端口。
*   **连接测试**: 提供按钮测试与服务器的 WebSocket 连接状态（包括 SSL）。
*   **文件选择**: 支持选择本地的音频/视频文件（如 `.wav`, `.mp3`, `.pcm`, `.mp4` 等）或 `.scp` 列表文件进行识别。
*   **离线识别**: 通过调用客户端脚本 (`simple_funasr_client.py`) 执行 FunASR 的离线识别模式。
*   **实时输出显示**: 在 GUI 中实时显示识别过程中的状态信息和最终识别结果。
*   **高级选项**: 支持启用/禁用逆文本标准化 (ITN) 和 SSL 连接。
*   **依赖检查与安装**: 自动检查并提示/尝试安装所需的 Python 依赖包 (`websockets`, `asyncio`)。
*   **状态反馈**: 通过状态栏和输出区域提供清晰的操作状态反馈。

## 🐍 环境要求

*   **Python**: 3.8 或更高版本 (推荐使用项目运行时使用的 Python 版本，例如 3.12)。
*   **Tkinter**: Python 标准库，通常随 Python 安装。
*   **必要的 Python 包**:
    *   `websockets`: 用于 WebSocket 通信。
    *   `asyncio`: 用于异步操作。
    *   *(注意: GUI 客户端会在首次连接或识别时尝试自动安装这些依赖)*

## 🚀 安装与设置

1.  **获取代码**: 克隆或下载本仓库到您的本地计算机。
2.  **FunASR 服务端**: 确保您已经按照 FunASR 官方文档部署并运行了 WebSocket 服务端 (包括 `wss_server_online.py` 或 `wss_server_offline.py`)。记下服务端的 IP 地址和端口。
3.  **安装依赖**:
    *   您可以手动安装:
        ```bash
        pip install websockets asyncio
        ```
    *   或者，启动 GUI 客户端，它会在需要时尝试自动安装。

## 🛠️ 使用方法

1.  **启动 GUI**:
    ```bash
    cd path/to/funasr-gui-win-ver2504 # 进入项目根目录
    python src/python-gui-client/funasr_gui_client_v2.py
    ```
2.  **配置服务器**: 在 "服务器连接配置" 区域输入 FunASR WebSocket 服务器的 IP 地址和端口。
3.  **测试连接 (可选)**: 点击 "连接服务器" 按钮检查网络连通性。连接成功后，指示灯会变绿。
4.  **选择文件**: 点击 "选择音/视频文件" 按钮，选择您要识别的音频或视频文件。
5.  **配置选项 (可选)**: 根据需要勾选或取消勾选 "启用 ITN" 和 "启用 SSL"。
6.  **开始识别**: 点击 "开始识别" 按钮。
7.  **查看结果**: 识别过程中的日志和最终结果将显示在 "状态与结果" 区域。状态栏会显示当前状态。识别结果文本文件将保存在 `src/python-gui-client/results/` 目录下 (默认覆盖同名文件)。

## 📁 文件结构

```
funasr-gui-win-ver2504/
├── src/
│   └── python-gui-client/
│       ├── funasr_gui_client_v2.py   # GUI 客户端主程序
│       ├── simple_funasr_client.py   # 实际执行识别的 WebSocket 客户端脚本
│       ├── requirements.txt          # (可能包含更多依赖)
│       └── results/                  # 存放识别结果文本文件的目录
├── samples/
│   └── funasr_wss_client.py          # FunASR 官方提供的 WebSocket 客户端示例 (供参考)
├── prd/
│   └── funasr-python-gui-client-v2-UI定义.md # UI 详细定义文档
└── README.md                         # 本文档
```

## ⚠️ 已知问题与限制

*   当前主要支持 FunASR 的 **离线 (offline)** 识别模式。
*   错误处理和提示可以进一步完善。
*   结果文件的保存路径目前固定在 `src/python-gui-client/results/`。
*   暂未实现对所有 `funasr_wss_client.py` 命令行参数的可视化配置（如 `chunk_size`, `chunk_interval`, `hotword` 等）。

## 🤝 贡献

欢迎提出问题、报告错误或贡献代码改进！

## 📄 许可证

(可在此添加许可证信息，例如 MIT License) 