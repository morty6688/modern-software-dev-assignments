# vn.py Agent Readiness 审计报告

**结论：当前本地仓库已具备供智能体开展开发工作的基础设施，但验证环境的可复现性、异常恢复和安全边界仍有明显改进空间。**

> **本报告不是 Factory 官方评分。** 未安装或运行 Droid；仅参考 Factory 的[八个评估维度](https://factory.com/news/agent-readiness)，依据本地文件进行人工静态审计，不赋予官方分数或成熟度等级。

审计日期：2026-11-01  
审计目录：`D:\project\self\test\vnpy`  
可读取的 HEAD：`c6e231caf32b7fc97e6459817fff66458cf7e7c4`

审计过程中没有修改文件，没有安装依赖、运行测试或构建、启动交易程序。`git status` 返回 `this operation must be run in a work tree`，因此**当前文件与 HEAD 是否完全一致为 Unknown**。结论针对实际读取的本地文件，不能直接归因于上游仓库。本 Markdown 文件是在审计完成后，按用户要求保存的报告。

状态含义：

- **通过**：存在直接的文件或代码证据；不等于运行验证通过。
- **缺失**：在明确检查的配置、实现或目录范围中未发现对应机制。
- **Unknown**：本次证据不足，无法判断。
- **P1 / P2 / P3**：分别表示优先解决、计划改进、按需求完善。

## 1. Style & Validation：代码风格与校验

| 状态 | 审计项 | 文件与代码证据 |
|---|---|---|
| 通过 | 配置了静态代码检查 | [pyproject.toml:88](D:/project/self/test/vnpy/pyproject.toml:88)：Ruff 目标版本为 `py310`，启用 `B/E/F/UP/W`，忽略 `E501`。 |
| 通过 | 配置了较严格的类型检查 | [pyproject.toml:102](D:/project/self/test/vnpy/pyproject.toml:102)：启用 `disallow_untyped_defs`、`disallow_incomplete_defs`、`warn_unused_ignores` 等。不能将其等同于完整 `strict` 模式。 |
| 通过 | CI 执行 lint 和类型检查 | [pythonapp.yml:35](D:/project/self/test/vnpy/.github/workflows/pythonapp.yml:35)：执行 `ruff check .` 和 `mypy vnpy`。 |
| 缺失 | 统一、自动执行的格式检查 | CI 没有 formatter 检查步骤；[贡献指南](D:/project/self/test/vnpy/docs/community/info/contribution.md)建议 `autopep8 --in-place --recursive .`，但未见对应固定工具版本或 CI 门禁。 |
| 缺失 | 仓库级 pre-commit 配置 | 根目录未发现 `.pre-commit-config.yaml`。开发者是否自行安装本地钩子为 Unknown。 |
| Unknown | 当前代码是否通过上述检查 | 本次未执行 Ruff 或 mypy，不能以配置存在推断检查通过。 |

**建议：P2** 明确唯一的格式化工具、版本和检查命令，并在 CI 中执行；可将已有 lint/type 检查接入 pre-commit。避免直接对整个仓库执行格式化造成大量无关差异。

## 2. Build System：构建系统

| 状态 | 审计项 | 文件与代码证据 |
|---|---|---|
| 通过 | 构建后端、版本来源和包范围明确 | [pyproject.toml:67](D:/project/self/test/vnpy/pyproject.toml:67)：使用 `hatchling.build`；版本取自 `vnpy/__init__.py`；wheel 包含 `vnpy`。 |
| 通过 | CI 有构建步骤 | [pythonapp.yml:44](D:/project/self/test/vnpy/.github/workflows/pythonapp.yml:44)：`uv build`。 |
| 通过 | 翻译资源生成过程明确 | [build_hook.py:22](D:/project/self/test/vnpy/vnpy/trader/locale/build_hook.py:22)：读取 `.po`、以 `wb` 写入 `.mo`；[pyproject.toml:85](D:/project/self/test/vnpy/pyproject.toml:85)将 `.mo` 强制纳入 wheel。 |
| 缺失 | 完整的可复现依赖约束 | 根目录未见锁文件；构建依赖使用 `hatchling>=1.27.0`、`babel>=2.17.0`，CI 中 `uv`、`pytest` 等也未固定版本。 |
| 缺失 | 构建产物的独立安装验证 | CI 在 `uv build` 后结束，没有在全新环境安装 wheel/sdist 并验证导入的步骤。 |
| Unknown | 当前产物能否完整安装和运行 | 本次未构建，也未检查现有 `dist/` 中产物的内容与来源。 |

**建议：P1** 为开发和 CI 环境维护锁文件或约束文件；库对外声明的宽版本范围可以保留。  
**建议：P2** 增加 wheel 全新环境安装检查，并验证翻译资源、类型标记等必要文件确实打包。

## 3. Testing：测试

| 状态 | 审计项 | 文件与代码证据 |
|---|---|---|
| 通过 | 存在组件和集成测试 | `tests/` 包含事件、引擎、订单转换、数据服务、RPC 和 Alpha 测试；[test_engine.py:50](D:/project/self/test/vnpy/tests/test_engine.py:50)验证委托和撤单路由。 |
| 通过 | 隔离真实配置 | [conftest.py:13](D:/project/self/test/vnpy/tests/conftest.py:13)：首次导入交易模块前创建临时 `.vntrader`、切换 cwd，并关闭文件/控制台日志。 |
| 通过 | 使用模拟网关和回环 RPC | [test_engine.py:18](D:/project/self/test/vnpy/tests/test_engine.py:18)定义 `FakeGateway`；[test_rpc.py:88](D:/project/self/test/vnpy/tests/test_rpc.py:88)绑定 `tcp://127.0.0.1:0`。 |
| 通过 | 测试包含清理和异常断言 | [test_rpc.py:92](D:/project/self/test/vnpy/tests/test_rpc.py:92)使用 `pytest.raises`，随后以 `finally` 清理；事件测试也包含 `finally`。 |
| 缺失 | 覆盖率报告与门槛 | 检查的 `pyproject.toml` 和 CI 未配置 coverage、`--cov` 或覆盖率门槛。不能据此判断实际覆盖率低。 |
| 缺失 | 多平台、多 Python 版本验证 | [pythonapp.yml:18](D:/project/self/test/vnpy/.github/workflows/pythonapp.yml:18)仅配置 Windows / Python 3.13，而项目声明 Python `>=3.10`。 |
| Unknown | 当前测试结果、稳定性、真实交易端到端行为 | 本次未运行测试；未验证交易账户、外部网关或 GUI 自动化场景。 |

**建议：P1** 为事件处理异常和线程退出行为增加回归测试；先建立核心模块的覆盖率基线。  
**建议：P2** 按实际支持承诺扩展 CI 矩阵；核心测试继续使用模拟网关，无需依赖真实交易账户。

## 4. Documentation：文档

| 状态 | 审计项 | 文件与代码证据 |
|---|---|---|
| 通过 | 存在面向智能体的仓库说明 | [AGENTS.md:1](D:/project/self/test/vnpy/AGENTS.md:1)涵盖架构、命令、约定；[Guardrails:61](D:/project/self/test/vnpy/AGENTS.md:61)明确交易、凭据和生成文件边界。 |
| 通过 | 安装与贡献指南齐全 | [README.md:233](D:/project/self/test/vnpy/README.md:233)说明 Python 要求；[贡献指南](D:/project/self/test/vnpy/docs/community/info/contribution.md)包含 PR 流程、命名、格式和质量检查。另有英文 README、CHANGELOG 和 `docs/`。 |
| 缺失 | 格式化策略的一致描述 | 贡献指南建议递归运行 autopep8，而 [AGENTS.md:58](D:/project/self/test/vnpy/AGENTS.md:58)说明没有既定 formatter 步骤。人工建议和实际自动化之间的区别没有统一说明。 |
| 缺失 | 文档自动验证 | 当前 CI 没有文档构建、链接检查或示例命令验证步骤。 |
| Unknown | 文档网站发布状态及全部内容准确性 | 未构建文档、检查所有链接或逐一执行示例。 |

**建议：P2** 统一 README、贡献指南和 AGENTS 中的开发流程；明确 autopep8 是可选建议还是提交要求。加入轻量文档构建或链接检查。

这里的 AGENTS.md 属于当前本地工作成果；不能据此认定上游原始版本也具备同样的智能体文档。

## 5. Dev Environment：开发环境

| 状态 | 审计项 | 文件与代码证据 |
|---|---|---|
| 通过 | 有环境搭建入口 | 根目录包含 Windows、Linux、macOS 安装脚本；[AGENTS.md:17](D:/project/self/test/vnpy/AGENTS.md:17)提供 Python 3.13 虚拟环境和开发依赖命令。 |
| 通过 | 文档说明安装与开发的差别 | [install.bat](D:/project/self/test/vnpy/install.bat)执行 `pip install .`；AGENTS 的开发步骤使用 `pip install -e '.[dev]'`。 |
| 缺失 | 开发依赖的统一声明 | [pyproject.toml:53](D:/project/self/test/vnpy/pyproject.toml:53)的 `dev` 仅列存根、Hatchling 和 Babel；pytest、Ruff、mypy、uv 等另外写在 CI 和 AGENTS 中。 |
| 缺失 | Alpha 直接依赖声明完整性 | [factor_performance.py:13](D:/project/self/test/vnpy/vnpy/alpha/dataset/factor_performance.py:13)直接导入 `statsmodels`；[alpha extra:45](D:/project/self/test/vnpy/pyproject.toml:45)未声明它，CI 则单独安装。 |
| Unknown | 新机器能否按文档一次完成搭建 | 本次未创建干净环境；已有 `.venv` 不能证明首次安装流程完整。Linux/macOS 安装脚本的可执行性也未验证。 |

**建议：P1** 把开发、测试及 Alpha 的直接依赖集中声明，CI 与 AGENTS 引用同一安装入口。这是本次审计中**最值得优先完成的智能体效率改进**：减少补装依赖、猜测环境和本地/CI 差异。

## 6. Code Quality：代码质量

| 状态 | 审计项 | 文件与代码证据 |
|---|---|---|
| 通过 | 领域数据结构和标识约定明确 | [object.py:17](D:/project/self/test/vnpy/vnpy/trader/object.py:17)使用 dataclass；[object.py:134](D:/project/self/test/vnpy/vnpy/trader/object.py:134)明确构造 `vt_symbol`、`vt_orderid`。 |
| 通过 | 模块职责和接口有明确边界 | `event`、`trader`、`rpc`、`alpha` 分目录；[EventEngine:35](D:/project/self/test/vnpy/vnpy/event/engine.py:35)包含职责说明和类型标注。 |
| 缺失 | 事件回调异常隔离或显式失败策略 | [engine.py:57](D:/project/self/test/vnpy/vnpy/event/engine.py:57)仅捕获 `queue.Empty`；[engine.py:76](D:/project/self/test/vnpy/vnpy/event/engine.py:76)直接调用各 handler。由控制流可判断，其他异常会逸出消费线程，没有在此层恢复。 |
| 缺失 | 复杂度检查门禁 | Ruff 的 `select` 未包含 `C90`，当前 CI 未见独立复杂度检查。 |
| Unknown | 全仓复杂度、重复率及缺陷数量 | 本次未进行完整静态分析或行为验证，不给出这些指标的估计值。 |

**建议：P1** 明确回调异常发生后的策略：记录并隔离、停止引擎并报告故障，或其他明确行为。交易系统不能简单吞掉异常继续运行；应配合测试验证后续事件、状态和资源清理。

**建议：P3** 对复杂模块逐步引入复杂度基线，优先约束新增代码。

## 7. Observability：可观测性

| 状态 | 审计项 | 文件与代码证据 |
|---|---|---|
| 通过 | 日志有时间、级别和网关上下文 | [logger.py:27](D:/project/self/test/vnpy/vnpy/trader/logger.py:27)：格式包含 `time`、`level`、`extra[gateway_name]`；支持控制台及文件输出。 |
| 通过 | RPC 有超时和心跳机制 | [client.py:69](D:/project/self/test/vnpy/vnpy/rpc/client.py:69)设置默认 30 秒调用超时；[server.py:147](D:/project/self/test/vnpy/vnpy/rpc/server.py:147)发布心跳。 |
| 缺失 | RPC 断连诊断统一接入日志 | [client.py:183](D:/project/self/test/vnpy/vnpy/rpc/client.py:183)的默认 `on_disconnected()` 使用 `print(msg)`，没有接入统一日志上下文。 |
| 缺失 | 当前文件日志配置的轮转和保留策略 | [logger.py:53](D:/project/self/test/vnpy/vnpy/trader/logger.py:53)按初始化日期生成文件名；`logger.add` 未配置 `rotation` 或 `retention`。 |
| 缺失 | 事件队列和消费线程健康指标 | 所读 [EventEngine](D:/project/self/test/vnpy/vnpy/event/engine.py)实现没有队列积压、处理时延或消费线程存活的监控接口。 |
| Unknown | 部署侧监控、告警及日志收集 | 外部部署配置未纳入审计；不能由仓库内缺少配置推断线上没有监控。 |

**建议：P1** 增加消费线程失效和队列积压的可观测信号。  
**建议：P2** 将 RPC 断连接入统一日志，并明确长时间运行时的日志轮转、保留策略。是否需要分布式追踪应由部署形态决定。

## 8. Security & Governance：安全与治理

| 状态 | 审计项 | 文件与代码证据 |
|---|---|---|
| 通过 | 存在许可证和责任归属 | [LICENSE](D:/project/self/test/vnpy/LICENSE)为 MIT；[CODEOWNERS:1](D:/project/self/test/vnpy/.github/CODEOWNERS:1)为 `* @vnpy`。另有行为准则和 PR 模板。 |
| 通过 | CI 声明较小权限 | [pythonapp.yml:9](D:/project/self/test/vnpy/.github/workflows/pythonapp.yml:9)：`permissions: contents: read`。 |
| 通过 | 本地敏感配置有忽略和操作约束 | [.gitignore:23](D:/project/self/test/vnpy/.gitignore:23)忽略 `.vntrader`；AGENTS 明确禁止擅自读取凭据或执行交易动作。忽略规则不证明历史中没有泄露。 |
| 缺失 | 核心 RPC 实现中的认证与安全反序列化边界 | [server.py:108](D:/project/self/test/vnpy/vnpy/rpc/server.py:108)使用 `recv_pyobj()`；[client.py:156](D:/project/self/test/vnpy/vnpy/rpc/client.py:156)直接 `pickle.loads()`。所读 client/server 初始化和连接代码未设置认证或加密。 |
| 缺失 | RPC 示例的保守默认监听地址 | [test_server.py:32](D:/project/self/test/vnpy/examples/simple_rpc/test_server.py:32)使用 `tcp://*:2014` 和 `tcp://*:4102`，监听所有接口。 |
| 缺失 | 仓库内自动安全扫描配置 | 当前 `.github/workflows/pythonapp.yml` 未包含依赖漏洞、秘密扫描或 SAST 步骤；根目录与 `.github/` 未发现 `SECURITY.md`。 |
| 缺失 | Actions 的不可变版本固定 | CI 使用 `actions/checkout@v4`、`actions/setup-python@v5`，没有固定到完整提交 SHA。 |
| Unknown | 分支保护、强制评审、托管扫描及实际网络暴露 | 未查询远程设置或部署环境。CODEOWNERS 存在不证明其评审被强制执行；示例监听所有接口也不证明服务实际已对外开放。 |

**建议：P1** 优先将 RPC 示例默认限制到回环地址，并在使用文档明确可信网络要求。需要跨主机部署时，设计认证、传输保护及安全序列化方案；这些机制必须在处理不可信负载前建立边界。

**建议：P2** 增加漏洞披露指引、依赖与秘密扫描，并固定 Actions SHA；远程分支保护需另行核验。

## 改进优先顺序

| 优先级 | 改进 | 预期收益 |
|---|---|---|
| P1 | 统一开发/测试依赖，补齐 Alpha 直接依赖，固定 CI 环境 | 让智能体可以稳定复现验证流程，减少环境排错。 |
| P1 | 明确事件回调异常策略，增加回归测试及线程健康信号 | 避免消费线程退出后，故障难以发现和定位。 |
| P1 | 收紧 RPC 示例默认监听范围，明确可信边界 | 降低误运行示例时暴露不安全反序列化入口的风险。 |
| P2 | 增加覆盖率基线、支持版本矩阵和产物安装检查 | 提高自动修改后的验证可信度。 |
| P2 | 统一格式化文档与门禁，完善日志和安全检查 | 减少指令歧义，增强诊断和维护能力。 |
| P3 | 渐进引入复杂度约束 | 控制新增代码的维护成本。 |

此前的 [Week 4 调查记录](D:/project/self/test/cs146s/modern-software-dev-assignments/week4/report/part-i-vnpy.md)记录过 Ruff/mypy 验证，以及用户反馈的 `162 passed, 2 warnings` 和构建成功。这些是**历史证据**；本报告没有将它们当作当前工作树已重新验证通过的结果。

**审计未修改 vn.py 仓库；本文件仅保存审计报告。所有结论均为独立审计判断，不代表 Factory 官方评分。**
