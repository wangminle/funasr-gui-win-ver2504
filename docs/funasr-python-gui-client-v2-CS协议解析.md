# FunASR中的Client-Server协议解析

**最后更新日期:** 2025-09-29

## 协议概述

从我们之前分析的 `funasr_wss_client.py` 脚本和服务器的标准交互流程来看，其核心协议本身**确实没有明确定义一个专门的‘取消’消息类型**。

整个流程被设计为一个完整的、从开始到结束的会话（Session），一旦开始，就预期会完整地走完：

1.  **开始会话**: `{"is_speaking": true}`
2.  **传输数据**: `Binary Chunks`
3.  **结束会话**: `{"is_speaking": false}`
4.  **获取结果**: `{"is_final": true}`

所以，如果一个客户端严格按照这个最基础的协议来通信，那么它能“取消”识别的唯一方式就是**提前中断WebSocket连接**。

### 中断连接如何实现“取消”？

当客户端强行关闭WebSocket连接时，服务器端会触发 `on_close` 事件。此时：

*   服务器会检测到这个连接已经关闭。
*   与这个连接关联的识别任务（ASR Instance）会被标记为异常中断。
*   服务器会清理与该任务相关的所有资源，包括已经接收并缓存的音频数据、占用的模型实例和内存等。
*   最终结果就是，这个识别任务被**丢弃**了，从而达到了“取消”的效果。

这是一种“野蛮”但有效的取消方式。

---

### 应用层面的扩展：`funasr_gui_client_v2.py` 的实现

但是，这是一个非常好的问题，它揭示了协议本身和上层应用实现之间的差异。在您提供的 `funasr_gui_client_v2.py` 这个更复杂的GUI客户端中，**开发者确实实现了一套更取消机制**。

这套机制并不是建立在WebSocket协议之上的，而是**GUI客户端与其启动的子进程 (`simple_funasr_client.py`) 之间的通信**。

让我们看一下 `funasr_gui_client_v2.py` 中的 `cancel_recognition` 函数：

1.  **用户点击“取消识别”按钮。**
2.  GUI程序会执行 `cancel_recognition` 方法。
3.  该方法会尝试向它启动的 `simple_funasr_client.py` 子进程的**标准输入(stdin)** 发送一个JSON命令：
    ```json
    {
        "type": "cancel_request",
        "timestamp": 1678886400.0,
        "reason": "user_initiated"
    }
    ```
4.  理想情况下，`simple_funasr_client.py` 脚本被设计成可以监听自己的标准输入。当它收到这个 `cancel_request` 命令后，它就会主动关闭与FunASR服务器的WebSocket连接。
5.  如果发送命令后，子进程没有在规定时间内结束，GUI客户端会采取强制措施：`process.terminate()` 然后 `process.kill()`，即强行终止子进程。这同样会导致WebSocket连接被中断。

### 结论

所以，我们可以得出以下两点结论：

1.  **在FunASR的WebSocket核心协议层面**：您是对的，没有原生的“取消”消息。取消操作只能通过**中断连接**来实现。
2.  **在GUI客户端的应用层面**：开发者为了提供更好的用户体验，通过“父进程给子进程发送指令”的方式，增加了一层“识别取消”的尝试。但其最终依赖的底层逻辑，仍然是让子进程去**中断WebSocket连接**。如果识别取消失败，就会退化为父进程直接杀死子进程，同样达到中断连接的目的。


## 了解FunASR开源项目中WebSocket本身的约定

好的，没有问题。我们来更深入地剖析一下 FunASR 通信中 **WebSocket 协议本身**的机制，以及**服务器视角下的事件定义**。

这可以帮助我们理解整个通信的底层骨架。

---

### 一、 WebSocket 连接的生命周期

一次完整的 WebSocket 通信遵循一个清晰的生命周期，可以分为三个核心阶段：

#### 1. 连接建立 (Handshake - 握手)

这不是简单地建立一个 TCP 连接，而是一个 "升级" 过程。

*   **客户端发起:** 当客户端代码执行 `websockets.connect(uri)` 时，它实际上是向服务器发送了一个标准的 **HTTP GET** 请求。但这个请求包含了特殊的请求头 (Header):
    *   `Upgrade: websocket`
    *   `Connection: Upgrade`
    *   `Sec-WebSocket-Key`: 一个随机生成的密钥，用于验证。

*   **服务器响应:**
    *   如果服务器支持 WebSocket 并且同意升级，它会返回一个 HTTP `101 Switching Protocols` 状态码。
    *   响应中也会包含一个 `Sec-WebSocket-Accept` 头，其值是根据客户端的 `Sec-WebSocket-Key` 计算出来的。
    *   客户端验证这个 `Accept` key，如果匹配，握手成功。

*   **结果:**
    *   底层的 TCP 连接从这一刻起，**从 HTTP 协议切换为 WebSocket 协议**。
    *   一条全双工、持久化的通信信道就建立好了。
    *   此时，服务器会触发它的 **`on_open`** 事件。

#### 2. 数据交换 (Data Transfer)

握手成功后，双方就可以互相发送数据了。

*   **数据帧 (Frame):** WebSocket 通信不再使用 HTTP 的请求/响应模式，而是通过 "帧" 来传输数据。每一条消息（无论是 JSON 还是二进制数据）都会被打包成一个或多个帧。
*   **帧类型:** 主要有文本帧 (Text Frame, 用于传输 UTF-8 文本，如我们的 JSON 命令) 和二进制帧 (Binary Frame, 用于传输音频数据)。此外还有 Ping/Pong 帧用于心跳检测，以及 Close 帧用于关闭连接。
*   **服务器事件:** 每当服务器成功接收并解析完一条完整的消息（可能由多个帧组成），就会触发它的 **`on_message`** 事件，并将消息内容传递给上层业务逻辑（即我们的 FunASR 识别引擎）。

#### 3. 连接关闭 (Closing Handshake)

与建立连接类似，关闭连接也应该是一个“握手”过程。

*   **主动关闭方 (客户端或服务器):** 发送一个特殊的 "Close" 帧。这个帧可以包含一个状态码和可选的关闭原因。
*   **被动关闭方:** 收到 Close 帧后，必须立即回送一个 Close 帧作为确认，然后关闭底层的 TCP 连接。
*   **结果:**
    *   双方都同意关闭，连接被干净地断开。
    *   服务器会触发它的 **`on_close`** 事件。

---

### 二、 服务器层面的事件定义与解读

服务器端的 WebSocket 框架（从日志看，很可能是基于 C++ 的 `websocketpp`）通常是事件驱动的。它会监听并响应以下关键事件，每种事件都对应着一种客户端行为或网络状态。

#### 1. `on_open` (连接成功)

*   **触发时机:** 在 WebSocket 握手成功后立即触发。
*   **服务器行为:**
    *   在日志中记录 `on_open`。
    *   将其内部的 `active_connections` (活动连接数) 计数器加一。
    *   为这个新连接分配必要的内存和资源，准备接收数据。
*   **对客户端的意义:**
    *   客户端的 `await websockets.connect(...)` 调用成功返回。
    *   这表示客户端现在可以安全地发送第一个消息了（即包含 `is_speaking: true` 的配置 JSON）。

#### 2. `on_message` (收到消息)

*   **触发时机:** 收到一个完整的文本或二进制消息时。
*   **服务器行为:**
    *   **解析消息类型:** 判断是 JSON 字符串还是二进制音频数据。
    *   **路由到业务逻辑:**
        *   如果是 `is_speaking: true` 的 JSON，则创建一个新的 ASR 任务实例。
        *   如果是音频二进制数据，则送入对应 ASR 实例的缓冲区。
        *   如果是 `is_speaking: false` 的 JSON，则通知 ASR 实例数据已完结，可以开始最终处理。
*   **对客户端的意义:**
    *   客户端的 `await websocket.send(...)` 已成功将数据发出，并且服务器已接收。

#### 3. `on_close` (连接正常关闭)

*   **触发时机:** 双方完成了 "Closing Handshake"。这通常发生在：
    1.  客户端在完成所有操作后，主动调用了 `websocket.close()`。
    2.  服务器在发送完最终结果 (`is_final: true`) 后，决定主动关闭连接。
*   **服务器行为:**
    *   在日志中记录 `on_close`。
    *   将其内部的 `active_connections` 计数器减一。
    *   **释放与该连接相关的所有资源**，包括 ASR 实例、缓冲区、内存等。这是一个**正常**的清理流程。
*   **对客户端的意义:**
    *   如果客户端主动关闭，则操作完成。
    *   如果客户端正在 `await websocket.recv()`，它会收到一个 `ConnectionClosedOK` 异常，表示会话正常结束。

#### 4. `on_fail` 或 `on_error` (连接异常中断)

*   **触发时机:** 这是一个非预期的事件，通常由底层网络问题引起：
    1.  **TCP 连接突然中断** (例如，拔掉网线、客户端进程崩溃、防火墙拦截)。
    2.  TLS/SSL 握手失败。
    3.  收到了格式错误的 WebSocket 帧。
*   **服务器行为:**
    *   这是一个**异常**的清理流程。服务器会立即尝试释放所有相关资源，但可能会在日志中记录 `error` 或 `fail`。
    *   它可能仍然会触发 `on_close` 来确保资源被回收。
*   **对客户端的意义:**
    *   这是实现“野蛮取消”的核心。当客户端强行终止进程或网络连接时，服务器就会感知到这个 `on_fail` 事件。
    *   客户端的任何 `send()` 或 `recv()` 操作都会立即抛出 `ConnectionClosedError` 或类似异常。

#### 5. `on_tls_init` (TLS 初始化，仅用于 `wss://`)

*   **触发时机:** 当客户端尝试连接安全的 `wss://` 地址时，在 `on_open` 之前触发。
*   **服务器行为:** 初始化 SSL/TLS 上下文，为加密通信做准备。
*   **对客户端的意义:** 这个过程对客户端代码是透明的，由 `websockets` 库和提供的 `ssl_context` 自动处理。

### 总结

| 服务器事件    | 触发原因                                                     | 客户端感知                                                   | 关键作用                                     |
| :------------ | :----------------------------------------------------------- | :----------------------------------------------------------- | :------------------------------------------- |
| **`on_open`** | 客户端成功完成 WebSocket 握手。                              | `connect()` 成功返回。                                       | 标志着一个新会话的开始，服务器准备好接收数据。 |
| **`on_message`**| 客户端发送了 JSON 命令或二进制音频数据。                     | `send()` 调用成功。                                          | 驱动核心的识别业务逻辑。                     |
| **`on_close`**  | **正常关闭**：客户端或服务器发起了关闭握手。           | `recv()` 抛出 `ConnectionClosedOK` 异常或 `close()` 调用完成。 | 标志着会话正常结束，服务器正常释放资源。     |
| **`on_fail`**   | **异常中断**：网络中断、进程崩溃、协议错误等。               | `send()`/`recv()` 抛出 `ConnectionClosedError` 异常。        | 实现“取消”操作的底层机制，服务器异常清理资源。 |





## 关于funasr_gui_client主程序对检测ws连接的说明

好的，我们来详细拆解一下从用户在GUI上点击“连接服务器”按钮，到最终在日志中看到“连接成功”的完整流程。这涉及到 `funasr_gui_client_v2.py` (GUI进程) 和 `simple_funasr_client.py` (识别子进程) 之间的协作，但在这个特定场景下，**核心工作完全由 `funasr_gui_client_v2.py` 独立完成**。`simple_funasr_client.py` 在此刻**并未被启动**。

以下是详细的步骤分解：

---

### 第一阶段：GUI 进程 (`funasr_gui_client_v2.py`) 的工作

1.  **用户点击 "连接服务器" 按钮**
    *   **触发事件:** `command=self.connect_server` 被调用。

2.  **`connect_server` 方法被执行**
    *   **获取参数:** 从输入框获取服务器 IP (`ip_var.get()`) 和端口 (`port_var.get()`)。
    *   **UI 更新 (准备阶段):**
        *   禁用 "连接服务器" 按钮 (`self.connect_button.config(state=tk.DISABLED)`)，防止用户重复点击。
        *   更新连接状态指示灯为 "未连接" (`_update_connection_indicator(False)`)。
        *   更新底部的状态栏，显示 "尝试连接服务器..."。
    *   **记录日志:** `logging.info("用户操作: 尝试连接服务器...")`
    *   **启动后台线程:** 创建一个新的 `threading.Thread`，目标是执行 `_test_connection` 方法。这是为了防止网络连接操作阻塞GUI主线程，导致界面卡死。

3.  **`_test_connection` 方法在后台线程中执行**
    *   **检查依赖 (如果需要):** 首次运行时会检查 `websockets` 等库是否存在，如果不存在会尝试自动安装。
    *   **关键步骤：调用异步测试函数:** `asyncio.run(self._async_test_connection(ip, port, ssl_enabled))`。这是核心，它启动了一个临时的 `asyncio` 事件循环，专门用来执行WebSocket的异步连接测试。

4.  **`_async_test_connection` 方法在 `asyncio` 事件循环中执行**
    *   **构建URI:** 根据 "启用SSL" 复选框的状态，决定使用 `wss://` (安全) 还是 `ws://` (不安全) 协议来构造连接地址 `uri`。
    *   **配置SSL上下文 (如果需要):** 如果启用SSL，会创建一个 `ssl.create_default_context()`，并设置为不验证服务器证书 (`check_hostname = False`, `verify_mode = ssl.CERT_NONE`)。这简化了客户端连接，使其能连接自签名证书的服务器。
    *   **记录日志:** `logging.info("尝试WebSocket连接到: {}")`
    *   **执行连接 (核心中的核心):**
        ```python
        websocket = await asyncio.wait_for(websockets.connect(uri, ...), timeout=5)
        ```
        *   `websockets.connect()`: 这是 `websockets` 库的函数，它会执行我们之前讨论过的 **WebSocket 握手** (发送 HTTP Upgrade 请求)。
        *   `asyncio.wait_for()`: 这是一个超时控制器，如果 `websockets.connect()` 在5秒内没有完成握手，就会抛出 `asyncio.TimeoutError` 异常。

5.  **连接后的交互与验证**
    *   **如果握手成功:**
        *   **进入 `async with websocket:` 代码块。**
        *   **发送测试消息:**
            ```python
            message = json.dumps({"mode": "offline", "is_speaking": True})
            await websocket.send(message)
            ```
            GUI客户端模拟了一个真实识别任务的开始，向服务器发送了一个标准的“开始会话”消息。
        *   **尝试接收响应:** `await asyncio.wait_for(websocket.recv(), timeout=2)`。它会等待服务器的回应，最多2秒。FunASR服务器通常在收到开始消息后不会立即回复，所以这里很可能会超时，但这**不影响连接测试的成功判断**。
        *   **记录日志:** `logging.info("系统事件: WebSocket连接测试成功")`。

6.  **更新最终状态 (回到主线程)**
    *   **无论 `recv()` 是否超时，只要 `send()` 成功了，就认为连接是可用的。**
    *   **更新UI:**
        *   调用 `_update_connection_indicator(True)`，将状态指示灯变为**绿色**的 "已连接"。
        *   更新状态栏为 "连接成功"。
    *   **设置标志:** `self.connection_status = True`。这个布尔值标志着现在可以开始真正的识别任务了。
    *   **恢复按钮:** `self.connect_button.config(state=tk.NORMAL)`，连接按钮恢复可用。

---

### 第二阶段：`simple_funasr_client.py` 在做什么？

**什么都没做。**

在整个“连接服务器”的测试流程中，`simple_funasr_client.py` 脚本**完全没有被调用或启动**。GUI客户端 `funasr_gui_client_v2.py` 自身包含了一个**轻量级的、临时的WebSocket客户端** (`_async_test_connection` 函数)，专门用于测试与服务器的连通性。

`simple_funasr_client.py` 只会在用户**点击 "开始识别" 按钮**后，才会被 `funasr_gui_client_v2.py` 作为一个**独立的子进程** (`subprocess.Popen`) 启动起来，去执行真正的、长时间的音频文件上传和识别任务。

### 总结流程图

<svg aria-roledescription="sequence" role="graphics-document document" viewBox="-50 -10 1853 1022" style="max-width: 1853px;" xmlns="http://www.w3.org/2000/svg" width="100%" id="mermaid-svg-1750243312231-l5xh4gln5"><g><rect class="actor" ry="3" rx="3" height="65" width="150" stroke="#666" fill="#eaeaea" y="936" x="1503"/><text style="text-anchor: middle; font-size: 16px; font-weight: 400;" class="actor" alignment-baseline="central" dominant-baseline="central" y="968.5" x="1578"><tspan dy="0" x="1578">AsyncIO</tspan></text></g><g><rect class="actor" ry="3" rx="3" height="65" width="150" stroke="#666" fill="#eaeaea" y="936" x="1303"/><text style="text-anchor: middle; font-size: 16px; font-weight: 400;" class="actor" alignment-baseline="central" dominant-baseline="central" y="968.5" x="1378"><tspan dy="0" x="1378">异步事件循环</tspan></text></g><g><rect class="actor" ry="3" rx="3" height="65" width="150" stroke="#666" fill="#eaeaea" y="936" x="1103"/><text style="text-anchor: middle; font-size: 16px; font-weight: 400;" class="actor" alignment-baseline="central" dominant-baseline="central" y="968.5" x="1178"><tspan dy="0" x="1178">BG Thread</tspan></text></g><g><rect class="actor" ry="3" rx="3" height="65" width="150" stroke="#666" fill="#eaeaea" y="936" x="903"/><text style="text-anchor: middle; font-size: 16px; font-weight: 400;" class="actor" alignment-baseline="central" dominant-baseline="central" y="968.5" x="978"><tspan dy="0" x="978">后台线程</tspan></text></g><g><rect class="actor" ry="3" rx="3" height="65" width="150" stroke="#666" fill="#eaeaea" y="936" x="685"/><text style="text-anchor: middle; font-size: 16px; font-weight: 400;" class="actor" alignment-baseline="central" dominant-baseline="central" y="968.5" x="760"><tspan dy="0" x="760">GUI</tspan></text></g><g><rect class="actor" ry="3" rx="3" height="65" width="150" stroke="#666" fill="#eaeaea" y="936" x="485"/><text style="text-anchor: middle; font-size: 16px; font-weight: 400;" class="actor" alignment-baseline="central" dominant-baseline="central" y="968.5" x="560"><tspan dy="0" x="560">Server</tspan></text></g><g><rect class="actor" ry="3" rx="3" height="65" width="235" stroke="#666" fill="#eaeaea" y="936" x="200"/><text style="text-anchor: middle; font-size: 16px; font-weight: 400;" class="actor" alignment-baseline="central" dominant-baseline="central" y="968.5" x="317.5"><tspan dy="0" x="317.5">GUI (funasr_gui_client_v2.py)</tspan></text></g><g><rect class="actor" ry="3" rx="3" height="65" width="150" stroke="#666" fill="#eaeaea" y="936" x="0"/><text style="text-anchor: middle; font-size: 16px; font-weight: 400;" class="actor" alignment-baseline="central" dominant-baseline="central" y="968.5" x="75"><tspan dy="0" x="75">User</tspan></text></g><g><line stroke="#999" stroke-width="0.5px" class="200" y2="936" x2="1578" y1="5" x1="1578" id="actor47"/><g id="root-47"><rect class="actor" ry="3" rx="3" height="65" width="150" stroke="#666" fill="#eaeaea" y="0" x="1503"/><text style="text-anchor: middle; font-size: 16px; font-weight: 400;" class="actor" alignment-baseline="central" dominant-baseline="central" y="32.5" x="1578"><tspan dy="0" x="1578">AsyncIO</tspan></text></g></g><g><line stroke="#999" stroke-width="0.5px" class="200" y2="936" x2="1378" y1="5" x1="1378" id="actor46"/><g id="root-46"><rect class="actor" ry="3" rx="3" height="65" width="150" stroke="#666" fill="#eaeaea" y="0" x="1303"/><text style="text-anchor: middle; font-size: 16px; font-weight: 400;" class="actor" alignment-baseline="central" dominant-baseline="central" y="32.5" x="1378"><tspan dy="0" x="1378">异步事件循环</tspan></text></g></g><g><line stroke="#999" stroke-width="0.5px" class="200" y2="936" x2="1178" y1="5" x1="1178" id="actor45"/><g id="root-45"><rect class="actor" ry="3" rx="3" height="65" width="150" stroke="#666" fill="#eaeaea" y="0" x="1103"/><text style="text-anchor: middle; font-size: 16px; font-weight: 400;" class="actor" alignment-baseline="central" dominant-baseline="central" y="32.5" x="1178"><tspan dy="0" x="1178">BG Thread</tspan></text></g></g><g><line stroke="#999" stroke-width="0.5px" class="200" y2="936" x2="978" y1="5" x1="978" id="actor44"/><g id="root-44"><rect class="actor" ry="3" rx="3" height="65" width="150" stroke="#666" fill="#eaeaea" y="0" x="903"/><text style="text-anchor: middle; font-size: 16px; font-weight: 400;" class="actor" alignment-baseline="central" dominant-baseline="central" y="32.5" x="978"><tspan dy="0" x="978">后台线程</tspan></text></g></g><g><line stroke="#999" stroke-width="0.5px" class="200" y2="936" x2="760" y1="5" x1="760" id="actor43"/><g id="root-43"><rect class="actor" ry="3" rx="3" height="65" width="150" stroke="#666" fill="#eaeaea" y="0" x="685"/><text style="text-anchor: middle; font-size: 16px; font-weight: 400;" class="actor" alignment-baseline="central" dominant-baseline="central" y="32.5" x="760"><tspan dy="0" x="760">GUI</tspan></text></g></g><g><line stroke="#999" stroke-width="0.5px" class="200" y2="936" x2="560" y1="5" x1="560" id="actor42"/><g id="root-42"><rect class="actor" ry="3" rx="3" height="65" width="150" stroke="#666" fill="#eaeaea" y="0" x="485"/><text style="text-anchor: middle; font-size: 16px; font-weight: 400;" class="actor" alignment-baseline="central" dominant-baseline="central" y="32.5" x="560"><tspan dy="0" x="560">Server</tspan></text></g></g><g><line stroke="#999" stroke-width="0.5px" class="200" y2="936" x2="317.5" y1="5" x1="317.5" id="actor41"/><g id="root-41"><rect class="actor" ry="3" rx="3" height="65" width="235" stroke="#666" fill="#eaeaea" y="0" x="200"/><text style="text-anchor: middle; font-size: 16px; font-weight: 400;" class="actor" alignment-baseline="central" dominant-baseline="central" y="32.5" x="317.5"><tspan dy="0" x="317.5">GUI (funasr_gui_client_v2.py)</tspan></text></g></g><g><line stroke="#999" stroke-width="0.5px" class="200" y2="936" x2="75" y1="5" x1="75" id="actor40"/><g id="root-40"><rect class="actor" ry="3" rx="3" height="65" width="150" stroke="#666" fill="#eaeaea" y="0" x="0"/><text style="text-anchor: middle; font-size: 16px; font-weight: 400;" class="actor" alignment-baseline="central" dominant-baseline="central" y="32.5" x="75"><tspan dy="0" x="75">User</tspan></text></g></g><style>#mermaid-svg-1750243312231-l5xh4gln5{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;fill:#cccccc;}#mermaid-svg-1750243312231-l5xh4gln5 .error-icon{fill:#90274a;}#mermaid-svg-1750243312231-l5xh4gln5 .error-text{fill:#f48771;stroke:#f48771;}#mermaid-svg-1750243312231-l5xh4gln5 .edge-thickness-normal{stroke-width:2px;}#mermaid-svg-1750243312231-l5xh4gln5 .edge-thickness-thick{stroke-width:3.5px;}#mermaid-svg-1750243312231-l5xh4gln5 .edge-pattern-solid{stroke-dasharray:0;}#mermaid-svg-1750243312231-l5xh4gln5 .edge-pattern-dashed{stroke-dasharray:3;}#mermaid-svg-1750243312231-l5xh4gln5 .edge-pattern-dotted{stroke-dasharray:2;}#mermaid-svg-1750243312231-l5xh4gln5 .marker{fill:#cccccc;stroke:#cccccc;}#mermaid-svg-1750243312231-l5xh4gln5 .marker.cross{stroke:#cccccc;}#mermaid-svg-1750243312231-l5xh4gln5 svg{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;}#mermaid-svg-1750243312231-l5xh4gln5 .actor{stroke:hsl(49.5652173913, 0%, 51.3725490196%);fill:#75715e;}#mermaid-svg-1750243312231-l5xh4gln5 text.actor&gt;tspan{fill:#ffffff;stroke:none;}#mermaid-svg-1750243312231-l5xh4gln5 .actor-line{stroke:#cccccc;}#mermaid-svg-1750243312231-l5xh4gln5 .messageLine0{stroke-width:1.5;stroke-dasharray:none;stroke:#cccccc;}#mermaid-svg-1750243312231-l5xh4gln5 .messageLine1{stroke-width:1.5;stroke-dasharray:2,2;stroke:#cccccc;}#mermaid-svg-1750243312231-l5xh4gln5 #arrowhead path{fill:#cccccc;stroke:#cccccc;}#mermaid-svg-1750243312231-l5xh4gln5 .sequenceNumber{fill:rgba(204, 204, 204, 0.7);}#mermaid-svg-1750243312231-l5xh4gln5 #sequencenumber{fill:#cccccc;}#mermaid-svg-1750243312231-l5xh4gln5 #crosshead path{fill:#cccccc;stroke:#cccccc;}#mermaid-svg-1750243312231-l5xh4gln5 .messageText{fill:#cccccc;stroke:none;}#mermaid-svg-1750243312231-l5xh4gln5 .labelBox{stroke:#454545;fill:#1e1f1c;}#mermaid-svg-1750243312231-l5xh4gln5 .labelText,#mermaid-svg-1750243312231-l5xh4gln5 .labelText&gt;tspan{fill:#cccccc;stroke:none;}#mermaid-svg-1750243312231-l5xh4gln5 .loopText,#mermaid-svg-1750243312231-l5xh4gln5 .loopText&gt;tspan{fill:#f8f8f2;stroke:none;}#mermaid-svg-1750243312231-l5xh4gln5 .loopLine{stroke-width:2px;stroke-dasharray:2,2;stroke:#454545;fill:#454545;}#mermaid-svg-1750243312231-l5xh4gln5 .note{stroke:#75715e;fill:#414339;}#mermaid-svg-1750243312231-l5xh4gln5 .noteText,#mermaid-svg-1750243312231-l5xh4gln5 .noteText&gt;tspan{fill:#cccccc;stroke:none;}#mermaid-svg-1750243312231-l5xh4gln5 .activation0{fill:rgba(135, 139, 145, 0.25);stroke:#99947c;}#mermaid-svg-1750243312231-l5xh4gln5 .activation1{fill:rgba(135, 139, 145, 0.25);stroke:#99947c;}#mermaid-svg-1750243312231-l5xh4gln5 .activation2{fill:rgba(135, 139, 145, 0.25);stroke:#99947c;}#mermaid-svg-1750243312231-l5xh4gln5 .actorPopupMenu{position:absolute;}#mermaid-svg-1750243312231-l5xh4gln5 .actorPopupMenuPanel{position:absolute;fill:#75715e;box-shadow:0px 8px 16px 0px rgba(0,0,0,0.2);filter:drop-shadow(3px 5px 2px rgb(0 0 0 / 0.4));}#mermaid-svg-1750243312231-l5xh4gln5 .actor-man line{stroke:hsl(49.5652173913, 0%, 51.3725490196%);fill:#75715e;}#mermaid-svg-1750243312231-l5xh4gln5 .actor-man circle,#mermaid-svg-1750243312231-l5xh4gln5 line{stroke:hsl(49.5652173913, 0%, 51.3725490196%);fill:#75715e;stroke-width:2px;}#mermaid-svg-1750243312231-l5xh4gln5 :root{--mermaid-font-family:"trebuchet ms",verdana,arial,sans-serif;}</style><g/><defs><symbol height="24" width="24" id="computer"><path d="M2 2v13h20v-13h-20zm18 11h-16v-9h16v9zm-10.228 6l.466-1h3.524l.467 1h-4.457zm14.228 3h-24l2-6h2.104l-1.33 4h18.45l-1.297-4h2.073l2 6zm-5-10h-14v-7h14v7z" transform="scale(.5)"/></symbol></defs><defs><symbol clip-rule="evenodd" fill-rule="evenodd" id="database"><path d="M12.258.001l.256.004.255.005.253.008.251.01.249.012.247.015.246.016.242.019.241.02.239.023.236.024.233.027.231.028.229.031.225.032.223.034.22.036.217.038.214.04.211.041.208.043.205.045.201.046.198.048.194.05.191.051.187.053.183.054.18.056.175.057.172.059.168.06.163.061.16.063.155.064.15.066.074.033.073.033.071.034.07.034.069.035.068.035.067.035.066.035.064.036.064.036.062.036.06.036.06.037.058.037.058.037.055.038.055.038.053.038.052.038.051.039.05.039.048.039.047.039.045.04.044.04.043.04.041.04.04.041.039.041.037.041.036.041.034.041.033.042.032.042.03.042.029.042.027.042.026.043.024.043.023.043.021.043.02.043.018.044.017.043.015.044.013.044.012.044.011.045.009.044.007.045.006.045.004.045.002.045.001.045v17l-.001.045-.002.045-.004.045-.006.045-.007.045-.009.044-.011.045-.012.044-.013.044-.015.044-.017.043-.018.044-.02.043-.021.043-.023.043-.024.043-.026.043-.027.042-.029.042-.03.042-.032.042-.033.042-.034.041-.036.041-.037.041-.039.041-.04.041-.041.04-.043.04-.044.04-.045.04-.047.039-.048.039-.05.039-.051.039-.052.038-.053.038-.055.038-.055.038-.058.037-.058.037-.06.037-.06.036-.062.036-.064.036-.064.036-.066.035-.067.035-.068.035-.069.035-.07.034-.071.034-.073.033-.074.033-.15.066-.155.064-.16.063-.163.061-.168.06-.172.059-.175.057-.18.056-.183.054-.187.053-.191.051-.194.05-.198.048-.201.046-.205.045-.208.043-.211.041-.214.04-.217.038-.22.036-.223.034-.225.032-.229.031-.231.028-.233.027-.236.024-.239.023-.241.02-.242.019-.246.016-.247.015-.249.012-.251.01-.253.008-.255.005-.256.004-.258.001-.258-.001-.256-.004-.255-.005-.253-.008-.251-.01-.249-.012-.247-.015-.245-.016-.243-.019-.241-.02-.238-.023-.236-.024-.234-.027-.231-.028-.228-.031-.226-.032-.223-.034-.22-.036-.217-.038-.214-.04-.211-.041-.208-.043-.204-.045-.201-.046-.198-.048-.195-.05-.19-.051-.187-.053-.184-.054-.179-.056-.176-.057-.172-.059-.167-.06-.164-.061-.159-.063-.155-.064-.151-.066-.074-.033-.072-.033-.072-.034-.07-.034-.069-.035-.068-.035-.067-.035-.066-.035-.064-.036-.063-.036-.062-.036-.061-.036-.06-.037-.058-.037-.057-.037-.056-.038-.055-.038-.053-.038-.052-.038-.051-.039-.049-.039-.049-.039-.046-.039-.046-.04-.044-.04-.043-.04-.041-.04-.04-.041-.039-.041-.037-.041-.036-.041-.034-.041-.033-.042-.032-.042-.03-.042-.029-.042-.027-.042-.026-.043-.024-.043-.023-.043-.021-.043-.02-.043-.018-.044-.017-.043-.015-.044-.013-.044-.012-.044-.011-.045-.009-.044-.007-.045-.006-.045-.004-.045-.002-.045-.001-.045v-17l.001-.045.002-.045.004-.045.006-.045.007-.045.009-.044.011-.045.012-.044.013-.044.015-.044.017-.043.018-.044.02-.043.021-.043.023-.043.024-.043.026-.043.027-.042.029-.042.03-.042.032-.042.033-.042.034-.041.036-.041.037-.041.039-.041.04-.041.041-.04.043-.04.044-.04.046-.04.046-.039.049-.039.049-.039.051-.039.052-.038.053-.038.055-.038.056-.038.057-.037.058-.037.06-.037.061-.036.062-.036.063-.036.064-.036.066-.035.067-.035.068-.035.069-.035.07-.034.072-.034.072-.033.074-.033.151-.066.155-.064.159-.063.164-.061.167-.06.172-.059.176-.057.179-.056.184-.054.187-.053.19-.051.195-.05.198-.048.201-.046.204-.045.208-.043.211-.041.214-.04.217-.038.22-.036.223-.034.226-.032.228-.031.231-.028.234-.027.236-.024.238-.023.241-.02.243-.019.245-.016.247-.015.249-.012.251-.01.253-.008.255-.005.256-.004.258-.001.258.001zm-9.258 20.499v.01l.001.021.003.021.004.022.005.021.006.022.007.022.009.023.01.022.011.023.012.023.013.023.015.023.016.024.017.023.018.024.019.024.021.024.022.025.023.024.024.025.052.049.056.05.061.051.066.051.07.051.075.051.079.052.084.052.088.052.092.052.097.052.102.051.105.052.11.052.114.051.119.051.123.051.127.05.131.05.135.05.139.048.144.049.147.047.152.047.155.047.16.045.163.045.167.043.171.043.176.041.178.041.183.039.187.039.19.037.194.035.197.035.202.033.204.031.209.03.212.029.216.027.219.025.222.024.226.021.23.02.233.018.236.016.24.015.243.012.246.01.249.008.253.005.256.004.259.001.26-.001.257-.004.254-.005.25-.008.247-.011.244-.012.241-.014.237-.016.233-.018.231-.021.226-.021.224-.024.22-.026.216-.027.212-.028.21-.031.205-.031.202-.034.198-.034.194-.036.191-.037.187-.039.183-.04.179-.04.175-.042.172-.043.168-.044.163-.045.16-.046.155-.046.152-.047.148-.048.143-.049.139-.049.136-.05.131-.05.126-.05.123-.051.118-.052.114-.051.11-.052.106-.052.101-.052.096-.052.092-.052.088-.053.083-.051.079-.052.074-.052.07-.051.065-.051.06-.051.056-.05.051-.05.023-.024.023-.025.021-.024.02-.024.019-.024.018-.024.017-.024.015-.023.014-.024.013-.023.012-.023.01-.023.01-.022.008-.022.006-.022.006-.022.004-.022.004-.021.001-.021.001-.021v-4.127l-.077.055-.08.053-.083.054-.085.053-.087.052-.09.052-.093.051-.095.05-.097.05-.1.049-.102.049-.105.048-.106.047-.109.047-.111.046-.114.045-.115.045-.118.044-.12.043-.122.042-.124.042-.126.041-.128.04-.13.04-.132.038-.134.038-.135.037-.138.037-.139.035-.142.035-.143.034-.144.033-.147.032-.148.031-.15.03-.151.03-.153.029-.154.027-.156.027-.158.026-.159.025-.161.024-.162.023-.163.022-.165.021-.166.02-.167.019-.169.018-.169.017-.171.016-.173.015-.173.014-.175.013-.175.012-.177.011-.178.01-.179.008-.179.008-.181.006-.182.005-.182.004-.184.003-.184.002h-.37l-.184-.002-.184-.003-.182-.004-.182-.005-.181-.006-.179-.008-.179-.008-.178-.01-.176-.011-.176-.012-.175-.013-.173-.014-.172-.015-.171-.016-.17-.017-.169-.018-.167-.019-.166-.02-.165-.021-.163-.022-.162-.023-.161-.024-.159-.025-.157-.026-.156-.027-.155-.027-.153-.029-.151-.03-.15-.03-.148-.031-.146-.032-.145-.033-.143-.034-.141-.035-.14-.035-.137-.037-.136-.037-.134-.038-.132-.038-.13-.04-.128-.04-.126-.041-.124-.042-.122-.042-.12-.044-.117-.043-.116-.045-.113-.045-.112-.046-.109-.047-.106-.047-.105-.048-.102-.049-.1-.049-.097-.05-.095-.05-.093-.052-.09-.051-.087-.052-.085-.053-.083-.054-.08-.054-.077-.054v4.127zm0-5.654v.011l.001.021.003.021.004.021.005.022.006.022.007.022.009.022.01.022.011.023.012.023.013.023.015.024.016.023.017.024.018.024.019.024.021.024.022.024.023.025.024.024.052.05.056.05.061.05.066.051.07.051.075.052.079.051.084.052.088.052.092.052.097.052.102.052.105.052.11.051.114.051.119.052.123.05.127.051.131.05.135.049.139.049.144.048.147.048.152.047.155.046.16.045.163.045.167.044.171.042.176.042.178.04.183.04.187.038.19.037.194.036.197.034.202.033.204.032.209.03.212.028.216.027.219.025.222.024.226.022.23.02.233.018.236.016.24.014.243.012.246.01.249.008.253.006.256.003.259.001.26-.001.257-.003.254-.006.25-.008.247-.01.244-.012.241-.015.237-.016.233-.018.231-.02.226-.022.224-.024.22-.025.216-.027.212-.029.21-.03.205-.032.202-.033.198-.035.194-.036.191-.037.187-.039.183-.039.179-.041.175-.042.172-.043.168-.044.163-.045.16-.045.155-.047.152-.047.148-.048.143-.048.139-.05.136-.049.131-.05.126-.051.123-.051.118-.051.114-.052.11-.052.106-.052.101-.052.096-.052.092-.052.088-.052.083-.052.079-.052.074-.051.07-.052.065-.051.06-.05.056-.051.051-.049.023-.025.023-.024.021-.025.02-.024.019-.024.018-.024.017-.024.015-.023.014-.023.013-.024.012-.022.01-.023.01-.023.008-.022.006-.022.006-.022.004-.021.004-.022.001-.021.001-.021v-4.139l-.077.054-.08.054-.083.054-.085.052-.087.053-.09.051-.093.051-.095.051-.097.05-.1.049-.102.049-.105.048-.106.047-.109.047-.111.046-.114.045-.115.044-.118.044-.12.044-.122.042-.124.042-.126.041-.128.04-.13.039-.132.039-.134.038-.135.037-.138.036-.139.036-.142.035-.143.033-.144.033-.147.033-.148.031-.15.03-.151.03-.153.028-.154.028-.156.027-.158.026-.159.025-.161.024-.162.023-.163.022-.165.021-.166.02-.167.019-.169.018-.169.017-.171.016-.173.015-.173.014-.175.013-.175.012-.177.011-.178.009-.179.009-.179.007-.181.007-.182.005-.182.004-.184.003-.184.002h-.37l-.184-.002-.184-.003-.182-.004-.182-.005-.181-.007-.179-.007-.179-.009-.178-.009-.176-.011-.176-.012-.175-.013-.173-.014-.172-.015-.171-.016-.17-.017-.169-.018-.167-.019-.166-.02-.165-.021-.163-.022-.162-.023-.161-.024-.159-.025-.157-.026-.156-.027-.155-.028-.153-.028-.151-.03-.15-.03-.148-.031-.146-.033-.145-.033-.143-.033-.141-.035-.14-.036-.137-.036-.136-.037-.134-.038-.132-.039-.13-.039-.128-.04-.126-.041-.124-.042-.122-.043-.12-.043-.117-.044-.116-.044-.113-.046-.112-.046-.109-.046-.106-.047-.105-.048-.102-.049-.1-.049-.097-.05-.095-.051-.093-.051-.09-.051-.087-.053-.085-.052-.083-.054-.08-.054-.077-.054v4.139zm0-5.666v.011l.001.02.003.022.004.021.005.022.006.021.007.022.009.023.01.022.011.023.012.023.013.023.015.023.016.024.017.024.018.023.019.024.021.025.022.024.023.024.024.025.052.05.056.05.061.05.066.051.07.051.075.052.079.051.084.052.088.052.092.052.097.052.102.052.105.051.11.052.114.051.119.051.123.051.127.05.131.05.135.05.139.049.144.048.147.048.152.047.155.046.16.045.163.045.167.043.171.043.176.042.178.04.183.04.187.038.19.037.194.036.197.034.202.033.204.032.209.03.212.028.216.027.219.025.222.024.226.021.23.02.233.018.236.017.24.014.243.012.246.01.249.008.253.006.256.003.259.001.26-.001.257-.003.254-.006.25-.008.247-.01.244-.013.241-.014.237-.016.233-.018.231-.02.226-.022.224-.024.22-.025.216-.027.212-.029.21-.03.205-.032.202-.033.198-.035.194-.036.191-.037.187-.039.183-.039.179-.041.175-.042.172-.043.168-.044.163-.045.16-.045.155-.047.152-.047.148-.048.143-.049.139-.049.136-.049.131-.051.126-.05.123-.051.118-.052.114-.051.11-.052.106-.052.101-.052.096-.052.092-.052.088-.052.083-.052.079-.052.074-.052.07-.051.065-.051.06-.051.056-.05.051-.049.023-.025.023-.025.021-.024.02-.024.019-.024.018-.024.017-.024.015-.023.014-.024.013-.023.012-.023.01-.022.01-.023.008-.022.006-.022.006-.022.004-.022.004-.021.001-.021.001-.021v-4.153l-.077.054-.08.054-.083.053-.085.053-.087.053-.09.051-.093.051-.095.051-.097.05-.1.049-.102.048-.105.048-.106.048-.109.046-.111.046-.114.046-.115.044-.118.044-.12.043-.122.043-.124.042-.126.041-.128.04-.13.039-.132.039-.134.038-.135.037-.138.036-.139.036-.142.034-.143.034-.144.033-.147.032-.148.032-.15.03-.151.03-.153.028-.154.028-.156.027-.158.026-.159.024-.161.024-.162.023-.163.023-.165.021-.166.02-.167.019-.169.018-.169.017-.171.016-.173.015-.173.014-.175.013-.175.012-.177.01-.178.01-.179.009-.179.007-.181.006-.182.006-.182.004-.184.003-.184.001-.185.001-.185-.001-.184-.001-.184-.003-.182-.004-.182-.006-.181-.006-.179-.007-.179-.009-.178-.01-.176-.01-.176-.012-.175-.013-.173-.014-.172-.015-.171-.016-.17-.017-.169-.018-.167-.019-.166-.02-.165-.021-.163-.023-.162-.023-.161-.024-.159-.024-.157-.026-.156-.027-.155-.028-.153-.028-.151-.03-.15-.03-.148-.032-.146-.032-.145-.033-.143-.034-.141-.034-.14-.036-.137-.036-.136-.037-.134-.038-.132-.039-.13-.039-.128-.041-.126-.041-.124-.041-.122-.043-.12-.043-.117-.044-.116-.044-.113-.046-.112-.046-.109-.046-.106-.048-.105-.048-.102-.048-.1-.05-.097-.049-.095-.051-.093-.051-.09-.052-.087-.052-.085-.053-.083-.053-.08-.054-.077-.054v4.153zm8.74-8.179l-.257.004-.254.005-.25.008-.247.011-.244.012-.241.014-.237.016-.233.018-.231.021-.226.022-.224.023-.22.026-.216.027-.212.028-.21.031-.205.032-.202.033-.198.034-.194.036-.191.038-.187.038-.183.04-.179.041-.175.042-.172.043-.168.043-.163.045-.16.046-.155.046-.152.048-.148.048-.143.048-.139.049-.136.05-.131.05-.126.051-.123.051-.118.051-.114.052-.11.052-.106.052-.101.052-.096.052-.092.052-.088.052-.083.052-.079.052-.074.051-.07.052-.065.051-.06.05-.056.05-.051.05-.023.025-.023.024-.021.024-.02.025-.019.024-.018.024-.017.023-.015.024-.014.023-.013.023-.012.023-.01.023-.01.022-.008.022-.006.023-.006.021-.004.022-.004.021-.001.021-.001.021.001.021.001.021.004.021.004.022.006.021.006.023.008.022.01.022.01.023.012.023.013.023.014.023.015.024.017.023.018.024.019.024.02.025.021.024.023.024.023.025.051.05.056.05.06.05.065.051.07.052.074.051.079.052.083.052.088.052.092.052.096.052.101.052.106.052.11.052.114.052.118.051.123.051.126.051.131.05.136.05.139.049.143.048.148.048.152.048.155.046.16.046.163.045.168.043.172.043.175.042.179.041.183.04.187.038.191.038.194.036.198.034.202.033.205.032.21.031.212.028.216.027.22.026.224.023.226.022.231.021.233.018.237.016.241.014.244.012.247.011.25.008.254.005.257.004.26.001.26-.001.257-.004.254-.005.25-.008.247-.011.244-.012.241-.014.237-.016.233-.018.231-.021.226-.022.224-.023.22-.026.216-.027.212-.028.21-.031.205-.032.202-.033.198-.034.194-.036.191-.038.187-.038.183-.04.179-.041.175-.042.172-.043.168-.043.163-.045.16-.046.155-.046.152-.048.148-.048.143-.048.139-.049.136-.05.131-.05.126-.051.123-.051.118-.051.114-.052.11-.052.106-.052.101-.052.096-.052.092-.052.088-.052.083-.052.079-.052.074-.051.07-.052.065-.051.06-.05.056-.05.051-.05.023-.025.023-.024.021-.024.02-.025.019-.024.018-.024.017-.023.015-.024.014-.023.013-.023.012-.023.01-.023.01-.022.008-.022.006-.023.006-.021.004-.022.004-.021.001-.021.001-.021-.001-.021-.001-.021-.004-.021-.004-.022-.006-.021-.006-.023-.008-.022-.01-.022-.01-.023-.012-.023-.013-.023-.014-.023-.015-.024-.017-.023-.018-.024-.019-.024-.02-.025-.021-.024-.023-.024-.023-.025-.051-.05-.056-.05-.06-.05-.065-.051-.07-.052-.074-.051-.079-.052-.083-.052-.088-.052-.092-.052-.096-.052-.101-.052-.106-.052-.11-.052-.114-.052-.118-.051-.123-.051-.126-.051-.131-.05-.136-.05-.139-.049-.143-.048-.148-.048-.152-.048-.155-.046-.16-.046-.163-.045-.168-.043-.172-.043-.175-.042-.179-.041-.183-.04-.187-.038-.191-.038-.194-.036-.198-.034-.202-.033-.205-.032-.21-.031-.212-.028-.216-.027-.22-.026-.224-.023-.226-.022-.231-.021-.233-.018-.237-.016-.241-.014-.244-.012-.247-.011-.25-.008-.254-.005-.257-.004-.26-.001-.26.001z" transform="scale(.5)"/></symbol></defs><defs><symbol height="24" width="24" id="clock"><path d="M12 2c5.514 0 10 4.486 10 10s-4.486 10-10 10-10-4.486-10-10 4.486-10 10-10zm0-2c-6.627 0-12 5.373-12 12s5.373 12 12 12 12-5.373 12-12-5.373-12-12-12zm5.848 12.459c.202.038.202.333.001.372-1.907.361-6.045 1.111-6.547 1.111-.719 0-1.301-.582-1.301-1.301 0-.512.77-5.447 1.125-7.445.034-.192.312-.181.343.014l.985 6.238 5.394 1.011z" transform="scale(.5)"/></symbol></defs><defs><marker orient="auto" markerHeight="12" markerWidth="12" markerUnits="userSpaceOnUse" refY="5" refX="7.9" id="arrowhead"><path d="M 0 0 L 10 5 L 0 10 z"/></marker></defs><defs><marker refY="4.5" refX="4" orient="auto" markerHeight="8" markerWidth="15" id="crosshead"><path style="stroke-dasharray: 0, 0;" d="M 1,2 L 6,7 M 6,2 L 1,7" stroke-width="1pt" stroke="#000000" fill="none"/></marker></defs><defs><marker orient="auto" markerHeight="28" markerWidth="20" refY="7" refX="15.5" id="filled-head"><path d="M 18,7 L9,13 L14,7 L9,1 Z"/></marker></defs><defs><marker orient="auto" markerHeight="40" markerWidth="60" refY="15" refX="15" id="sequencenumber"><circle r="6" cy="15" cx="15"/></marker></defs><g><rect class="note" ry="0" rx="0" height="77" width="168" stroke="#666" fill="#EDF2AE" y="205" x="785"/><text style="font-size: 16px; font-weight: 400;" dy="1em" class="noteText" alignment-baseline="middle" dominant-baseline="middle" text-anchor="middle" y="210" x="869"><tspan x="869">1. 禁用按钮</tspan></text><text style="font-size: 16px; font-weight: 400;" dy="1em" class="noteText" alignment-baseline="middle" dominant-baseline="middle" text-anchor="middle" y="229" x="869"><tspan x="869">2. 更新UI为“连接中”</tspan></text><text style="font-size: 16px; font-weight: 400;" dy="1em" class="noteText" alignment-baseline="middle" dominant-baseline="middle" text-anchor="middle" y="248" x="869"><tspan x="869">3. 启动后台线程</tspan></text></g><g><rect class="note" ry="0" rx="0" height="39" width="1068" stroke="#666" fill="#EDF2AE" y="492" x="535"/><text style="font-size: 16px; font-weight: 400;" dy="1em" class="noteText" alignment-baseline="middle" dominant-baseline="middle" text-anchor="middle" y="497" x="1069"><tspan x="1069">WebSocket连接建立</tspan></text></g><g><rect class="note" ry="0" rx="0" height="39" width="150" stroke="#666" fill="#EDF2AE" y="633" x="1603"/><text style="font-size: 16px; font-weight: 400;" dy="1em" class="noteText" alignment-baseline="middle" dominant-baseline="middle" text-anchor="middle" y="638" x="1678"><tspan x="1678">连接测试成功</tspan></text></g><g><rect class="note" ry="0" rx="0" height="58" width="164" stroke="#666" fill="#EDF2AE" y="858" x="785"/><text style="font-size: 16px; font-weight: 400;" dy="1em" class="noteText" alignment-baseline="middle" dominant-baseline="middle" text-anchor="middle" y="863" x="867"><tspan x="867">1. 更新UI为“已连接”</tspan></text><text style="font-size: 16px; font-weight: 400;" dy="1em" class="noteText" alignment-baseline="middle" dominant-baseline="middle" text-anchor="middle" y="882" x="867"><tspan x="867">2. 恢复按钮</tspan></text></g><text style="font-size: 16px; font-weight: 400;" dy="1em" class="messageText" alignment-baseline="middle" dominant-baseline="middle" text-anchor="middle" y="80" x="416">点击 "连接服务器" 按钮</text><line style="fill: none;" marker-end="url(#arrowhead)" stroke="none" stroke-width="2" class="messageLine0" y2="119" x2="756" y1="119" x1="76"/><text style="font-size: 16px; font-weight: 400;" dy="1em" class="messageText" alignment-baseline="middle" dominant-baseline="middle" text-anchor="middle" y="134" x="761">connect_server()</text><path style="fill: none;" marker-end="url(#arrowhead)" stroke="none" stroke-width="2" class="messageLine0" d="M 761,165 C 821,155 821,195 761,185"/><text style="font-size: 16px; font-weight: 400;" dy="1em" class="messageText" alignment-baseline="middle" dominant-baseline="middle" text-anchor="middle" y="297" x="968">执行 _test_connection()</text><line style="fill: none;" marker-end="url(#arrowhead)" stroke="none" stroke-width="2" class="messageLine0" y2="328" x2="1174" y1="328" x1="761"/><text style="font-size: 16px; font-weight: 400;" dy="1em" class="messageText" alignment-baseline="middle" dominant-baseline="middle" text-anchor="middle" y="343" x="1377">asyncio.run(_async_test_connection())</text><line style="fill: none;" marker-end="url(#arrowhead)" stroke="none" stroke-width="2" class="messageLine0" y2="374" x2="1574" y1="374" x1="1179"/><text style="font-size: 16px; font-weight: 400;" dy="1em" class="messageText" alignment-baseline="middle" dominant-baseline="middle" text-anchor="middle" y="389" x="1071">发送 HTTP Upgrade 请求 (WebSocket握手)</text><line style="fill: none;" marker-end="url(#arrowhead)" stroke="none" stroke-width="2" class="messageLine0" y2="428" x2="564" y1="428" x1="1577"/><text style="font-size: 16px; font-weight: 400;" dy="1em" class="messageText" alignment-baseline="middle" dominant-baseline="middle" text-anchor="middle" y="443" x="1068">返回 HTTP 101 (握手成功)</text><line style="stroke-dasharray: 3, 3; fill: none;" marker-end="url(#arrowhead)" stroke="none" stroke-width="2" class="messageLine1" y2="482" x2="1574" y1="482" x1="561"/><text style="font-size: 16px; font-weight: 400;" dy="1em" class="messageText" alignment-baseline="middle" dominant-baseline="middle" text-anchor="middle" y="546" x="1071">发送测试JSON: {"mode":"offline",...}</text><line style="fill: none;" marker-end="url(#arrowhead)" stroke="none" stroke-width="2" class="messageLine0" y2="577" x2="564" y1="577" x1="1577"/><text style="font-size: 16px; font-weight: 400;" dy="1em" class="messageText" alignment-baseline="middle" dominant-baseline="middle" text-anchor="middle" y="592" x="1068">(可选) 服务器响应</text><line style="stroke-dasharray: 3, 3; fill: none;" marker-end="url(#arrowhead)" stroke="none" stroke-width="2" class="messageLine1" y2="623" x2="1574" y1="623" x1="561"/><text style="font-size: 16px; font-weight: 400;" dy="1em" class="messageText" alignment-baseline="middle" dominant-baseline="middle" text-anchor="middle" y="687" x="1380">_async_test_connection() 执行完毕</text><line style="stroke-dasharray: 3, 3; fill: none;" marker-end="url(#arrowhead)" stroke="none" stroke-width="2" class="messageLine1" y2="718" x2="1182" y1="718" x1="1577"/><text style="font-size: 16px; font-weight: 400;" dy="1em" class="messageText" alignment-baseline="middle" dominant-baseline="middle" text-anchor="middle" y="733" x="971">线程结束</text><line style="stroke-dasharray: 3, 3; fill: none;" marker-end="url(#arrowhead)" stroke="none" stroke-width="2" class="messageLine1" y2="764" x2="764" y1="764" x1="1177"/><text style="font-size: 16px; font-weight: 400;" dy="1em" class="messageText" alignment-baseline="middle" dominant-baseline="middle" text-anchor="middle" y="779" x="761">_update_connection_indicator(True)</text><path style="fill: none;" marker-end="url(#arrowhead)" stroke="none" stroke-width="2" class="messageLine0" d="M 761,818 C 821,808 821,848 761,838"/></svg>

这个设计非常好，它将“快速的连通性测试”和“耗时的识别任务”分离开来，使得用户可以先确认网络和服务器状态，再提交真正的任务，提供了很好的用户体验。