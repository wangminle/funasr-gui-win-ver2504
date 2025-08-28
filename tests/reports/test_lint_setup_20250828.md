# Lint 接入测试总结（2025-08-28）

- 目标：引入 black、isort、flake8，并提供一键运行脚本。
- 配置位置：`dev/config/pyproject.toml`（black/isort）、`dev/config/flake8.ini`（flake8）
- 运行脚本：`dev/src/tools/run_lints.py`
- 开发依赖：`dev/requirements-dev.txt`

## 安装与环境
- Python：3.12.10（macOS）
- 安装命令：
  - 升级基础工具：`python3 -m pip install --upgrade pip setuptools wheel`
  - 安装依赖：`python3 -m pip install -r dev/requirements-dev.txt`

## 最小范围验证
- 修复并检查：
  - `python3 dev/src/tools/run_lints.py --fix --paths dev/src/tools/run_lints.py tests/scripts/test_lint_runner.py`
- 仅检查：
  - `python3 dev/src/tools/run_lints.py --paths dev/src/tools/run_lints.py tests/scripts/test_lint_runner.py`
- 结论：最小范围通过（black/isort/flake8 均通过）。

## 默认范围验证（dev/src + tests）
- 命令：`python3 dev/src/tools/run_lints.py`
- 结果：flake8 报告大量历史样式问题（E/W/D 类告警），主要集中在 tests 下的历史测试脚本；脚本功能正常。

## 建议与后续
- 阶段性采用 `--paths` 仅对变更文件或小范围目录执行检查；
- 分阶段修复历史样式问题（空行、导入顺序、行宽、docstring 等）。

## 快速使用
```bash
# 安装依赖（一次性）
python3 -m pip install -r dev/requirements-dev.txt

# 全仓库默认检查（仅检查）
python3 dev/src/tools/run_lints.py

# 指定路径并自动修复（black & isort 修复，flake8 仅检查）
python3 dev/src/tools/run_lints.py --fix --paths dev/src tests/scripts/test_lint_runner.py
```

生成时间：2025-08-28
