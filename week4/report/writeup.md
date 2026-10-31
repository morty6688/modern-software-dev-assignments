# Week 4：让 vn.py 仓库适合 Agent 工作

完成日期：2026-11-01。

**所选仓库：** [vn.py / VeighNa](https://github.com/vnpy/vnpy)，事件驱动的 Python 量化交易框架。

**Fork 地址：** [morty6688/vnpy](https://github.com/morty6688/vnpy)。地址来自本地 `origin` 配置；本次未核查远程同步状态或 GitHub fork 元数据。

**编写的文件：** vn.py 仓库根目录的 `AGENTS.md`；`../lab/` 保留内容一致的 [提交副本](../lab/AGENTS.md)。详细调查见 [Part I 报告](part-i-vnpy.md)。

## Part I：探索仓库

| 项目 | 调查结论 |
|---|---|
| 构建 / 运行 | CI 使用 Windows、Python 3.13；`uv build` 通过 Hatchling/Babel 构建，并生成翻译 `.mo`。GUI 入口为 `examples/veighna_trader/run.py`，另需四个插件；不存在 `python -m vnpy` 入口。开发安装使用 `pip install -e '.[dev]'`，还需按 CI 补齐检查工具及依赖。 |
| 测试 | 正式范围是 `python -m pytest tests`，组件测试可指定文件；无范围收集可能误执行 RPC 示例。`tests/conftest.py` 在交易模块首次导入前建立临时 `.vntrader` 并关闭日志输出。 |
| Lint / 格式化 | `ruff check .`、`mypy vnpy`；Ruff 选择 B/E/F/UP/W、忽略 E501，没有既定全仓 formatter 步骤。不能把安装了 Ruff 推断为应执行全仓格式化。 |
| 目录与入口 | `vnpy/event` 为事件分发，`vnpy/trader` 为交易核心，`trader/ui` 与 `chart` 为界面，`rpc` 为 ZeroMQ 通信，`alpha` 为研究与回测；具体网关和 CTA 等应用来自独立插件。 |
| 代码与测试约定 | 使用 Data/Request dataclass、枚举和派生 `vt_*` 标识；保留通用/专属双事件，回报对象发布后不再修改。测试使用 FakeGateway、有界等待、`finally` 清理及全局状态恢复。 |
| 操作边界 | 不手改生成的 `.mo` 或构建产物，不随手格式化第三方 `vendor.css`；保护真实配置、数据库与研究数据。自动交易示例不能充当普通测试，pickle RPC 不可暴露给不可信网络。 |

核心架构的区别直接决定修改位置：EventEngine 负责队列、定时事件和同步回调分发；MainEngine 管理网关、应用与生命周期，并按 `gateway_name` 路由命令；OmsEngine 订阅事件、维护交易缓存和持仓转换状态；BaseGateway 定义外部交易接口和回报入口。

- **命令链路：** GUI/策略 → MainEngine → 指定 Gateway → 外部接口。
- **事件链路：** Gateway 回报 → EventEngine 队列 → 各订阅者；OMS 缓存数据，UI/策略独立订阅。`MainEngine.get_tick` 查询 OMS 缓存，不会主动请求行情。

**调查方法与人工参与：** 我先要求 Agent 只调查、不修改源码，读取 README、CI、pyproject、入口、引擎、网关和测试，并沿命令与事件链路交叉核实。随后由我手动验证安装、GUI、完整测试及构建，Agent 补充环境和静态检查。最终审阅时，我指出 `main_engine_test.py` 是自写脚本，不能作为上游标准入口，并要求区分首次安装与日常命令、压缩 Guardrails。没有把未记录的人工源码阅读写成已完成事实。

Part I 中，Agent 验证过核心组件共 27 项、Ruff 和 mypy；完整测试的 **162 passed, 2 warnings**、GUI 启动及构建产物由用户反馈，不能视为 Agent 独立复验。真实交易、远程 CI 和真实服务端到端集成不在这些结果的证明范围内。

## Part II：编写 AGENTS.md

最终文件保留五节，每节对应一个 Agent 实际决策：

| 章节 | 存在的理由 |
|---|---|
| Project Overview | 说明领域和插件边界，避免在核心仓库寻找全部网关/策略实现。 |
| Architecture | 给出修改入口，区分命令路由、事件订阅和缓存查询；提示线程及构造副作用。 |
| Commands | 提供可复制的安装、测试、Lint、类型检查、构建及 GUI 命令，并区分使用时机。 |
| Conventions | 保存会影响兼容性与正确性的契约，例如标识格式、双事件、数据不可变约定及测试隔离。 |
| Guardrails | 限定真实凭据、交易动作、网络暴露及生成物操作，防止以验证为由执行有实际副作用的脚本。 |

**有意省略：** 个人绝对路径、安装排错历史、具体环境故障日志、完整目录/插件名单、逐方法说明、RPC 心跳参数、提交历史和通用命名建议。这些内容或易过期，或可按需查询，不值得在每次任务中重复加载。历史测试成绩保留在报告中，不写成长期指令。

**最难的取舍：** 如何兼顾篇幅和可执行性。安装命令较长，但只写“安装开发依赖”会遗漏 pytest、Ruff、mypy 及类型存根；因此保留 CI 依赖命令，将其与日常检查分开。架构篇幅优先给四个核心类和两条链路，其余模块只保留定位信息。

## Part III：实际试用

两次任务均先读取 vn.py 根目录的 `AGENTS.md`，在仓库根目录运行 PowerShell，并复用 `.venv`。任务 1 实测解释器为 Python 3.13.16、pytest 9.1.1。没有重建环境或重新安装依赖。

### 任务 1：执行 EventEngine 相关测试

要求只验证、不修改源码或配置。为原样使用文件中的组件命令，执行了包含 EventEngine 的四文件测试组，而非仅运行单个事件测试。

```powershell
$py = '.\.venv\Scripts\python.exe'
& $py --version
& $py -m pytest --version
& $py -m pytest -q tests/test_event.py tests/test_engine.py tests/test_object.py tests/test_converter.py
```

首次执行在 `conftest.py` 创建临时 `.vntrader` 时遇到 `PermissionError: [WinError 5]`，测试尚未开始，临时目录清理也出现权限错误。获准在沙箱外重跑同一测试命令后，结果为 **23 passed in 4.25s，退出码 0**。没有通过修改 conftest 或绕过隔离机制解决环境问题。

EventEngine 原有用例检查事件投递、重复注册去重和停止后的线程退出。其余组件测试使用 FakeGateway，不连接真实交易服务。

### 任务 2：补充处理器执行顺序测试

检查发现 `tests/test_event.py` 原先没有覆盖特定事件处理器与 general handler 的执行顺序。仅在该文件新增 `test_event_engine_calls_specific_handler_before_general_handler`，未修改 EventEngine 生产源码。

测试先注册 general handler，再注册特定处理器，通过真实队列投递同一个 Event，断言记录为 `["specific", "general"]`。两个回调按事件对象身份过滤，避免定时事件干扰；使用 `time.monotonic()` 的 2 秒截止时间，在 `finally` 中调用 `stop()`，最后确认消费线程和定时线程均已退出。即使顺序被反转，两个回调仍会被记录，顺序断言会失败。

```powershell
$py = '.\.venv\Scripts\python.exe'
& $py -m pytest -q tests/test_event.py tests/test_engine.py tests/test_object.py tests/test_converter.py
& $py -m ruff check .
git diff --check -- tests/test_event.py
```

沿用已确认可访问隔离临时目录的沙箱外环境，结果为 **24 passed in 5.21s**；Ruff 输出 **All checks passed!**；差异空白检查通过。没有执行真实交易操作。此次只修改测试，未运行面向生产包 `vnpy` 的 mypy，也未重跑构建或全量测试；不能把 Part I 的全量结果当成新增测试后的全量结果。

### AGENTS.md 的实际影响与修订

| 任务 | 实际遵循的指令 | 观察 |
|---|---|---|
| 1：运行测试 | 使用 `.venv`、明确的四文件命令和原始 conftest 隔离；不执行交易示例。 | Agent 没有重复安装环境，也没有把临时目录权限问题当成业务测试失败；但针对 EventEngine 的任务执行范围扩大到了整组组件。 |
| 2：新增最小测试 | 保留类型标注，使用有界等待、`finally` 清理和线程退出断言；沿用正式测试范围，执行 Ruff，不做全仓格式化。 | 架构中明确的“特定处理器先于 general handler”转化成了可执行的回归测试，生产实现未被修改。 |

**试用后的一项主要改进：按使用时机拆分 Commands。** 两次验证只需要现有环境和检查命令，原先将安装、检查及运行混排容易使 Agent 误以为每次都需要安装。最终版本拆成“首次安装”“日常检查与构建”“按需运行 GUI”，明确已有环境应跳过安装。

审阅还纠正了来源判断：删除用户自写的 `main_engine_test.py` 命令，改为仓库已有 GUI 入口并列明插件依赖；Guardrails 压缩为三条。上述文档修订发生在两次任务之后，只核对了文本及入口源码，没有声称已用修订版重新执行全部任务或 GUI。

## 交付与状态

- [AGENTS.md](../lab/AGENTS.md)：vn.py 根目录最终指令文件的提交副本。
- [writeup.md](writeup.md)：本最终报告。
- [Part I 调查报告](part-i-vnpy.md)：详细依据与分阶段验证记录。
- vn.py 的 `tests/test_event.py`：保留 Part III 新增顺序测试。

Week 4 的本地编写与两项试用已完成。本次收尾未执行 Git 提交/推送、添加课程协作者或 Gradescope 提交；远程提交状态未核查。正式提交仍需按课程要求推送相关更改，并确认作业仓库已添加 `mihail911`、`isaackann`、`vdaita` 后提交 Gradescope。
