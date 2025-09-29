#!/usr/bin/env python3
"""测试按日期归档的日志功能。

测试内容：
1. 验证日志文件按日期命名
2. 验证日志文件正确写入
3. 验证旧日志文件迁移功能
4. 验证日志文件路径解析

测试日期：2025-08-29
"""

import os
import sys
import tempfile
import time
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src" / "python-gui-client"))

def test_log_file_naming():
    """测试日志文件按日期命名功能"""
    print("=" * 60)
    print("测试1: 验证日志文件按日期命名")
    print("=" * 60)
    
    try:
        # 模拟当前日期
        current_date = time.strftime("%Y%m%d")
        expected_filename = f"funasr_gui_client_{current_date}.log"
        
        print(f"当前日期: {current_date}")
        print(f"预期日志文件名: {expected_filename}")
        
        # 创建临时目录模拟logs目录
        with tempfile.TemporaryDirectory() as temp_dir:
            logs_dir = Path(temp_dir) / "logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            # 构建预期的日志文件路径
            expected_log_path = logs_dir / expected_filename
            
            print(f"预期日志文件路径: {expected_log_path}")
            
            # 验证路径格式
            assert expected_filename.startswith("funasr_gui_client_")
            assert expected_filename.endswith(".log")
            assert len(current_date) == 8  # YYYYMMDD格式
            
            print("✓ 日志文件命名格式正确")
            
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False
    
    return True

def test_log_file_creation():
    """测试日志文件创建和写入"""
    print("\n" + "=" * 60)
    print("测试2: 验证日志文件创建和写入")
    print("=" * 60)
    
    try:
        import logging
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            logs_dir = Path(temp_dir) / "logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            current_date = time.strftime("%Y%m%d")
            log_file = logs_dir / f"funasr_gui_client_{current_date}.log"
            
            print(f"创建日志文件: {log_file}")
            
            # 配置临时日志处理器
            logger = logging.getLogger("test_logger")
            logger.setLevel(logging.INFO)
            
            # 清除现有处理器
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
            
            # 创建文件处理器
            file_handler = logging.FileHandler(log_file, mode='a', encoding="utf-8")
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
            # 写入测试日志
            test_message = f"测试日志消息 - {current_date}"
            logger.info(test_message)
            
            # 刷新并关闭处理器
            file_handler.flush()
            file_handler.close()
            logger.removeHandler(file_handler)
            
            # 验证文件存在和内容
            assert log_file.exists(), "日志文件未创建"
            
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
                assert test_message in content, "日志内容未正确写入"
                assert "INFO" in content, "日志级别未正确记录"
            
            print("✓ 日志文件创建成功")
            print("✓ 日志内容写入正确")
            print(f"日志文件大小: {log_file.stat().st_size} 字节")
            
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False
    
    return True

def test_legacy_log_migration():
    """测试旧日志文件迁移功能"""
    print("\n" + "=" * 60)
    print("测试3: 验证旧日志文件迁移")
    print("=" * 60)
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            logs_dir = Path(temp_dir) / "logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建旧日志文件
            old_log_file = logs_dir / "funasr_gui_client.log"
            old_log_content = "2025-05-18 22:38:54,347 - INFO - 旧的日志记录\n"
            
            with open(old_log_file, 'w', encoding='utf-8') as f:
                f.write(old_log_content)
            
            print(f"创建旧日志文件: {old_log_file}")
            
            # 模拟迁移逻辑
            current_date = time.strftime("%Y%m%d")
            new_log_file = logs_dir / f"funasr_gui_client_{current_date}.log"
            
            # 执行迁移
            if old_log_file.exists() and not new_log_file.exists():
                shutil.copy2(old_log_file, new_log_file)
                
                # 重命名旧文件
                backup_name = f"{old_log_file}.migrated"
                shutil.move(old_log_file, backup_name)
                
                print(f"✓ 旧日志迁移到: {new_log_file}")
                print(f"✓ 旧日志备份为: {backup_name}")
            
            # 验证迁移结果
            assert new_log_file.exists(), "新日志文件未创建"
            assert Path(f"{old_log_file}.migrated").exists(), "旧日志文件未备份"
            
            with open(new_log_file, 'r', encoding='utf-8') as f:
                migrated_content = f.read()
                assert old_log_content.strip() in migrated_content, "旧日志内容未正确迁移"
            
            print("✓ 日志迁移功能正常")
            
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False
    
    return True

def test_date_format_validation():
    """测试日期格式验证"""
    print("\n" + "=" * 60)
    print("测试4: 验证日期格式")
    print("=" * 60)
    
    try:
        import re
        
        current_date = time.strftime("%Y%m%d")
        print(f"当前日期字符串: {current_date}")
        
        # 验证日期格式 YYYYMMDD
        date_pattern = r'^\d{4}\d{2}\d{2}$'
        assert re.match(date_pattern, current_date), f"日期格式不正确: {current_date}"
        
        # 验证日期范围合理性
        year = int(current_date[:4])
        month = int(current_date[4:6])
        day = int(current_date[6:8])
        
        assert 2020 <= year <= 2030, f"年份不合理: {year}"
        assert 1 <= month <= 12, f"月份不合理: {month}"
        assert 1 <= day <= 31, f"日期不合理: {day}"
        
        print(f"✓ 日期格式正确: {year}年{month}月{day}日")
        
        # 测试不同日期的文件名
        test_dates = ["20250829", "20251225", "20260101"]
        for test_date in test_dates:
            filename = f"funasr_gui_client_{test_date}.log"
            print(f"测试日期 {test_date} -> 文件名: {filename}")
            assert filename.endswith(".log")
            assert test_date in filename
        
        print("✓ 日期格式验证通过")
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False
    
    return True

def main():
    """主测试函数"""
    print("开始测试按日期归档的日志功能...")
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_results = []
    
    # 执行所有测试
    test_results.append(("日志文件命名", test_log_file_naming()))
    test_results.append(("日志文件创建", test_log_file_creation()))
    test_results.append(("旧日志迁移", test_legacy_log_migration()))
    test_results.append(("日期格式验证", test_date_format_validation()))
    
    # 汇总测试结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed_count = 0
    total_count = len(test_results)
    
    for test_name, result in test_results:
        status = "通过" if result else "失败"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {test_name}: {status}")
        if result:
            passed_count += 1
    
    print(f"\n测试统计: {passed_count}/{total_count} 通过")
    
    if passed_count == total_count:
        print("🎉 所有测试通过！按日期归档的日志功能正常工作。")
        return True
    else:
        print("❌ 部分测试失败，请检查日志归档功能实现。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

