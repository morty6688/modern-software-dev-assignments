# Assignments for CS146S: The Modern Software Developer

This is the home of the assignments for [CS146S: The Modern Software Developer](https://themodernsoftware.dev), taught at Stanford University fall 2026.

## Repo Setup
These steps work with Python 3.12.

1. Install Anaconda
   - Download and install: [Anaconda Individual Edition](https://www.anaconda.com/download)
   - Open a new terminal so `conda` is on your `PATH`.

2. Create and activate a Conda environment (Python 3.12)
   ```bash
   conda create -n cs146s python=3.12 -y
   conda activate cs146s
   ```

3. Install Poetry
   ```bash
   curl -sSL https://install.python-poetry.org | python -
   ```

4. Install project dependencies with Poetry (inside the activated Conda env)
   From the repository root:
   ```bash
   poetry install --no-interaction
   ```

## 个人作业记录
### week1 
为了方便中文用户，改用 mimo-cli 来重写 assignment 文档。并基于 mimo 完成 report。

### week2
将 GitHub Issues API 封装为 Python MCP Server，重点验证工具接口设计、OAuth 授权与刷新、Agent 调用行为以及可追踪日志。客户端使用 Codex CLI 进行测试。

### week3
实现 `bug-reproduction` skill。以 `iamkun/dayjs` 的发布版本 **1.11.23** 完成未使用 Skill 的基线调查，再以 Day.js 和 Lodash 的独立调查验证 Skill 的端到端工作流。
