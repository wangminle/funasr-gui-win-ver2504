#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试demo目录路径修改验证脚本
测试日期: 2025-01-15
功能: 验证测试文件路径修改是否正确
"""

import sys
from pathlib import Path


def test_demo_path_fix():
    """测试demo路径修改是否正确"""
    print("=== Demo路径修改验证测试 ===")

    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    print(f"项目根目录: {project_root}")

    # 测试新的 demo 目录路径（迁移到 @resources/demo）
    new_demo_dir = project_root / "@resources" / "demo"
    print(f"新的demo目录: {new_demo_dir}")

    # 检查目录是否存在
    if new_demo_dir.exists():
        print("✅ dev/demo 目录存在")
    else:
        print("❌ dev/demo 目录不存在")
        return False

    # 检查测试文件是否存在
    test_files = ["tv-report-1.mp4", "tv-report-1.wav"]
    all_files_exist = True

    for file_name in test_files:
        file_path = new_demo_dir / file_name
        if file_path.exists():
            file_size = file_path.stat().st_size
            print(f"✅ {file_name} 存在 (大小: {file_size:,} 字节)")
        else:
            print(f"❌ {file_name} 不存在")
            all_files_exist = False

    # 测试旧路径是否还存在文件
    old_demo_dir = project_root / "dev" / "demo"
    if old_demo_dir.exists():
        print(f"⚠️  旧的demo目录仍存在: {old_demo_dir}")
        for file_name in test_files:
            old_file_path = old_demo_dir / file_name
            if old_file_path.exists():
                print(f"⚠️  旧位置仍有文件: {old_file_path}")
    else:
        print("✅ 旧的demo目录已清理")

    return all_files_exist


def test_gui_client_import():
    """测试GUI客户端是否能正确导入并找到demo文件"""
    print("\n=== GUI客户端demo路径测试 ===")

    try:
        # 添加 src 路径到 sys.path
        project_root = Path(__file__).parent.parent
        src_path = project_root / "src" / "python-gui-client"
        sys.path.insert(0, str(src_path))

        # 模拟 GUI 客户端的路径计算
        current_dir = src_path
        calculated_project_root = (
            current_dir.parent.parent
        )  # python-gui-client -> src -> root
        demo_dir = calculated_project_root / "@resources" / "demo"

        print(f"计算出的项目根目录: {calculated_project_root}")
        print(f"计算出的demo目录: {demo_dir}")

        # 检查路径是否正确
        mp4_file = demo_dir / "tv-report-1.mp4"
        wav_file = demo_dir / "tv-report-1.wav"

        if mp4_file.exists() and wav_file.exists():
            print("✅ GUI客户端能正确找到测试文件")
            return True
        else:
            print("❌ GUI客户端无法找到测试文件")
            print(f"MP4文件存在: {mp4_file.exists()}")
            print(f"WAV文件存在: {wav_file.exists()}")
            return False

    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        return False


if __name__ == "__main__":
    print("开始验证demo目录路径修改...")

    # 运行测试
    test1_passed = test_demo_path_fix()
    test2_passed = test_gui_client_import()

    print("\n=== 测试结果总结 ===")
    print(f"demo路径验证: {'✅ 通过' if test1_passed else '❌ 失败'}")
    print(f"GUI客户端路径测试: {'✅ 通过' if test2_passed else '❌ 失败'}")

    if test1_passed and test2_passed:
        print("🎉 所有测试通过！demo目录路径修改成功。")
    else:
        print("⚠️  部分测试失败，请检查路径配置。")
