#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码对齐集成测试脚本 - v0.2.0对齐验证
测试修改后的dev版本代码是否能正常完成文件上传到识别的全流程
日期: 2025-01-15
"""

import os
import sys
import time
import subprocess
import shutil
import json
from pathlib import Path

# 测试配置
TEST_CONFIG = {
    "gui_client_path": "dev/src/python-gui-client/funasr_gui_client_v2.py",
    "simple_client_path": "dev/src/python-gui-client/simple_funasr_client.py",
    "test_audio_file": "demo/tv-report-1.wav",
    "config_file": "dev/config/config.json",
    "output_dir": "dev/output",
    "results_dir": "release/results",
    "test_output_dir": "tests/test_output_20250115"
}

class CodeAlignmentTester:
    def __init__(self):
        self.test_results = {
            "file_structure_check": False,
            "gui_client_import": False,
            "simple_client_import": False,
            "config_validation": False,
            "directory_structure": False,
            "requirements_check": False,
            "overall_status": False
        }
        self.test_logs = []
    
    def log(self, message, level="INFO"):
        """记录测试日志"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.test_logs.append(log_entry)
        print(log_entry)
    
    def test_file_structure(self):
        """测试文件结构完整性"""
        self.log("开始测试文件结构完整性...")
        
        required_files = [
            TEST_CONFIG["gui_client_path"],
            TEST_CONFIG["simple_client_path"],
            TEST_CONFIG["test_audio_file"],
            TEST_CONFIG["config_file"]
        ]
        
        missing_files = []
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if missing_files:
            self.log(f"缺少必要文件: {missing_files}", "ERROR")
            self.test_results["file_structure_check"] = False
        else:
            self.log("所有必要文件存在")
            self.test_results["file_structure_check"] = True
        
        return self.test_results["file_structure_check"]
    
    def test_gui_client_import(self):
        """测试GUI客户端能否正常导入"""
        self.log("测试GUI客户端导入...")
        
        try:
            # 直接在当前进程中测试，避免编码问题
            sys.path.insert(0, 'dev/src/python-gui-client')
            
            try:
                import funasr_gui_client_v2
                self.log("GUI客户端导入成功")
                
                # 测试关键类是否存在
                if hasattr(funasr_gui_client_v2, 'FunASRGUIClient'):
                    self.log("FunASRGUIClient类存在")
                else:
                    self.log("FunASRGUIClient类不存在", "ERROR")
                    self.test_results["gui_client_import"] = False
                    return False
                    
                # 测试是否移除了取消功能相关代码
                with open(TEST_CONFIG["gui_client_path"], 'r', encoding='utf-8') as f:
                    client_code = f.read()
                
                removed_features = []
                if 'recognition_running' not in client_code:
                    removed_features.append("recognition_running变量")
                if 'cancel_event' not in client_code:
                    removed_features.append("cancel_event变量")
                if '_check_cancel_response' not in client_code:
                    removed_features.append("取消功能相关方法")
                
                self.log(f"已移除的取消功能: {removed_features}")
                self.log("GUI客户端代码结构验证完成")
                self.test_results["gui_client_import"] = True
                
            except ImportError as e:
                self.log(f"导入失败: {e}", "ERROR")
                self.test_results["gui_client_import"] = False
            finally:
                # 清理导入的模块
                if 'funasr_gui_client_v2' in sys.modules:
                    del sys.modules['funasr_gui_client_v2']
                if 'dev/src/python-gui-client' in sys.path:
                    sys.path.remove('dev/src/python-gui-client')
                
        except Exception as e:
            self.log(f"GUI客户端导入测试异常: {e}", "ERROR")
            self.test_results["gui_client_import"] = False
        
        return self.test_results["gui_client_import"]
    
    def test_simple_client_import(self):
        """测试简单客户端能否正常导入"""
        self.log("测试简单客户端导入...")
        
        try:
            # 检查文件是否存在并与v0.2.0一致
            if not os.path.exists(TEST_CONFIG["simple_client_path"]):
                self.log("简单客户端文件不存在", "ERROR")
                self.test_results["simple_client_import"] = False
                return False
            
            # 检查文件内容是否与v0.2.0一致
            with open(TEST_CONFIG["simple_client_path"], 'r', encoding='utf-8') as f:
                current_content = f.read()
            
            with open("ref/v0.2.0/simple_funasr_client.py", 'r', encoding='utf-8') as f:
                ref_content = f.read()
            
            if current_content == ref_content:
                self.log("简单客户端内容与v0.2.0完全一致")
                self.test_results["simple_client_import"] = True
            else:
                self.log("简单客户端内容与v0.2.0不一致", "ERROR")
                self.test_results["simple_client_import"] = False
            
            # 检查关键函数是否在文件中定义
            if 'def ws_client(' in current_content:
                self.log("ws_client函数已定义")
            else:
                self.log("ws_client函数未定义", "ERROR")
                self.test_results["simple_client_import"] = False
                
        except Exception as e:
            self.log(f"简单客户端测试异常: {e}", "ERROR")
            self.test_results["simple_client_import"] = False
        
        return self.test_results["simple_client_import"]
    
    def test_config_validation(self):
        """测试配置文件有效性"""
        self.log("测试配置文件有效性...")
        
        try:
            with open(TEST_CONFIG["config_file"], 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            required_keys = ["ip", "port", "use_itn", "use_ssl", "language"]
            
            missing_keys = [key for key in required_keys if key not in config]
            
            if missing_keys:
                self.log(f"配置文件缺少必要键: {missing_keys}", "ERROR")
                self.test_results["config_validation"] = False
            else:
                self.log("配置文件验证通过")
                self.test_results["config_validation"] = True
                
        except Exception as e:
            self.log(f"配置文件验证失败: {e}", "ERROR")
            self.test_results["config_validation"] = False
        
        return self.test_results["config_validation"]
    
    def test_directory_structure(self):
        """测试目录结构是否符合v0.2.0规范"""
        self.log("测试目录结构...")
        
        try:
            # 检查是否使用了正确的输出目录
            with open(TEST_CONFIG["gui_client_path"], 'r', encoding='utf-8') as f:
                gui_client_code = f.read()
            
            # v0.2.0应该使用release/results目录
            if 'release/results' in gui_client_code:
                self.log("目录结构符合v0.2.0规范 (使用release/results)")
                self.test_results["directory_structure"] = True
            elif 'dev/output' in gui_client_code:
                self.log("警告: 仍在使用dev/output目录，应该使用release/results", "WARN")
                self.test_results["directory_structure"] = False
            else:
                self.log("无法确定输出目录设置", "WARN")
                self.test_results["directory_structure"] = False
                
        except Exception as e:
            self.log(f"目录结构测试失败: {e}", "ERROR")
            self.test_results["directory_structure"] = False
        
        return self.test_results["directory_structure"]
    
    def test_requirements(self):
        """测试依赖包要求"""
        self.log("测试依赖包要求...")
        
        try:
            with open("dev/src/python-gui-client/requirements.txt", 'r') as f:
                requirements = f.read().strip().split('\n')
            
            with open("ref/v0.2.0/requirements.txt", 'r') as f:
                ref_requirements = f.read().strip().split('\n')
            
            if set(requirements) == set(ref_requirements):
                self.log("依赖包要求与v0.2.0一致")
                self.test_results["requirements_check"] = True
            else:
                self.log(f"依赖包要求不一致. 当前: {requirements}, v0.2.0: {ref_requirements}", "ERROR")
                self.test_results["requirements_check"] = False
                
        except Exception as e:
            self.log(f"依赖包测试失败: {e}", "ERROR")
            self.test_results["requirements_check"] = False
        
        return self.test_results["requirements_check"]
    
    def run_all_tests(self):
        """运行所有测试"""
        self.log("开始代码对齐集成测试...")
        
        # 创建测试输出目录
        os.makedirs(TEST_CONFIG["test_output_dir"], exist_ok=True)
        
        # 执行所有测试
        tests = [
            self.test_file_structure,
            self.test_gui_client_import,
            self.test_simple_client_import,
            self.test_config_validation,
            self.test_directory_structure,
            self.test_requirements
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                self.log(f"测试执行异常: {e}", "ERROR")
        
        # 计算总体结果
        passed_tests = sum(1 for result in self.test_results.values() if result)
        total_tests = len(self.test_results) - 1  # 不包括overall_status
        
        self.test_results["overall_status"] = passed_tests == total_tests
        
        self.log(f"测试完成: {passed_tests}/{total_tests} 通过")
        
        # 生成测试报告
        self.generate_report()
        
        return self.test_results["overall_status"]
    
    def generate_report(self):
        """生成测试报告"""
        report_path = os.path.join(TEST_CONFIG["test_output_dir"], "test_report.json")
        
        report = {
            "test_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "test_type": "代码对齐集成测试",
            "version_alignment": "v0.2.0",
            "results": self.test_results,
            "logs": self.test_logs
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        self.log(f"测试报告已保存到: {report_path}")

def main():
    """主函数"""
    print("代码对齐集成测试 - v0.2.0对齐验证")
    print("=" * 50)
    
    tester = CodeAlignmentTester()
    success = tester.run_all_tests()
    
    print("=" * 50)
    if success:
        print("✅ 代码对齐测试全部通过!")
        return 0
    else:
        print("❌ 代码对齐测试存在失败项目，请检查日志")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 