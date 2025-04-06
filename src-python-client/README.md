# FunASR Python客户端

FunASR是一套功能强大的语音识别系统，本客户端提供了使用Python语言与FunASR服务端进行通信的方法，支持离线文件转写和实时语音识别两种模式。

## 功能特点

- 支持离线文件转写（offline模式）
- 支持实时语音识别（online模式和2pass模式）
- 支持热词功能
- 支持时间戳标注
- 支持多种音频格式（wav, pcm, mp3等）
- 支持麦克风实时输入
- 支持多线程并发处理

## 环境要求

- Python 3.7+
- websockets库
- pyaudio库（仅麦克风输入模式需要）

## 安装

```bash
# 安装依赖
pip install -r requirements.txt

# 如果需要麦克风输入功能，还需要安装pyaudio
pip install pyaudio
```

## 使用方法

### 1. 简单调用接口（命令行）

#### 离线文件转写

```bash
# 单个音频文件转写
python funasr_wss_client.py --host "127.0.0.1" --port 10095 --mode offline --audio_in "音频文件路径.wav" --output_dir "./results"

# 批量音频文件转写
python funasr_wss_client.py --host "127.0.0.1" --port 10095 --mode offline --audio_in "wav.scp" --output_dir "./results" --thread_num 4
```

#### 实时语音识别（2pass模式）

```bash
# 从麦克风输入
python funasr_wss_client.py --host "127.0.0.1" --port 10095 --mode 2pass

# 从音频文件模拟实时输入
python funasr_wss_client.py --host "127.0.0.1" --port 10095 --mode 2pass --audio_in "音频文件路径.wav"
```

### 2. 集成到自己的项目中

```python
import asyncio
from funasr_client import FunasrClient

async def main():
    # 创建客户端对象
    client = FunasrClient(host="127.0.0.1", port=10095, is_ssl=True, mode="offline")
    
    # 连接到服务端
    await client.connect()
    
    try:
        # 发送音频文件
        await client.send_audio_file(
            audio_path="音频文件路径.wav",
            hotwords="热词文件路径.txt",
            use_itn=True
        )
        
        # 接收识别结果
        results = await client.receive_results()
        
        # 处理结果
        for result in results:
            text = result.get("text", "")
            print(f"识别结果: {text}")
            if "timestamp" in result:
                print(f"时间戳: {result.get('timestamp', '')}")
                
    finally:
        # 关闭连接
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## 参数说明

### 命令行参数

| 参数 | 说明 | 默认值 |
| --- | --- | --- |
| --host | 服务器地址 | 127.0.0.1 |
| --port | 服务器端口 | 10095 |
| --mode | 识别模式: offline(离线), online(在线), 2pass(两遍识别) | offline |
| --chunk_size | 分块大小，格式如"5,10,5" | "5,10,5" |
| --chunk_interval | 分块间隔 | 10 |
| --hotword | 热词文件路径 | "" |
| --audio_in | 音频文件路径，不提供则使用麦克风输入 | None |
| --audio_fs | 音频采样率 | 16000 |
| --thread_num | 并发线程数 | 1 |
| --output_dir | 输出目录 | None |
| --ssl | 是否使用SSL: 1(开启), 0(关闭) | 1 |
| --use_itn | 是否使用ITN: 1(开启), 0(关闭) | 1 |

### 热词文件格式

热词文件每行一个热词，格式为：`热词 权重`

例如：
```
阿里巴巴 20
达摩院 15
FunASR 30
```

## API参考

### FunasrClient类

提供FunASR WebSocket客户端基本功能。

#### 主要方法

- `__init__(host, port, is_ssl, mode)`: 初始化客户端
- `connect()`: 建立WebSocket连接
- `send_init_message(...)`: 发送初始化消息
- `send_audio_file(audio_path, ...)`: 发送音频文件
- `send_audio_bytes(audio_bytes, ...)`: 发送音频数据
- `send_end_message()`: 发送结束标志
- `receive_results()`: 接收识别结果
- `receive_one_result()`: 接收单个识别结果
- `close()`: 关闭连接

### FunasrMicrophoneClient类

提供从麦克风捕获音频并发送到FunASR服务的功能。

#### 主要方法

- `__init__(host, port, ...)`: 初始化麦克风客户端
- `start()`: 启动麦克风客户端
- `start_recording()`: 开始录音
- `process_microphone()`: 处理麦克风输入并发送到服务器
- `stop_recording()`: 停止录音
- `stop()`: 停止麦克风客户端

## 常见问题

1. **Q: 连接服务器失败怎么办？**  
   A: 检查服务器地址和端口是否正确，确认服务器是否已启动，以及网络连接是否正常。

2. **Q: 如何使用热词功能？**  
   A: 创建一个热词文件，每行一个热词，格式为"热词 权重"，然后通过--hotword参数指定该文件路径。

3. **Q: 如何获取带时间戳的识别结果？**  
   A: 服务端需要部署带时间戳功能的模型，结果中会自动包含时间戳信息。

4. **Q: SSL连接问题如何解决？**  
   A: 如果遇到SSL证书问题，可以尝试使用--ssl 0参数关闭SSL校验。

## 版权和许可

本项目基于MIT许可证开源。 