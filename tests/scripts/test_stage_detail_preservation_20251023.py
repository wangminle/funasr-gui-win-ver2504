#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：StatusManager.set_stage 方法的 detail 参数保留功能测试

测试目标：
1. 验证 STAGE_PREPARING 阶段能正确显示 ETA 信息
2. 验证 STAGE_CONNECTING 阶段能正确显示服务器信息
3. 验证其他阶段的 detail 参数正常工作
4. 验证空 detail 参数不会导致异常

创建时间：2025-10-23
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock

# 添加 src 目录到路径
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "../../src/python-gui-client"
        )
    )
)


class TestStageDetailPreservation(unittest.TestCase):
    """测试 StatusManager 的 stage detail 保留功能"""

    def setUp(self):
        """设置测试环境"""
        # Mock tkinter 组件
        with patch("tkinter.Tk"), \
             patch("tkinter.ttk.Frame"), \
             patch("tkinter.ttk.Label"), \
             patch("tkinter.ttk.Button"):
            
            # 导入模块
            import funasr_gui_client_v2
            
            # 创建 mock 的 status_var 和 status_bar
            self.mock_status_var = Mock()
            self.mock_status_var.set = Mock()
            
            self.mock_status_bar = Mock()
            self.mock_status_bar.config = Mock()
            
            # 创建 LanguageManager 实例
            self.lang_manager = funasr_gui_client_v2.LanguageManager()
            
            # 创建 StatusManager 实例
            self.status_manager = funasr_gui_client_v2.StatusManager(
                self.mock_status_var,
                self.mock_status_bar,
                self.lang_manager
            )

    def test_stage_preparing_with_eta(self):
        """测试准备阶段显示 ETA 信息"""
        print("\n测试1: STAGE_PREPARING 显示 ETA 信息")
        
        # 模拟带 ETA 的准备阶段
        eta_detail = "预计2分30秒"
        self.status_manager.set_stage(
            self.status_manager.STAGE_PREPARING,
            eta_detail
        )
        
        # 验证 status_var.set 被调用
        self.mock_status_var.set.assert_called()
        
        # 获取传递给 set 的参数
        call_args = self.mock_status_var.set.call_args
        status_text = call_args[0][0] if call_args and call_args[0] else ""
        
        # 验证 ETA 信息在状态文本中
        print(f"  状态文本: {status_text}")
        self.assertIn(eta_detail, status_text, 
                     f"状态文本应包含 ETA 信息 '{eta_detail}'")
        
        # 验证包含准备任务的提示
        self.assertIn("准备识别任务", status_text,
                     "状态文本应包含'准备识别任务'")
        
        print("  ✓ ETA 信息正确显示")

    def test_stage_preparing_without_detail(self):
        """测试准备阶段不带 detail 参数"""
        print("\n测试2: STAGE_PREPARING 不带 detail 参数")
        
        # 不传递 detail 参数
        self.status_manager.set_stage(self.status_manager.STAGE_PREPARING)
        
        # 验证不会抛出异常
        self.mock_status_var.set.assert_called()
        
        call_args = self.mock_status_var.set.call_args
        status_text = call_args[0][0] if call_args and call_args[0] else ""
        
        print(f"  状态文本: {status_text}")
        self.assertIn("准备识别任务", status_text)
        
        print("  ✓ 无 detail 参数时正常工作")

    def test_stage_connecting_with_server_info(self):
        """测试连接阶段显示服务器信息"""
        print("\n测试3: STAGE_CONNECTING 显示服务器信息")
        
        # 模拟带服务器信息的连接阶段
        server_detail = "127.0.0.1:10095 (SSL: 否)"
        self.status_manager.set_stage(
            self.status_manager.STAGE_CONNECTING,
            server_detail
        )
        
        # 验证 status_var.set 被调用
        self.mock_status_var.set.assert_called()
        
        # 获取传递给 set 的参数
        call_args = self.mock_status_var.set.call_args
        status_text = call_args[0][0] if call_args and call_args[0] else ""
        
        # 验证服务器信息在状态文本中
        print(f"  状态文本: {status_text}")
        self.assertIn(server_detail, status_text,
                     f"状态文本应包含服务器信息 '{server_detail}'")
        
        # 验证包含连接服务器的提示
        self.assertIn("连接服务器", status_text,
                     "状态文本应包含'连接服务器'")
        
        print("  ✓ 服务器信息正确显示")

    def test_stage_connecting_without_detail(self):
        """测试连接阶段不带 detail 参数"""
        print("\n测试4: STAGE_CONNECTING 不带 detail 参数")
        
        # 不传递 detail 参数
        self.status_manager.set_stage(self.status_manager.STAGE_CONNECTING)
        
        # 验证不会抛出异常
        self.mock_status_var.set.assert_called()
        
        call_args = self.mock_status_var.set.call_args
        status_text = call_args[0][0] if call_args and call_args[0] else ""
        
        print(f"  状态文本: {status_text}")
        self.assertIn("连接服务器", status_text)
        
        print("  ✓ 无 detail 参数时正常工作")

    def test_stage_reading_file_with_filename(self):
        """测试读取文件阶段显示文件名"""
        print("\n测试5: STAGE_READING_FILE 显示文件名")
        
        filename = "test_audio.wav"
        self.status_manager.set_stage(
            self.status_manager.STAGE_READING_FILE,
            filename
        )
        
        call_args = self.mock_status_var.set.call_args
        status_text = call_args[0][0] if call_args and call_args[0] else ""
        
        print(f"  状态文本: {status_text}")
        self.assertIn(filename, status_text,
                     f"状态文本应包含文件名 '{filename}'")
        
        print("  ✓ 文件名正确显示")

    def test_stage_uploading_with_progress(self):
        """测试上传阶段显示进度"""
        print("\n测试6: STAGE_UPLOADING 显示上传进度")
        
        progress = "45%"
        self.status_manager.set_stage(
            self.status_manager.STAGE_UPLOADING,
            progress
        )
        
        call_args = self.mock_status_var.set.call_args
        status_text = call_args[0][0] if call_args and call_args[0] else ""
        
        print(f"  状态文本: {status_text}")
        self.assertIn(progress, status_text,
                     f"状态文本应包含进度 '{progress}'")
        
        print("  ✓ 上传进度正确显示")

    def test_stage_completed_with_result(self):
        """测试完成阶段显示结果信息"""
        print("\n测试7: STAGE_COMPLETED 显示结果信息")
        
        result_info = " (1分30秒)"
        self.status_manager.set_stage(
            self.status_manager.STAGE_COMPLETED,
            result_info
        )
        
        call_args = self.mock_status_var.set.call_args
        status_text = call_args[0][0] if call_args and call_args[0] else ""
        
        print(f"  状态文本: {status_text}")
        self.assertIn("识别完成", status_text)
        self.assertIn(result_info, status_text,
                     f"状态文本应包含结果信息 '{result_info}'")
        
        print("  ✓ 结果信息正确显示")

    def test_language_switch_preserves_detail(self):
        """测试语言切换后 detail 信息仍然保留"""
        print("\n测试8: 语言切换后 detail 信息保留")
        
        # 设置中文状态（默认就是中文）
        eta_detail = "预计3分钟"
        self.status_manager.set_stage(
            self.status_manager.STAGE_PREPARING,
            eta_detail
        )
        
        call_args = self.mock_status_var.set.call_args
        status_text_zh = call_args[0][0] if call_args and call_args[0] else ""
        
        print(f"  中文状态: {status_text_zh}")
        self.assertIn(eta_detail, status_text_zh)
        self.assertIn("准备识别任务", status_text_zh)
        
        # 切换到英文
        self.lang_manager.switch_language()
        self.status_manager.set_stage(
            self.status_manager.STAGE_PREPARING,
            eta_detail
        )
        
        call_args = self.mock_status_var.set.call_args
        status_text_en = call_args[0][0] if call_args and call_args[0] else ""
        
        print(f"  英文状态: {status_text_en}")
        self.assertIn(eta_detail, status_text_en)
        self.assertIn("Preparing", status_text_en)
        
        print("  ✓ 语言切换后 detail 信息正确保留")


def run_tests():
    """运行所有测试"""
    print("=" * 70)
    print("StatusManager Stage Detail 保留功能测试")
    print("=" * 70)
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestStageDetailPreservation)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 打印测试总结
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)
    print(f"运行测试: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✓ 所有测试通过！")
        return 0
    else:
        print("\n✗ 部分测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())

