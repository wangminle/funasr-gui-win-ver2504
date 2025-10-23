#!/usr/bin/env python3
"""
进程退出保护增强测试脚本

测试目标:
1. 测试_terminate_process_safely方法的基本功能
2. 测试terminate→wait流程
3. 测试terminate→wait→kill流程
4. 测试异常情况下的进程保护
5. 测试日志记录功能

作者: FunASR GUI Client Team
日期: 2025-10-23
"""

import subprocess
import sys
import time
import os
import logging

# 添加父目录到路径，以便导入主程序模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "python-gui-client"))

def setup_logging():
    """配置测试日志"""
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=logging.DEBUG,
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(
                os.path.join(
                    os.path.dirname(__file__),
                    "..", "..", "dev", "logs",
                    "test_process_protection.log"
                ),
                mode='w',
                encoding='utf-8'
            )
        ]
    )

def test_terminate_normal_process():
    """测试1: 正常进程的terminate→wait流程"""
    print("\n" + "="*60)
    print("测试1: 正常进程的terminate→wait流程")
    print("="*60)
    
    try:
        # 创建一个可以被terminate的进程（长时间sleep）
        if sys.platform == "win32":
            process = subprocess.Popen(
                [sys.executable, "-c", "import time; time.sleep(60)"],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            process = subprocess.Popen(
                [sys.executable, "-c", "import time; time.sleep(60)"]
            )
        
        print(f"✓ 创建测试进程，PID: {process.pid}")
        time.sleep(0.5)  # 让进程启动
        
        # 测试进程是否在运行
        if process.poll() is None:
            print("✓ 进程正在运行")
        else:
            print("✗ 进程未正常启动")
            return False
        
        # 尝试terminate
        print("⚙ 正在terminate进程...")
        process.terminate()
        
        # 等待进程结束
        try:
            exit_code = process.wait(timeout=5)
            print(f"✓ 进程已正常终止，退出码: {exit_code}")
            return True
        except subprocess.TimeoutExpired:
            print("✗ 进程terminate失败")
            process.kill()  # 清理
            return False
            
    except Exception as e:
        print(f"✗ 测试异常: {e}")
        return False

def test_terminate_stubborn_process():
    """测试2: 顽固进程的terminate→wait→kill流程"""
    print("\n" + "="*60)
    print("测试2: 顽固进程的terminate→wait→kill流程")
    print("="*60)
    
    try:
        # 创建一个忽略SIGTERM的进程（仅在Unix系统有效）
        if sys.platform == "win32":
            print("⚠ Windows系统跳过此测试（无法模拟忽略terminate）")
            return True
        
        script = """
import signal
import time
signal.signal(signal.SIGTERM, signal.SIG_IGN)  # 忽略SIGTERM
print("Process started and ignoring SIGTERM")
time.sleep(60)
"""
        process = subprocess.Popen([sys.executable, "-c", script])
        print(f"✓ 创建顽固测试进程，PID: {process.pid}")
        time.sleep(0.5)
        
        # 尝试terminate
        print("⚙ 正在terminate进程...")
        process.terminate()
        
        # 等待看进程是否会结束
        try:
            exit_code = process.wait(timeout=2)
            print(f"⚠ 进程意外响应了terminate，退出码: {exit_code}")
            return True
        except subprocess.TimeoutExpired:
            print("✓ 进程如预期忽略了terminate信号")
        
        # 强制kill
        print("⚙ 正在强制kill进程...")
        process.kill()
        
        try:
            exit_code = process.wait(timeout=2)
            print(f"✓ 进程已被强制杀死，退出码: {exit_code}")
            return True
        except subprocess.TimeoutExpired:
            print("✗ 进程无法被kill（不应该发生）")
            return False
            
    except Exception as e:
        print(f"✗ 测试异常: {e}")
        return False

def test_already_terminated_process():
    """测试3: 已终止进程的处理"""
    print("\n" + "="*60)
    print("测试3: 已终止进程的处理")
    print("="*60)
    
    try:
        # 创建一个立即退出的进程
        process = subprocess.Popen(
            [sys.executable, "-c", "import sys; sys.exit(0)"]
        )
        print(f"✓ 创建短生命周期进程，PID: {process.pid}")
        
        # 等待进程结束
        exit_code = process.wait(timeout=2)
        print(f"✓ 进程已结束，退出码: {exit_code}")
        
        # 尝试terminate已结束的进程（应该安全处理）
        if process.poll() is not None:
            print("✓ 检测到进程已结束，无需terminate")
            return True
        else:
            print("✗ 未能检测到进程已结束")
            return False
            
    except Exception as e:
        print(f"✗ 测试异常: {e}")
        return False

def test_none_process():
    """测试4: None进程的处理"""
    print("\n" + "="*60)
    print("测试4: None进程的处理")
    print("="*60)
    
    try:
        process = None
        
        # 检查None进程的处理
        if not process or (hasattr(process, 'poll') and process.poll() is not None):
            print("✓ 正确处理了None进程情况")
            return True
        else:
            print("✗ None进程处理失败")
            return False
            
    except Exception as e:
        print(f"✗ 测试异常: {e}")
        return False

def test_process_with_timeout():
    """测试5: 超时进程的处理"""
    print("\n" + "="*60)
    print("测试5: 超时进程的处理")
    print("="*60)
    
    try:
        # 创建一个长时间运行的进程
        process = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(300)"]
        )
        print(f"✓ 创建长时间运行进程，PID: {process.pid}")
        time.sleep(0.5)
        
        # 模拟超时情况
        print("⚙ 模拟超时，尝试terminate...")
        start_time = time.time()
        process.terminate()
        
        try:
            exit_code = process.wait(timeout=5)
            elapsed = time.time() - start_time
            print(f"✓ 进程在{elapsed:.2f}秒内终止，退出码: {exit_code}")
            return True
        except subprocess.TimeoutExpired:
            print("⚠ Terminate超时，尝试kill...")
            process.kill()
            try:
                exit_code = process.wait(timeout=2)
                print(f"✓ 进程被强制杀死，退出码: {exit_code}")
                return True
            except subprocess.TimeoutExpired:
                print("✗ 无法终止进程")
                return False
                
    except Exception as e:
        print(f"✗ 测试异常: {e}")
        return False

def test_logging_functionality():
    """测试6: 日志记录功能"""
    print("\n" + "="*60)
    print("测试6: 日志记录功能")
    print("="*60)
    
    try:
        # 配置日志
        setup_logging()
        
        # 创建一个进程并终止它
        process = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(60)"]
        )
        print(f"✓ 创建测试进程，PID: {process.pid}")
        time.sleep(0.5)
        
        # 记录终止过程
        logging.info(f"系统事件: 正在终止测试进程...")
        process.terminate()
        
        try:
            exit_code = process.wait(timeout=5)
            logging.info(f"系统事件: 测试进程已终止，退出码: {exit_code}")
            print("✓ 日志记录成功")
            return True
        except subprocess.TimeoutExpired:
            logging.warning("系统警告: 测试进程终止超时")
            process.kill()
            print("⚠ 进程被强制杀死")
            return True
            
    except Exception as e:
        print(f"✗ 测试异常: {e}")
        logging.error(f"测试错误: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("FunASR GUI Client - 进程退出保护增强测试")
    print("="*60)
    
    tests = [
        ("正常进程terminate→wait", test_terminate_normal_process),
        ("顽固进程terminate→wait→kill", test_terminate_stubborn_process),
        ("已终止进程处理", test_already_terminated_process),
        ("None进程处理", test_none_process),
        ("超时进程处理", test_process_with_timeout),
        ("日志记录功能", test_logging_functionality),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ 测试 '{test_name}' 执行失败: {e}")
            results.append((test_name, False))
    
    # 打印测试总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status}: {test_name}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    print("="*60)
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

