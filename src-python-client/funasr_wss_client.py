#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FunASR WebSocket客户端示例
支持离线文件转写和实时语音识别
"""

import os
import time
import asyncio
import websockets
import ssl
import json
import argparse
import wave
import traceback
from multiprocessing import Process

def parse_args():
    parser = argparse.ArgumentParser(description='FunASR WebSocket客户端')
    parser.add_argument("--host", type=str, default="127.0.0.1", help="服务器地址")
    parser.add_argument("--port", type=int, default=10095, help="服务器端口")
    parser.add_argument("--mode", type=str, default="offline", choices=["offline", "online", "2pass"], 
                        help="识别模式: offline(离线), online(在线), 2pass(两遍识别)")
    parser.add_argument("--chunk_size", type=str, default="5,10,5", help="分块大小")
    parser.add_argument("--chunk_interval", type=int, default=10, help="分块间隔")
    parser.add_argument("--hotword", type=str, default="", help="热词文件路径")
    parser.add_argument("--audio_in", type=str, default=None, help="音频文件路径")
    parser.add_argument("--audio_fs", type=int, default=16000, help="音频采样率")
    parser.add_argument("--thread_num", type=int, default=1, help="并发线程数")
    parser.add_argument("--output_dir", type=str, default=None, help="输出目录")
    parser.add_argument("--ssl", type=int, default=1, help="是否使用SSL: 1(开启), 0(关闭)")
    parser.add_argument("--use_itn", type=int, default=1, help="是否使用ITN: 1(开启), 0(关闭)")
    parser.add_argument("--words_max_print", type=int, default=10000, help="最大打印字数")
    
    args = parser.parse_args()
    args.chunk_size = [int(x) for x in args.chunk_size.split(",")]
    return args

async def send_audio_from_microphone(websocket, args):
    """从麦克风捕获音频并发送"""
    try:
        import pyaudio
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        chunk_size = 60 * args.chunk_size[1] / args.chunk_interval
        CHUNK = int(RATE / 1000 * chunk_size)
        
        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT, 
                        channels=CHANNELS, 
                        rate=RATE, 
                        input=True, 
                        frames_per_buffer=CHUNK)
        
        # 处理热词
        hotword_msg = ""
        if args.hotword.strip():
            fst_dict = {}
            with open(args.hotword, 'r') as f:
                for line in f:
                    words = line.strip().split(" ")
                    if len(words) >= 2:
                        try:
                            fst_dict[" ".join(words[:-1])] = int(words[-1])
                        except ValueError:
                            print("热词格式错误")
            hotword_msg = json.dumps(fst_dict)
        
        use_itn = True if args.use_itn == 1 else False
        
        # 发送初始化消息
        message = json.dumps({
            "mode": args.mode, 
            "chunk_size": args.chunk_size, 
            "chunk_interval": args.chunk_interval,
            "wav_name": "microphone", 
            "is_speaking": True, 
            "hotwords": hotword_msg, 
            "itn": use_itn
        })
        
        await websocket.send(message)
        
        # 从麦克风捕获音频并发送
        print("正在录音，按Ctrl+C停止...")
        try:
            while True:
                data = stream.read(CHUNK)
                await websocket.send(data)
                await asyncio.sleep(0.005)
        except KeyboardInterrupt:
            print("\n停止录音")
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()
            
        # 发送结束标志
        await websocket.send(json.dumps({"is_speaking": False}))
    
    except ImportError:
        print("未安装pyaudio库，请先安装: pip install pyaudio")
    except Exception as e:
        print(f"麦克风录音异常: {e}")
        traceback.print_exc()

async def send_audio_from_file(websocket, args):
    """从文件读取音频并发送"""
    try:
        # 处理热词
        hotword_msg = ""
        if args.hotword.strip():
            fst_dict = {}
            with open(args.hotword, 'r') as f:
                for line in f:
                    words = line.strip().split(" ")
                    if len(words) >= 2:
                        try:
                            fst_dict[" ".join(words[:-1])] = int(words[-1])
                        except ValueError:
                            print("热词格式错误")
            hotword_msg = json.dumps(fst_dict)
        
        use_itn = True if args.use_itn == 1 else False
        
        # 处理音频文件或文件列表
        if args.audio_in.endswith(".scp"):
            with open(args.audio_in, 'r') as f:
                wavs = f.readlines()
        else:
            wavs = [args.audio_in]
            
        for wav in wavs:
            wav = wav.strip()
            if not wav:
                continue
                
            # 解析wav.scp格式或直接使用文件路径
            wav_splits = wav.strip().split()
            wav_name = wav_splits[0] if len(wav_splits) > 1 else os.path.basename(wav)
            wav_path = wav_splits[1] if len(wav_splits) > 1 else wav_splits[0]
            
            # 读取音频数据
            sample_rate = args.audio_fs
            if wav_path.endswith(".pcm"):
                wav_format = "pcm"
                with open(wav_path, "rb") as f:
                    audio_bytes = f.read()
            elif wav_path.endswith(".wav"):
                wav_format = "wav"
                with wave.open(wav_path, "rb") as wav_file:
                    sample_rate = wav_file.getframerate()
                    frames = wav_file.readframes(wav_file.getnframes())
                    audio_bytes = bytes(frames)
            else:
                wav_format = "others"
                with open(wav_path, "rb") as f:
                    audio_bytes = f.read()
            
            # 发送初始化消息
            message = json.dumps({
                "mode": args.mode, 
                "chunk_size": args.chunk_size, 
                "chunk_interval": args.chunk_interval,
                "wav_name": wav_name, 
                "wav_format": wav_format,
                "audio_fs": sample_rate,
                "is_speaking": True, 
                "hotwords": hotword_msg, 
                "itn": use_itn
            })
            
            await websocket.send(message)
            
            # 根据模式发送音频数据
            if args.mode in ["online", "2pass"]:
                # 分块发送
                stride = int(60 * args.chunk_size[1] / args.chunk_interval / 1000 * sample_rate * 2)
                chunk_num = (len(audio_bytes) - 1) // stride + 1
                
                for i in range(chunk_num):
                    beg = i * stride
                    data = audio_bytes[beg:beg + stride]
                    await websocket.send(data)
                    
                    if i == chunk_num - 1:
                        # 发送结束标志
                        await websocket.send(json.dumps({"is_speaking": False}))
                    
                    # 控制发送速度
                    sleep_duration = 0.001 if args.mode == "offline" else 60 * args.chunk_size[1] / args.chunk_interval / 1000
                    await asyncio.sleep(sleep_duration)
            else:
                # 离线模式直接发送整个音频
                await websocket.send(audio_bytes)
                # 发送结束标志
                await websocket.send(json.dumps({"is_speaking": False}))
                
            # 离线模式需要等待结果
            if args.mode == "offline":
                # 等待获取完整的识别结果
                while True:
                    try:
                        message = await websocket.recv()
                        result = json.loads(message)
                        if result.get("is_final", False):
                            break
                    except Exception:
                        break
    
    except Exception as e:
        print(f"发送音频文件异常: {e}")
        traceback.print_exc()

async def receive_results(websocket, args, process_id=0):
    """接收识别结果"""
    text_print = ""
    text_print_2pass_online = ""
    text_print_2pass_offline = ""
    
    # 如果指定了输出目录，创建输出文件
    ibest_writer = None
    if args.output_dir:
        os.makedirs(args.output_dir, exist_ok=True)
        ibest_writer = open(os.path.join(args.output_dir, f"text.{process_id}"), "a", encoding="utf-8")
    
    try:
        while True:
            try:
                message = await websocket.recv()
                result = json.loads(message)
                
                # 获取结果信息
                wav_name = result.get("wav_name", "demo")
                text = result.get("text", "")
                timestamp = result.get("timestamp", "")
                mode = result.get("mode", "")
                
                # 写入结果到文件
                if ibest_writer:
                    if timestamp:
                        text_write_line = f"{wav_name}\t{text}\t{timestamp}\n"
                    else:
                        text_write_line = f"{wav_name}\t{text}\n"
                    ibest_writer.write(text_write_line)
                
                # 根据模式处理结果
                if mode == "online":
                    text_print = text
                    os.system('clear')
                    print(f"\rpid{process_id}: {text_print}")
                elif mode == "offline":
                    if timestamp:
                        text_print = f"{text} timestamp: {timestamp}"
                    else:
                        text_print = text
                    print(f"\rpid{process_id}: {wav_name}: {text_print}")
                elif mode == "2pass-online":
                    text_print_2pass_online = text
                    text_print = text_print_2pass_offline + text_print_2pass_online
                    os.system('clear')
                    print(f"\rpid{process_id}: {text_print}")
                elif mode == "2pass-offline":
                    text_print_2pass_online = ""
                    text_print = text_print_2pass_offline + text
                    text_print_2pass_offline = text
                    os.system('clear')
                    print(f"\rpid{process_id}: {text_print}")
                
                # 限制打印长度
                text_print = text_print[-args.words_max_print:]
                
            except websockets.exceptions.ConnectionClosed:
                break
            except Exception as e:
                print(f"接收结果异常: {e}")
                break
    finally:
        if ibest_writer:
            ibest_writer.close()

async def ws_client(process_id, chunk_begin, chunk_size, args):
    """WebSocket客户端主函数"""
    # 创建SSL上下文
    if args.ssl == 1:
        ssl_context = ssl.SSLContext()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        uri = f"wss://{args.host}:{args.port}"
    else:
        uri = f"ws://{args.host}:{args.port}"
        ssl_context = None
    
    print(f"连接到: {uri}")
    
    # 对于每个处理的文件创建一个会话
    for i in range(chunk_begin, chunk_begin + chunk_size):
        async with websockets.connect(uri, subprotocols=["binary"], ping_interval=None, ssl=ssl_context) as websocket:
            # 创建发送和接收任务
            if args.audio_in is None:
                # 从麦克风录音
                send_task = asyncio.create_task(send_audio_from_microphone(websocket, args))
            else:
                # 处理文件
                current_args = args
                if args.audio_in.endswith(".scp"):
                    # 分片处理wav.scp
                    with open(args.audio_in, 'r') as f:
                        all_wavs = f.readlines()
                    
                    # 为当前进程选择一个文件
                    if i < len(all_wavs):
                        current_args = argparse.Namespace(**vars(args))
                        current_args.audio_in = all_wavs[i].strip()
                
                send_task = asyncio.create_task(send_audio_from_file(websocket, current_args))
            
            receive_task = asyncio.create_task(receive_results(websocket, args, f"{process_id}_{i}"))
            
            # 等待任务完成
            await asyncio.gather(send_task, receive_task)

def one_thread(id, chunk_begin, chunk_size, args):
    """单个线程函数"""
    asyncio.run(ws_client(id, chunk_begin, chunk_size, args))

def main():
    """主函数"""
    args = parse_args()
    
    # 麦克风模式
    if args.audio_in is None:
        # 单进程处理麦克风输入
        p = Process(target=one_thread, args=(0, 0, 1, args))
        p.start()
        p.join()
    else:
        # 计算每个进程处理的文件数
        if args.audio_in.endswith(".scp"):
            with open(args.audio_in, 'r') as f:
                wavs = f.readlines()
        else:
            wavs = [args.audio_in]
        
        total_len = len(wavs)
        if total_len >= args.thread_num:
            chunk_size = int(total_len / args.thread_num)
            remain_wavs = total_len - chunk_size * args.thread_num
        else:
            chunk_size = 1
            remain_wavs = 0
        
        # 创建多个进程处理文件
        process_list = []
        chunk_begin = 0
        for i in range(args.thread_num):
            now_chunk_size = chunk_size
            if remain_wavs > 0:
                now_chunk_size = chunk_size + 1
                remain_wavs = remain_wavs - 1
            
            # 进程i处理从chunk_begin开始的now_chunk_size个文件
            p = Process(target=one_thread, args=(i, chunk_begin, now_chunk_size, args))
            chunk_begin = chunk_begin + now_chunk_size
            p.start()
            process_list.append(p)
        
        # 等待所有进程完成
        for p in process_list:
            p.join()
    
    print('完成')

if __name__ == "__main__":
    main() 