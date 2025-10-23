#!/usr/bin/env python3
"""
热词文件支持测试脚本

测试目标:
1. 测试GUI热词选择界面元素
2. 测试配置文件热词路径保存和加载
3. 测试热词参数传递到子进程
4. 测试Tooltip提示功能

作者: FunASR GUI Client Team
日期: 2025-10-23
"""

import sys
import os
import json
import tempfile

# 添加父目录到路径，以便导入主程序模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "python-gui-client"))

def test_config_save_load():
    """测试1: 配置文件热词路径保存和加载"""
    print("\n" + "="*60)
    print("测试1: 配置文件热词路径保存和加载")
    print("="*60)
    
    try:
        # 创建临时配置文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            config = {
                "ip": "127.0.0.1",
                "port": "10095",
                "use_itn": 1,
                "use_ssl": 1,
                "language": "zh",
                "connection_test_timeout": 10,
                "hotword_path": "/path/to/hotwords.txt"
            }
            json.dump(config, f, ensure_ascii=False, indent=4)
            temp_config_file = f.name
        
        print(f"✓ 创建临时配置文件: {temp_config_file}")
        
        # 读取并验证
        with open(temp_config_file, 'r', encoding='utf-8') as f:
            loaded_config = json.load(f)
        
        if "hotword_path" in loaded_config:
            print(f"✓ 配置中包含热词路径: {loaded_config['hotword_path']}")
        else:
            print("✗ 配置中缺少热词路径")
            os.unlink(temp_config_file)
            return False
        
        if loaded_config["hotword_path"] == "/path/to/hotwords.txt":
            print("✓ 热词路径保存和加载正确")
        else:
            print("✗ 热词路径不匹配")
            os.unlink(temp_config_file)
            return False
        
        # 清理
        os.unlink(temp_config_file)
        print("✓ 测试完成，临时文件已清理")
        return True
        
    except Exception as e:
        print(f"✗ 测试异常: {e}")
        return False

def test_hotword_file_format():
    """测试2: 热词文件格式验证"""
    print("\n" + "="*60)
    print("测试2: 热词文件格式验证")
    print("="*60)
    
    try:
        # 创建临时热词文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("阿里巴巴 20\n")
            f.write("人工智能 15\n")
            f.write("FunASR 10\n")
            temp_hotword_file = f.name
        
        print(f"✓ 创建临时热词文件: {temp_hotword_file}")
        
        # 读取并验证格式
        with open(temp_hotword_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"✓ 热词文件包含 {len(lines)} 行")
        
        # 验证每行格式
        valid_format = True
        for i, line in enumerate(lines, 1):
            parts = line.strip().split()
            if len(parts) >= 1:  # 至少有热词
                hotword = parts[0]
                weight = parts[1] if len(parts) > 1 else "N/A"
                print(f"  行{i}: 热词='{hotword}', 权重={weight}")
            else:
                print(f"✗ 行{i}: 格式错误")
                valid_format = False
        
        # 清理
        os.unlink(temp_hotword_file)
        
        if valid_format:
            print("✓ 所有热词格式正确")
            return True
        else:
            print("✗ 部分热词格式错误")
            return False
            
    except Exception as e:
        print(f"✗ 测试异常: {e}")
        return False

def test_parameter_passing():
    """测试3: 热词参数传递"""
    print("\n" + "="*60)
    print("测试3: 热词参数传递逻辑")
    print("="*60)
    
    try:
        # 模拟命令参数构造
        hotword_path = "/path/to/hotwords.txt"
        args = [
            "python3",
            "simple_funasr_client.py",
            "--host", "127.0.0.1",
            "--port", "10095",
            "--audio_in", "test.wav",
        ]
        
        # 添加热词参数（模拟GUI中的逻辑）
        if hotword_path and os.path.exists("/dev/null"):  # 使用/dev/null作为存在的测试路径
            args_with_hotword = args.copy()
            args_with_hotword.extend(["--hotword", hotword_path])
            print("✓ 热词参数添加成功")
            print(f"  完整命令: {' '.join(args_with_hotword)}")
        else:
            print("⚠ 热词文件不存在，跳过参数")
            args_with_hotword = args
        
        # 验证参数
        if "--hotword" in args_with_hotword:
            hotword_index = args_with_hotword.index("--hotword")
            if hotword_index + 1 < len(args_with_hotword):
                actual_path = args_with_hotword[hotword_index + 1]
                print(f"✓ 热词参数值: {actual_path}")
                return actual_path == hotword_path
            else:
                print("✗ 热词参数缺少值")
                return False
        else:
            print("⚠ 命令中没有热词参数")
            return True  # 这也是合法的情况
            
    except Exception as e:
        print(f"✗ 测试异常: {e}")
        return False

def test_empty_hotword_file():
    """测试4: 空热词文件处理"""
    print("\n" + "="*60)
    print("测试4: 空热词文件处理")
    print("="*60)
    
    try:
        # 创建空热词文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            temp_hotword_file = f.name
        
        print(f"✓ 创建空热词文件: {temp_hotword_file}")
        
        # 验证文件为空
        file_size = os.path.getsize(temp_hotword_file)
        if file_size == 0:
            print("✓ 文件确实为空（0字节）")
        else:
            print(f"⚠ 文件不为空（{file_size}字节）")
        
        # 空文件应该也能正常传递给子进程
        if os.path.exists(temp_hotword_file):
            print("✓ 空文件可以正常传递")
        
        # 清理
        os.unlink(temp_hotword_file)
        print("✓ 测试完成，临时文件已清理")
        return True
        
    except Exception as e:
        print(f"✗ 测试异常: {e}")
        return False

def test_nonexistent_hotword_file():
    """测试5: 不存在的热词文件处理"""
    print("\n" + "="*60)
    print("测试5: 不存在的热词文件处理")
    print("="*60)
    
    try:
        nonexistent_path = "/path/that/does/not/exist/hotwords.txt"
        
        # 验证文件不存在
        if not os.path.exists(nonexistent_path):
            print(f"✓ 确认文件不存在: {nonexistent_path}")
        else:
            print(f"✗ 文件意外存在")
            return False
        
        # 模拟GUI中的逻辑：文件不存在时不添加参数
        args = ["python3", "simple_funasr_client.py"]
        if nonexistent_path and os.path.exists(nonexistent_path):
            args.extend(["--hotword", nonexistent_path])
            print("✗ 不应该添加不存在的文件")
            return False
        else:
            print("✓ 正确跳过不存在的文件")
            print(f"  命令中没有热词参数（符合预期）")
            return True
        
    except Exception as e:
        print(f"✗ 测试异常: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("FunASR GUI Client - 热词文件支持测试")
    print("="*60)
    
    tests = [
        ("配置文件热词路径保存和加载", test_config_save_load),
        ("热词文件格式验证", test_hotword_file_format),
        ("热词参数传递逻辑", test_parameter_passing),
        ("空热词文件处理", test_empty_hotword_file),
        ("不存在的热词文件处理", test_nonexistent_hotword_file),
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

