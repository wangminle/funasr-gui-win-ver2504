#!/usr/bin/env python3
"""lint 脚本基础自测：验证帮助信息与最小路径检查。

说明：本测试只验证工具链可运行，不强制整个仓库当前即满足规范。
"""

from __future__ import annotations

import subprocess
import sys


def run(cmd: list[str]) -> int:
    """执行命令并返回退出码。"""
    proc = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    print(proc.stdout)
    return int(proc.returncode or 0)


def test_help() -> None:
    """校验 --help 可正常输出并退出码为 0。"""
    rc = run([sys.executable, "src/tools/run_lints.py", "--help"])
    assert rc == 0


def test_minimal_check() -> None:
    """仅对脚本自身与本测试文件执行检查，应当通过。"""
    rc = run(
        [
            sys.executable,
            "src/tools/run_lints.py",
            "--paths",
            "src/tools/run_lints.py",
            "tests/scripts/test_lint_runner.py",
        ]
    )
    assert rc == 0


if __name__ == "__main__":
    test_help()
    test_minimal_check()
