# FastAPI Agent Readiness 审计报告

**结论：本地快照的自动化验证、依赖管理和可观测性基础较完整。优先改进回归证明的退出码判断，以及供仓库贡献者使用的本地操作指引。**

> **本报告不是 Factory 官方评分。** 未安装或运行 Droid，仅沿用 [Factory 八个维度](https://factory.com/news/agent-readiness)进行独立静态审计，不给出官方分数或成熟度等级。

- 审计日期：2026-11-01。
- 目录：`D:\project\self\test\cs146s\fastapi`。
- HEAD：`45cb2252c737906f37544f5ba6bee0295fb81468`；源码版本：`0.162.0`。
- `git --no-optional-locks status --short` 成功且无输出；审计时未发现 Git 报告的工作树变更。不证明文件来源可信或远程状态一致。
- 方法：只读检查本地源码、配置、工作流、文档和代表性测试。没有安装依赖、运行检查/测试/构建、访问部署或修改被审计仓库；仅保存本报告。
- **通过**表示存在静态证据，不代表本次执行通过；**缺失**限于注明的检查范围；**Unknown**表示无法验证。P1 为优先解决，P2 为计划改进，P3 为按需完善。

## 1. Style & Validation

| 状态 | 项目与证据 |
|---|---|
| 通过 | [pyproject.toml:224](D:/project/self/test/cs146s/fastapi/pyproject.toml:224)配置 `pydantic.mypy`、`strict = true`，并明确部分模块例外。 |
| 通过 | [scripts/lint.sh:6](D:/project/self/test/cs146s/fastapi/scripts/lint.sh:6)执行 `mypy fastapi`、`ty check`、Ruff lint 和 `ruff format ... --check`。 |
| 通过 | [.pre-commit-config.yaml:25](D:/project/self/test/cs146s/fastapi/.pre-commit-config.yaml:25)包含 Ruff lint/format、mypy、ty；[pre-commit.yml:56](D:/project/self/test/cs146s/fastapi/.github/workflows/pre-commit.yml:56)通过 `prek run` 执行钩子。 |
| 缺失 | Markdown 内嵌代码尚未纳入这些 Ruff 钩子的类型范围：钩子第 32–43 行注释明确待翻译更新后恢复，目前为 `types: python`。这不等于所有文档示例都缺少测试。 |
| Unknown | 当前 lint、格式与类型检查结果，以及例外规则是否全部必要；本次未执行。 |

**P2：**明确文档代码检查的范围和恢复条件，逐步恢复可检查的 Markdown 示例。保留必要教学示例例外，避免为消除告警改变示例语义。

## 2. Build System

| 状态 | 项目与证据 |
|---|---|
| 通过 | [pyproject.toml:1](D:/project/self/test/cs146s/fastapi/pyproject.toml:1)声明 `pdm.backend`；第 211 行起声明版本来源及 sdist 包含 `tests/`、`docs_src/`、`scripts/`。 |
| 通过 | [test-redistribute.yml:26](D:/project/self/test/cs146s/fastapi/.github/workflows/test-redistribute.yml:26)构建 sdist、解压、安装测试依赖、运行源码发行包测试，再由 sdist 构建 wheel。 |
| 通过 | 根目录有 [uv.lock](D:/project/self/test/cs146s/fastapi/uv.lock)，[test.yml:295](D:/project/self/test/cs146s/fastapi/.github/workflows/test.yml:295)存在 `uv sync --locked`。 |
| 缺失 | 上述发行包工作流没有安装最终 wheel 并从仓库外导入的验证；构建出 wheel 不等于 wheel 内容可用。 |
| 缺失 | 发行包构建工具链未完全固定：`requires = ["pdm-backend"]`，发行包 CI 使用 `pip install build`。锁文件不能自动证明这些隔离构建依赖也被固定。 |
| Unknown | 当前构建结果、产物完整性及发布状态；本次未运行构建。 |

**P2：**增加独立环境中的 wheel 安装、CLI/导入及包资源检查；为发行构建记录或约束工具链版本。

## 3. Testing

| 状态 | 项目与证据 |
|---|---|
| 通过 | [scripts/test.sh:6](D:/project/self/test/cs146s/fastapi/scripts/test.sh:6)设置 `PYTHONPATH=./docs_src`，执行 `pytest -n auto --dist loadgroup tests scripts/tests/`。 |
| 通过 | [test.yml:52](D:/project/self/test/cs146s/fastapi/.github/workflows/test.yml:52)包含 Windows、macOS、Ubuntu 以及 Python 3.10、3.12、3.13、3.14/3.14t 的不同组合，并测试 Starlette 源码等兼容场景；不是所有平台与版本的全笛卡尔积。 |
| 通过 | [pyproject.toml:244](D:/project/self/test/cs146s/fastapi/pyproject.toml:244)启用严格配置、严格 marker、警告作为错误和 20 秒超时；[test.yml:311](D:/project/self/test/cs146s/fastapi/.github/workflows/test.yml:311)要求 `coverage report --fail-under=100`。门槛基于配置的统计范围及排除项，不证明实际达到 100%。 |
| 通过 | [test.yml:189](D:/project/self/test/cs146s/fastapi/.github/workflows/test.yml:189)配置 CodSpeed 性能及内存基准；第 200 行起尝试在 base revision 上运行变更后的测试。 |
| 缺失 | 回归证明缺少退出码分类：[test.yml:259](D:/project/self/test/cs146s/fastapi/.github/workflows/test.yml:259)通过 `xargs` 执行 pytest；第 262–268 行把任何非零状态都打印为“base fails as expected”。采集、启动、参数或运行器错误可能被当作回归证据；xargs 也可能映射子进程退出码。 |
| Unknown | 当前通过率、覆盖率、性能变化及测试是否存在偶发失败；未执行、未读取远程运行日志。 |

**P1：**让回归证明区分实际断言失败与采集/环境/运行器故障；保留 pytest 原始结果或结构化报告，不仅判断 xargs 状态。对已有测试在 base 通过的情况继续明确标为“未证明回归”，不能冒充成功证明。

## 4. Documentation

| 状态 | 项目与证据 |
|---|---|
| 通过 | 本地有 `docs/en/docs/`、多语言文档、`docs_src/` 与教程测试；[build-docs.yml:104](D:/project/self/test/cs146s/fastapi/.github/workflows/build-docs.yml:104)执行 `scripts/docs.py build-lang`。 |
| 通过 | [.pre-commit-config.yaml:67](D:/project/self/test/cs146s/fastapi/.pre-commit-config.yaml:67)从英文首页生成 README，明确部分文档的生成关系。 |
| 通过 | 包内存在 [FastAPI skill](D:/project/self/test/cs146s/fastapi/fastapi/.agents/skills/fastapi/SKILL.md)，介绍 API、依赖注入、流式响应等使用约定。它是审计证据，本次没有调用它开展代码编写。 |
| 缺失 | 根目录未发现 AGENTS.md/CLAUDE.md；[contributing.md:5](D:/project/self/test/cs146s/fastapi/docs/en/docs/contributing.md:5)的开发部分主要跳转外部通用贡献指南，缺少在该入口直接给出的本仓库验证路径。包内使用指南不能完全替代贡献者操作说明。 |
| Unknown | 外部贡献指南的当前完整性、所有文档链接与示例是否有效；未逐一访问或执行。 |

**P2：**新增简洁的仓库贡献者指引，引用依赖组、lint/test 命令、生成文档边界及按修改范围选测试的方法；无需复制整套用户教程。

## 5. Dev Environment

| 状态 | 项目与证据 |
|---|---|
| 通过 | [.python-version](D:/project/self/test/cs146s/fastapi/.python-version)指定 3.11；[pyproject.toml:136](D:/project/self/test/cs146s/fastapi/pyproject.toml:136)集中声明 dev/tests/docs 等依赖组，根目录有 uv.lock。 |
| 通过 | [test.yml:125](D:/project/self/test/cs146s/fastapi/.github/workflows/test.yml:125)提供 `uv sync --no-dev --group tests --extra all` 安装入口；兼容测试有显式的依赖覆盖。 |
| 缺失 | 主测试安装步骤没有 `--locked`，另会安装 Starlette `main`；这有利于兼容性探索，但单凭提交 SHA 不能重放该组合的全部外部输入。缺少在该步骤强制锁一致性的保证。 |
| Unknown | 新机器一次安装成功率、Windows Bash 可用性及本地资源需求；未创建环境。 |

**P2：**保留探索最新依赖的矩阵，同时明确一个固定锁文件的基线任务；记录动态依赖实际版本/提交及工具版本，补充 Windows Shell 前提。

## 6. Code Quality

| 状态 | 项目与证据 |
|---|---|
| 通过 | `fastapi/` 分为 routing、dependencies、openapi、security、telemetry 等模块，存在 `py.typed`；严格 mypy 配置与类型检查脚本提供自动验证机制。 |
| 通过 | [pyproject.toml:292](D:/project/self/test/cs146s/fastapi/pyproject.toml:292)启用 Ruff `B/C4/UP` 等规则，并对例外文件逐项列出。 |
| 缺失 | 此配置没有复杂度门禁：第 305 行显式忽略 `C901`，启用规则也未包含 C90。不能因此断言代码复杂度过高。 |
| Unknown | 全仓重复率、复杂度分布、类型覆盖率和潜在缺陷数；本次未进行完整度量。 |

**P3：**先度量高变更频率模块，再对新增复杂函数设置基线；避免为了指标进行无需求的大规模重构。

## 7. Observability

| 状态 | 项目与证据 |
|---|---|
| 通过 | [pyproject.toml:50](D:/project/self/test/cs146s/fastapi/pyproject.toml:50)包含 OpenTelemetry API，extra 包含 SDK/OTLP exporter；[fastapi/logger.py](D:/project/self/test/cs146s/fastapi/fastapi/logger.py)定义命名 logger。 |
| 通过 | [telemetry/_api.py:214](D:/project/self/test/cs146s/fastapi/fastapi/telemetry/_api.py:214)创建 span，第 235 行记录 `error.type`；`_asgi.py` 为请求 span 设置属性。 |
| 通过 | [OpenTelemetry 文档](D:/project/self/test/cs146s/fastapi/docs/en/docs/advanced/opentelemetry.md)说明采集和接收端配置；`tests/test_telemetry/` 包含 HTTP、WebSocket、异常、集成和数据测试。 |
| 缺失 | 本次检查范围未发现必须补充的框架级遥测入口。应用专属仪表盘、告警和 SLO 不能作为这个库必须内置的功能扣分。 |
| Unknown | 实际遥测导出、接收端可用性、生产告警与性能开销；本次没有启动应用。 |

**P2：**在隔离验证环境用内存 exporter 核验异常、请求上下文与敏感字段处理；优先复用已有测试，不要求接入真实监控账户。

## 8. Security & Governance

| 状态 | 项目与证据 |
|---|---|
| 通过 | [LICENSE](D:/project/self/test/cs146s/fastapi/LICENSE)及项目元数据声明 MIT；[ISSUE_TEMPLATE/config.yml:3](D:/project/self/test/cs146s/fastapi/.github/ISSUE_TEMPLATE/config.yml:3)提供 security@tiangolo.com 漏洞联系渠道。不能因没有 SECURITY.md 就认定没有披露渠道。 |
| 通过 | [test.yml:12](D:/project/self/test/cs146s/fastapi/.github/workflows/test.yml:12)默认 `permissions: {}`，按任务授权；所检查 Actions 固定完整 SHA，checkout 使用 `persist-credentials: false`。 |
| 通过 | [zizmor.yml:24](D:/project/self/test/cs146s/fastapi/.github/workflows/zizmor.yml:24)扫描工作流安全；[dependabot.yml](D:/project/self/test/cs146s/fastapi/.github/dependabot.yml)配置 GitHub Actions 与 uv 更新。更新机器人不等同于证明没有漏洞。 |
| 缺失 | 根目录和 `.github/` 未发现 CODEOWNERS，仓库内缺少以该文件表达的模块评审归属；这不证明维护团队没有评审流程。 |
| Unknown | 分支保护、强制评审、托管秘密扫描、依赖漏洞告警及发布权限；未检查远程设置。 |
| Unknown | 所有遥测集成是否正确脱敏：[telemetry/_api.py:88](D:/project/self/test/cs146s/fastapi/fastapi/telemetry/_api.py:88)要求集成在导出前应用采集/脱敏设置，不能据此认定每个集成都已做到。 |

**P2：**按实际维护分工补充评审归属，并另行核查托管治理设置；针对敏感遥测字段保留明确的集成测试。

## 优先顺序与范围限制

1. **P1：修正回归证明的失败分类。** 防止基础设施故障被记录为修复有效的证据。
2. **P2：补充贡献者操作指引和固定依赖基线。** 现有工具齐全，提升的是智能体找到并稳定使用工具的效率。
3. **P2：验证最终 wheel、完善文档检查和评审归属。**
4. **P3：按度量结果引入复杂度约束。**

本报告不推断当前 CI 为绿色，也不把 100% 覆盖率门槛当作实际测量值。对库项目，生产告警和部署配置由应用承担，不机械套用服务型仓库要求。审计未修改 FastAPI；只新增本报告。
