# Part I: Explore the Repo — vn.py

初次调查日期：2026-10-24；验证记录更新：2026-10-26。目标：`D:\project\self\test\vnpy`；HEAD 为 `c6e231caf32b7fc97e6459817fff66458cf7e7c4`，源码版本为 4.5.0。本报告基于当前本地文件与 Git 历史，不代表其他版本或远程最新状态。

Agent 在本阶段未创建 AGENTS.md、未修改 vn.py 源码、未启动 GUI 或交易服务。用户随后手动验证了 GUI 启动、最小无 UI 引擎脚本、完整 tests 套件及 uv build，结果见下方最新验证汇总。初次调查后，用户已执行 install.bat；本报告已补充运行依赖及开发工具安装后的核验。用户随后安装 pytest、ruff、mypy，并授权 Agent 按 CI 补齐其余依赖；现已完成安装与 mypy 复核。Git 历史可读，但 `git status` 在当前沙箱中失败，因此不能宣称工作树与 HEAD 完全一致。

状态标记：**Agent 已验证**表示 Agent 实际执行；**用户手动验证**表示用户执行并反馈结果，Agent 未独立重跑或审阅完整日志；**受阻**表示实际尝试但未完成；**配置确认**表示命令有仓库依据但未执行；**建议**表示由配置推导的操作，不是仓库既定要求。

### 最新验证汇总（2026-10-26）

| 项目 | 结果 | 验证来源 |
|---|---|---|
| 核心组件测试 | 27 项通过 | Agent 分次执行，2026-10-24 |
| 完整 tests 套件 | **162 passed, 2 warnings** | 用户在 VS Code 中运行完整 tests 并反馈；warnings 内容尚未提供，不能判断具体原因 |
| Ruff | 0.14.1，检查通过 | Agent 执行 |
| mypy | 1.19.1，61 个源码文件检查通过 | Agent 补齐 CI 依赖后执行 |
| 构建 | `uv build` 已运行，`.whl` 和 `.tar.gz` 产物已生成 | 用户手动验证；未进一步验证产物在全新环境中的安装 |
| GUI | 四个额外插件已安装，GUI 启动验证通过 | 用户手动验证；不代表交易连接、下单或策略运行已验证 |
| 无 UI 最小引擎 | `examples/no_ui/main_engine_test.py` 已测试 | 用户手动验证；脚本只创建 MainEngine/EventEngine、等待输入后关闭，不注册或连接交易网关，也不启动 RPC |
| 交易与 RPC 集成场景 | 未测试：暂无交易账号配置及 RPC 设置 | 不影响已有本机回环 RPC 自动化测试记录 |
| 远程 CI 状态 | 暂不核查 | 按用户要求；不宣称远程工作流通过 |

用户补充的范围说明：暂无交易账号配置及 RPC 设置，因此除已明确记录的启动验证、自动化测试和构建外，其他手动交易/RPC 集成场景未测试。已有本机回环 RPC 自动化测试通过，不等同于配置真实 RPC 服务后的端到端验证。按用户要求，远程 CI 运行状态暂不核查；仓库 CI 文件仍作为依赖与命令依据。

## Build / Run

### 环境与安装

Python 元数据要求 `>=3.10`，README 推荐 64 位 Python 3.13，CI 实际选择 Windows + Python 3.13。应优先复现 CI，而不能因为元数据没有上限就断言 Python 3.14/3.15 已兼容。运行时包含 PySide6、TA-Lib、NumPy、pandas、ZeroMQ 等依赖；开发 extra 没有包含 pytest、ruff、mypy 或 uv。

以下为 **PowerShell** 命令。当前已有可用 `.venv`，无需重复创建；下一段仅供从零准备环境参考。若 Windows `py` launcher 已安装，可执行（本机未验证 launcher）：

```powershell
Set-Location 'D:\project\self\test\vnpy'
py -3.13 -m venv .venv
$py = (Resolve-Path '.venv\Scripts\python.exe').Path
& $py --version
```

### 安装后复核（2026-10-24）

用户报告已执行 install.bat；Agent 随后只读核实了安装结果，而没有重跑安装脚本或审阅完整安装日志：

- `.venv/pyvenv.cfg` 显示 uv 0.13.4 创建、Python 3.13、`seed = true`；实际解释器为 Python 3.13.16。
- `.venv/Lib/site-packages` 中安装了 vnpy 4.5.0；direct_url.json 指向本地目标仓库，未设置 editable，符合 bat 的普通安装方式。
- 已安装 PySide6 6.8.2.1、TA-Lib 0.6.4、NumPy 2.5.4、pandas 3.1.0、tzlocal 5.4.5、pyzmq 27.2.0。
- `python -m pip check` 返回 `No broken requirements found.`；这只验证声明依赖关系，不证明所有运行行为兼容。
- 已安装包包含 `vnpy/trader/locale/en/LC_MESSAGES/vnpy.mo`，初次检查时未独立执行 CI 的 `uv build`。用户后续已运行该命令并确认生成 `.whl` 和 `.tar.gz`，见构建节。
- install.bat 本身不安装开发工具；用户后来单独安装了 pytest 9.1.1、ruff 0.14.1、mypy 1.19.1，已用此虚拟环境逐一核实版本。Ruff/mypy 与 CI 固定版本一致。

当前环境的精确检查命令（已执行前两条）：

```powershell
Set-Location 'D:\project\self\test\vnpy'
$py = (Resolve-Path '.venv\Scripts\python.exe').Path
& $py --version
& $py -m pip check
```

若从零使用 uv 创建环境且仍要调用 bat，应使用 `uv venv --python 3.13 --seed` 给环境提供 pip，再执行 `.\install.bat .\.venv\Scripts\python.exe`。bat 内部调用的是 pip；全程使用 `uv pip install` 则不需要 seed。当前环境已经建好，不要再次初始化。

最初的 bat 普通安装意味着源码修改不会自动同步到 site-packages；仓库 pytest 的 conftest 会把仓库根目录插入 sys.path，故测试通常针对工作树源码，而外部目录启动程序可能使用已安装副本。本轮已按下面 CI 命令改成 editable 安装，direct_url.json 确认 editable=true，后续该环境直接使用工作树源码。

随后按 CI 安装开发与测试依赖，使用同一个解释器，避免 PATH 混用：

```powershell
& $py -m pip install --upgrade pip
& $py -m pip install ruff==0.14.1 mypy==1.19.1 uv pytest types-tqdm
& $py -m pip install 'ta-lib==0.6.4' --index-url https://pypi.vnpy.com
& $py -m pip install -e '.[dev]' 'polars>=1.26.0' 'scipy>=1.15.2' 'pyarrow>=19.0.1' statsmodels matplotlib
& $py -m pip install vnpy_sqlite
```

以上依赖命令是 CI 的等价解释器绑定写法。**已按 CI 清单实际执行完成**（含升级 pip、固定版本工具、TA-Lib 0.6.4、editable 的 .[dev]、Polars/SciPy/PyArrow、statsmodels、matplotlib 和 vnpy_sqlite）；本地默认包源为阿里云镜像，TA-Lib 步骤使用 CI 指定的 vn.py 源，不表示远程 CI 的所有未固定依赖版本与此完全相同。这是较大的依赖集合，涉及外部包源。完整 Alpha 功能另有 `& $py -m pip install -e '.[dev,alpha]'`，会额外引入 torch、lightgbm 等；它不是本次小范围调查的必要步骤。值得注意：源码 `factor_performance.py` 导入 statsmodels，CI 单独安装它，而 pyproject 的 alpha extra 未列出它，因此不能保证仅安装 alpha extra 就覆盖当前所有研究功能。

README 的 Windows 安装命令在 PowerShell 中应写为：

```powershell
.\install.bat
```

脚本会升级 pip/wheel、安装 TA-Lib 0.6.4，最后 `python -m pip install .`，属于非 editable 安装。它默认使用 PATH 中的 python；激活当前 `.venv` 或显式传入其解释器才能确保使用 Python 3.13，不能依赖其他终端的默认 python。Ubuntu / macOS 文档命令分别为 `bash install.sh`、`bash install_osx.sh`，未验证；前者含下载、编译、`make install` 和 `locale-gen`，后者含 Homebrew 安装，不能当作无副作用检查。

### 构建

CI 的原始命令是：

```powershell
uv build
```

在上述独立环境中可明确使用：

```powershell
.\.venv\Scripts\uv.exe build
```

**用户手动验证（2026-10-26 更新）**：用户已运行 `uv build` 并确认生成 `.whl` 和 `.tar.gz`。Agent 未重跑构建，未审阅完整构建日志或进一步检查包内容。后端为 `hatchling.build`，构建依赖含 Babel；版本从 `vnpy/__init__.py` 提取，wheel 打包 `vnpy`。自定义构建 hook 会把翻译 `.po` 编译成源码目录下的 `.mo`，再强制纳入 wheel。构建不仅检查代码，还会写入生成文件，并可能下载隔离构建依赖。

### 运行

仓库提供示例脚本，没有在 pyproject 声明 console-script 入口；未找到包级 `__main__.py`，因此不要写成 `python -m vnpy`。

GUI 示例的实际额外导入为 CTP、CTA strategy、CTA backtester 和 data manager；这些不是核心包的 dependencies：

```powershell
# 复现命令；用户已确认安装以下四个额外插件
& $py -m pip install vnpy_ctp vnpy_ctastrategy vnpy_ctabacktester vnpy_datamanager
# 仓库 GUI 启动命令；用户已手动验证 GUI 启动，Agent 未重跑
& $py .\examples\veighna_trader\run.py
```

用户确认已安装 `vnpy_ctp`、`vnpy_ctastrategy`、`vnpy_ctabacktester`、`vnpy_datamanager` 并启动验证 GUI。反馈不包含交易连接、下单或策略运行验证。

脚本依次创建 QApplication、EventEngine、MainEngine，注册 gateway/apps，再显示 MainWindow 并进入 Qt 事件循环。仅启动此脚本没有显式调用 connect；但引擎会启动线程、读取配置并改变工作目录。不能据此把它归为无副作用 smoke test。

无 UI 的用户手动验证入口为 [examples/no_ui/main_engine_test.py](D:/project/self/test/vnpy/examples/no_ui/main_engine_test.py)，复现命令：

```powershell
Set-Location 'D:\project\self\test\vnpy'
.\.venv\Scripts\python.exe .\examples\no_ui\main_engine_test.py
# 出现提示后按 Enter，脚本调用 engine.close()
```

Agent 已只读检查该脚本：它构造 `MainEngine(EventEngine())`，打印启动消息，等待输入，再调用 `engine.close()`；没有 add_gateway、connect、策略启动或 RPC 调用。这是最小引擎生命周期的启动验证，不是 `examples/no_ui/run.py` 自动交易示例的验证。MainEngine 构造仍会读取配置、改变 cwd 并启动事件线程，不能把此脚本当作无副作用的导入检查。由于没有交易账号及 RPC 配置，用户未测试其他相关运行场景。

证据：[pyproject.toml](D:/project/self/test/vnpy/pyproject.toml)、[CI](D:/project/self/test/vnpy/.github/workflows/pythonapp.yml)、[README](D:/project/self/test/vnpy/README.md:229)、[install.bat](D:/project/self/test/vnpy/install.bat)、[install.sh](D:/project/self/test/vnpy/install.sh)、[install_osx.sh](D:/project/self/test/vnpy/install_osx.sh)、[构建 hook](D:/project/self/test/vnpy/vnpy/trader/locale/build_hook.py)、[GUI 入口](D:/project/self/test/vnpy/examples/veighna_trader/run.py)、[Alpha 依赖](D:/project/self/test/vnpy/vnpy/alpha/dataset/factor_performance.py)。

**适合 AGENTS：** Python 3.13、CI 安装入口、构建命令、GUI 需独立插件且不能作为默认验证。发行版宣传、完整网关名单和各平台安装脚本全文不必放入一页配置。

## Test

### 正式命令与范围

CI 的完整测试命令为 `python -m pytest tests`，不是无范围的 `pytest`。在前述环境下：

```powershell
# 从仓库根目录执行；先小范围，后按任务扩大
& $py -m pytest -q tests/test_event.py
& $py -m pytest -q tests/test_object.py tests/test_converter.py
& $py -m pytest -q tests/test_engine.py
# RPC 测试会绑定本机回环随机端口；不会连接交易服务
& $py -m pytest -q tests/test_rpc.py
# CI 全量命令；用户已在 VS Code 中验证完整 tests 范围
& $py -m pytest tests
```

以上命令有配置/源码依据；其中五个核心测试文件已经实际验证通过，见下方最新结果。完整 tests 套件已由用户在 VS Code 中运行，结果为 **162 passed, 2 warnings**；Agent 没有独立重跑全套测试。显式限定 `tests` 可避免把 `examples/simple_rpc/test_*.py` 这类示例脚本当作正式测试范围。

`tests/conftest.py` 在首次导入交易模块前：将仓库加入 sys.path；建立临时 `.vntrader`；切换 cwd；导入 SETTINGS 并关闭文件/控制台日志；在 pytest 结束时恢复 cwd、清理目录。即使只选纯标准库的事件引擎测试，pytest 仍会加载这个 conftest，因此仍需 tzlocal、TA-Lib 等交易模块的导入依赖。

测试组织按组件命名：event/object/engine/converter/rpc/utility/data_services，以及 Alpha 根级测试和 `tests/alpha/`。引擎测试使用 FakeGateway；RPC 测试用 `127.0.0.1:0`；异步断言使用 monotonic deadline；资源在 finally 中 stop/close/join；数据服务测试保存并恢复全局单例与 SETTINGS。不能笼统称全部都是“纯单元测试”：其中包含本机线程、socket 和 SQLite 的集成行为。

### 初次调查结果（安装前，保留作历史记录）

| 检查 | 结果与边界 |
|---|---|
| 默认 `python --version` / `python -m pytest --version` | Python 3.15.1；缺少 pytest，不能开始正式测试 |
| Anaconda Python 环境探测 | 3.14.6；有 pytest、numpy、zmq，缺少 tzlocal、talib；不是 CI 环境 |
| Anaconda 执行事件测试 | 首次被沙箱临时目录权限阻断；将 TEMP/TMP 指向可写作业目录后，明确在 conftest 导入时因缺少 tzlocal 失败；没有测试用例完成 |
| 直接调用事件测试函数 | **通过**；标准库事件队列、重复注册去重、线程结束断言成功；绕过 pytest/conftest，只能算独立 smoke check |
| RPC、引擎、全套测试 | 未执行，不能宣称通过 |

### Agent 复核记录：开发工具安装后（2026-10-24）

当前 `.venv` 为 Python 3.13.16，pytest 9.1.1。先执行最小事件测试，再扩大到相关核心组件，结果如下；该轮 Agent 没有执行完整测试套件。完整测试的后续用户验证结果见最新汇总。

| 范围 | 实际结果 |
|---|---|
| tests/test_event.py | **1 passed** |
| tests/test_object.py、tests/test_converter.py、tests/test_engine.py | **22 passed** |
| tests/test_rpc.py | 沙箱内 4 项均在创建 zmq.Context 时 Permission denied；获准在沙箱外仅重跑本机回环测试后 **4 passed** |
| 五个核心文件合计 | **27 项通过**，来自上述分次执行，不代表全套 tests 通过 |
| Alpha、数据服务及其他测试 | 该轮 Agent 未执行；用户后续已运行完整 tests，汇总为 162 passed, 2 warnings |

实际执行使用同一个虚拟环境解释器，启用原仓库 conftest；它把仓库根目录加入 sys.path，因此本轮 pytest 检查的是工作树源码。为避免向目标仓库写缓存并规避先前临时目录权限问题，使用以下命令（RPC 在允许本机 socket 的环境执行）：

```powershell
$py = 'D:\project\self\test\vnpy\.venv\Scripts\python.exe'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
$env:TEMP = 'D:\project\self\test\cs146s'
$env:TMP = $env:TEMP
& $py -B -m pytest -q -p no:cacheprovider D:/project/self/test/vnpy/tests/test_event.py
& $py -B -m pytest -q -p no:cacheprovider D:/project/self/test/vnpy/tests/test_object.py D:/project/self/test/vnpy/tests/test_converter.py D:/project/self/test/vnpy/tests/test_engine.py D:/project/self/test/vnpy/tests/test_rpc.py
# 沙箱内 RPC 失败后，沙箱外重跑的确切测试范围
& $py -B -m pytest -q -p no:cacheprovider D:/project/self/test/vnpy/tests/test_rpc.py
```

这些环境变量只用于本次检查进程。RPC 测试使用 `127.0.0.1:0`，没有启动示例交易服务或连接交易账户。沙箱内失败与沙箱外通过均保留，不能将前者报告为已证实的 RPC 业务缺陷。

此前安装运行依赖后，还在临时 `.vntrader` 中成功导入已安装包的 setting/MainEngine（未实例化引擎），并直接调用事件测试函数成功。这些较早的 smoke check 证据保留，但最新源码验证应以上面的正式 pytest 结果为准。

初次独立 smoke check 的精确复现命令（无需安装交易依赖）：

```powershell
python -B -c "import sys,runpy; sys.path.insert(0,r'D:\project\self\test\vnpy'); ns=runpy.run_path(r'D:\project\self\test\vnpy\tests\test_event.py'); ns['test_event_engine_calls_registered_handler_once'](); print('PASS: standalone event test function (without pytest/conftest)')"
```

正式测试尝试使用 `-B`、`PYTHONDONTWRITEBYTECODE=1`、`-p no:cacheprovider`，并禁用环境中自动加载的 pytest 插件，避免向目标仓库写缓存。导入失败还触发了 Windows 临时目录清理报错，不能把它算成业务断言失败。

证据：[conftest](D:/project/self/test/vnpy/tests/conftest.py)、[事件测试](D:/project/self/test/vnpy/tests/test_event.py)、[引擎测试](D:/project/self/test/vnpy/tests/test_engine.py)、[RPC 测试](D:/project/self/test/vnpy/tests/test_rpc.py)、[数据服务测试](D:/project/self/test/vnpy/tests/test_data_services.py)、[CI](D:/project/self/test/vnpy/.github/workflows/pythonapp.yml)。

**适合 AGENTS：** 精确测试范围、优先组件测试、保留 conftest 配置隔离、FakeGateway 和线程清理惯例。个人机器路径、此次环境故障全文及绕过 conftest 的诊断命令只留在调查报告。

## Lint / Format

README 与 CI 一致要求：

```powershell
ruff check .
mypy vnpy
```

为绑定到前述独立环境，也可用：

```powershell
& $py -m ruff check .
& $py -m mypy vnpy
```

Ruff target 为 py310；选择 B/E/F/UP/W，忽略 E501。不要凭习惯引入全局行长修复或声称项目启用了 import sorting。Mypy 按 Python 3.13 检查，要求完整函数类型标注、严格 Optional 等，并对特定第三方模块设置例外；其检查范围是 `vnpy`，不是 examples/tests。

**最新实际验证：** 当前 `.venv` 的 Ruff 0.14.1 执行 `ruff check --no-cache .` 输出 `All checks passed!`；这次版本与 CI 一致，替代此前外部环境 Ruff 0.15.1 的通过记录作为主要证据。

补齐 CI 依赖前，Mypy 1.19.1 曾实际检查 61 个源码文件，退出码 1：`Found 19 errors in 8 files (checked 61 source files)`。错误包括 Babel、statsmodels、matplotlib 缺失模块，pandas/scipy/tqdm 缺少类型存根，以及部分 unused-ignore。当时环境尚未完成 CI 的 `[dev]`、`types-tqdm`、statsmodels、matplotlib 等安装，因此未将这些报错归为源码缺陷。随后经用户授权补齐依赖，未修改源码、检查规则或 ignore。

实际命令如下；mypy 缓存定向到作业工作区，避免写入 vn.py：

```powershell
Set-Location 'D:\project\self\test\vnpy'
.\.venv\Scripts\python.exe -B -m ruff check --no-cache .
.\.venv\Scripts\python.exe -B -m mypy --cache-dir D:/project/self/test/cs146s/.vnpy-mypy-cache vnpy
```

**最新结果：补齐 CI 清单后，使用上面同一条 mypy 命令复查，输出 `Success: no issues found in 61 source files`，类型检查通过。`pip check` 同时返回 `No broken requirements found.`。因此此前 19 项错误在补齐环境后全部消失，无需修改源码。该轮 Agent 没有重跑完整测试或独立 `uv build`；后续两项均已由用户手动验证，须与 Agent 执行记录区分。

**格式化没有已确认的项目命令。** pyproject 没有 `[tool.ruff.format]`，CI/README 没有 formatter 步骤。下列只读探测已执行：

```powershell
ruff format --check --no-cache vnpy/event/engine.py vnpy/rpc/client.py vnpy/rpc/server.py
```

结果是 1 个文件已符合、2 个 RPC 文件会被重新格式化，退出码 1。因此不能把 `ruff format .` 写成维护者既定要求。若将来明确决定使用 Ruff formatter，可仅对指定文件执行 `ruff format <文件路径>`，但这是新的工作方式选择，本次未执行任何格式化写入。

证据：[pyproject.toml](D:/project/self/test/vnpy/pyproject.toml)、[README 贡献规范](D:/project/self/test/vnpy/README.md:329)、[CI](D:/project/self/test/vnpy/.github/workflows/pythonapp.yml)。

**适合 AGENTS：** 两条检查命令、工具版本依据、无既定 formatter、避免顺手全仓格式化。无需重复罗列配置文件中全部 lint 规则。

## Key directories and entry points

| 路径 | 职责与入口依据 |
|---|---|
| [vnpy/event](D:/project/self/test/vnpy/vnpy/event/engine.py) | 标准库实现的 Event/EventEngine，队列分发与定时事件 |
| [vnpy/trader](D:/project/self/test/vnpy/vnpy/trader/engine.py) | MainEngine、OmsEngine、通知/日志引擎；交易数据、常量、网关与应用接口、持仓转换、数据库/数据服务 |
| [vnpy/trader/ui](D:/project/self/test/vnpy/vnpy/trader/ui/qt.py) | PySide6 QApplication、MainWindow、交易和设置界面 |
| [vnpy/rpc](D:/project/self/test/vnpy/vnpy/rpc/__init__.py) | 独立 ZeroMQ RpcClient/RpcServer 通信层 |
| [vnpy/chart](D:/project/self/test/vnpy/vnpy/chart/widget.py) | 图表 widget、行情数据 manager、绘图 item/axis |
| [vnpy/alpha](D:/project/self/test/vnpy/vnpy/alpha/__init__.py) | AlphaLab、因子数据集/表达式、模型、策略与回测；不是基础交易入口 |
| [examples](D:/project/self/test/vnpy/examples/veighna_trader/run.py) | GUI、无界面交易、RPC、数据下载和研究 notebooks；依赖与副作用各不相同 |
| [tests](D:/project/self/test/vnpy/tests/conftest.py) | 组件测试及隔离初始化 |
| [docs](D:/project/self/test/vnpy/docs/community/install/windows_install.md) | 社区/产品安装与功能文档、图片和静态资源 |
| [.github/workflows](D:/project/self/test/vnpy/.github/workflows/pythonapp.yml) | 安装 → lint → 类型检查 → 测试 → 构建的验证流程 |

### Core Execution and Data Flow

- **Startup:** `examples/veighna_trader/run.py` 创建 EventEngine 和 MainEngine；MainEngine 启动事件引擎、初始化内置功能引擎，然后由入口脚本注册 Gateway 和 App。
- **Command Flow:** GUI/Strategy → MainEngine → Gateway → 外部交易接口。具体命令按 `gateway_name` 路由到相应网关。
- **Market Data Flow:** `Gateway.on_tick()` → `Gateway.on_event()` → `EventEngine.put()` → Queue → `EventEngine._run()` → `EventEngine._process()` → `OmsEngine.process_tick_event()` → 按 `vt_symbol` 缓存最新行情。
- **Query Flow:** `MainEngine.get_tick(vt_symbol)` → `OmsEngine.get_tick(vt_symbol)` → 返回缓存的 TickData；未命中时返回 `None`。MainEngine 初始化时将 `get_tick` 绑定到 OMS 方法，查询不会主动请求外部行情。
- **Event Subscription:** OMS、GUI 和策略组件可以独立订阅对应事件，无需通过 OMS 转发。Gateway 发布通用 `EVENT_TICK` 和合约专属 `EVENT_TICK + tick.vt_symbol` 两种 Tick 事件；OMS 订阅通用 Tick 事件。
- **Lifecycle:** MainEngine 创建时启动事件引擎；`MainEngine.close()` 先停止事件引擎，再关闭功能引擎和网关。

证据：[启动入口](D:/project/self/test/vnpy/examples/veighna_trader/run.py)、[MainEngine 初始化与查询绑定](D:/project/self/test/vnpy/vnpy/trader/engine.py:149)、[网关 Tick 发布](D:/project/self/test/vnpy/vnpy/trader/gateway.py:99)、[事件队列与分发](D:/project/self/test/vnpy/vnpy/event/engine.py)、[OMS 订阅及行情缓存](D:/project/self/test/vnpy/vnpy/trader/engine.py:401)、[缓存查询](D:/project/self/test/vnpy/vnpy/trader/engine.py:495)、[关闭顺序](D:/project/self/test/vnpy/vnpy/trader/engine.py:321)。

### 事件引擎

`Event(type, data)` 是通信载体。EventEngine 有一个队列消费线程和一个 timer 线程；默认每秒投递 `eTimer`。先执行对应类型 handlers，再执行 general handlers；重复注册同一个 handler 会去重。handler 在消费线程内同步调用，所以耗时处理会阻塞后续事件。`_run` 只捕获 Queue.Empty，没有通用 handler 异常隔离；不能假设异常后该消费线程仍正常运行。`stop()` 会 join 两个线程，生命周期清理不可省略。

### 交易引擎与依赖

依赖链：示例/GUI → MainEngine → BaseGateway / BaseApp 对应引擎；网关通过 EventEngine 发出数据 → OmsEngine 缓存并更新持仓转换状态 → UI/策略等订阅者消费。

MainEngine 构造即启动 EventEngine、切换到 TRADER_DIR，并创建 LogEngine、OmsEngine、EmailEngine、WechatEngine。`send_order`、`cancel_order`、`connect` 按 gateway_name 转发；不是天然模拟交易。OMS 缓存 tick/order/trade/position/account/contract/quote，并维护活跃委托；收到 contract 时建立该网关的 OffsetConverter，后续成交/持仓/委托事件更新转换器。平今/平昨和冻结量规则位于 converter.py，修改它属于交易语义变更。

BaseApp 提供应用元数据及 engine_class；具体 CTP、CTA 等实现由外部 `vnpy_*` 包提供。本仓库不是全部交易插件的单体仓库。database/datafeed 按设置动态导入 `vnpy_<name>` 并缓存实例；数据库缺驱动时回退到 vnpy_sqlite，数据服务缺配置/模块时使用 BaseDatafeed。

证据：[MainEngine / OMS](D:/project/self/test/vnpy/vnpy/trader/engine.py)、[BaseGateway](D:/project/self/test/vnpy/vnpy/trader/gateway.py)、[BaseApp](D:/project/self/test/vnpy/vnpy/trader/app.py)、[converter](D:/project/self/test/vnpy/vnpy/trader/converter.py)、[database](D:/project/self/test/vnpy/vnpy/trader/database.py)、[datafeed](D:/project/self/test/vnpy/vnpy/trader/datafeed.py)。

### RPC

REQ/REP 用于同步远程调用；PUB/SUB 用于推送。客户端 `__getattr__` 生成调用代理，发送函数名/args/kwargs；服务端只查找已 register 的函数，返回成功结果或 traceback，客户端将失败包装为 RemoteException。默认调用超时为 30000 毫秒。

推送由 UTF-8 topic + pickle payload 两帧组成，订阅是前缀匹配。heartbeat 每 10 秒发布，容忍窗口 30 秒；非空主题订阅也会保留 heartbeat。stop 设置标志，join 等待线程，socket 在线程退出时关闭。RPC 核心不直接依赖 MainEngine；完整交易 RPC 示例通过外部插件整合。

证据：[client.py](D:/project/self/test/vnpy/vnpy/rpc/client.py)、[server.py](D:/project/self/test/vnpy/vnpy/rpc/server.py)、[common.py](D:/project/self/test/vnpy/vnpy/rpc/common.py)、[交易 RPC 示例](D:/project/self/test/vnpy/examples/client_server/run_server.py)。

**适合 AGENTS：** event/trader/rpc/alpha 四个职责、GUI 入口、插件边界、MainEngine 构造副作用。逐个引擎方法、全部子目录和协议细节可按需查看，不必全部载入每次上下文。

## Unstated conventions

这些规则在 README 中没有完整说明；其中部分明确写在源码 docstring，部分是现有实现/测试的惯例，不应混称为官方强制规范。

| 规则或惯例 | 依据与实际意义 |
|---|---|
| 使用 XxxData / XxxRequest、Enum 与派生 vt_* 标识 | [object.py](D:/project/self/test/vnpy/vnpy/trader/object.py) 的 dataclass、[constant.py](D:/project/self/test/vnpy/vnpy/trader/constant.py)。vt_symbol=`symbol.exchange.value`；vt_orderid=`gateway_name.orderid`。不能随意改分隔符或用显示文本替换枚举 |
| 维持双层事件命名 | [gateway.py](D:/project/self/test/vnpy/vnpy/trader/gateway.py) 的 on_tick/on_order 等同时发布通用事件和带 vt_* 后缀的事件；[event.py](D:/project/self/test/vnpy/vnpy/trader/event.py) 定义前缀。仅保留一种会改变订阅行为 |
| 网关回调后的数据视作不可变 | BaseGateway docstring 要求线程安全、非阻塞、断线重连；缓存对象应 copy.copy 后再发布。dataclass 并未 frozen，这一约束主要靠调用者遵守 |
| 核心代码有较密集类型标注 | 参数、返回值、实例属性及局部变量常有注解；使用 list[T]、T \| None、Callable。mypy 检查核心包；GUI 示例 main 没有注解，因此不能把观察夸大成全仓严格一致 |
| 错误处理按边界区分 | MainEngine 找不到网关时日志加空返回；BaseGateway 抽象接口、RpcClient.callback 使用抽象约束或 NotImplementedError；RPC 把服务端异常传给客户端；EventEngine 不吞掉所有回调异常。不要统一“修复”为 except Exception: pass |
| 对用户可见消息采用 gettext `_()` | [locale/__init__.py](D:/project/self/test/vnpy/vnpy/trader/locale/__init__.py)、engine.py、ui/widget.py。修改消息时关注翻译源，不直接编辑 .mo |
| 配置导入和引擎构造并非纯操作 | [utility.py](D:/project/self/test/vnpy/vnpy/trader/utility.py) 导入时选定运行目录并修改 sys.path；load_json 缺文件会写 `{}`；[setting.py](D:/project/self/test/vnpy/vnpy/trader/setting.py) 导入即加载配置；MainEngine 改 cwd。测试必须先建立隔离目录 |
| 并发测试有界等待且显式清理 | [test_event.py](D:/project/self/test/vnpy/tests/test_event.py)、[test_engine.py](D:/project/self/test/vnpy/tests/test_engine.py)、[test_rpc.py](D:/project/self/test/vnpy/tests/test_rpc.py)。沿用 deadline、finally 和 FakeGateway，而不是依赖真实连接或无限 sleep |
| 更改全局状态的测试恢复原值 | [test_data_services.py](D:/project/self/test/vnpy/tests/test_data_services.py) 对 SETTINGS 和缓存单例 try/finally 恢复，避免测试顺序依赖 |

**适合 AGENTS：** vt_* 标识、双事件发布、发布后不变、隔离配置、线程和单例清理、遵循局部异常语义。snake_case / PascalCase 等通用风格无需占用篇幅。

## Off-limits

以下是依据实际副作用提出的 Agent 操作边界；不意味着这些目录都被维护者声明为永久禁止修改。

| 对象 | 边界与证据 |
|---|---|
| `.mo`、构建产物、缓存 | [build_hook.py](D:/project/self/test/vnpy/vnpy/trader/locale/build_hook.py) 自动生成 .mo；[.gitignore](D:/project/self/test/vnpy/.gitignore) 忽略 build/dist、*.egg-info、*.pyc、.pytest_cache/.ruff_cache/.mypy_cache、notebook checkpoints 等。不要手改或提交这些产物 |
| 翻译模板与源文件 | [generate_pot.bat](D:/project/self/test/vnpy/vnpy/trader/locale/generate_pot.bat) 提取 vnpy.pot；[vnpy.po](D:/project/self/test/vnpy/vnpy/trader/locale/en/LC_MESSAGES/vnpy.po) 是翻译源，应在翻译任务中维护。批处理硬编码 `C:\veighna_studio`，不能认定本机可执行 |
| 已确认的第三方静态资源 | [docs/_static/vendor.css](D:/project/self/test/vnpy/docs/_static/vendor.css) 文件头包含 Bootstrap 3.3.7、normalize.css 3.0.3 的来源和许可。应按上游资源更新，不做随手格式化。没有证据把 Alpha101 等领域实现一概称为第三方 vendored 源码 |
| docs/_static 不能整体删掉 | .gitignore 有 `_static`，但 Git tree 实际跟踪 vendor.css、custom.css、vnpy.ico。忽略规则不代表这些文件未跟踪，也不能把 custom.css 自动归为生成物 |
| `.vntrader` 与账户文件 | utility.py 优先当前目录已有 `.vntrader`，否则使用用户 home；setting.py 读 vt_setting.json；[ui/widget.py](D:/project/self/test/vnpy/vnpy/trader/ui/widget.py:669) 读写 connect_<gateway>.json；engine.py 读写 wechat_setting.json。不要读取、覆盖、复制进报告或提交真实账户/密码/token/数据库配置 |
| 数据库、研究数据与模型 | setting.py 默认 database.db；[AlphaLab](D:/project/self/test/vnpy/vnpy/alpha/lab.py) 创建 daily/minute/component/dataset/model/signal 和 contract.json；.gitignore 忽略 lab/。这些可能是用户数据，不是可随意清理的临时文件 |
| 自动连接/启动策略的脚本 | [examples/no_ui/run.py](D:/project/self/test/vnpy/examples/no_ui/run.py) 调用 connect、init_all_strategies、start_all_strategies；[data_recorder.py](D:/project/self/test/vnpy/examples/data_recorder/data_recorder.py) 连接 CTP；[run_server.py](D:/project/self/test/vnpy/examples/client_server/run_server.py) 连接网关。未经明确交易/服务授权不要执行；无 GUI 不代表安全 |
| RPC 网络边界 | [simple_rpc/test_server.py](D:/project/self/test/vnpy/examples/simple_rpc/test_server.py) 绑定 `tcp://*`；核心使用 pickle.loads/recv_pyobj，未见认证或加密配置。不要对不可信网络开放，也不要把反序列化不可信消息当普通数据读取 |
| 资金动作与通知 | MainEngine.send_order/cancel_order 实际转发至 gateway；EmailEngine/WechatEngine 有外发能力。测试用 FakeGateway，不能用“验证能运行”为由下单、撤单、发送通知或使用现有凭据 |

本次没有打开用户真实 `.vntrader`，没有验证任何账户/端点，也没有证明示例连接一定属于仿真。不能仅凭 README 提到 SimNow 就对所有脚本作此假设。

**适合 AGENTS：** 不碰真实配置与资金动作、不运行自动交易示例、不暴露 pickle RPC、不手改生成文件/vendor.css、不要按 .gitignore 批量删除目录。具体密码、账户内容、服务地址不应进入 Agent 配置。

## How you figured it out

1. 阅读本地 Week 4 作业要求，限定只完成 Part I；枚举目标目录与配置，没有创建 Agent 指令文件。
2. 交叉比对 README / README_ENG、pyproject、三个安装脚本与 CI，区分用户安装、开发安装、额外插件以及 CI 验证链。以实际导入补充 README GUI 片段遗漏的 data manager 依赖。
3. 沿入口追踪 QApplication → MainEngine → gateway/app → EventEngine → OMS/converter；另外完整阅读 RPC client/server/common，确认协议、线程、心跳和异常行为。
4. 检查 tests/conftest 与代表性测试，先理解配置隔离和资源清理，再尝试最小事件测试。发现环境不齐后不安装大依赖，不扩大到全套测试；以独立事件 smoke check补充有限证据。
5. 只读执行 Ruff lint 和三个核心文件的格式探测，记录版本差异；不把“存在 Ruff”推断为“项目要求 Ruff format”。
6. 结合 .gitignore、Git tree、locale 构建 hook 和 vendor.css 文件头识别产物/第三方内容；再由设置、JSON 持久化和示例 connect/start 调用确认敏感边界。
7. 用户执行 install.bat 后，核实 `.venv/pyvenv.cfg`、安装分发元数据和 pip check，并在隔离配置目录内验证已安装包导入与独立事件测试函数。保留安装前记录，明确区分当前环境、已安装副本和源码测试；未补装开发依赖。
8. 用户补装 pytest/ruff/mypy 后，再验证五个核心测试文件共 27 项通过；RPC 沙箱权限失败经沙箱外回环重跑排除。Ruff 固定版本通过；mypy 实际失败并记录依赖/存根缺口，未擅自改源码或安装依赖。
9. 用户授权补齐 CI 依赖后，逐步执行工作流安装命令，确认 editable=true；pip check 通过，mypy 再检查 61 个源码文件全部通过。没有通过更改源码、屏蔽错误或放宽配置来消除报错。
10. 2026-10-26 根据用户反馈更新验证记录：四个 GUI 插件已安装、GUI 启动验证通过；VS Code 中完整 tests 为 162 passed, 2 warnings；uv build 已生成 .whl 和 .tar.gz。未将用户反馈表述为 Agent 独立执行，未猜测 warnings 内容。
11. 用户补充无 UI 测试入口 main_engine_test.py 后，只读检查该文件，确认其范围限于引擎创建与关闭；记录暂无交易账号/RPC 设置、其他集成场景未测，并将远程 CI 状态核查暂缓。
12. 查看近期 Git 历史：`3938dabf` 涉及 RPC 心跳与发布 socket，`ed893b7a` 涉及 BarGenerator 极值，当前 `c6e231ca` 涉及 mypy 修正。这支持优先研究对应回归测试，但提交说明不代替本次执行验证。

关键证据：[Week 4 作业](D:/project/self/test/cs146s/modern-software-dev-assignments/week4/chinese/assignment.md)、[CI](D:/project/self/test/vnpy/.github/workflows/pythonapp.yml)、[pyproject](D:/project/self/test/vnpy/pyproject.toml)、[test_rpc.py](D:/project/self/test/vnpy/tests/test_rpc.py)、[test_utility.py](D:/project/self/test/vnpy/tests/test_utility.py)。未进行外部网页检索，项目结构与命令结论来自本地仓库，执行结果另包含明确标注的用户手动反馈；Fork 归属仍未验证；远程 CI 是否绿色按用户要求暂不核查。本地构建产物已由用户确认生成。

下一阶段的一页 AGENTS 应保留：项目一句话、四个核心目录与入口、Python/CI命令、按组件测试、配置隔离和线程清理、少数交易数据契约、明确操作边界。完整探索过程、机器环境诊断、提交历史、目录全表、第三方依赖清单留在本报告即可。
