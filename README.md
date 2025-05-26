# FunASR GUI Client V2

This is a Tkinter-based graphical user interface (GUI) client for interacting with FunASR (FunASR ASR) WebSocket service to implement speech recognition functionality.

## ✨ Features

*   **Server Connection Configuration**: Allows users to input the IP address and port of the FunASR WebSocket server.
*   **Connection Testing**: Provides a button to test the WebSocket connection status with the server (including SSL).
*   **File Selection**: Supports selecting local audio/video files (such as `.wav`, `.mp3`, `.pcm`, `.mp4`, etc.) or `.scp` list files for recognition.
*   **Offline Recognition**: Executes FunASR's offline recognition mode by calling the client script (`simple_funasr_client.py`).
*   **Real-time Output Display**: Displays status information and final recognition results in real-time in the GUI.
*   **Advanced Options**: Supports enabling/disabling Inverse Text Normalization (ITN) and SSL connections.
*   **Dependency Check and Installation**: Automatically checks and prompts/attempts to install required Python dependency packages (`websockets`, `asyncio`).
*   **Status Feedback**: Provides clear operation status feedback through the status bar and output area.
*   **Logging**: Generates independent log files containing detailed operation records and error information for troubleshooting.
*   **Configuration Persistence**: Saves the last used server IP, port, and advanced option settings, which are automatically loaded at next startup.
*   **Upload Speed Optimization**: Optimizes upload speed for offline mode, improving processing efficiency.
*   **Protocol Optimization**: Corrects protocol handling in offline mode, ensuring correct communication with the server.
*   **File Structure Optimization**: Restructures file storage, storing configuration files, logs, and recognition results in separate directories.
*   **Server Speed Testing**: Provides a dedicated button to test the server's upload speed and transcription speed, using test files from the demo directory to calculate and display upload speed (MB/s) and transcription speed (real-time factor).
*   **Internationalization Support**: Provides language switching between Chinese and English interfaces to meet the needs of users with different language backgrounds.

## 🐍 Requirements

*   **Python**: 3.8 or higher (recommended to use the Python version used in the project runtime, e.g., 3.12).
*   **Tkinter**: Python standard library, usually installed with Python.
*   **Necessary Python Packages**:
    *   `websockets`: For WebSocket communication.
    *   `asyncio`: For asynchronous operations.
    *   `logging`: For generating log files (Python standard library).
    *   *(Note: The GUI client will attempt to automatically install these dependencies upon first connection or recognition)*

## 🚀 Installation and Setup

1.  **Get the Code**: Clone or download this repository to your local computer.
2.  **FunASR Server**: Ensure you have deployed and are running the WebSocket server according to the FunASR official documentation (including `wss_server_online.py` or `wss_server_offline.py`). Note down the server's IP address and port.
3.  **Install Dependencies**:
    *   You can install manually:
        ```bash
        pip install websockets asyncio
        ```
    *   Or start the GUI client, which will attempt to automatically install them when needed.

## 🛠️ Usage

1.  **Start GUI**:
    ```bash
    cd path/to/funasr-gui-win-ver2504 # Navigate to the project root directory
    python src/python-gui-client/funasr_gui_client_v2.py
    ```
2.  **Configure Server**: Enter the IP address and port of the FunASR WebSocket server in the "Server Connection Configuration" area.
3.  **Test Connection (Optional)**: Click the "Connect to Server" button to check network connectivity. The indicator will turn green after a successful connection.
4.  **Select File**: Click the "Select Audio/Video File" button to choose the audio or video file you want to recognize.
5.  **Configure Options (Optional)**: Check or uncheck "Enable ITN" and "Enable SSL" as needed.
6.  **Switch Language (Optional)**: Select "中文" or "English" from the language dropdown to switch the interface language.
7.  **Start Recognition**: Click the "Start Recognition" button.
8.  **View Results**: Logs and final results during the recognition process will be displayed in the "Running Logs and Results" area. The status bar will show the current status. Recognition result text files will be saved in the `release/results/` directory.
9.  **View Logs**: Click the "Open Log File" button to open the log file and view detailed operation records and error information.
10. **View Recognition Results**: Click the "Open Results Directory" button to directly open the directory where recognition results are saved.
11. **Test Server Speed**: Click the "Speed Test" button to test the server's upload speed and transcription speed. The test will automatically use test files (tv-report-1.mp4 and tv-report-1.wav) from the demo directory to perform two tests, and calculate the average upload speed (MB/s) and transcription speed (real-time factor). After the test is completed, the results will be displayed on the interface, and a detailed test results dialog will pop up.

## 📁 File Structure

```
funasr-gui-win-ver2504/
├── src/
│   └── python-gui-client/
│       ├── funasr_gui_client_v2.py   # GUI client main program
│       ├── language_resources.py     # Language resource file containing Chinese and English string mappings
│       └── simple_funasr_client.py   # WebSocket client script that actually performs recognition
├── release/
│   ├── config/                       # Configuration file directory
│   │   └── config.json               # File that saves user configuration
│   ├── logs/                         # Log file directory
│   │   └── funasr_gui_client.log     # Program running log file
│   └── results/                      # Directory for storing recognition result text files
│       └── speed_test/               # Subdirectory for storing speed test results
├── ref_codes/                        # Reference code directory
│   ├── funasr_client_api.py          # FunASR client API
│   ├── funasr_wss_client.py          # Original FunASR WebSocket client
│   └── requirements_client.txt       # Client dependency list
├── ref_docs/                         # Reference document directory
├── demo/                             # Demo audio and video file directory
│   ├── tv-report-1.mp4               # Example video file (for speed testing)
│   └── tv-report-1.wav               # Example audio file (for speed testing)
├── prd/                              # Project requirements and documentation directory
│   ├── funasr-python-gui-client-v2-需求文档.md # Project requirements document
│   ├── funasr-python-gui-client-v2-项目管理.md # Project management document
│   ├── funasr-python-gui-client-v2-UI定义.md   # Detailed UI definition document
│   ├── FunASR客户端流程记录.md                 # Client and server interaction process record
│   └── FunASR-performance.md                   # Performance test record
└── README.md                                   # This document
```

## ⚠️ Known Issues and Limitations

*   Currently mainly supports FunASR's **offline** recognition mode.
*   Error handling and prompts can be further improved.
*   Visual configuration for all `funasr_wss_client.py` command line parameters (such as `chunk_size`, `chunk_interval`, `hotword`, etc.) is not yet implemented.

## 🔜 Development Plan

According to the project management document, the following features are under development:

*   **Separation of Results and Logs**: Displaying recognition results and running logs separately to provide a clearer user experience.
*   **Enhanced Status Bar Information**: Displaying more detailed recognition stage and progress information.
*   **Enhanced Error Handling**: Capturing and displaying common errors in a friendly manner.
*   **Adding "Cancel" Button**: Allowing users to abort an ongoing recognition task.
*   **Supporting Hotword Files**: Adding the function to select hotword files to improve recognition accuracy in specific domains.
*   **Configurable Output Directory**: Allowing users to customize the location where results are saved.
*   **Supporting Online and 2Pass Modes**: Extending support for more recognition modes to meet different scenario requirements.
*   **Internationalization Support Enhancement**: Improving the Chinese and English interface switching functionality, enhancing user experience, and facilitating the addition of more language support.

## 🤝 Contribution

Questions, bug reports, or code improvements are welcome!

## 📄 License

(License information can be added here, e.g., MIT License) 