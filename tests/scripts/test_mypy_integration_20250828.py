#!/usr/bin/env python3
"""mypy 集成最小验证：

- 仅对 run_lints.py 与本文件执行 mypy 检查，预期通过。
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


def test_mypy_minimal() -> None:
    """仅验证 mypy 在最小范围内可以通过。"""
    rc = run(
        [
            sys.executable,
            "src/tools/run_lints.py",
            "--mypy-only",
            "--paths",
            "src/tools/run_lints.py",
            "tests/scripts/test_mypy_integration_20250828.py",
        ]
    )
    assert rc == 0


if __name__ == "__main__":
    test_mypy_minimal()
