# FunASR GUI Client V2

A Tkinter-based graphical user interface (GUI) client for interacting with FunASR (FunASR ASR) WebSocket services to perform speech recognition.

## ✨ Features

*   **Server Connection Configuration**: Allows users to input the IP address and port of the FunASR WebSocket server.
*   **Connection Testing**: Provides a button to test WebSocket connection status with the server (including SSL).
*   **File Selection**: Supports selecting local audio/video files (such as `.wav`, `.mp3`, `.pcm`, `.mp4`, etc.) or `.scp` list files for recognition.
*   **Offline Recognition**: Executes FunASR's offline recognition mode by calling the client script (`simple_funasr_client.py`).
*   **Real-time Output Display**: Displays status information and final recognition results in real-time within the GUI during the recognition process.
*   **Advanced Options**: Supports enabling/disabling Inverse Text Normalization (ITN) and SSL connections.
*   **Dependency Check and Installation**: Automatically checks and prompts/attempts to install required Python dependencies (`websockets`, `mutagen`).
*   **Status Feedback**: Provides clear operational status feedback through the status bar and output area.
*   **Logging**: Generates independent log files containing detailed operation records and error information for troubleshooting.
*   **Configuration Persistence**: Saves the last used server IP, port, and advanced option settings, automatically loading them on next startup.
*   **Upload Speed Optimization**: Optimized upload speed for offline mode, improving processing efficiency.
*   **Protocol Optimization**: Fixed protocol handling in offline mode to ensure proper communication with the server.
*   **File Structure Optimization**: Restructured file storage, storing configuration files, logs, and recognition results in separate directories.
*   **Server Speed Testing**: Provides dedicated button to test server upload speed and transcription speed, using test files from the demo directory to calculate and display upload speed (MB/s) and transcription speed (RTF).
*   **Intelligent Duration Estimation**: Automatically detects the actual playback duration of audio/video files, dynamically calculates transcription estimated time and wait timeout based on speed test results, providing real-time progress display and countdown functionality.
*   **Fallback Strategy**: Uses a fixed 20-minute wait time when unable to obtain audio duration, ensuring all files can be processed normally.
*   **Internationalization Support**: Provides Chinese and English interface switching to meet the needs of users with different language backgrounds.
*   **Code Alignment with v0.2.0**: Simplified and stabilized codebase by aligning with proven v0.2.0 reference implementation.

## 🐍 Requirements

*   **Python**: 3.8 or higher (recommended to use the Python version used during project runtime, e.g., 3.12).
*   **Tkinter**: Python standard library, usually installed with Python.
*   **Required Python Packages**:
    *   `websockets`: For WebSocket communication.
    *   `mutagen`: For detecting audio/video file duration.
    *   `logging`: For generating log files (Python standard library).
    *   *(Note: The GUI client will attempt to automatically install these dependencies when first connecting or recognizing)*

## 🚀 Installation and Setup

1.  **Get the Code**: Clone or download this repository to your local computer.
2.  **FunASR Server**: Ensure you have deployed and are running the WebSocket server according to the official FunASR documentation (including `wss_server_online.py` or `wss_server_offline.py`). Note the server's IP address and port.
3.  **Install Dependencies (pipenv)**:
    ```bash
    pipenv install --skip-lock
    pipenv install --dev --skip-lock
    ```

## 🛠️ Usage

1.  **Start GUI**:
    ```bash
    cd path/to/funasr-gui-win-ver2504 # Enter project root directory
    pipenv run python src/python-gui-client/funasr_gui_client_v2.py
    ```
2.  **Configure Server**: Enter the IP address and port of the FunASR WebSocket server in the "Server Connection Configuration" area.
3.  **Test Connection (Optional)**: Click the "Connect Server" button to check network connectivity. The indicator will turn green when connection is successful.
4.  **Select File**: Click the "Select Audio/Video File" button to choose the audio or video file you want to recognize.
5.  **Configure Options (Optional)**: Check or uncheck "Enable ITN" and "Enable SSL" as needed.
6.  **Switch Language (Optional)**: Select "中文" or "English" from the language dropdown to switch the interface language.
7.  **Start Recognition**: Click the "Start Recognition" button.
8.  **View Results**: Logs and final results during the recognition process will be displayed in the "Logs and Results" area. The status bar will show the current status. Recognition result text files will be saved in the `release/results/` directory.
9.  **View Logs**: Click the "Open Log File" button to open the log file and view detailed operation records and error information.
10. **View Recognition Results**: Click the "Open Results Directory" button to directly open the directory where recognition results are saved.
11. **Test Server Speed**: Click the "Speed Test" button to test server upload speed and transcription speed. The test will automatically use test files from the demo directory (tv-report-1.mp4 and tv-report-1.wav) for two tests, calculating average upload speed (MB/s) and transcription speed (RTF). After completion, results will be displayed on the interface with a detailed test results dialog.

### Lint/Type Check (pipenv)
```bash
pipenv run python src/tools/run_lints.py
pipenv run python src/tools/run_lints.py --fix
pipenv run python src/tools/run_lints.py --mypy-only --paths src
```

## 📁 File Structure

```
funasr-gui-win-ver2504/
├── dev/
│   ├── config/                           # Configuration file directory
│   │   └── config.json                   # User configuration file
│   ├── logs/                             # Log file directory
│   │   └── funasr_gui_client.log         # Program runtime log file
│   └── release/                          # Release directory
│       └── results/                      # Directory for recognition result text files
├── src/
│   ├── python-gui-client/
│   │   ├── funasr_gui_client_v2.py       # GUI client main program
│   │   └── simple_funasr_client.py       # WebSocket client script that performs actual recognition
│   └── tools/
│       └── run_lints.py                  # Lint & type check runner
├── docs/                                 # Project documentation directory
├── tests/                                # Test file directory
├── ref/                                  # Reference materials directory
├── @resources/                           # Demo audio/video files
│   └── demo/
│       ├── tv-report-1.mp4
│       └── tv-report-1.wav
├── README.md                             # This document (English README)
└── README_cn.md                          # Chinese version README
```

## ⚠️ Known Issues and Limitations

*   Currently mainly supports FunASR's **offline** recognition mode.
*   Visual configuration for all `funasr_wss_client.py` command-line parameters (such as `chunk_size`, `chunk_interval`, `hotword`, etc.) is not yet implemented.
*   Some audio files may have corrupted metadata, in which case the fallback strategy (fixed 20-minute wait time) is automatically enabled.

## 🔜 Development Plan

According to the project management document, the following features are under development:

*   **Results and Logs Separation**: Separate display of recognition results and runtime logs for a clearer user experience.
*   **Support for Hotword Files**: Add functionality to select hotword files, improving recognition accuracy for specific domains.
*   **Configure Output Directory**: Allow users to customize result save location.
*   **Support for Online and 2Pass Modes**: Extend support for more recognition modes to meet different scenario needs.

## ✅ Recent Updates (V2.3 - Code Alignment Edition)

### Major Updates (2025-01-15)
*   **Code Alignment with v0.2.0**: Successfully aligned dev version with proven v0.2.0 reference implementation
*   **Simplified Architecture**: Removed overly complex cancel recognition functionality to improve stability
*   **Directory Structure Optimization**: Updated to use `release/results` output directory following v0.2.0 standards
*   **Enhanced Reliability**: Replaced complex implementation with v0.2.0's concise and efficient version
*   **Complete Integration Testing**: All 6/6 integration tests passed successfully

### Previous Updates (V2.2)
*   **Intelligent Duration Estimation**: Completed audio duration auto-detection and intelligent estimation functionality
*   **Fallback Strategy**: Implemented fallback mechanism when audio duration acquisition fails
*   **Enhanced Status Bar Information**: Completed real-time transcription progress display and countdown functionality
*   **Enhanced Error Handling**: Improved error handling and user-friendly prompts
*   **Complete Internationalization Support**: Completed Chinese-English interface switching functionality, including complete translation of new features
*   **Timeout Mechanism Optimization**: Fixed hard-coded 10-second communication timeout issue, changed to intelligent dynamic timeout based on audio duration
*   **Multi-layer Timeout Protection**: Implemented three-layer protection mechanism with main timeout, communication timeout, and fallback timeout

### Technical Debt Cleanup
*   Removed `recognition_running`, `cancel_event` and other complex state variables
*   Simplified recognition workflow, improved code stability
*   Optimized error handling logic using proven v0.2.0 implementation
*   Enhanced process and resource management mechanisms

## 🤝 Contributing

Welcome to raise issues, report bugs, or contribute code improvements!

## 📄 License

(License information can be added here, e.g., MIT License) 