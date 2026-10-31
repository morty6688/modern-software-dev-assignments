# AGENTS.md

## Project Overview

vn.py（VeighNa）是事件驱动的 Python 量化交易框架，包含交易基础设施、Qt 界面和 Alpha 研究工具。具体交易网关及 CTA 等应用主要来自独立的 `vnpy_*` 插件包；本仓库不是全部插件的实现。

## Architecture

- `vnpy/event/engine.py`：EventEngine 管理事件队列、消费线程和定时线程；先调用类型订阅者，再调用全局订阅者。回调在消费线程同步执行，耗时操作会阻塞分发，未捕获的回调异常可终止该线程。
- `vnpy/trader/engine.py`：MainEngine 注册网关/应用、按 `gateway_name` 路由命令并管理生命周期；构造时启动 EventEngine、切换 cwd、初始化内置引擎，`close()` 先停止事件引擎再关闭功能引擎和网关。
- 同文件的 OmsEngine 订阅交易事件，缓存行情、委托、成交、持仓、账户、合约和报价，维护活跃委托/报价及各网关的 OffsetConverter。`MainEngine.get_tick` 绑定 OMS 缓存查询，未命中返回 `None`，不会请求外部行情。
- `vnpy/trader/gateway.py`：BaseGateway 定义交易接口及 `on_*` 回报入口；具体插件实现连接、订阅和交易。接口要求线程安全、非阻塞、断线重连。
- **命令链路**：GUI/策略 → MainEngine.`connect/subscribe/send_order/cancel_order` → 指定 Gateway → 外部接口；不经过事件队列。
- **事件链路**：Gateway.`on_tick` → `on_event` → EventEngine.`put` → Queue → `_run/_process` → 各订阅者；OMS 用 `vt_symbol` 缓存 tick，UI/策略独立订阅，不依赖 OMS 转发。
- `vnpy/trader/ui`、`vnpy/chart` 为界面/图表；`vnpy/rpc` 为 ZeroMQ 通信；`vnpy/alpha` 为因子、模型和回测。`examples/veighna_trader/run.py` 是 GUI 入口（另需 CTP、CTA strategy/backtester、data manager 插件）；`tests/` 是正式测试范围。

## Commands

在仓库根目录用 PowerShell 执行，使用 Python 3.13 和同一 `.venv` 解释器。安装依赖以 `.github/workflows/pythonapp.yml` 为准；`[dev]` 不包含 pytest、Ruff 或 mypy。

**首次安装**（已有可用环境时跳过；仅在依赖变化时按需补装）：

```powershell
py -3.13 -m venv .venv
$py = '.\.venv\Scripts\python.exe'
& $py -m pip install --upgrade pip
& $py -m pip install ruff==0.14.1 mypy==1.19.1 uv pytest types-tqdm
& $py -m pip install 'ta-lib==0.6.4' --index-url https://pypi.vnpy.com
& $py -m pip install -e '.[dev]' 'polars>=1.26.0' 'scipy>=1.15.2' 'pyarrow>=19.0.1' statsmodels matplotlib
& $py -m pip install vnpy_sqlite
```

**日常检查与构建**（按修改范围选择组件测试或全量测试）：

```powershell
$py = '.\.venv\Scripts\python.exe'
& $py -m pytest -q tests/test_event.py tests/test_engine.py tests/test_object.py tests/test_converter.py
& $py -m pytest tests
& $py -m ruff check .
& $py -m mypy vnpy
.\.venv\Scripts\uv.exe build
```

构建使用 Hatchling/Babel，会生成翻译 `.mo` 和分发包。不要用无范围的 `pytest` 收集 `examples/simple_rpc/test_*.py`。

**按需运行 GUI**：首次运行需另装下面四个插件，已安装则跳过安装行。入口会读取配置、改变 cwd 并启动线程，不作为默认测试；没有 `python -m vnpy` 入口。

```powershell
$py = '.\.venv\Scripts\python.exe'
& $py -m pip install vnpy_ctp vnpy_ctastrategy vnpy_ctabacktester vnpy_datamanager
& $py .\examples\veighna_trader\run.py
```

## Conventions

- 沿用 `trader/object.py` 的 `XxxData/XxxRequest` dataclass 和 `constant.py` 枚举；保持 `vt_symbol=symbol.exchange.value`、`vt_orderid=gateway_name.orderid`。保留已有通用/专属双事件，如 `EVENT_TICK` 与 `EVENT_TICK + vt_symbol`。
- 传给网关 `on_*` 的数据之后不得修改；缓存对象先 `copy.copy` 再发布。修改 `trader/converter.py` 的平今/平昨、冻结量逻辑须覆盖相应交易语义测试。
- 核心函数保留完整类型标注；用户可见消息沿用 gettext `_()`。Ruff 选 B/E/F/UP/W、忽略 E501；没有既定 formatter 步骤，不做全仓 `ruff format`。保留各边界的异常/空返回语义。
- 测试沿用 `tests/conftest.py` 在首次交易模块导入前建立临时 `.vntrader` 的隔离方式；使用 FakeGateway、有界等待和 `finally` 清理线程/引擎，恢复 SETTINGS/缓存单例。RPC 测试绑定本机回环随机端口。

## Guardrails

- 测试/验证须隔离 `.vntrader`，勿读取、覆盖或提交真实凭据；数据库与 `lab/` 数据/模型不可当缓存清理。
- 未获明确授权，不连接交易账户、下单/撤单、启动策略或外发通知；勿将 `examples/no_ui/run.py`、录制或交易 RPC 示例当测试。pickle RPC 不可暴露给不可信网络。
- 不手改/提交 `.mo`、构建产物和缓存；翻译改 `.po`。勿随手格式化第三方 `docs/_static/vendor.css`，勿按 `.gitignore` 批量删除已跟踪资源。
