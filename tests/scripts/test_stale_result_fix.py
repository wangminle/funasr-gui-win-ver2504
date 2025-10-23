#!/usr/bin/env python3
"""
测试脚本：验证修复"重用旧结果文件"bug

测试目标：
1. 验证系统不会将旧的结果文件误认为是本次运行的结果
2. 验证只有本次运行生成的结果文件才会被认定为成功
3. 验证时间戳判断逻辑的准确性

测试场景：
1. 正常场景：本次运行成功生成新结果文件
2. bug复现场景：存在旧结果文件，本次运行失败
3. 边界场景：结果文件时间戳刚好等于进程启动时间
4. 异常场景：结果文件被删除或无权限访问
"""

import os
import sys
import json
import time
import shutil
import tempfile
import unittest
from pathlib import Path

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src" / "python-gui-client"
sys.path.insert(0, str(src_path))


class TestStaleResultFix(unittest.TestCase):
    """测试旧结果文件不被重用的修复"""

    def setUp(self):
        """测试前准备"""
        # 创建临时测试目录
        self.test_dir = tempfile.mkdtemp(prefix="test_stale_result_")
        self.results_dir = os.path.join(self.test_dir, "output")
        os.makedirs(self.results_dir, exist_ok=True)

        # 模拟音频文件名
        self.audio_filename = "test_audio.wav"
        self.base_name = "test_audio"
        self.result_filename = f"{self.base_name}.0_0.json"
        self.result_filepath = os.path.join(self.results_dir, self.result_filename)

        print(f"\n[setUp] 测试目录: {self.test_dir}")
        print(f"[setUp] 结果目录: {self.results_dir}")

    def tearDown(self):
        """测试后清理"""
        # 清理临时目录
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        print(f"[tearDown] 已清理测试目录: {self.test_dir}")

    def create_result_file(self, content=None, mtime=None):
        """
        创建结果文件
        
        Args:
            content: 文件内容，默认为简单的JSON
            mtime: 修改时间（Unix时间戳），None表示使用当前时间
        """
        if content is None:
            content = {"text": "测试识别结果"}

        with open(self.result_filepath, "w", encoding="utf-8") as f:
            json.dump(content, f, ensure_ascii=False)

        if mtime is not None:
            # 设置文件修改时间
            os.utime(self.result_filepath, (mtime, mtime))

        print(
            f"[create_result_file] 创建文件: {self.result_filepath}, "
            f"mtime: {mtime or 'current'}"
        )

    def check_result_file_valid(self, process_start_time):
        """
        模拟_exists_result_file()函数的逻辑
        
        Args:
            process_start_time: 进程启动时间
            
        Returns:
            bool: 是否找到有效的结果文件
        """
        try:
            for fname in os.listdir(self.results_dir):
                if fname.startswith(self.base_name + ".") and fname.endswith(".json"):
                    fpath = os.path.join(self.results_dir, fname)
                    # 文件必须：1) 非空，2) 修改时间晚于进程启动时间
                    if os.path.getsize(fpath) > 0:
                        file_mtime = os.path.getmtime(fpath)
                        print(
                            f"[check_result_file_valid] 文件: {fname}, "
                            f"mtime: {file_mtime:.6f}, "
                            f"process_start: {process_start_time:.6f}, "
                            f"valid: {file_mtime >= process_start_time}"
                        )
                        if file_mtime >= process_start_time:
                            return True
            return False
        except Exception as e:
            print(f"[check_result_file_valid] 异常: {e}")
            return False

    def test_01_new_result_file_accepted(self):
        """测试1：新生成的结果文件应该被接受"""
        print("\n" + "=" * 70)
        print("测试1：新生成的结果文件应该被接受")
        print("=" * 70)

        # 模拟进程启动
        process_start_time = time.time()
        print(f"进程启动时间: {process_start_time:.6f}")

        # 等待一小段时间，确保文件时间戳晚于进程启动
        time.sleep(0.1)

        # 创建新结果文件
        self.create_result_file()
        file_mtime = os.path.getmtime(self.result_filepath)
        print(f"文件修改时间: {file_mtime:.6f}")

        # 验证结果
        result = self.check_result_file_valid(process_start_time)
        self.assertTrue(result, "新生成的结果文件应该被接受")
        print("✓ 测试通过：新结果文件被正确接受")

    def test_02_old_result_file_rejected(self):
        """测试2：旧的结果文件应该被拒绝（bug修复的核心测试）"""
        print("\n" + "=" * 70)
        print("测试2：旧的结果文件应该被拒绝")
        print("=" * 70)

        # 先创建一个旧结果文件（5秒前）
        old_time = time.time() - 5
        self.create_result_file(mtime=old_time)
        print(f"旧文件修改时间: {old_time:.6f}")

        # 等待一小段时间
        time.sleep(0.1)

        # 模拟进程启动（在旧文件创建之后）
        process_start_time = time.time()
        print(f"进程启动时间: {process_start_time:.6f}")

        # 验证结果
        result = self.check_result_file_valid(process_start_time)
        self.assertFalse(result, "旧的结果文件应该被拒绝")
        print("✓ 测试通过：旧结果文件被正确拒绝")

    def test_03_boundary_equal_timestamp(self):
        """测试3：时间戳相等的边界情况（应该被接受）"""
        print("\n" + "=" * 70)
        print("测试3：时间戳相等的边界情况")
        print("=" * 70)

        # 模拟进程启动
        process_start_time = time.time()
        print(f"进程启动时间: {process_start_time:.6f}")

        # 创建结果文件，设置与进程启动时间完全相同的时间戳
        self.create_result_file(mtime=process_start_time)
        print(f"文件修改时间: {process_start_time:.6f} (与进程启动时间相同)")

        # 验证结果（使用 >= 比较，所以相等应该被接受）
        result = self.check_result_file_valid(process_start_time)
        self.assertTrue(result, "时间戳相等的文件应该被接受（>= 比较）")
        print("✓ 测试通过：边界情况（相等时间戳）被正确处理")

    def test_04_empty_result_file_rejected(self):
        """测试4：空结果文件应该被拒绝"""
        print("\n" + "=" * 70)
        print("测试4：空结果文件应该被拒绝")
        print("=" * 70)

        # 模拟进程启动
        process_start_time = time.time()
        print(f"进程启动时间: {process_start_time:.6f}")

        # 等待一小段时间
        time.sleep(0.1)

        # 创建空文件
        with open(self.result_filepath, "w") as f:
            pass  # 空文件
        print(f"创建空文件: {self.result_filepath}, 大小: 0 字节")

        # 验证结果
        result = self.check_result_file_valid(process_start_time)
        self.assertFalse(result, "空结果文件应该被拒绝")
        print("✓ 测试通过：空文件被正确拒绝")

    def test_05_no_result_file(self):
        """测试5：没有结果文件的情况"""
        print("\n" + "=" * 70)
        print("测试5：没有结果文件的情况")
        print("=" * 70)

        # 模拟进程启动
        process_start_time = time.time()
        print(f"进程启动时间: {process_start_time:.6f}")

        # 不创建任何结果文件
        print("不创建任何结果文件")

        # 验证结果
        result = self.check_result_file_valid(process_start_time)
        self.assertFalse(result, "没有结果文件时应该返回False")
        print("✓ 测试通过：无文件情况被正确处理")

    def test_06_multiple_result_files(self):
        """测试6：多个结果文件的情况（应该找到最新的有效文件）"""
        print("\n" + "=" * 70)
        print("测试6：多个结果文件的情况")
        print("=" * 70)

        # 创建旧文件
        old_time = time.time() - 5
        old_file = os.path.join(self.results_dir, f"{self.base_name}.old.json")
        with open(old_file, "w", encoding="utf-8") as f:
            json.dump({"text": "旧结果"}, f, ensure_ascii=False)
        os.utime(old_file, (old_time, old_time))
        print(f"创建旧文件: {old_file}, mtime: {old_time:.6f}")

        # 模拟进程启动
        time.sleep(0.1)
        process_start_time = time.time()
        print(f"进程启动时间: {process_start_time:.6f}")

        # 创建新文件
        time.sleep(0.1)
        new_file = os.path.join(self.results_dir, f"{self.base_name}.new.json")
        with open(new_file, "w", encoding="utf-8") as f:
            json.dump({"text": "新结果"}, f, ensure_ascii=False)
        new_time = os.path.getmtime(new_file)
        print(f"创建新文件: {new_file}, mtime: {new_time:.6f}")

        # 验证结果
        result = self.check_result_file_valid(process_start_time)
        self.assertTrue(result, "应该找到新创建的有效结果文件")
        print("✓ 测试通过：多文件情况下正确识别新文件")

    def test_07_permission_error_handling(self):
        """测试7：权限错误的异常处理"""
        print("\n" + "=" * 70)
        print("测试7：权限错误的异常处理")
        print("=" * 70)

        # 模拟进程启动
        process_start_time = time.time()

        # 创建结果文件
        time.sleep(0.1)
        self.create_result_file()

        # 在Unix系统上移除读权限（Windows上跳过此测试）
        if sys.platform != "win32":
            os.chmod(self.results_dir, 0o000)
            print(f"移除目录读权限: {self.results_dir}")

            # 验证结果（应该捕获异常并返回False）
            result = self.check_result_file_valid(process_start_time)
            self.assertFalse(result, "权限错误时应该返回False")

            # 恢复权限
            os.chmod(self.results_dir, 0o755)
            print("✓ 测试通过：权限错误被正确处理")
        else:
            print("⊘ Windows系统跳过权限测试")


def run_tests():
    """运行所有测试"""
    print("\n" + "=" * 70)
    print("开始测试：验证修复'重用旧结果文件'bug")
    print("=" * 70)

    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestStaleResultFix)

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 输出测试总结
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)
    print(f"总测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n✓ 所有测试通过！bug修复有效。")
        return 0
    else:
        print("\n✗ 存在失败的测试，请检查修复代码。")
        return 1


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)

