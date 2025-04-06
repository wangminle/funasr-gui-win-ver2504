#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FunASR客户端使用示例
展示如何使用FunasrClient类进行语音识别
"""

import os
import asyncio
import argparse
from funasr_client import FunasrClient

async def offline_transcribe(host, port, audio_path, output_dir=None, is_ssl=True, hotwords=None, use_itn=True):
    """离线文件转写示例"""
    print(f"开始处理文件: {audio_path}")
    
    # 创建客户端
    client = FunasrClient(host=host, port=port, is_ssl=is_ssl, mode="offline")
    
    try:
        # 连接到服务端
        await client.connect()
        print(f"已连接到服务器: {host}:{port}")
        
        # 发送音频文件
        await client.send_audio_file(
            audio_path=audio_path,
            hotwords=hotwords,
            use_itn=use_itn
        )
        
        # 接收识别结果
        results = await client.receive_results()
        
        # 处理结果
        for result in results:
            text = result.get("text", "")
            print(f"识别结果: {text}")
            
            if "timestamp" in result:
                print(f"时间戳: {result.get('timestamp', '')}")
        
        # 保存结果
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, f"{os.path.basename(audio_path)}.txt")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                for result in results:
                    text = result.get("text", "")
                    if "timestamp" in result:
                        f.write(f"{text}\t{result.get('timestamp', '')}\n")
                    else:
                        f.write(f"{text}\n")
                        
            print(f"结果已保存到: {output_file}")
                
    finally:
        # 关闭连接
        await client.close()
        print("连接已关闭")

async def realtime_transcribe(host, port, audio_path, is_ssl=True, hotwords=None, use_itn=True):
    """实时语音识别示例"""
    print(f"开始实时处理文件: {audio_path}")
    
    # 创建客户端
    client = FunasrClient(host=host, port=port, is_ssl=is_ssl, mode="2pass")
    
    try:
        # 连接到服务端
        await client.connect()
        print(f"已连接到服务器: {host}:{port}")
        
        # 发送音频文件
        await client.send_audio_file(
            audio_path=audio_path,
            chunk_size=[5, 10, 5],
            chunk_interval=10,
            hotwords=hotwords,
            use_itn=use_itn
        )
        
        # 接收识别结果
        results = await client.receive_results()
        
        # 处理结果
        final_text = ""
        for result in results:
            mode = result.get("mode", "")
            text = result.get("text", "")
            
            if mode == "2pass-offline":
                final_text = text
                
        print(f"最终识别结果: {final_text}")
                
    finally:
        # 关闭连接
        await client.close()
        print("连接已关闭")

async def microphone_transcribe(host, port, is_ssl=True, hotwords=None, use_itn=True):
    """麦克风实时识别示例"""
    print("开始麦克风实时识别")
    
    # 导入麦克风客户端
    from funasr_client import FunasrMicrophoneClient
    
    # 创建麦克风客户端
    mic_client = FunasrMicrophoneClient(
        host=host,
        port=port,
        is_ssl=is_ssl,
        mode="2pass",
        chunk_size=[5, 10, 5],
        chunk_interval=10,
        hotwords=hotwords,
        use_itn=use_itn
    )
    
    try:
        # 启动客户端
        await mic_client.start()
        print(f"已连接到服务器: {host}:{port}")
        print("开始录音，按Ctrl+C停止...")
        
        # 创建任务
        mic_task = asyncio.create_task(mic_client.process_microphone())
        
        # 接收结果任务
        text_print = ""
        try:
            while True:
                result = await mic_client.client.receive_one_result()
                if not result:
                    break
                    
                mode = result.get("mode", "")
                text = result.get("text", "")
                
                if mode == "2pass-online":
                    print(f"\r实时识别: {text}", end="")
                elif mode == "2pass-offline":
                    print(f"\n修正结果: {text}")
                    
        except KeyboardInterrupt:
            print("\n停止录音")
            
    finally:
        # 停止客户端
        await mic_client.stop()
        print("连接已关闭")

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='FunASR客户端示例')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='服务器地址')
    parser.add_argument('--port', type=int, default=10095, help='服务器端口')
    parser.add_argument('--audio', type=str, help='音频文件路径，不提供则使用麦克风输入')
    parser.add_argument('--mode', type=str, default='offline', choices=['offline', 'realtime'], 
                        help='识别模式: offline(离线), realtime(实时)')
    parser.add_argument('--ssl', type=int, default=1, help='是否使用SSL: 1(开启), 0(关闭)')
    parser.add_argument('--hotword', type=str, default='', help='热词文件路径')
    parser.add_argument('--use_itn', type=int, default=1, help='是否使用ITN: 1(开启), 0(关闭)')
    parser.add_argument('--output_dir', type=str, default=None, help='输出目录')
    
    args = parser.parse_args()
    
    # 处理参数
    is_ssl = args.ssl == 1
    use_itn = args.use_itn == 1
    
    # 根据模式选择不同的处理方法
    if args.audio:
        if args.mode == 'offline':
            await offline_transcribe(
                host=args.host,
                port=args.port,
                audio_path=args.audio,
                output_dir=args.output_dir,
                is_ssl=is_ssl,
                hotwords=args.hotword,
                use_itn=use_itn
            )
        else:
            await realtime_transcribe(
                host=args.host,
                port=args.port,
                audio_path=args.audio,
                is_ssl=is_ssl,
                hotwords=args.hotword,
                use_itn=use_itn
            )
    else:
        # 麦克风输入
        await microphone_transcribe(
            host=args.host,
            port=args.port,
            is_ssl=is_ssl,
            hotwords=args.hotword,
            use_itn=use_itn
        )

if __name__ == '__main__':
    asyncio.run(main()) 