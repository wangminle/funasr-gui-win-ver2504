#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI分离功能实现测试脚本
测试架构设计文档规范的目录结构修改和UI分离功能
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

# 添加项目路径以便导入
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, os.path.join(project_root, 'dev', 'src', 'python-gui-client'))

def test_directory_structure():
    """测试目录结构是否符合架构设计文档"""
    print("=" * 60)
    print("测试1: 验证目录结构符合架构设计文档")
    print("=" * 60)
    
    project_root = Path(__file__).parent.parent
    dev_dir = project_root / 'dev'
    
    # 检查必要的目录是否存在
    required_dirs = [
        dev_dir / 'config',
        dev_dir / 'logs', 
        dev_dir / 'output',
        dev_dir / 'src' / 'python-gui-client'
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if dir_path.exists():
            print(f"✅ 目录存在: {dir_path}")
        else:
            print(f"❌ 目录缺失: {dir_path}")
            all_exist = False
    
    if all_exist:
        print("✅ 目录结构测试通过 - 符合架构设计文档规范")
    else:
        print("❌ 目录结构测试失败 - 不符合架构设计文档规范")
    
    return all_exist

def test_config_file_migration():
    """测试配置文件迁移功能"""
    print("\n" + "=" * 60)
    print("测试2: 验证配置文件迁移功能")
    print("=" * 60)
    
    try:
        # 导入GUI客户端
        import funasr_gui_client_v2
        
        # 创建一个临时的配置文件来测试迁移
        project_root = Path(__file__).parent.parent
        release_config_path = project_root / 'release' / 'config' / 'config.json'
        dev_config_path = project_root / 'dev' / 'config' / 'config.json'
        
        # 备份现有配置（如果存在）
        backup_content = None
        if dev_config_path.exists():
            with open(dev_config_path, 'r', encoding='utf-8') as f:
                backup_content = f.read()
            os.remove(dev_config_path)
        
        # 如果release目录有配置文件，测试迁移
        if release_config_path.exists():
            print(f"✅ 找到release配置文件: {release_config_path}")
            
            # 创建GUI实例触发迁移
            app = funasr_gui_client_v2.FunASRGUIClient()
            
            # 检查是否成功迁移
            if dev_config_path.exists():
                print(f"✅ 配置文件已成功迁移到: {dev_config_path}")
                # 验证配置内容
                with open(dev_config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    print(f"✅ 配置内容验证: IP={config.get('ip')}, PORT={config.get('port')}")
            else:
                print(f"❌ 配置文件迁移失败")
                return False
                
            app.destroy()
        else:
            print("ℹ️  未找到release配置文件，跳过迁移测试")
            
        # 恢复备份
        if backup_content:
            with open(dev_config_path, 'w', encoding='utf-8') as f:
                f.write(backup_content)
                
        print("✅ 配置文件迁移测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 配置文件迁移测试失败: {e}")
        return False

def test_ui_components():
    """测试UI组件是否正确实现了分离"""
    print("\n" + "=" * 60)
    print("测试3: 验证UI分离功能实现")
    print("=" * 60)
    
    try:
        import tkinter as tk
        import funasr_gui_client_v2
        
        # 创建GUI实例
        app = funasr_gui_client_v2.FunASRGUIClient()
        
        # 检查是否存在选项卡控件
        if hasattr(app, 'notebook'):
            print("✅ 选项卡控件 (Notebook) 已创建")
        else:
            print("❌ 选项卡控件 (Notebook) 未找到")
            app.destroy()
            return False
            
        # 检查是否存在结果文本区域
        if hasattr(app, 'result_text'):
            print("✅ 识别结果文本区域已创建")
        else:
            print("❌ 识别结果文本区域未找到")
            app.destroy()
            return False
            
        # 检查是否存在日志文本区域
        if hasattr(app, 'log_text'):
            print("✅ 运行日志文本区域已创建")
        else:
            print("❌ 运行日志文本区域未找到")
            app.destroy()
            return False
            
        # 检查选项卡数量
        tab_count = app.notebook.index('end')
        if tab_count == 2:
            print(f"✅ 选项卡数量正确: {tab_count} 个")
        else:
            print(f"❌ 选项卡数量错误: 期望2个，实际{tab_count}个")
            app.destroy()
            return False
            
        # 检查选项卡标题
        result_tab_text = app.notebook.tab(0, 'text')
        log_tab_text = app.notebook.tab(1, 'text')
        print(f"✅ 选项卡标题: '{result_tab_text}' 和 '{log_tab_text}'")
        
        # 检查功能按钮
        if hasattr(app, 'copy_result_button'):
            print("✅ 复制结果按钮已创建")
        else:
            print("❌ 复制结果按钮未找到")
            
        if hasattr(app, 'clear_result_button'):
            print("✅ 清空结果按钮已创建")
        else:
            print("❌ 清空结果按钮未找到")
        
        # 测试结果显示功能
        app._display_recognition_result("这是一个测试识别结果")
        result_content = app.result_text.get("1.0", tk.END).strip()
        if "这是一个测试识别结果" in result_content:
            print("✅ 结果显示功能测试通过")
        else:
            print("❌ 结果显示功能测试失败")
            app.destroy()
            return False
        
        app.destroy()
        print("✅ UI分离功能测试通过")
        return True
        
    except Exception as e:
        print(f"❌ UI分离功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_language_support():
    """测试多语言支持是否工作正常"""
    print("\n" + "=" * 60)
    print("测试4: 验证多语言支持功能")
    print("=" * 60)
    
    try:
        import funasr_gui_client_v2
        
        # 创建GUI实例
        app = funasr_gui_client_v2.FunASRGUIClient()
        
        # 测试中文
        app.lang_manager.current_lang = "zh"
        zh_result_tab = app.lang_manager.get("result_tab")
        zh_log_tab = app.lang_manager.get("log_tab")
        print(f"✅ 中文界面: 结果选项卡='{zh_result_tab}', 日志选项卡='{zh_log_tab}'")
        
        # 测试英文
        app.lang_manager.current_lang = "en"
        en_result_tab = app.lang_manager.get("result_tab")
        en_log_tab = app.lang_manager.get("log_tab")
        print(f"✅ 英文界面: 结果选项卡='{en_result_tab}', 日志选项卡='{en_log_tab}'")
        
        # 验证翻译正确性
        if zh_result_tab != en_result_tab and zh_log_tab != en_log_tab:
            print("✅ 多语言翻译功能正常")
        else:
            print("❌ 多语言翻译功能异常")
            app.destroy()
            return False
        
        app.destroy()
        print("✅ 多语言支持测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 多语言支持测试失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("UI分离功能实现测试开始")
    print("测试架构设计文档规范的目录结构修改和UI分离功能")
    print("测试时间:", os.popen('date').read().strip())
    
    test_results = []
    
    # 运行所有测试
    test_results.append(("目录结构验证", test_directory_structure()))
    test_results.append(("配置文件迁移", test_config_file_migration()))
    test_results.append(("UI分离功能", test_ui_components()))
    test_results.append(("多语言支持", test_language_support()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！UI分离功能实现成功")
        return 0
    else:
        print("⚠️  部分测试失败，需要检查实现")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 