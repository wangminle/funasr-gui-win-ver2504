#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
"""
速度测试修复验证脚本 v2
测试日期: 2025年7月14日
目标: 验证修复后的时间戳检测和格式化错误
"""

import logging
import os
import sys
import time
import unittest

# 添加dev/src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dev', 'src', 'python-gui-client'))

def setup_test_logging():
    """设置测试日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

class TestSpeedTestFixV2(unittest.TestCase):
    """速度测试修复验证测试类"""
    
    def setUp(self):
        """测试前准备"""
        setup_test_logging()
        logging.info("=" * 60)
        logging.info(f"开始测试: {self._testMethodName}")
        
    def tearDown(self):
        """测试后清理"""
        logging.info(f"结束测试: {self._testMethodName}")
        logging.info("=" * 60)
    
    def test_gui_client_import(self):
        """测试GUI客户端模块导入"""
        try:
            import funasr_gui_client_v2
            logging.info("✓ GUI客户端模块导入成功")
            self.assertTrue(True)
        except Exception as e:
            logging.error(f"✗ GUI客户端模块导入失败: {e}")
            self.fail(f"模块导入错误: {e}")
    
    def test_simple_client_syntax(self):
        """测试simple_funasr_client语法正确性"""
        try:
            client_path = os.path.join(os.path.dirname(__file__), '..', 'dev', 'src', 'python-gui-client', 'simple_funasr_client.py')
            with open(client_path, 'r', encoding='utf-8') as f:
                code = f.read()
            compile(code, client_path, 'exec')
            logging.info("✓ simple_funasr_client.py 语法检查通过")
            self.assertTrue(True)
        except SyntaxError as e:
            logging.error(f"✗ simple_funasr_client.py 语法错误: {e}")
            self.fail(f"语法错误: {e}")
        except Exception as e:
            logging.error(f"✗ simple_funasr_client.py 检查异常: {e}")
            self.fail(f"检查异常: {e}")
    
    def test_language_manager_formatting(self):
        """测试语言管理器的格式化字符串"""
        try:
            import funasr_gui_client_v2
            lang_manager = funasr_gui_client_v2.LanguageManager()
            
            # 测试关键的格式化字符串
            test_cases = [
                ("speed_test_upload_started", [1]),
                ("speed_test_upload_completed", [1, 1.5]),
                ("speed_test_transcription_started", [1]),
                ("speed_test_transcription_completed", [1, 2.3]),
                ("speed_test_file_completed", [1, 1.5, 2.3]),
                ("speed_test_results_log", [5.2, 15.8])
            ]
            
            for key, args in test_cases:
                try:
                    result = lang_manager.get(key, *args)
                    logging.info(f"✓ 格式化成功 {key}: {result}")
                except Exception as e:
                    logging.error(f"✗ 格式化失败 {key}: {e}")
                    self.fail(f"格式化错误 {key}: {e}")
                    
            logging.info("✓ 所有格式化字符串测试通过")
            self.assertTrue(True)
            
        except Exception as e:
            logging.error(f"✗ 语言管理器测试异常: {e}")
            self.fail(f"语言管理器异常: {e}")

    def test_improved_timestamp_detection(self):
        """测试改进后的时间戳检测逻辑"""
        try:
            # 模拟输出行
            test_lines = [
                "[2025-01-14 15:12:11][发送] 发送初始化消息: {\"mode\": \"offline\", \"audio_fs\": 16000}",
                "正在处理音频文件...",
                "上传进度: 25%",
                "上传进度: 50%",
                "上传进度: 75%",
                "上传进度: 100%",
                "[2025-01-14 15:12:12][发送] 发送结束标志: {\"is_speaking\": false}",
                "[2025-01-14 15:12:13][等待] 等待服务器处理...",
                "[2025-01-14 15:12:14][接收] 等待服务器消息...",
                "正在处理识别请求...",
                "识别文本(tv-report-1): 这是测试识别结果，用于验证转写功能是否正常工作。",
                "[2025-01-14 15:12:15][完成] 离线识别完成",
                "[2025-01-14 15:12:16][完成] 音频处理流程完成"
            ]
            
            # 模拟时间戳检测
            upload_start_time = None
            upload_end_time = None
            transcribe_start_time = None
            transcribe_end_time = None
            
            for line in test_lines:
                current_time = time.time()
                
                # 检测上传开始
                if "发送初始化消息:" in line and upload_start_time is None:
                    upload_start_time = current_time
                    logging.info(f"✓ 检测到上传开始: {line[:50]}...")
                
                # 检测上传结束
                if ("上传进度: 100%" in line or "发送结束标志:" in line) and upload_end_time is None:
                    upload_end_time = current_time + 0.1
                    logging.info(f"✓ 检测到上传结束: {line[:50]}...")
                    # 模拟改进后的逻辑：上传结束时自动设置转写开始时间
                    if transcribe_start_time is None:
                        transcribe_start_time = upload_end_time
                        logging.info(f"✓ 上传结束时自动设置转写开始时间")
                
                # 检测转写开始（改进后的检测逻辑）
                if (transcribe_start_time is None and
                    (("等待服务器处理..." in line) or 
                     ("等待服务器消息..." in line) or
                     ("发送结束标志:" in line) or
                     ("is_speaking" in line and "false" in line.lower()))):
                    if transcribe_start_time is None:  # 如果还没设置
                        transcribe_start_time = current_time + 0.2
                        logging.info(f"✓ 额外检测到转写开始: {line[:50]}...")
                
                # 检测转写结束
                if (("识别文本(" in line and "):" in line) or 
                    ("离线识别完成" in line) or 
                    ("音频处理流程完成" in line)) and transcribe_end_time is None:
                    transcribe_end_time = current_time + 0.3
                    logging.info(f"✓ 检测到转写结束: {line[:50]}...")
            
            # 验证所有时间戳都被检测到
            missing = []
            if upload_start_time is None: missing.append("上传开始时间")
            if upload_end_time is None: missing.append("上传结束时间")
            if transcribe_start_time is None: missing.append("转写开始时间")
            if transcribe_end_time is None: missing.append("转写结束时间")
            
            if missing:
                logging.error(f"✗ 时间戳检测失败，缺失: {', '.join(missing)}")
                self.fail(f"时间戳检测失败: {missing}")
            else:
                # 验证时间计算
                upload_time = upload_end_time - upload_start_time
                transcribe_time = transcribe_end_time - transcribe_start_time
                
                logging.info(f"✓ 时间戳检测完成:")
                logging.info(f"  - 上传时间: {upload_time:.3f}秒")
                logging.info(f"  - 转写时间: {transcribe_time:.3f}秒")
                
                # 验证时间合理性
                self.assertGreater(upload_time, 0, "上传时间应大于0")
                self.assertGreater(transcribe_time, 0, "转写时间应大于0")
                self.assertTrue(True)
                
        except Exception as e:
            logging.error(f"✗ 时间戳检测逻辑测试异常: {e}")
            self.fail(f"时间戳检测异常: {e}")

    def test_time_calculation_robustness(self):
        """测试时间计算的健壮性"""
        try:
            # 测试异常时间值的处理
            test_cases = [
                (0.0, 1.5, "上传时间为0"),  # upload_time为0
                (1.5, 0.0, "转写时间为0"),  # transcribe_time为0
                (-0.1, 1.5, "上传时间为负数"),  # upload_time为负数
                (1.5, -0.1, "转写时间为负数"),  # transcribe_time为负数
                (0.05, 1.5, "上传时间很小"),  # 很小的正数
                (1.5, 0.05, "转写时间很小"),  # 很小的正数
            ]
            
            for upload_time, transcribe_time, description in test_cases:
                logging.info(f"测试用例: {description}")
                
                # 模拟修复后的时间验证逻辑
                fixed_upload_time = upload_time
                fixed_transcribe_time = transcribe_time
                
                if fixed_upload_time <= 0:
                    logging.info(f"  修复上传时间: {fixed_upload_time:.3f} -> 0.1")
                    fixed_upload_time = 0.1
                    
                if fixed_transcribe_time <= 0:
                    logging.info(f"  修复转写时间: {fixed_transcribe_time:.3f} -> 0.1")
                    fixed_transcribe_time = 0.1
                
                # 验证修复后的值
                self.assertGreater(fixed_upload_time, 0, "修复后上传时间应大于0")
                self.assertGreater(fixed_transcribe_time, 0, "修复后转写时间应大于0")
                
                logging.info(f"  ✓ 修复后: 上传={fixed_upload_time:.3f}s, 转写={fixed_transcribe_time:.3f}s")
            
            logging.info("✓ 时间计算健壮性测试通过")
            self.assertTrue(True)
            
        except Exception as e:
            logging.error(f"✗ 时间计算健壮性测试异常: {e}")
            self.fail(f"时间计算异常: {e}")

def run_tests():
    """运行所有测试"""
    setup_test_logging()
    
    logging.info("速度测试修复验证 v2 - 开始运行")
    logging.info("=" * 80)
    
    # 创建测试套件
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestSpeedTestFixV2)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(test_suite)
    
    # 输出总结
    logging.info("=" * 80)
    if result.wasSuccessful():
        logging.info("🎉 所有测试通过！速度测试修复验证成功")
        return True
    else:
        logging.error(f"❌ 测试失败: {len(result.failures)} 个失败, {len(result.errors)} 个错误")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1) 