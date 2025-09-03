# FunASR 客户端工作流程分析

**最后更新日期:** 2025-07-23

假设我们执行以下命令：
```bash
python3 funasr_wss_client.py --host "127.0.0.1" --port 10095 --mode offline --audio_in "../audio/asr_example.wav"
```

## 1. 参数解析与初始化
- **操作**：脚本通过 `argparse` 解析命令行参数
- **中间结果**：
  - host = "127.0.0.1"
  - port = 10095
  - mode = "offline"
  - audio_in = "../audio/asr_example.wav"
  - chunk_size = [5, 10, 5]（默认值）
  - chunk_interval = 10（默认值）
  - thread_num = 1（默认值）
  - ssl = 1（默认启用SSL）
  - use_itn = 1（默认启用itn）

## 2. 音频文件处理
- **操作**：检查 `audio_in` 参数
  - 若为 .scp 文件，加载音频列表
  - 若为单个音频文件，直接处理
- **中间结果**：
  - 创建 `wavs` 列表：["../audio/asr_example.wav"]

## 3. 线程分配
- **操作**：根据 `thread_num` 和音频文件数量，计算每个线程处理的文件数
- **中间结果**：
  - 对于单个文件且 thread_num=1，每个线程处理1个文件
  - 创建1个进程，调用 `one_thread(0, 0, 1)`

## 4. WebSocket 连接建立
- **操作**：建立 WebSocket 连接
  - 如果 ssl=1，使用 wss:// 协议
  - 否则使用 ws:// 协议
- **中间结果**：
  - 连接 URL：wss://127.0.0.1:10095（启用SSL时）
  - 成功连接后，创建两个异步任务：`record_from_scp` 和 `message`

## 5. 初始参数发送
- **操作**：发送包含识别参数的 JSON 消息
- **中间结果**：
  ```json
  {
    "mode": "offline", 
    "audio_fs": 16000,          // 采样率，如果输入是 pcm 格式，需要提供
    "wav_name": "实际文件名",   // **重要:** 客户端必须正确设置此字段
    "wav_format": "pcm",      // 或根据实际文件格式设置
    "is_speaking": true, 
    "hotwords": "",           // 如果有热词，在此设置
    "itn": true               // 根据 --use_itn 参数设置
  }
  ```
  **注意:** 根据服务端日志分析，`wav_name` 字段在之前的交互中可能未被正确设置为实际文件名（日志显示为 "demo"），这对于日志追踪和结果对应至关重要。务必确保客户端实现中正确传递了文件名。

## 6. 音频数据读取与发送
- **操作**：
  - 打开音频文件，读取音频数据
  - 对于 .wav 文件，使用 wave 模块读取参数和帧数据
  - 计算分块大小和块数
- **中间结果**：
  - 对于一个典型的音频文件，读取二进制音频数据 `audio_bytes`
  - 计算每块大小 `stride`，如：`stride = int(60 * 10 / 10 / 1000 * 16000 * 2)`
  - 计算总块数 `chunk_num = (len(audio_bytes) - 1) // stride + 1`

## 7. 音频数据分块发送
- **操作**：循环发送音频块
  - 按计算的 `stride` 大小切分音频数据
  - 将每块数据通过 WebSocket 二进制消息发送
- **中间结果**：
  - 对于每个块 i，发送 `audio_bytes[beg:beg + stride]`
  - 当 i 达到最后一块时，发送结束信号 `{"is_speaking": false}`
  - 在离线模式下，发送间隔很短（0.001秒）

## 8. 接收识别结果
- **操作**：从服务器接收 WebSocket 消息
  - 在 `message` 异步函数中处理
  - 将收到的 JSON 消息解析为文本
- **中间结果**：
  - 收到包含识别结果的 JSON：
  ```json
  {
    "wav_name": "demo",
    "text": "识别出的文本内容",
    "timestamp": [[起始时间, 结束时间, 单词], ...], // 如果有时间戳信息
    "mode": "offline",
    "is_final": true
  }
  ```

## 9. 结果处理与输出
- **操作**：
  - 解析服务器返回的 JSON 结果
  - 提取识别文本和时间戳（如果有）
  - 根据识别模式（offline/online/2pass）处理结果
- **中间结果**：
  - 在控制台打印结果，格式为 `pid{id}: {wav_name}: {text}`
  - 如果指定了 `output_dir`，将结果写入对应的文件

## 10. 等待处理完成与连接关闭
- **操作**：
  - 设置 `offline_msg_done = True` 标志处理完成
  - 关闭 WebSocket 连接
- **中间结果**：
  - 离线模式下，等待 `offline_msg_done` 信号表示结果接收完成
  - WebSocket 连接关闭，进程结束

## 11. 程序结束
- **操作**：主进程等待所有子进程完成并结束
- **中间结果**：
  - 控制台打印 "end" 信息
  - 脚本执行完毕

这个流程反映了 FunASR 客户端如何通过 WebSocket 协议与服务端通信，发送音频数据并接收识别结果。整个过程通过异步编程和多进程处理实现高效的请求发送和结果接收。


# Google Gemini

好的，我们来梳理一下从客户端视角看 `funasr_wss_client.py` 脚本执行的主要步骤和可能的中间结果。这里假设我们执行一个类似文档中示例的命令：

```bash
python3 funasr_wss_client.py --host "127.0.0.1" --port 10095 --mode offline --audio_in "../audio/asr_example.wav"
```

**执行流程：**

1.  **脚本启动与参数解析:**
    *   **操作:** Python 解释器加载并开始执行 `funasr_wss_client.py`。脚本内部使用 `argparse` 库解析命令行传入的参数，如 `--host`, `--port`, `--mode`, `--audio_in`, `--output_dir`, `--ssl`, `--hotword`, `--use_itn`, `--thread_num` 等。
    *   **中间结果:** 程序获取到一个包含所有参数值的配置对象（例如 `args`）。在这个例子中，`args.host` 为 "127.0.0.1"，`args.port` 为 10095，`args.mode` 为 "offline"，`args.audio_in` 为 "../audio/asr_example.wav"。其他未指定的参数会取默认值（例如 `args.thread_num` 为 1，`args.ssl` 为 1，`args.use_itn` 为 1）。

2.  **确定音频输入:**
    *   **操作:** 脚本检查 `--audio_in` 参数的值。
        *   如果它指向一个 `.scp` 文件 (如 `wav.scp`)，脚本会读取这个文件，获取一个音频文件路径列表。
        *   如果它指向一个具体的音频文件路径 (如本例中的 `"../audio/asr_example.wav"`），则将该路径作为一个列表处理。
    *   **中间结果:** 生成一个包含所有待处理音频文件完整路径的列表 `wav_list`。例如：`['../audio/asr_example.wav']`。

3.  **初始化客户端API:**
    *   **操作:** 脚本实例化 `funasr_client_api.py` 中定义的 `FunASR_Client` 类。在初始化过程中，会根据解析到的参数设置客户端的基本配置，特别是服务器地址 (`host`, `port`) 和连接模式 (`mode`)。
    *   **中间结果:** 创建了一个 `FunASR_Client` 对象，该对象封装了与服务器通信所需的方法和状态。

4.  **并发处理设置 (如果 `thread_num > 1`):**
    *   **操作:** 如果 `--thread_num` 大于 1，脚本会创建一个线程池 (`ThreadPoolExecutor`) 来并发处理 `wav_list` 中的多个音频文件。每个线程将独立执行后续的连接、发送和接收步骤。如果 `thread_num` 为 1（如此例），则直接在主线程中处理。
    *   **中间结果:** 准备好执行环境（单线程或线程池）。

5.  **(针对每个音频文件) 建立WebSocket连接:**
    *   **操作:** 对于 `wav_list` 中的每一个音频文件（在此例中只有一个），客户端尝试使用 `websockets` 库与指定的服务器地址 (`ws://127.0.0.1:10095` 或 `wss://` 如果 `ssl=1`) 建立 WebSocket 连接。`FunASR_Client` 内部的 `asr_connect` 方法会被调用。
    *   **中间结果:** 成功建立 WebSocket 连接，或者连接失败并抛出异常。客户端持有了一个活动的 WebSocket 连接对象。

6.  **(针对每个音频文件) 发送握手/配置信息:**
    *   **操作:** 连接建立后，客户端立刻向服务器发送一个 JSON 格式的 "握手" 消息。这个消息包含了识别模式 (`mode`)、音频格式信息（通常从文件头推断或默认）、热词 (`hotword`)、是否启用 ITN (`use_itn`) 等配置。这是通过 `FunASR_Client` 内部的 `send_start_params` 方法完成的。
    *   **中间结果:** 服务器收到客户端的配置请求，并准备接收音频数据。客户端可能收到服务器确认连接或状态的消息（具体取决于服务器实现）。

7.  **(针对每个音频文件) 发送音频数据:**
    *   **操作:** 客户端打开对应的音频文件 (`../audio/asr_example.wav`)。它以二进制模式读取文件内容，通常是分块 (chunk by chunk) 读取。每个音频块被封装成 WebSocket 的二进制消息发送给服务器。这是通过 `FunASR_Client` 内部的 `send_audio_chunks` (或类似) 方法完成的。
    *   **中间结果:** 音频数据块被陆续发送到服务器。客户端会持续读取和发送，直到文件末尾。

8.  **(针对每个音频文件) 发送结束信号:**
    *   **操作:** 音频文件数据全部发送完毕后，客户端向服务器发送一个特殊的结束消息（通常是 JSON 格式，例如 `{"is_final": true}`），告知服务器该文件的音频流结束。这是通过 `FunASR_Client` 内部的 `send_end_signal` (或类似) 方法完成的。
    *   **中间结果:** 服务器知道当前音频流已结束，开始进行最终处理并准备发送最终结果。

9.  **(针对每个音频文件) 接收并处理识别结果:**
    *   **操作:** 客户端进入监听状态，等待接收来自服务器的 WebSocket 消息。服务器会发送包含识别结果的 JSON 消息。
        *   对于 `offline` 模式，通常只会在收到结束信号后收到一个或多个包含最终识别结果的消息。
        *   对于 `online` 或 `2pass` 模式，在发送音频过程中可能就会收到中间结果，最后收到最终结果。
        `funasr_wss_client.py` 脚本会调用 `FunASR_Client` 的 `receive_results` (或类似) 方法来处理接收到的消息。脚本会将接收到的识别文本（可能还有时间戳等信息）累积起来。
    *   **中间结果:** 客户端接收到 JSON 格式的识别结果字符串，例如 `{"text": "欢迎使用FunASR。", "timestamp": [[...], ...], ...}`。脚本解析这些 JSON，提取出所需的文本或其他信息。

10. **(针对每个音频文件) 输出/保存结果:**
    *   **操作:** 脚本将获取到的最终识别结果进行处理。默认情况下，它可能会直接打印到标准输出 (console)。如果指定了 `--output_dir`，它会将结果写入到对应的输出文件中（通常以原音频文件名命名，扩展名为 `.txt` 或 `.json`）。
    *   **中间结果:** 在控制台看到识别的文本，或者在指定的输出目录中生成了结果文件。

11. **(针对每个音频文件) 关闭WebSocket连接:**
    *   **操作:** 处理完一个音频文件的所有结果后，客户端主动关闭与服务器的 WebSocket 连接。
    *   **中间结果:** 连接被断开。

12. **(如果使用线程池) 等待所有任务完成:**
    *   **操作:** 如果使用了线程池，主线程会等待所有处理音频文件的子线程执行完毕。
    *   **中间结果:** 所有音频文件都已被处理。

13. **脚本结束:**
    *   **操作:** 所有任务完成，脚本退出。
    *   **中间结果:** 程序执行完毕。

这个流程描述了主要的步骤。实际代码 (`funasr_wss_client.py` 和 `funasr_client_api.py`) 中会有更详细的错误处理、日志记录、异步操作（如果使用了 `asyncio`）等实现细节。



# 服务端日志分析记录
好的，我们来分析一下您提供的这段服务端日志 (`server-log.txt` 的 122-132 行，虽然实际包含的行数更多，但核心交互在此)：

```
# ------------------ 连接建立与参数接收 ------------------
I20250424 20:58:23.751111 21649 websocket-server.cpp:29] on_tls_init called with hdl: 0x76401c025ef0  # TLS初始化 (新连接)
I20250424 20:58:23.751161 21649 websocket-server.cpp:30] using TLS mode: Mozilla Intermediate
I20250424 20:58:23.861783 21649 websocket-server.cpp:174] on_open, active connections: 2            # 连接建立，活动连接变为2
I20250424 20:58:23.976612 21650 websocket-server.cpp:347] hotwords:                                 # 收到参数，检查热词（此处为空）

# --- 一个较早的、可能不相关的连接关闭 ---
I20250424 20:58:24.269450 21648 websocket-server.cpp:250] connection is closed.                 # 注意：这个关闭事件非常快，可能与前一个任务相关
I20250424 20:58:24.272753 21648 websocket-server.cpp:211] remove one connection                 # 活动连接数减少

# ------------------ 数据传输与处理 ------------------
I20250424 20:58:33.000890 21651 websocket-server.cpp:375] client done                           # 客户端数据发送完毕 (约9秒后)
I20250424 20:58:35.356354 21598 websocket-server.cpp:127] buffer.size=5743360,result json={...} # 服务端生成识别结果 (数据完毕后约2.3秒)
                                                                                             # "wav_name":"demo" - 注意这里的文件名是demo

# ------------------ 连接关闭 ------------------
I20250424 20:58:41.367774 21650 websocket-server.cpp:191] on_close, active connections: 1           # 本次识别任务的连接关闭 (结果生成后约6秒)
I20250424 20:58:42.291394 21648 websocket-server.cpp:250] connection is closed.                 # 另一个连接关闭 (可能是第一个任务的连接)
I20250424 20:58:42.294812 21648 websocket-server.cpp:211] remove one connection                 # 活动连接数再次减少
```

**结论分析:**

1.  **标准流程确认:** 这段日志清晰地展示了 `offline` 模式下一次成功识别的标准交互流程：建立连接 (`on_open`) -> 接收参数 -> 等待客户端数据传输完成 (`client done`) -> 服务器处理并生成结果 (`result json`) -> 关闭连接 (`on_close`)。
2.  **关键时间点:**
    *   **数据传输是主要耗时:** 从连接打开 (`20:58:23.8`) 到客户端数据传输完成 (`20:58:33.0`) 大约花费了 9 秒。这部分时间主要取决于音频文件大小和网络速度。
    *   **服务端处理较快:** 服务端在收到全部数据后，仅用约 2.3 秒就完成了识别并生成了结果。
    *   **连接维持时间:** 服务端在发送完结果后，并没有立即关闭连接，而是等待了大约 6 秒才记录 `on_close`。
3.  **`wav_name` 问题:** 服务端日志记录的 `wav_name` 是 `"demo"`，而不是客户端日志中显示的实际文件名（如 `tv-report-1.wav`）。这强烈暗示客户端在发送初始配置JSON时，`wav_name` 字段没有被正确设置或被服务端忽略/覆盖了。**这是需要客户端修正的关键点。**
4.  **并发与连接:** 日志显示 `active connections: 2`，说明服务器确实支持并发连接。日志中出现了多个 `on_close` 事件，并且时间点与任务流程不完全匹配（例如 `20:58:24` 的关闭），这可能与客户端的连接管理策略（是否复用连接、何时关闭旧连接）以及服务端清理超时或异常连接的机制有关。
5.  **热词:** 服务端日志明确记录了检查热词 (`hotwords:`)，但内容为空，符合本次客户端请求未使用热词的情况。

**对客户端开发的启示:**

1.  **正确发送 `wav_name`:** **务必**检查客户端发送给服务端的第一个 JSON 消息，确保 `"wav_name"` 字段被正确设置为当前处理的文件名。这对于日志追踪和问题排查至关重要。参考 `funasr_wss_client.py` 中构造该 JSON 的部分。
2.  **处理等待时间:**
    *   客户端在发送完所有音频数据（包括最后的 `{"is_speaking": false}` 消息）后，需要设置一个合理的**等待超时时间**来接收最终的识别结果 JSON。根据日志，这个处理时间（从`client done`到`result json`）可能需要几秒钟。
    *   考虑到数据传输时间可能更长（取决于文件大小），整体的超时时间需要覆盖 **数据传输 + 服务端处理** 的总和。
3.  **明确连接管理策略:**
    *   **推荐复用连接:** 为了效率，客户端最好在一次会话中复用同一个 WebSocket 连接来处理多个文件。这意味着在一个文件识别完成后（收到结果），可以直接在同一个连接上发送下一个文件的配置 JSON 和音频数据。
    *   **显式关闭:** 无论是否复用，当客户端确认不再需要连接时（例如程序退出或用户明确断开），应调用 `websocket.close()` 来主动关闭连接，而不是仅仅依赖服务端超时关闭。这有助于及时释放双方资源。
4.  **健壮的错误和状态处理:**
    *   客户端需要能处理网络错误、连接意外断开（如日志中 `20:58:24` 的关闭事件所示）等情况。
    *   应该清晰地向用户展示当前状态：连接中、上传中、处理中、识别完成、失败等。
5.  **结果解析:** 客户端需要正确解析服务端返回的 `result json`，提取 `"text"` 字段获取识别结果，如果需要，还可以提取 `"stamp_sents"` 或 `"timestamp"` 获取时间戳信息。


# 时序图
sequenceDiagram
    participant Client as FunASR客户端
    participant Server as FunASR服务端
    
    Note over Client: 1. 参数解析与初始化<br>(host, port, mode, audio_in等)
    Note over Client: 2. 音频文件处理<br>(检查单个文件或.scp文件列表)
    Note over Client: 3. 线程分配<br>(根据thread_num创建处理线程)
    
    Client->>Server: 4. WebSocket连接请求<br>(wss://host:port 或 ws://host:port)
    Server-->>Client: 连接确认(on_open)
    Note over Server: 记录active connections
    
    Client->>Server: 5. 发送初始参数(JSON)<br>{"mode": "offline", "wav_name": "实际文件名",<br>"wav_format": "pcm", "is_speaking": true,<br>"hotwords": "", "itn": true}
    Note over Server: 检查参数(如hotwords)
    
    Note over Client: 6. 音频数据读取<br>(打开文件, 获取音频数据)
    
    loop 7. 音频数据分块发送
        Client->>Server: 发送音频数据块(二进制)
        Note over Client: 切分数据: stride = int(60*10/10/1000*16000*2)
    end
    
    Client->>Server: 发送结束标志<br>{"is_speaking": false}
    Note over Server: 记录client done
    
    Note over Server: 执行语音识别处理<br>(约2-30秒，取决于音频长度)
    
    Server-->>Client: 8. 发送识别结果(JSON)<br>{"wav_name": "文件名", "text": "识别文本",<br>"timestamp": [[起始时间,结束时间],...],<br>"mode": "offline", "is_final": true}
    
    Note over Client: 9. 处理识别结果<br>(显示或保存到文件)
    
    Client->>Server: 10. 关闭WebSocket连接
    Server-->>Client: 确认连接关闭(on_close)
    Note over Server: 更新active connections
    
    Note over Client: 11. 程序结束


# 时序图--mermaid图像
https://www.mermaidchart.com/raw/606cb197-c143-43c3-88a8-cf509487efb4?theme=light&version=v0.1&format=svg
prd/FunASR-Client&Server-sequenceDiagram.png