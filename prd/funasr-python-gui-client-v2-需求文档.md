# FunASR Python客户端的简单需求说明书

这是一个使用 Python 和 Tkinter 库创建一个简单 GUI 客户端的方案，该客户端将调用您提供的 `funasr_wss_client.py` 脚本来与 FunASR runtime 服务器交互。

## 功能描述
1. GUI框架：脚本信息一目了然，可以在windows环境执行；
2. 服务连接：提供websocker的SSL连接服务，支持手动修改网址和端口地址；
3. 选择本地文件并发送脚本：将选中的文件发送到服务器的api端口；
4. 接收文本结果：按照接口协议接收结果，并将最终结果显示在软件的输出文本框中。

**方案概述:**

1.  **GUI 框架:** 使用 Python 内置的 `tkinter` 库来创建图形用户界面。
    *   默认800x600大小的整体窗口；
    *   可以全屏或者缩小至初始大小；
    *   有“网络连接”，“开始识别”，“导出结果”等按钮。
    *   UI的具体内容见文档：C:\Users\wangminle\Documents\VSCode\2-Cursor实战记录\2-FunASR-practice\funasr-gui-win-ver2504\prd\funasr-python-gui-client-v2-UI定义.md
2.  **用户输入:**
    *   提供输入框让用户指定 FunASR runtime 服务器的 IP 地址和端口号。
    *   提供一个按钮，允许用户浏览并选择本地的音频或视频文件。
    *   显示用户选择的文件路径。
3.  **执行脚本:**
    *   添加一个“开始识别”按钮。
    *   点击按钮时，GUI 程序会收集用户输入的服务器地址、端口和文件路径。
    *   使用 Python 的 `subprocess` 模块在后台启动 `funasr_wss_client.py` 脚本，并将收集到的信息作为命令行参数传递给它（例如 `--host`, `--port`, `--audio_in`, `--mode offline`）。
4.  **结果输出** 
    *   添加一个文本框，用于显示 `funasr_wss_client.py` 脚本的输出或错误信息。
5.  **状态显示:**
    *   添加一个状态栏，用于显示操作状态（如“正在识别…”）等连接或工作状态；
6.  **线程处理:** 为了防止在执行识别任务时 GUI 界面卡死，将在一个单独的线程中运行 `subprocess`。

**实现步骤:**

1.  **创建 Python 文件:** 创建一个新的 Python 文件（例如 `funasr_gui_client.py`）。
2.  **编写 GUI 代码:** 使用 `tkinter` 构建界面元素（标签、输入框、按钮、文本框）。
3.  **实现文件选择功能:** 使用 `tkinter.filedialog.askopenfilename`。
4.  **实现“开始识别”按钮的回调函数:**
    *   获取界面上的输入值。
    *   构建 `funasr_wss_client.py` 的命令行参数列表。
    *   创建一个新线程来执行 `subprocess.run`（或 `subprocess.Popen`）调用 `funasr_wss_client.py`。
    *   在线程中捕获脚本的标准输出和标准错误。
    *   将状态和脚本输出更新到 GUI 的文本区域（注意：从非主线程更新 Tkinter 控件需要使用 `widget.after` 或类似机制）。

**注意事项:**

*   **`funasr_wss_client.py` 的位置:** 这个 GUI 脚本需要能够找到并执行 `funasr_wss_client.py`。最简单的方式是将它们放在同一个目录下，或者确保 `funasr_wss_client.py` 所在的目录在系统的 PATH 环境变量中。
*   **Python 环境:** 运行此 GUI 脚本的 Python 环境需要安装 `funasr_wss_client.py` 所需的所有依赖。
*   **错误处理:** 需要添加适当的错误处理，例如检查用户输入是否有效，以及处理 `subprocess` 执行过程中可能出现的异常。
*   **输出:** `funasr_wss_client.py` 的输出将直接显示在 GUI 的文本框中。如果该脚本将结果写入文件（如使用 `--output_dir`），GUI 不会直接显示文件内容，只会显示脚本执行过程的标准输出。
