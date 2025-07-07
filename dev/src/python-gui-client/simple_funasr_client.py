# -*- encoding: utf-8 -*-
"""
FunASR WebSocket客户端 - 增强版本
主要修复：
1. wav_name字段正确设置为实际文件名
2. Windows平台取消功能兼容性优化
3. 增强的错误处理和日志输出
4. 改进的WebSocket连接管理
"""
import os
import time
import websockets, ssl
import asyncio
import sys
import argparse
import json
import traceback
from multiprocessing import Process
import logging
import gc

# 根据平台导入相应模块
if sys.platform != "win32":
    import select

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
                    default=True,
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
parser.add_argument("--no-itn", action='store_false', dest='use_itn', default=None, help="disable ITN")
parser.add_argument("--no-ssl", action='store_false', dest='ssl', default=None, help="disable SSL")
parser.add_argument("--mode",
                    type=str,
                    default="offline",
                    help="offline, online, 2pass")
parser.add_argument("--transcribe_timeout",
                    type=int,
                    default=600,
                    help="transcribe timeout in seconds for offline mode")

# 初始化全局变量
args = parser.parse_args()
# 在全局范围内转换chunk_size为整数列表
args.chunk_size = [int(x) for x in args.chunk_size.split(",")]
websocket = None
offline_msg_done = False
cancel_requested = False
# 添加全局变量存储当前处理的文件名（修复wav_name问题）
current_wav_name = "unknown"

def log(msg, msg_type="调试"):
    """增强的日志输出函数"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}][{msg_type}] {msg}", flush=True)

def check_stdin_for_cancel_enhanced():
    """增强的Windows兼容性取消检测函数"""
    global cancel_requested, websocket
    
    try:
        if sys.platform == "win32":
            # Windows平台优化方案
            import threading
            import queue
            
            def windows_stdin_reader():
                """Windows平台安全的标准输入读取"""
                try:
                    # 方案1: 尝试使用msvcrt进行非阻塞检测
                    try:
                        import msvcrt
                        if msvcrt.kbhit():
                            # 快速读取可用字符
                            line_chars = []
                            while msvcrt.kbhit():
                                char = msvcrt.getch()
                                if char in (b'\r', b'\n'):
                                    break
                                line_chars.append(char)
                            
                            if line_chars:
                                line = b''.join(line_chars).decode('utf-8', errors='ignore').strip()
                                return line
                                
                    except ImportError:
                        # 方案2: msvcrt不可用时的备用方案
                        pass
                    
                    # 方案3: 尝试使用select（在某些Windows环境下可能工作）
                    try:
                        if hasattr(select, 'select'):
                            if select.select([sys.stdin], [], [], 0.0)[0]:
                                return sys.stdin.readline().strip()
                    except (ImportError, OSError):
                        pass
                        
                except Exception:
                    pass
                return None
            
            # 使用线程进行超时控制
            result_queue = queue.Queue()
            
            def threaded_reader():
                result = windows_stdin_reader()
                if result:
                    result_queue.put(result)
            
            # 创建读取线程，设置短超时
            reader_thread = threading.Thread(target=threaded_reader)
            reader_thread.daemon = True
            reader_thread.start()
            reader_thread.join(timeout=0.01)  # 10ms超时
            
            # 检查是否有结果
            try:
                line = result_queue.get_nowait()
                if line:
                    try:
                        command = json.loads(line)
                        if command.get("type") == "cancel_request":
                            log("收到取消请求", "取消")
                            cancel_requested = True
                            
                            # 发送确认响应
                            response = {
                                "type": "cancel_response",
                                "success": True,
                                "message": "Windows平台取消请求已处理",
                                "timestamp": time.time()
                            }
                            print(f"CANCEL_RESPONSE:{json.dumps(response)}", flush=True)
                            
                            # 关闭WebSocket连接
                            if websocket and not websocket.closed:
                                try:
                                    loop = asyncio.get_event_loop()
                                    if loop.is_running():
                                        asyncio.create_task(close_websocket_safely())
                                except RuntimeError:
                                    pass
                                    
                    except json.JSONDecodeError:
                        pass
            except queue.Empty:
                pass
                
        else:
            # Unix/Linux系统的标准处理
            try:
                if hasattr(select, 'select') and select.select([sys.stdin], [], [], 0.0)[0]:
                    line = sys.stdin.readline().strip()
                    if line:
                        try:
                            command = json.loads(line)
                            if command.get("type") == "cancel_request":
                                log("收到取消请求", "取消")
                                cancel_requested = True
                                
                                response = {
                                    "type": "cancel_response", 
                                    "success": True,
                                    "message": "Unix平台取消请求已处理",
                                    "timestamp": time.time()
                                }
                                print(f"CANCEL_RESPONSE:{json.dumps(response)}", flush=True)
                                
                                if websocket and not websocket.closed:
                                    try:
                                        loop = asyncio.get_event_loop()
                                        if loop.is_running():
                                            asyncio.create_task(close_websocket_safely())
                                    except RuntimeError:
                                        pass
                        except json.JSONDecodeError:
                            pass
            except (ImportError, OSError):
                pass
                
    except Exception as e:
        # 静默处理所有异常，不影响主流程
        pass

# 为了保持向后兼容性，保留原函数名
check_stdin_for_cancel = check_stdin_for_cancel_enhanced

async def close_websocket_safely():
    """安全关闭WebSocket连接"""
    global websocket, offline_msg_done
    try:
        if websocket and not websocket.closed:
            log("正在安全关闭WebSocket连接", "系统")
            offline_msg_done = True
            await websocket.close()
            log("WebSocket连接已关闭", "系统")
    except Exception as e:
        log(f"关闭WebSocket时出错: {e}", "错误")

# 为了保持向后兼容性，保留原函数名
close_websocket_immediately = close_websocket_safely

def extract_wav_name_from_path(file_path):
    """从文件路径提取正确的wav_name"""
    if not file_path:
        return "demo"
    
    # 获取文件名（包含扩展名）
    filename = os.path.basename(file_path)
    
    # 如果需要去除扩展名，可以使用下面的代码
    # filename = os.path.splitext(filename)[0]
    
    log(f"从路径 '{file_path}' 提取文件名: '{filename}'", "解析")
    return filename

async def record_from_scp_enhanced(chunk_begin, chunk_size):
    """增强的音频数据读取和发送函数"""
    global websocket, offline_msg_done, cancel_requested, current_wav_name
    
    if cancel_requested:
        log("检测到取消请求，跳过音频处理", "取消")
        return
    
    # 解析输入文件
    if args.audio_in.endswith(".scp"):
        with open(args.audio_in, 'r') as f:
            wavs = f.readlines()
    else:
        wavs = [args.audio_in]

    # 热词处理
    hotword_msg = ""
    if args.hotword.strip():
        try:
            fst_dict = {}
            with open(args.hotword, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        try:
                            word = " ".join(parts[:-1])
                            weight = int(parts[-1])
                            fst_dict[word] = weight
                        except ValueError:
                            log(f"热词格式错误: {line.strip()}", "警告")
            hotword_msg = json.dumps(fst_dict, ensure_ascii=False)
            log(f"加载热词: {hotword_msg}", "配置")
        except Exception as e:
            log(f"加载热词文件失败: {e}", "错误")

    # 基本配置
    sample_rate = args.audio_fs
    wav_format = "pcm"
    use_itn = bool(args.use_itn)
    
    if chunk_size > 0:
        wavs = wavs[chunk_begin:chunk_begin + chunk_size]
    
    log(f"准备处理 {len(wavs)} 个文件", "处理")
    
    for wav_line in wavs:
        if cancel_requested:
            log("检测到取消请求，停止处理", "取消")
            return
            
        wav_parts = wav_line.strip().split()
        
        if len(wav_parts) > 1:
            # SCP文件格式: "name path"
            wav_name = wav_parts[0]
            wav_path = wav_parts[1]
            log(f"SCP格式 - 名称: '{wav_name}', 路径: '{wav_path}'", "解析")
        else:
            # 单个文件路径
            wav_path = wav_parts[0]
            # 【关键修复】正确提取文件名
            wav_name = extract_wav_name_from_path(wav_path)
            log(f"单文件格式 - 路径: '{wav_path}', 提取的名称: '{wav_name}'", "解析")
        
        # 【关键修复】更新全局变量，确保后续处理一致
        current_wav_name = wav_name
        
        if not wav_path.strip():
            continue
        
        try:
            file_size = os.path.getsize(wav_path)
            log(f"文件大小: {file_size/1024/1024:.2f}MB", "信息")
        except OSError as e:
            log(f"无法访问文件 {wav_path}: {e}", "错误")
            continue
        
        # 读取音频数据
        try:
            if wav_path.endswith(".pcm"):
                with open(wav_path, "rb") as f:
                    audio_bytes = f.read()
                wav_format = "pcm"
            elif wav_path.endswith(".wav"):
                import wave
                with wave.open(wav_path, "rb") as wav_file:
                    sample_rate = wav_file.getframerate()
                    frames = wav_file.readframes(wav_file.getnframes())
                    audio_bytes = bytes(frames)
                wav_format = "wav"
            else:
                with open(wav_path, "rb") as f:
                    audio_bytes = f.read()
                wav_format = "others"
                
            log(f"成功读取音频数据: {len(audio_bytes)/1024/1024:.2f}MB", "读取")
            
        except Exception as e:
            log(f"读取音频文件失败: {e}", "错误")
            continue

        # 计算分块参数
        if args.mode == "offline":
            stride = 65536  # 离线模式使用固定分块大小
        else:
            stride = int(60 * args.chunk_size[1] / args.chunk_interval / 1000 * sample_rate * 2)
        
        chunk_num = (len(audio_bytes) - 1) // stride + 1
        log(f"分块参数: 数量={chunk_num}, 大小={stride/1024:.1f}KB", "分块")

        # 【关键修复】构造WebSocket初始消息，确保wav_name正确
        init_message = {
            "mode": args.mode,
            "audio_fs": sample_rate,
            "wav_name": wav_name,  # 使用正确提取的文件名
            "wav_format": wav_format,
            "is_speaking": True,
            "hotwords": hotword_msg,
            "itn": use_itn
        }
        
        # 非离线模式添加chunk参数
        if args.mode != "offline":
            init_message["chunk_size"] = args.chunk_size
            init_message["chunk_interval"] = args.chunk_interval
        
        message_json = json.dumps(init_message, ensure_ascii=False)
        log(f"发送初始化消息: {message_json}", "发送")
        
        await websocket.send(message_json)
        
        # 发送音频数据
        total_sent = 0
        last_progress = -1
        
        for i in range(chunk_num):
            if cancel_requested:
                log("检测到取消请求，停止数据发送", "取消")
                return
            
            # 每20个块检查一次取消请求
            if i % 20 == 0:
                check_stdin_for_cancel_enhanced()
            
            if cancel_requested:
                log("检测到取消请求，停止数据发送", "取消")
                return
            
            # 发送音频块
            start_pos = i * stride
            end_pos = min(start_pos + stride, len(audio_bytes))
            data_chunk = audio_bytes[start_pos:end_pos]
            
            await websocket.send(data_chunk)
            total_sent += len(data_chunk)
            
            # 进度报告
            progress = int(total_sent / len(audio_bytes) * 100)
            if progress % 10 == 0 and progress != last_progress:
                print(f"上传进度: {progress}%", flush=True)
                last_progress = progress
            
            # 发送结束标志
            if i == chunk_num - 1:
                end_message = {"is_speaking": False}
                end_json = json.dumps(end_message)
                log(f"发送结束标志: {end_json}", "发送")
                await websocket.send(end_json)
            
            # 发送间隔控制
            if not args.send_without_sleep and args.mode != "offline":
                sleep_time = 60 * args.chunk_size[1] / args.chunk_interval / 1000
                await asyncio.sleep(sleep_time)
        
        log(f"文件 '{wav_name}' 发送完成", "完成")
    
    # 等待处理完成
    if args.mode == "offline":
        log("等待服务器处理...", "等待")
        timeout = args.transcribe_timeout
        start_time = time.time()
        
        while not offline_msg_done and not cancel_requested:
            await asyncio.sleep(0.5)
            if time.time() - start_time > timeout:
                log(f"等待超时({timeout}秒)", "超时")
                break
    
    log("音频处理流程完成", "完成")

# 为了保持向后兼容性，保留原函数名
record_from_scp = record_from_scp_enhanced

async def message_handler_enhanced(session_id):
    """增强的消息接收处理函数"""
    global websocket, offline_msg_done, cancel_requested, current_wav_name
    
    # 输出文件准备
    text_writer = None
    json_writer = None
    all_results = []
    
    if args.output_dir:
        os.makedirs(args.output_dir, exist_ok=True)
        text_file = os.path.join(args.output_dir, f"text.{session_id}")
        json_file = os.path.join(args.output_dir, f"results.{session_id}.json")
        
        text_writer = open(text_file, "a", encoding="utf-8")
        json_writer = open(json_file, "w", encoding="utf-8")
    
    try:
        while not cancel_requested:
            try:
                # 接收消息
                check_stdin_for_cancel_enhanced()
                if cancel_requested:
                    break
                
                log("等待服务器消息...", "接收")
                message = await asyncio.wait_for(websocket.recv(), timeout=60)
                
                if cancel_requested:
                    break
                
                # 解析消息
                try:
                    result = json.loads(message)
                    
                    # 【关键修复】处理wav_name字段
                    server_wav_name = result.get("wav_name", "")
                    effective_wav_name = current_wav_name if current_wav_name != "unknown" else server_wav_name or "demo"
                    
                    if server_wav_name != current_wav_name and current_wav_name != "unknown":
                        log(f"wav_name不一致: 服务器='{server_wav_name}', 本地='{current_wav_name}', 使用本地值", "校正")
                    
                    text_content = result.get("text", "")
                    
                    if text_content.strip():
                        log(f"收到识别结果: {effective_wav_name}", "结果")
                        print(f"识别文本({effective_wav_name}): {text_content}")
                        
                        # 保存文本结果
                        if text_writer:
                            text_writer.write(f"{effective_wav_name}\t{text_content}\n")
                            text_writer.flush()
                        
                        # 保存JSON结果
                        result_record = {
                            "wav_name": effective_wav_name,
                            "text": text_content,
                            "mode": args.mode,
                            "timestamp": result.get("timestamp", ""),
                            "stamp_sents": result.get("stamp_sents", [])
                        }
                        all_results.append(result_record)
                        
                        if json_writer:
                            json.dump(all_results, json_writer, ensure_ascii=False, indent=2)
                            json_writer.flush()
                        
                        # 离线模式收到结果后完成
                        if args.mode == "offline":
                            log("离线识别完成", "完成")
                            offline_msg_done = True
                            break
                    
                    # 处理实时模式的final标志
                    if args.mode in ["online", "2pass"] and result.get("is_final", False):
                        log("实时识别完成", "完成")
                        break
                        
                except json.JSONDecodeError as e:
                    log(f"JSON解析失败: {e}", "错误")
                    
            except asyncio.TimeoutError:
                log("接收消息超时", "超时")
                break
            except Exception as e:
                log(f"接收消息异常: {e}", "错误")
                break
        
    finally:
        # 清理资源
        if text_writer:
            text_writer.close()
        if json_writer:
            json_writer.close()
        log("消息处理结束", "清理")

# 为了保持向后兼容性，保留原函数名
message = message_handler_enhanced

async def websocket_client_enhanced(session_id, chunk_begin, chunk_size):
    """增强的WebSocket客户端"""
    global websocket, cancel_requested
    
    # 构造连接URI
    protocol = "wss" if args.ssl else "ws"
    uri = f"{protocol}://{args.host}:{args.port}"
    log(f"连接服务器: {uri}", "连接")
    
    # SSL配置
    ssl_context = None
    if args.ssl:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
    
    try:
        async with websockets.connect(uri, ssl=ssl_context) as ws:
            websocket = ws
            log("WebSocket连接建立成功", "连接")
            
            # 并发执行发送和接收任务
            send_task = asyncio.create_task(record_from_scp_enhanced(chunk_begin, chunk_size))
            recv_task = asyncio.create_task(message_handler_enhanced(session_id))
            
            # 等待任务完成
            done, pending = await asyncio.wait(
                [send_task, recv_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # 取消未完成的任务
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            log("WebSocket会话结束", "连接")
            
    except Exception as e:
        log(f"WebSocket连接错误: {e}", "错误")
        traceback.print_exc()

# 为了保持向后兼容性，保留原函数名
ws_client = websocket_client_enhanced

def one_thread(id, chunk_begin, chunk_size):
    """每个线程要执行的主函数"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(ws_client(id, chunk_begin, chunk_size))

def main():
    """主函数，解析参数并启动处理线程"""
    try:
        global args
        log(f"FunASR客户端启动", "启动")
        log(f"运行参数: {vars(args)}", "配置")
        
        # 禁用 asyncio 的调试日志，除非显式启用
        logging.getLogger('asyncio').setLevel(logging.WARNING)

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
        
        if args.thread_num == 1:
            # 单线程模式
            one_thread(0, 0, 0)
        else:
            # 多线程模式（用于SCP文件）
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
        
        log("程序执行完成", "完成")
        
    except KeyboardInterrupt:
        log("程序被用户中断", "中断")
    except Exception as e:
        log(f"主程序异常: {e}", "错误")
        # 为了保持向后兼容性，仍然打印到stderr
        print(f"simple_funasr_client 在主函数发生致命错误: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    # 将整个 main() 的调用包裹在 try-except 块中
    # 这是捕获所有未处理异常的最后一道防线
    try:
        main()
    except Exception as e:
        # 在极少数情况下，如果 main() 本身或其外部的全局代码初始化出错，
        # 这个块会捕获到异常。
        print(f"simple_funasr_client 启动时发生致命错误: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1) 