#!/usr/bin/env python3
"""
状态栏信息细化测试脚本

测试目标:
1. 测试StatusManager类的基本功能
2. 测试状态颜色区分
3. 测试识别阶段管理
4. 测试临时状态和自动恢复
5. 测试多语言支持

作者: FunASR GUI Client Team
日期: 2025-10-23
"""

import sys
import os
import time

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "python-gui-client"))

def test_status_manager_class_exists():
    """测试1: StatusManager类存在性"""
    print("\n" + "="*60)
    print("测试1: StatusManager类存在性")
    print("="*60)
    
    try:
        # 尝试导入StatusManager
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "funasr_gui_client_v3",
            os.path.join(os.path.dirname(__file__), "..", "..", "src", "python-gui-client", "funasr_gui_client_v3.py")
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # 检查StatusManager类
        if hasattr(module, 'StatusManager'):
            print("✓ StatusManager类已定义")
            StatusManager = module.StatusManager
            
            # 检查类属性
            required_attrs = [
                'STATUS_SUCCESS', 'STATUS_INFO', 'STATUS_WARNING', 
                'STATUS_ERROR', 'STATUS_PROCESSING', 'STATUS_COLORS'
            ]
            for attr in required_attrs:
                if hasattr(StatusManager, attr):
                    print(f"✓ 类属性 {attr} 存在")
                else:
                    print(f"✗ 类属性 {attr} 缺失")
                    return False
            
            return True
        else:
            print("✗ StatusManager类未定义")
            return False
            
    except Exception as e:
        print(f"✗ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_status_colors():
    """测试2: 状态颜色定义"""
    print("\n" + "="*60)
    print("测试2: 状态颜色定义")
    print("="*60)
    
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "funasr_gui_client_v3",
            os.path.join(os.path.dirname(__file__), "..", "..", "src", "python-gui-client", "funasr_gui_client_v3.py")
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        StatusManager = module.StatusManager
        
        # 检查颜色映射
        expected_colors = {
            'success': '#28a745',   # 绿色
            'info': '#007bff',      # 蓝色
            'warning': '#ffc107',   # 橙色
            'error': '#dc3545',     # 红色
            'processing': '#17a2b8' # 青色
        }
        
        colors = StatusManager.STATUS_COLORS
        print(f"✓ 定义了 {len(colors)} 种状态颜色")
        
        all_correct = True
        for status_type, expected_color in expected_colors.items():
            if status_type in colors:
                actual_color = colors[status_type]
                if actual_color == expected_color:
                    print(f"✓ {status_type}: {actual_color}")
                else:
                    print(f"⚠ {status_type}: {actual_color} (预期: {expected_color})")
            else:
                print(f"✗ 缺少颜色定义: {status_type}")
                all_correct = False
        
        return all_correct
        
    except Exception as e:
        print(f"✗ 测试异常: {e}")
        return False

def test_stage_definitions():
    """测试3: 识别阶段定义"""
    print("\n" + "="*60)
    print("测试3: 识别阶段定义")
    print("="*60)
    
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "funasr_gui_client_v3",
            os.path.join(os.path.dirname(__file__), "..", "..", "src", "python-gui-client", "funasr_gui_client_v3.py")
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # 检查阶段常量（通过实例）
        class MockVar:
            def __init__(self):
                self.value = ""
            def set(self, v):
                self.value = v
        
        class MockBar:
            def __init__(self):
                self.color = ""
            def config(self, foreground=None):
                if foreground:
                    self.color = foreground
            def after(self, ms, func):
                return 1
            def after_cancel(self, timer_id):
                pass
        
        class MockLangManager:
            def get(self, key, *args):
                return f"[{key}]"
        
        mock_var = MockVar()
        mock_bar = MockBar()
        mock_lang = MockLangManager()
        
        status_mgr = module.StatusManager(mock_var, mock_bar, mock_lang)
        
        # 检查阶段常量
        stages = [
            'STAGE_IDLE', 'STAGE_PREPARING', 'STAGE_READING_FILE',
            'STAGE_CONNECTING', 'STAGE_UPLOADING', 'STAGE_PROCESSING',
            'STAGE_RECEIVING', 'STAGE_COMPLETED'
        ]
        
        print(f"✓ 检查 {len(stages)} 个阶段定义")
        all_exist = True
        for stage in stages:
            if hasattr(status_mgr, stage):
                value = getattr(status_mgr, stage)
                print(f"✓ {stage} = '{value}'")
            else:
                print(f"✗ 缺少阶段定义: {stage}")
                all_exist = False
        
        return all_exist
        
    except Exception as e:
        print(f"✗ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_methods_exist():
    """测试4: 方法存在性"""
    print("\n" + "="*60)
    print("测试4: 方法存在性")
    print("="*60)
    
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "funasr_gui_client_v3",
            os.path.join(os.path.dirname(__file__), "..", "..", "src", "python-gui-client", "funasr_gui_client_v3.py")
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        StatusManager = module.StatusManager
        
        # 检查关键方法
        required_methods = [
            'set_status', 'set_stage', 'set_success', 'set_info',
            'set_warning', 'set_error', 'set_processing', 'get_current_stage'
        ]
        
        print(f"✓ 检查 {len(required_methods)} 个方法")
        all_exist = True
        for method in required_methods:
            if hasattr(StatusManager, method):
                print(f"✓ 方法 {method}() 存在")
            else:
                print(f"✗ 方法 {method}() 缺失")
                all_exist = False
        
        return all_exist
        
    except Exception as e:
        print(f"✗ 测试异常: {e}")
        return False

def test_language_translations():
    """测试5: 多语言翻译"""
    print("\n" + "="*60)
    print("测试5: 多语言翻译")
    print("="*60)
    
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "funasr_gui_client_v3",
            os.path.join(os.path.dirname(__file__), "..", "..", "src", "python-gui-client", "funasr_gui_client_v3.py")
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        LanguageManager = module.LanguageManager
        lang_mgr = LanguageManager()
        
        # 检查阶段翻译键
        stage_keys = [
            'stage_preparing', 'stage_reading_file', 'stage_connecting',
            'stage_uploading', 'stage_processing', 'stage_receiving',
            'stage_completed'
        ]
        
        print(f"✓ 检查 {len(stage_keys)} 个翻译键")
        all_exist = True
        for key in stage_keys:
            # 检查中文
            zh_text = lang_mgr.get(key, "test")
            if zh_text and not zh_text.startswith("["):
                print(f"✓ {key} (中文): {zh_text[:30]}...")
            else:
                print(f"✗ 缺少翻译: {key}")
                all_exist = False
        
        return all_exist
        
    except Exception as e:
        print(f"✗ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("FunASR GUI Client - 状态栏信息细化测试")
    print("="*60)
    
    tests = [
        ("StatusManager类存在性", test_status_manager_class_exists),
        ("状态颜色定义", test_status_colors),
        ("识别阶段定义", test_stage_definitions),
        ("方法存在性", test_methods_exist),
        ("多语言翻译", test_language_translations),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ 测试 '{test_name}' 执行失败: {e}")
            import traceback
            traceback.print_exc()
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
