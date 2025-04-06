#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FunASR Python客户端
支持离线文件转写和实时语音识别两种模式
"""

import json
import asyncio
import websockets
import ssl
import wave
import os
import argparse
from typing import Dict, List, Union, Optional

class FunasrClient:
    """FunASR WebSocket客户端
    
    支持离线文件转写和实时语音识别两种模式，通过WebSocket协议与FunASR服务进行通信。
    """
    
    def __init__(self, host="127.0.0.1", port=10095, is_ssl=True, mode="offline"):
        """初始化客户端
        
        Args:
            host: 服务器主机地址
            port: 服务器端口
            is_ssl: 是否使用SSL连接
            mode: 识别模式，可选值为"offline"、"online"、"2pass"
        """
        self.host = host
        self.port = port
        self.is_ssl = is_ssl
        self.mode = mode
        self.websocket = None
        
    async def connect(self):
        """建立WebSocket连接"""
        if self.is_ssl:
            ssl_context = ssl.SSLContext()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            uri = f"wss://{self.host}:{self.port}"
        else:
            uri = f"ws://{self.host}:{self.port}"
            ssl_context = None
            
        self.websocket = await websockets.connect(
            uri, subprotocols=["binary"], ping_interval=None, ssl=ssl_context
        )
        return self
        
    async def send_init_message(self, wav_name="default", wav_format="pcm", 
                               chunk_size=None, chunk_interval=10, 
                               hotwords=None, use_itn=True, audio_fs=16000):
        """发送初始化消息
        
        Args:
            wav_name: 音频文件名
            wav_format: 音频格式，如pcm、wav、mp3等
            chunk_size: 分块大小，适用于online和2pass模式
            chunk_interval: 分块间隔
            hotwords: 热词文件路径或热词字典
            use_itn: 是否使用ITN
            audio_fs: 音频采样率
        """
        hotword_msg = ""
        if hotwords:
            if isinstance(hotwords, str) and os.path.exists(hotwords):
                fst_dict = {}
                with open(hotwords, 'r') as f:
                    for line in f:
                        words = line.strip().split(" ")
                        if len(words) >= 2:
                            try:
                                fst_dict[" ".join(words[:-1])] = int(words[-1])
                            except ValueError:
                                print("热词格式错误")
                hotword_msg = json.dumps(fst_dict)
            else:
                hotword_msg = json.dumps(hotwords)
                
        message = {
            "mode": self.mode,
            "wav_name": wav_name,
            "wav_format": wav_format,
            "is_speaking": True,
            "itn": use_itn,
            "audio_fs": audio_fs
        }
        
        if self.mode in ["online", "2pass"] and chunk_size:
            message["chunk_size"] = chunk_size
            message["chunk_interval"] = chunk_interval
            
        if hotword_msg:
            message["hotwords"] = hotword_msg
            
        await self.websocket.send(json.dumps(message))
        
    async def send_audio_file(self, audio_path, chunk_size=None, chunk_interval=10, 
                             hotwords=None, use_itn=True):
        """发送音频文件
        
        Args:
            audio_path: 音频文件路径
            chunk_size: 分块大小，适用于online和2pass模式
            chunk_interval: 分块间隔
            hotwords: 热词文件路径或热词字典
            use_itn: 是否使用ITN
        """
        wav_format = "pcm"
        sample_rate = 16000
        
        # 处理不同格式的音频文件
        if audio_path.endswith(".pcm"):
            with open(audio_path, "rb") as f:
                audio_bytes = f.read()
        elif audio_path.endswith(".wav"):
            with wave.open(audio_path, "rb") as wav_file:
                sample_rate = wav_file.getframerate()
                frames = wav_file.readframes(wav_file.getnframes())
                audio_bytes = bytes(frames)
        else:
            wav_format = "others"
            with open(audio_path, "rb") as f:
                audio_bytes = f.read()
                
        # 发送初始化消息
        await self.send_init_message(
            wav_name=os.path.basename(audio_path),
            wav_format=wav_format,
            chunk_size=chunk_size,
            chunk_interval=chunk_interval,
            hotwords=hotwords,
            use_itn=use_itn,
            audio_fs=sample_rate
        )
        
        # 分块发送音频数据
        if self.mode in ["online", "2pass"] and chunk_size:
            stride = int(60 * chunk_size[1] / chunk_interval / 1000 * sample_rate * 2)
            chunk_num = (len(audio_bytes) - 1) // stride + 1
            
            for i in range(chunk_num):
                beg = i * stride
                data = audio_bytes[beg:beg + stride]
                await self.websocket.send(data)
                
                if i == chunk_num - 1:
                    await self.send_end_message()
                
                sleep_duration = 0.001 if self.mode == "offline" else 60 * chunk_size[1] / chunk_interval / 1000
                await asyncio.sleep(sleep_duration)
        else:
            # 离线模式直接发送整个音频
            await self.websocket.send(audio_bytes)
            await self.send_end_message()
            
    async def send_audio_bytes(self, audio_bytes, sample_rate=16000, is_final_chunk=False):
        """发送音频数据
        
        Args:
            audio_bytes: 音频数据字节
            sample_rate: 音频采样率
            is_final_chunk: 是否为最后一个音频块
        """
        await self.websocket.send(audio_bytes)
        
        if is_final_chunk:
            await self.send_end_message()
            
    async def send_end_message(self):
        """发送结束标志"""
        await self.websocket.send(json.dumps({"is_speaking": False}))
        
    async def receive_results(self):
        """接收识别结果"""
        results = []
        try:
            while True:
                message = await self.websocket.recv()
                result = json.loads(message)
                results.append(result)
                
                # 如果是离线模式且已完成，则退出
                if self.mode == "offline" and result.get("is_final", False):
                    break
        except websockets.exceptions.ConnectionClosed:
            pass
            
        return results
        
    async def receive_one_result(self):
        """接收单个识别结果"""
        try:
            message = await self.websocket.recv()
            return json.loads(message)
        except websockets.exceptions.ConnectionClosed:
            return None
        
    async def close(self):
        """关闭连接"""
        if self.websocket:
            await self.websocket.close()


class FunasrMicrophoneClient:
    """FunASR麦克风客户端
    
    用于实时语音识别，支持从麦克风捕获音频并发送到FunASR服务。
    """
    
    def __init__(self, host="127.0.0.1", port=10095, is_ssl=True, mode="2pass",
                chunk_size=None, chunk_interval=10, hotwords=None, use_itn=True):
        """初始化麦克风客户端
        
        Args:
            host: 服务器主机地址
            port: 服务器端口
            is_ssl: 是否使用SSL连接
            mode: 识别模式，建议使用"2pass"
            chunk_size: 分块大小，如[5,10,5]
            chunk_interval: 分块间隔
            hotwords: 热词文件路径或热词字典
            use_itn: 是否使用ITN
        """
        self.client = FunasrClient(host, port, is_ssl, mode)
        self.chunk_size = chunk_size or [5, 10, 5]
        self.chunk_interval = chunk_interval
        self.hotwords = hotwords
        self.use_itn = use_itn
        
        # 麦克风参数
        self.FORMAT = None  # 将在start_recording中初始化
        self.CHANNELS = 1
        self.RATE = 16000
        self.CHUNK = int(self.RATE / 1000 * 60 * self.chunk_size[1] / self.chunk_interval)
        
        self.stream = None
        self.p = None
        self.is_running = False
    
    async def start(self):
        """启动麦克风客户端"""
        await self.client.connect()
        
        # 热词处理
        hotword_msg = ""
        if self.hotwords:
            if isinstance(self.hotwords, str) and os.path.exists(self.hotwords):
                fst_dict = {}
                with open(self.hotwords, 'r') as f:
                    for line in f:
                        words = line.strip().split(" ")
                        if len(words) >= 2:
                            try:
                                fst_dict[" ".join(words[:-1])] = int(words[-1])
                            except ValueError:
                                print("热词格式错误")
                hotword_msg = json.dumps(fst_dict)
            else:
                hotword_msg = json.dumps(self.hotwords)
        
        # 发送初始化消息
        message = {
            "mode": self.client.mode,
            "chunk_size": self.chunk_size,
            "chunk_interval": self.chunk_interval,
            "wav_name": "microphone",
            "is_speaking": True,
            "itn": self.use_itn
        }
        
        if hotword_msg:
            message["hotwords"] = hotword_msg
            
        await self.client.websocket.send(json.dumps(message))
        
        return self
    
    def start_recording(self):
        """开始录音"""
        try:
            import pyaudio
            self.FORMAT = pyaudio.paInt16
            self.p = pyaudio.PyAudio()
            self.stream = self.p.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )
            self.is_running = True
            return True
        except ImportError:
            print("未安装pyaudio库，请先安装: pip install pyaudio")
            return False
        except Exception as e:
            print(f"启动麦克风失败: {e}")
            return False
    
    async def process_microphone(self):
        """处理麦克风输入并发送到服务器"""
        if not self.start_recording():
            return
        
        try:
            while self.is_running:
                data = self.stream.read(self.CHUNK)
                await self.client.websocket.send(data)
                await asyncio.sleep(0.005)  # 防止发送过快
        finally:
            self.stop_recording()
    
    def stop_recording(self):
        """停止录音"""
        self.is_running = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.p:
            self.p.terminate()
    
    async def stop(self):
        """停止麦克风客户端"""
        self.stop_recording()
        await self.client.send_end_message()
        await self.client.close()


async def process_audio_file(args):
    """处理音频文件"""
    # 处理参数
    is_ssl = args.ssl == 1
    use_itn = args.use_itn == 1
    chunk_size = [int(x) for x in args.chunk_size.split(',')] if args.mode in ['online', '2pass'] else None
    
    # 创建客户端并连接
    client = FunasrClient(host=args.host, port=args.port, is_ssl=is_ssl, mode=args.mode)
    
    try:
        await client.connect()
        
        # 处理音频文件
        if args.audio_in.endswith('.scp'):
            # 处理wav.scp文件
            with open(args.audio_in, 'r') as f:
                wav_lines = f.readlines()
                
            for line in wav_lines:
                line = line.strip()
                if not line:
                    continue
                    
                parts = line.split()
                if len(parts) >= 2:
                    wav_name = parts[0]
                    wav_path = parts[1]
                else:
                    wav_name = os.path.basename(line)
                    wav_path = line
                
                # 发送音频文件
                await client.send_audio_file(
                    audio_path=wav_path,
                    chunk_size=chunk_size,
                    chunk_interval=args.chunk_interval,
                    hotwords=args.hotword,
                    use_itn=use_itn
                )
                
                # 接收并处理结果
                results = await client.receive_results()
                process_results(results, args.output_dir, wav_name)
        else:
            # 处理单个音频文件
            await client.send_audio_file(
                audio_path=args.audio_in,
                chunk_size=chunk_size,
                chunk_interval=args.chunk_interval,
                hotwords=args.hotword,
                use_itn=use_itn
            )
            
            # 接收并处理结果
            results = await client.receive_results()
            process_results(results, args.output_dir)
            
    finally:
        await client.close()


def process_results(results, output_dir=None, wav_name=None):
    """处理识别结果"""
    for result in results:
        mode = result.get('mode', '')
        text = result.get('text', '')
        name = result.get('wav_name', wav_name or 'unknown')
        
        print(f"模式: {mode}, 文件: {name}")
        print(f"识别结果: {text}")
        
        if 'timestamp' in result:
            print(f"时间戳: {result.get('timestamp', '')}")
            
    # 保存结果
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"{wav_name or 'results'}.txt")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for result in results:
                name = result.get('wav_name', wav_name or 'unknown')
                text = result.get('text', '')
                
                if 'timestamp' in result:
                    f.write(f"{name}\t{text}\t{result.get('timestamp', '')}\n")
                else:
                    f.write(f"{name}\t{text}\n")
                    
        print(f"结果已保存到: {output_file}")


async def process_microphone(args):
    """处理麦克风输入"""
    # 处理参数
    is_ssl = args.ssl == 1
    use_itn = args.use_itn == 1
    chunk_size = [int(x) for x in args.chunk_size.split(',')]
    
    # 创建麦克风客户端
    mic_client = FunasrMicrophoneClient(
        host=args.host,
        port=args.port,
        is_ssl=is_ssl,
        mode=args.mode,
        chunk_size=chunk_size,
        chunk_interval=args.chunk_interval,
        hotwords=args.hotword,
        use_itn=use_itn
    )
    
    try:
        # 启动客户端
        await mic_client.start()
        
        # 创建任务
        mic_task = asyncio.create_task(mic_client.process_microphone())
        
        # 接收结果任务
        text_print = ""
        text_print_2pass_online = ""
        text_print_2pass_offline = ""
        
        try:
            while True:
                result = await mic_client.client.receive_one_result()
                if not result:
                    break
                    
                mode = result.get('mode', '')
                text = result.get('text', '')
                
                if mode == "online":
                    text_print = text
                    os.system('clear')
                    print(f"\r{text_print}")
                elif mode == "offline":
                    text_print = text
                    os.system('clear')
                    print(f"\r{text_print}")
                elif mode == "2pass-online":
                    text_print_2pass_online = text
                    text_print = text_print_2pass_offline + text_print_2pass_online
                    os.system('clear')
                    print(f"\r{text_print}")
                elif mode == "2pass-offline":
                    text_print_2pass_online = ""
                    text_print_2pass_offline += text
                    text_print = text_print_2pass_offline
                    os.system('clear')
                    print(f"\r{text_print}")
                    
        except KeyboardInterrupt:
            print("\n停止录音...")
            
    finally:
        # 停止客户端
        await mic_client.stop()


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='FunASR Python Client')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='服务器地址')
    parser.add_argument('--port', type=int, default=10095, help='服务器端口')
    parser.add_argument('--mode', type=str, default='offline', choices=['offline', 'online', '2pass'], 
                       help='识别模式: offline(离线), online(在线), 2pass(两遍识别)')
    parser.add_argument('--audio_in', type=str, help='音频文件路径，不提供则使用麦克风输入')
    parser.add_argument('--ssl', type=int, default=1, help='是否使用SSL: 1(开启), 0(关闭)')
    parser.add_argument('--hotword', type=str, default='', help='热词文件路径')
    parser.add_argument('--use_itn', type=int, default=1, help='是否使用ITN: 1(开启), 0(关闭)')
    parser.add_argument('--chunk_size', type=str, default='5,10,5', 
                       help='分块大小，适用于online和2pass模式，格式如: 5,10,5')
    parser.add_argument('--chunk_interval', type=int, default=10, 
                       help='分块间隔，适用于online和2pass模式')
    parser.add_argument('--output_dir', type=str, default=None, help='输出目录')
    parser.add_argument('--thread_num', type=int, default=1, help='并发线程数')
    
    args = parser.parse_args()
    
    # 处理音频文件或麦克风输入
    if args.audio_in:
        await process_audio_file(args)
    else:
        await process_microphone(args)


if __name__ == '__main__':
    asyncio.run(main()) 