#!/usr/bin/env python3
"""简单的一键 Lint/Type 运行脚本：black、isort、flake8、mypy。

用法：
    - 仅检查（默认）：python3 src/tools/run_lints.py [--paths 路径 ...]
    - 自动修复（black/isort）：python3 src/tools/run_lints.py --fix [--paths 路径 ...]
    - 仅运行 mypy：python3 src/tools/run_lints.py --mypy-only [--paths 路径 ...]

说明：
    - 配置文件放在 dev/config/ 下：
      pyproject.toml（black/isort）、flake8.ini（flake8）、mypy.ini（mypy）。
    - 默认检测目标包含 src 与 tests 目录；也可通过 --paths 自定义目标。
    - 本脚本会将执行日志记录到 dev/logs/lint_runner.log。
"""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from pathlib import Path
from typing import List, TypedDict


class ProjectPaths(TypedDict):
    """项目路径映射的类型定义。"""

    root: Path
    dev: Path
    config: Path
    logs: Path
    targets: List[Path]


def resolve_project_paths() -> ProjectPaths:
    """解析项目关键路径。

    返回字典包含：root、dev、config、logs，以及默认检测的 targets。
    """
    script_path = Path(__file__).resolve()
    # 布局：<root>/src/tools/run_lints.py → 根目录为 parents[2]
    root_dir = script_path.parents[2]
    dev_dir = root_dir / "dev"
    config_dir = dev_dir / "config"
    logs_dir = dev_dir / "logs"
    default_targets = [root_dir / "src", root_dir / "tests"]

    return {
        "root": root_dir,
        "dev": dev_dir,
        "config": config_dir,
        "logs": logs_dir,
        "targets": [p for p in default_targets if p.exists()],
    }


def setup_logging(log_file: Path) -> None:
    """初始化日志记录，输出到文件与控制台。"""
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


def run_command(command: List[str], cwd: Path) -> int:
    """在指定目录下执行命令并实时输出，返回退出码。"""
    logging.info("执行命令: %s", " ".join(command))
    try:
        process = subprocess.run(
            command,
            cwd=str(cwd),
            stdout=sys.stdout,
            stderr=sys.stderr,
            check=False,
        )
        return int(process.returncode or 0)
    except FileNotFoundError:
        logging.error("未找到命令，可尝试先安装依赖：%s", command[0])
        return 127


def ensure_paths_exist(paths: List[Path]) -> List[Path]:
    """过滤不存在的路径并按路径字符串升序排序。"""
    existing = [p for p in paths if p.exists()]
    return sorted(existing, key=lambda p: str(p))


def build_commands(
    config_dir: Path, targets: List[Path], apply_fix: bool, mypy_only: bool
) -> list[tuple[str, list[str]]]:
    """构建 black/isort/flake8 的命令列表。"""
    pyproject = config_dir / "pyproject.toml"
    flake8_ini = config_dir / "flake8.ini"

    target_args = [str(p) for p in targets]

    # black 支持 --config 指定 pyproject.toml
    black_cmd = ["black", "--config", str(pyproject)]
    if not apply_fix:
        black_cmd += ["--check", "--diff"]
    black_cmd += target_args

    # isort 支持 --settings-path 指定 pyproject.toml
    isort_cmd = ["isort", "--settings-path", str(pyproject)]
    if not apply_fix:
        isort_cmd += ["--check-only", "--diff"]
    isort_cmd += target_args

    # flake8 使用独立配置文件
    flake8_cmd = ["flake8", "--config", str(flake8_ini)] + target_args

    # mypy 使用独立配置文件
    mypy_ini = config_dir / "mypy.ini"
    mypy_cmd = ["mypy", "--config-file", str(mypy_ini)] + target_args

    if mypy_only:
        return [("mypy", mypy_cmd)]

    return [
        ("black", black_cmd),
        ("isort", isort_cmd),
        ("flake8", flake8_cmd),
        ("mypy", mypy_cmd),
    ]


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="运行 black/isort/flake8 的简单工具",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="自动修复（black 和 isort），flake8 仅检查",
    )
    parser.add_argument(
        "--mypy-only",
        action="store_true",
        help="仅运行 mypy 类型检查",
    )
    parser.add_argument(
        "--paths",
        nargs="+",
        default=None,
        help="指定需要检查/修复的路径（默认：dev/src 与 tests）",
    )
    return parser.parse_args()


def main() -> int:
    """脚本主入口。"""
    args = parse_args()
    paths = resolve_project_paths()

    setup_logging(paths["logs"] / "lint_runner.log")
    logging.info("Lint 开始，模式：%s", "修复" if args.fix else "仅检查")

    if args.paths:
        target_paths = [Path(p).resolve() for p in args.paths]
    else:
        target_paths = paths["targets"]

    target_paths = ensure_paths_exist(target_paths)
    if not target_paths:
        logging.error("未找到任何有效目标路径，请检查 --paths 或项目结构。")
        return 2

    commands = build_commands(paths["config"], target_paths, args.fix, args.mypy_only)

    overall_rc = 0
    for name, cmd in commands:
        logging.info("开始执行：%s", name)
        rc = run_command(cmd, cwd=paths["root"])
        if rc != 0:
            logging.warning("%s 发现问题（退出码=%s）", name, rc)
            overall_rc = rc if overall_rc == 0 else overall_rc
        else:
            logging.info("%s 完成且未发现问题", name)

    logging.info(
        "Lint 结束：%s",
        "通过" if overall_rc == 0 else f"存在问题（退出码={overall_rc}）",
    )
    return overall_rc


if __name__ == "__main__":
    sys.exit(main())
