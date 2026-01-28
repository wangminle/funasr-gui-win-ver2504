#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：验证演示文件路径更新的功能

测试目标：
1. 验证新的路径配置是否正确
2. 确认测试文件能够被正确找到
3. 测试路径解析的各种场景

创建时间：2025年8月28日
"""

import os
import sys
import unittest

# 添加src目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
src_dir = os.path.join(project_root, 'src', 'python-gui-client')
sys.path.insert(0, src_dir)


class TestDemoPathUpdate(unittest.TestCase):
    """演示文件路径更新测试类"""
    
    def setUp(self):
        """测试初始化"""
        self.project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
        self.demo_dir = os.path.join(self.project_root, 'resources', 'demo')
        self.mp4_file = os.path.join(self.demo_dir, 'tv-report-1.mp4')
        self.wav_file = os.path.join(self.demo_dir, 'tv-report-1.wav')
        
    def test_demo_directory_exists(self):
        """测试演示目录是否存在"""
        self.assertTrue(os.path.exists(self.demo_dir), 
                       f"演示目录不存在: {self.demo_dir}")
        self.assertTrue(os.path.isdir(self.demo_dir), 
                       f"演示路径不是目录: {self.demo_dir}")
        
    def test_demo_files_exist(self):
        """测试演示文件是否存在"""
        self.assertTrue(os.path.exists(self.mp4_file), 
                       f"MP4文件不存在: {self.mp4_file}")
        self.assertTrue(os.path.exists(self.wav_file), 
                       f"WAV文件不存在: {self.wav_file}")
        
    def test_demo_files_readable(self):
        """测试演示文件是否可读"""
        self.assertTrue(os.access(self.mp4_file, os.R_OK), 
                       f"MP4文件不可读: {self.mp4_file}")
        self.assertTrue(os.access(self.wav_file, os.R_OK), 
                       f"WAV文件不可读: {self.wav_file}")
        
    def test_demo_files_size(self):
        """测试演示文件大小"""
        mp4_size = os.path.getsize(self.mp4_file)
        wav_size = os.path.getsize(self.wav_file)
        
        # 文件大小应该大于0
        self.assertGreater(mp4_size, 0, f"MP4文件大小为0: {self.mp4_file}")
        self.assertGreater(wav_size, 0, f"WAV文件大小为0: {self.wav_file}")
        
        # 根据实际文件大小进行合理性检查
        self.assertGreater(mp4_size, 1024*1024, "MP4文件大小应该大于1MB")  # MP4应该较大
        self.assertGreater(wav_size, 1024*1024, "WAV文件大小应该大于1MB")  # WAV也应该较大
        
        print(f"MP4文件大小: {mp4_size/1024/1024:.2f}MB")
        print(f"WAV文件大小: {wav_size/1024/1024:.2f}MB")
        
    def test_path_construction_logic(self):
        """测试路径构建逻辑"""
        # 模拟GUI客户端中的路径构建逻辑
        current_file_dir = src_dir  # 模拟当前文件所在目录
        project_root_simulated = os.path.abspath(os.path.join(current_file_dir, '..', '..'))
        demo_dir_simulated = os.path.join(project_root_simulated, 'resources', 'demo')
        
        # 验证模拟的路径与实际路径一致
        self.assertEqual(demo_dir_simulated, self.demo_dir, 
                        "模拟的路径构建逻辑与实际路径不一致")
        
    def test_old_path_not_exists(self):
        """测试旧路径确实不存在（确保迁移完成）"""
        old_demo_dir = os.path.join(self.project_root, 'dev', 'demo')
        old_mp4_file = os.path.join(old_demo_dir, 'tv-report-1.mp4')
        old_wav_file = os.path.join(old_demo_dir, 'tv-report-1.wav')
        
        # 旧路径应该不存在或者不包含文件
        if os.path.exists(old_demo_dir):
            self.assertFalse(os.path.exists(old_mp4_file), 
                           f"旧MP4文件仍然存在: {old_mp4_file}")
            self.assertFalse(os.path.exists(old_wav_file), 
                           f"旧WAV文件仍然存在: {old_wav_file}")


def run_tests():
    """运行所有测试"""
    print("="*60)
    print("演示文件路径更新测试开始")
    print("="*60)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestDemoPathUpdate)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print(f"运行测试数量: {result.testsRun}")
    print(f"失败测试数量: {len(result.failures)}")
    print(f"错误测试数量: {len(result.errors)}")
    
    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\n测试结果: {'✅ 通过' if success else '❌ 失败'}")
    
    return success


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
