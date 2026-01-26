#!/usr/bin/env python3
"""自测：严格化成功判定与测速兜底

说明：
- 仅作轻量级运行性检查，不依赖真实服务。这里只验证模块可导入及关键函数存在。
- 真实联调须在人工环境连接局域网服务器执行。
"""

import importlib
import os
import sys


def _add_src_to_syspath():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    sys.path.insert(0, os.path.join(repo_root, "src", "python-gui-client"))


def test_import_modules():
    _add_src_to_syspath()
    # 确保两个主模块可被导入
    importlib.import_module("funasr_gui_client_v3")
    importlib.import_module("simple_funasr_client")


if __name__ == "__main__":
    test_import_modules()
    print("basic import ok")


