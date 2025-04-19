# -*- encoding: utf-8 -*-
import os
import time
import websockets, ssl
import asyncio
import sys
import argparse
import json
import traceback
from multiprocessing import Process

# 解决中文显示乱码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

parser = argparse.ArgumentParser()
parser.add_argument("--host",
                    type=str,
                    default="localhost",
                    required=False,
                    help="host ip, localhost, 0.0.0.0")
parser.add_argument("--port",
                    type=int,
                    default=10095,
                    required=False,
                    help="grpc server port")
parser.add_argument("--chunk_size",
                    type=str,
                    default="5, 10, 5",
                    help="chunk")
parser.add_argument("--chunk_interval",
                    type=int,
                    default=10,
                    help="chunk")
parser.add_argument("--hotword",
                    type=str,
                    default="",
                    help="hotword file path, one hotword perline (e.g.:阿里巴巴 20)")
parser.add_argument("--audio_in",
                    type=str,
                    required=True,
                    help="audio_in")
parser.add_argument("--audio_fs",
                    type=int,
                    default=16000,
                    help="audio_fs")
parser.add_argument("--send_without_sleep",
                    action="store_true",
                    default=False,
                    help="if audio_in is set, send_without_sleep")
parser.add_argument("--thread_num",
                    type=int,
                    default=1,
                    help="thread_num")
parser.add_argument("--words_max_print",
                    type=int,
                    default=10000,
                    help="chunk")
parser.add_argument("--output_dir",
                    type=str,
                    default=None,
                    help="output_dir")
parser.add_argument("--ssl",
                    type=int,
                    default=1,
                    help="1 for ssl connect, 0 for no ssl")
parser.add_argument("--use_itn",
                    type=int,
                    default=1,
                    help="1 for using itn, 0 for not itn")
parser.add_argument("--mode",
                    type=str,
                    default="offline",
                    help="offline, online, 2pass")

# 初始化全局变量
args = parser.parse_args()
# 在全局范围内转换chunk_size为整数列表
args.chunk_size = [int(x) for x in args.chunk_size.split(",")]
websocket = None
offline_msg_done = False
debug = True  # 开启详细日志

def log(msg):
    """调试日志输出"""
    if debug:
        print(f"[DEBUG] {msg}")

async def record_from_scp(chunk_begin, chunk_size):
    """从音频文件读取数据并发送"""
    global websocket, offline_msg_done
    is_finished = False
    
    if args.audio_in.endswith(".scp"):
        f_scp = open(args.audio_in)
        wavs = f_scp.readlines()
    else:
        wavs = [args.audio_in]

    # 热词处理
    fst_dict = {}
    hotword_msg = ""
    if args.hotword.strip() != "":
        f_scp = open(args.hotword)
        hot_lines = f_scp.readlines()
        for line in hot_lines:
            words = line.strip().split(" ")
            if len(words) < 2:
                print("Please checkout format of hotwords")
                continue
            try:
                fst_dict[" ".join(words[:-1])] = int(words[-1])
            except ValueError:
                print("Please checkout format of hotwords")
        hotword_msg = json.dumps(fst_dict)
        log(f"热词设置: {hotword_msg}")

    sample_rate = args.audio_fs
    wav_format = "pcm"
    use_itn = True
    if args.use_itn == 0:
        use_itn = False
    
    if chunk_size > 0:
        wavs = wavs[chunk_begin:chunk_begin + chunk_size]
        
    log(f"处理文件数: {len(wavs)}")
    
    for wav in wavs:
        wav_splits = wav.strip().split()
        wav_name = wav_splits[0] if len(wav_splits) > 1 else "demo"
        wav_path = wav_splits[1] if len(wav_splits) > 1 else wav_splits[0]
        
        if not len(wav_path.strip()) > 0:
            continue
            
        log(f"处理文件: {wav_path}")
        file_size = os.path.getsize(wav_path)
        log(f"文件大小: {file_size/1024/1024:.2f}MB")
        
        # 读取音频文件
        if wav_path.endswith(".pcm"):
            with open(wav_path, "rb") as f:
                audio_bytes = f.read()
                log(f"已读取PCM文件，大小: {len(audio_bytes)/1024/1024:.2f}MB")
        elif wav_path.endswith(".wav"):
            import wave
            with wave.open(wav_path, "rb") as wav_file:
                params = wav_file.getparams()
                sample_rate = wav_file.getframerate()
                frames = wav_file.readframes(wav_file.getnframes())
                audio_bytes = bytes(frames)
                log(f"已读取WAV文件，采样率: {sample_rate}, 大小: {len(audio_bytes)/1024/1024:.2f}MB")
        else:
            wav_format = "others"
            with open(wav_path, "rb") as f:
                audio_bytes = f.read()
                log(f"已读取其他格式文件，大小: {len(audio_bytes)/1024/1024:.2f}MB")

        # 计算每个音频块的大小
        stride = int(60 * args.chunk_size[1] / args.chunk_interval / 1000 * sample_rate * 2)
        chunk_num = (len(audio_bytes) - 1) // stride + 1
        log(f"分块数: {chunk_num}, 每块大小: {stride/1024:.2f}KB")

        # 发送初始化消息
        message = json.dumps({
            "mode": args.mode, 
            "chunk_size": args.chunk_size, 
            "chunk_interval": args.chunk_interval, 
            "audio_fs": sample_rate,
            "wav_name": wav_name, 
            "wav_format": wav_format, 
            "is_speaking": True, 
            "hotwords": hotword_msg, 
            "itn": use_itn
        })

        log(f"发送初始化消息: {message}")
        await websocket.send(message)
        
        # 发送音频数据
        is_speaking = True
        for i in range(chunk_num):
            beg = i * stride
            data = audio_bytes[beg:beg + stride]
            await websocket.send(data)
            log(f"已发送音频块 {i+1}/{chunk_num} ({(i+1)/chunk_num*100:.1f}%)")
            
            # 最后一块发送结束标志
            if i == chunk_num - 1:
                is_speaking = False
                message = json.dumps({"is_speaking": is_speaking})
                log("发送结束标志")
                await websocket.send(message)

            # 在非离线模式下每个块之间需要等待
            sleep_duration = 0.001 if args.mode == "offline" else 60 * args.chunk_size[1] / args.chunk_interval / 1000
            await asyncio.sleep(sleep_duration)
    
    if not args.mode == "offline":
        await asyncio.sleep(2)
    
    # 离线模式需要等待结果接收完成
    if args.mode == "offline":
        log("等待服务器处理完成...")
        timeout = 300  # 5分钟超时
        start_time = time.time()
        while not offline_msg_done:
            await asyncio.sleep(1)
            if time.time() - start_time > timeout:
                log(f"等待超时 ({timeout}秒)，强制结束")
                break
    
    log("处理完成，关闭连接")
    await websocket.close()

async def message(id):
    """接收服务器返回的消息并处理"""
    global websocket, offline_msg_done
    text_print = ""
    text_print_2pass_online = ""
    text_print_2pass_offline = ""
    
    if args.output_dir is not None:
        os.makedirs(args.output_dir, exist_ok=True)
        ibest_writer = open(os.path.join(args.output_dir, f"text.{id}"), "a", encoding="utf-8")
    else:
        ibest_writer = None
        
    try:
        while True:
            # 设置超时
            try:
                meg = await asyncio.wait_for(websocket.recv(), timeout=60)
                meg = json.loads(meg)
                
                wav_name = meg.get("wav_name", "demo")
                text = meg.get("text", "")
                timestamp = ""
                offline_msg_done = meg.get("is_final", False)
                
                if "timestamp" in meg:
                    timestamp = meg["timestamp"]
                
                log(f"接收到消息: {meg}")

                # 写入结果文件
                if ibest_writer is not None:
                    if timestamp != "":
                        text_write_line = f"{wav_name}\t{text}\t{timestamp}\n"
                    else:
                        text_write_line = f"{wav_name}\t{text}\n"
                    ibest_writer.write(text_write_line)

                # 根据不同模式处理输出
                if 'mode' not in meg:
                    continue
                    
                if meg["mode"] == "online":
                    text_print += f"{text}"
                    text_print = text_print[-args.words_max_print:]
                    print(f"\rpid{id}: {text_print}")
                    
                elif meg["mode"] == "offline":
                    if timestamp != "":
                        text_print = f"{text} timestamp: {timestamp}"
                    else:
                        text_print = f"{text}"
                    print(f"\rpid{id}: {wav_name}: {text_print}")
                    offline_msg_done = True
                    
                else:  # 2pass模式
                    if meg["mode"] == "2pass-online":
                        text_print_2pass_online += f"{text}"
                        text_print = text_print_2pass_offline + text_print_2pass_online
                    else:
                        text_print_2pass_online = ""
                        text_print = text_print_2pass_offline + f"{text}"
                        text_print_2pass_offline += f"{text}"
                    text_print = text_print[-args.words_max_print:]
                    print(f"\rpid{id}: {text_print}")
                    
            except asyncio.TimeoutError:
                log(f"等待服务器响应超时...")
                if offline_msg_done:
                    break
            except websockets.exceptions.ConnectionClosedOK as e:
                # 连接正常关闭，不作为错误处理
                log(f"连接已正常关闭: {e}")
                offline_msg_done = True
                break
                    
    except Exception as e:
        log(f"接收消息异常: {e}")
        traceback.print_exc()

async def ws_client(id, chunk_begin, chunk_size):
    """创建WebSocket客户端并开始通信"""
    global websocket, offline_msg_done, args
    
    if args.audio_in is None:
        chunk_begin = 0
        chunk_size = 1
    
    for i in range(chunk_begin, chunk_begin + chunk_size):
        offline_msg_done = False
        
        # 创建WebSocket连接
        if args.ssl == 1:
            log("使用SSL连接")
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            uri = f"wss://{args.host}:{args.port}"
        else:
            log("使用非SSL连接")
            uri = f"ws://{args.host}:{args.port}"
            ssl_context = None
            
        log(f"连接到 {uri}")
        
        try:
            async with websockets.connect(
                uri, 
                subprotocols=["binary"], 
                ping_interval=None, 
                ssl=ssl_context,
                close_timeout=60
            ) as websocket:
                log("连接已建立")
                
                # 创建并启动任务
                task1 = asyncio.create_task(record_from_scp(i, 1))
                task2 = asyncio.create_task(message(f"{id}_{i}"))
                
                try:
                    # 等待所有任务完成
                    await asyncio.gather(task1, task2)
                except websockets.exceptions.ConnectionClosedOK:
                    # 连接正常关闭，可能是服务器处理完成
                    log("连接已正常关闭，可能是处理完成")
                
        except Exception as e:
            log(f"WebSocket连接异常: {e}")
            traceback.print_exc()
            
    sys.exit(0)

def one_thread(id, chunk_begin, chunk_size):
    """每个线程要执行的主函数"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(ws_client(id, chunk_begin, chunk_size))

def main():
    """主函数，解析参数并启动处理线程"""
    global args
    # 不再需要重复初始化args和转换chunk_size
    # args = parser.parse_args()
    # args.chunk_size = [int(x) for x in args.chunk_size.split(",")]
    print(f"参数: {args}")
    
    # 计算每个进程处理的文件数量
    if args.audio_in.endswith(".scp"):
        with open(args.audio_in) as f_scp:
            wavs = f_scp.readlines()
    else:
        wavs = [args.audio_in]
    
    total_len = len(wavs)
    if total_len >= args.thread_num:
        chunk_size = int(total_len / args.thread_num)
        remain_wavs = total_len - chunk_size * args.thread_num
    else:
        chunk_size = 1
        remain_wavs = 0
    
    process_list = []
    chunk_begin = 0
    
    # 创建处理进程
    for i in range(args.thread_num):
        now_chunk_size = chunk_size
        if remain_wavs > 0:
            now_chunk_size = chunk_size + 1
            remain_wavs = remain_wavs - 1
        
        p = Process(target=one_thread, args=(i, chunk_begin, now_chunk_size))
        chunk_begin = chunk_begin + now_chunk_size
        p.start()
        process_list.append(p)
    
    # 等待所有进程完成
    for p in process_list:
        p.join()
    
    print('处理完成')

if __name__ == "__main__":
    main() 