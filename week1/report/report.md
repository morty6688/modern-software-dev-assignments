# 第 1 周报告：剖析一次 MiMo CLI 函数修复会话

本报告依据本地 `D:\project\self\session.flows`，按照 [MiMo 版作业要求](../chinese/assignment-mimo.md)完成五部分分析。捕获日期为 **2026 年 10 月 13 日**，下文时间均为北京时间（UTC+8）。

**证据定位约定：** 将全部 HTTP 记录按 `request.timestamp_start` 升序编号为 R001—R018；[R009][R009] 的 `messages[15]` 指 [R009][R009] 请求体中从 **0 开始**编号的第 16 条消息。响应为 SSE 时，按原顺序合并 `choices[].delta` 中的文本及同一索引的工具调用参数，再以 `tool_call_id` 关联后续请求中的工具结果。附录给出每个编号对应的原始 flow ID。

已导出的请求编号使用 Markdown 引用链接，点击可打开对应 JSON；后面的消息或工具索引保持不变。链接目标仅包含请求体：文中标明“响应”或 `usage` 的证据仍来自原始 flow，工具调用与结果也可在下一请求的历史中核对。R001—R004、R018 未导出，保留原始记录编号。

`[OBSERVED]` 表示能在捕获中直接定位的内容；`[INFERRED]` 表示基于这些内容作出的解释或设计推断。“补充核验”专指撰写报告时对本机环境或文件的检查，不冒充原会话中的行为。

## 第一部分：捕获一次会话（15 分）

### 1. 环境与捕获范围

| 项目 | 实际记录或核验结果 |
|---|---|
| MiMo CLI | `0.1.15`；请求客户端标识含 `mimocode/0.1.15`，撰写时 `mimo --version` 也返回 `0.1.15` |
| 模型 | 全部 18 条请求的 `model` 均为 `mimo-v2.6-pro` |
| API | `https://api.xiaomimimo.com/v1/chat/completions`；全部为 `POST`，HTTP 状态均为 `200` |
| 代理路径 | flow 的客户端监听地址为 `127.0.0.1:58888`，上游连接目标为 `api.xiaomimimo.com:443` |
| mitmproxy | 本机安装清单核验为 `12.2.3`；版本号不是从模型请求体推出来的 |
| 操作系统与 Shell | [R005][R005] 的 `tools[1].function.description` 明确写有 `Be aware: OS: win32, Shell: pwsh` |
| Python | 原始失败回溯指向 Conda 的 `cs146s` 环境；该环境在撰写时核验为 Python `3.12.14`，捕获本身没有运行版本查询 |
| 实验项目 | `D:\project\self\test\w1-lab1`；实际修改与测试均针对这个独立目录 |
| 本机项目配置 | `week1/lab/mimocode.json`；撰写时核验仍使用本地代理供应商 `mimo-capture` |
| 认证来源 | 当前配置引用环境变量 `MIMO_API_KEY`；捕获不能证明该变量当时由手工加载还是终端扩展注入 |
| 数据规模 | 2,105,787 字节，共 18 条 HTTP flow；16 条 SSE 响应、2 条普通 JSON 响应，均有可解析的响应体 |
| 正式任务范围 | **[R005][R005]—[R017][R017]，共 13 次模型请求**；首次请求约 21:17:27，最终响应于约 21:19:24 完成 |

源文件 SHA-256：

```text
7edd4775c91bd1111f45a921c4ad9e90f7c137ef8bb68af4a5f8db8c0eb41c5a
```

R001、R004 的用户消息要求生成不超过 48 字符的标题，响应调用 `StructuredOutput`；R003、R018 要求预测用户最可能的下一条输入。R002 仅回复 `hello`。这些请求都经过同一代理，但应与正式修复任务分开统计，不能当作编程步骤或子智能体活动。

### 2. 可复现配置

当前配置中与捕获有关的内容如下。它是撰写时核验的配置；网络路径与 flow 一致，但原始终端启动命令未被 HTTP 捕获记录保存。

```json
{
  "model": "mimo-capture/mimo-v2.6-pro",
  "small_model": "mimo-capture/mimo-v2.6-pro",
  "provider": {
    "mimo-capture": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "MiMo Capture",
      "options": {
        "baseURL": "http://127.0.0.1:58888/v1",
        "headers": {"api-key": "{env:MIMO_API_KEY}"}
      },
      "models": {
        "mimo-v2.6-pro": {"name": "MiMo V2.6 Pro"}
      }
    }
  }
}
```

重现实验时，可从 `week1/lab/missing-function-demo` 复制故障状态的 Python 文件和 README 到独立实验目录，将上述配置放在启动 MiMo 的项目目录，并准备 `MIMO_API_KEY`。使用新的捕获文件名保留原记录：

```powershell
mitmweb --listen-host 127.0.0.1 --listen-port 58888 --web-open-browser --mode reverse:https://api.xiaomimimo.com -w D:\project\self\session-new.flows
```

在另一个已准备好凭证的终端中启动：

```powershell
mimo --model mimo-capture/mimo-v2.6-pro
```

本次实际副本只包含三个 Python 文件，缺少 README；MiMo 因此搜索上层目录，并在作业仓库的原示例目录找到接口约定。这一点影响了调用轨迹，不能把本次过程写成“在实验目录直接读到 README”。如需复现这一额外故障，应保留缺少 README 的初始状态及原示例的位置；正常的新实验则应将 README 一并复制。

### 3. Q1：实际发送的任务

下列内容来自 [R005][R005].messages[1]，也是本报告原有的任务说明：

```text
阅读D:\project\self\test\w1-lab1项目，其中 pricing.py 的 calculate_total 函数被删除了，其他模块仍然依赖它。请恢复功能。

请按以下步骤完成：
1. 阅读 README.md，列出明确的任务计划，并在执行过程中更新状态。
2. 修改代码前，先运行 python -m unittest -v，解释实际错误。
3. 检查相关模块，按照 README.md 的接口约定恢复 calculate_total。
4. 保留现有测试，在 test_receipt.py 中增加边界测试，覆盖负数优惠、优惠超过折前金额、优惠恰好等于折前金额。
5. 重新运行完整测试，直到全部通过。
6. 汇报修改的文件、失败原因、修复方法和最终测试结果。

不要通过删除导入、跳过测试或放宽断言来绕过故障。
```

### 4. 四项会话要求与证据

| 要求 | 证据与判断 |
|---|---|
| 至少操作两个文件 | `[OBSERVED]` [R013][R013] 响应中的 `Edit` 恢复 `w1-lab1/pricing.py`；[R014][R014] 的 `Edit` 为 `w1-lab1/test_receipt.py` 增加三个测试。成功结果分别出现在 [R014][R014].messages[28]、[R015][R015].messages[30]。 |
| 至少失败一次并恢复 | `[OBSERVED]` [R008][R008] 发出首次测试命令；[R009][R009].messages[15] 返回缺少 `calculate_total` 的导入错误。修复后，[R016][R016].messages[32] 返回 `Ran 7 tests` 和 `OK`。 |
| 足够长并有明确计划 | `[OBSERVED]` [R011][R011]—[R012][R012] 创建并启动 T1；[R013][R013] 响应展示六步计划；[R017][R017] 最终报告更新完成状态。不过计划建立较晚，未严格遵守用户“先列计划”的顺序。 |
| 使用自己的临时项目 | `[OBSERVED]` 测试的 `workdir` 和两次修改的目标都在作业仓库之外的 `w1-lab1`。但 [R007][R007].messages[6] 的完整目录列表没有 `.git`，捕获中也没有 `git init`；撰写时检查同样未见 `.git`。可以确认独立实验项目，不能声称已创建独立 Git 仓库。 |

下方按四项要求展开证据。示例优先引用已经导出的请求体：其中 `role: "assistant"` 的历史消息保存了上一轮模型输出，`role: "tool"` 保存客户端执行工具后的反馈。工具反馈不是模型 API 自己运行测试的响应；它是客户端在下一轮请求中送回模型的结果。JSON 示例注明了字段位置与删节范围，可直接点击请求编号核对。

#### 4.1 至少操作两个文件：从修改参数到成功结果

`[OBSERVED]` 第一处修改可在 [R014][R014] 的 `messages[27].tool_calls[0]` 中查看，它保存了上一轮 R013 响应发出的 Edit 调用。工具名为 `Edit`，调用 ID 为 `call_a877bcafb2bc4c5eba51ffad`。以下将 `function.arguments` 这个 JSON 字符串解析为对象后展示，参数内容未改写：

```json
{
  "file_path": "D:\\project\\self\\test\\w1-lab1\\pricing.py",
  "old_string": "# calculate_total(items, discount_cents=0) 已被故意删除。\n# receipt.py 仍然导入并调用它，需要在实验会话中恢复。",
  "new_string": "def calculate_total(items: list[tuple[int, int]], discount_cents: int = 0) -> int:\n    \"\"\"实付金额 = 折前金额 - 优惠金额；优惠不能为负，也不能超过折前金额。\"\"\"\n    if discount_cents < 0:\n        raise ValueError(\"discount must be non-negative\")\n    subtotal = calculate_subtotal(items)\n    if discount_cents > subtotal:\n        raise ValueError(\"discount cannot exceed subtotal\")\n    return subtotal - discount_cents"
}
```

这段参数不仅指出了修改目标，也说明模型用完整函数替换了“函数已删除”的两行注释。对应的 [R014][R014] `messages[28]` 原文为：

```json
{
  "role": "tool",
  "tool_call_id": "call_a877bcafb2bc4c5eba51ffad",
  "content": "Edit applied successfully."
}
```

第二处修改来自 [R015][R015] 的 `messages[29].tool_calls[0]`，工具名同样为 `Edit`，调用 ID 为 `call_2b9ea07931be4f87bca8a48f`。下面只摘录解析后参数的 `file_path` 与 `old_string` 字段；完整 `new_string` 可在链接中查看，其中保留原测试并追加三个边界用例：

```json
{
  "file_path": "D:\\project\\self\\test\\w1-lab1\\test_receipt.py",
  "old_string": "    def test_negative_quantity_is_rejected(self):\n        with self.assertRaises(ValueError):\n            build_receipt([(100, -1)])"
}
```

紧随其后的 [R015][R015] `messages[30]` 为：

```json
{
  "role": "tool",
  "tool_call_id": "call_2b9ea07931be4f87bca8a48f",
  "content": "Edit applied successfully."
}
```

**判断：** 两个不同文件路径分别对应不同的调用 ID，并且两个 ID 都收到成功结果。因此有证据证明两个文件确实被修改，而非仅在计划里提到它们。至于修改是否正确，还要由下面的测试结果验证。

#### 4.2 至少失败一次并恢复：同一命令的前后结果

`[OBSERVED]` [R009][R009] 的 `messages[13].tool_calls[1]` 保存了 R008 响应发出的首次测试调用。其 ID 是 `call_07252762a57849d9a9bcc26e`，解析后的参数为：

```json
{
  "command": "python -m unittest -v",
  "workdir": "D:\\project\\self\\test\\w1-lab1",
  "description": "Run unit tests to see failures"
}
```

对应的 `messages[15]` 是 `role: "tool"`，`tool_call_id` 与上述 ID 一致。其 `content` 中的关键错误行如下；此处只摘录错误原因，完整加载栈仍保留在 JSON 中：

```text
ImportError: cannot import name 'calculate_total' from 'pricing' (D:\project\self\test\w1-lab1\pricing.py). Did you mean: 'calculate_subtotal'?
```

```text
Ran 1 test in 0.000s

FAILED (errors=1)
```

两次 Edit 完成后，[R016][R016] 的 `messages[31].tool_calls[0]` 保存了复测调用；解析后的参数如下。可见执行命令与工作目录均与首次测试一致：

```json
{
  "command": "python -m unittest -v",
  "description": "Re-run full unit tests",
  "workdir": "D:\\project\\self\\test\\w1-lab1"
}
```

该调用 ID 为 `call_78f94d7a38e5464d8077554f`；与它关联的 [R016][R016] `messages[32].content` 末尾为：

```text
Ran 7 tests in 0.000s

OK
```

**判断：** 原始测试模块先因导入错误无法加载，修复后完整七项测试全部通过。这里的成功依据是工具返回的测试输出，而不是助手最终回复中的“已完成”。前后的 `Ran 1 test` 与 `Ran 7 tests` 含义不同：前者是导入失败占位项，后者才是实际运行的七个业务测试。

#### 4.3 明确计划：计划文本和任务状态分别举证

`[OBSERVED]` [R012][R012] 的 `messages[23].tool_calls[0]` 中，Task 的参数如下；`messages[24]` 则确认客户端已经建立了可引用的任务 T1：

```json
{
  "operation": {
    "action": "create",
    "summary": "恢复 calculate_total 并补充边界测试"
  }
}
```

```json
{
  "role": "tool",
  "tool_call_id": "call_0ae25942ad2f405f97ba84d6",
  "content": "Created T1 (open): 恢复 calculate_total 并补充边界测试"
}
```

详细的六步计划在 R013 响应中出现，并被保留在 [R014][R014] 的 `messages[27].content` 开头。下面逐字摘录该计划部分：

```text
**任务计划**
1. 阅读 README，明确 `calculate_total` 接口约定 — 完成（README 在源目录 `missing-function-demo`，w1-lab1 为其副本）
2. 运行 `python -m unittest -v`，记录实际错误 — 完成
3. 恢复 `pricing.calculate_total` — 进行中
4. 在 `test_receipt.py` 增加边界测试 — 待办
5. 重跑完整测试至全部通过 — 待办
6. 汇报 — 待办
```

测试通过之后，[R017][R017] 的 `messages[33].tool_calls[0]` 保存了 Task.done 参数，`messages[34]` 保存其结果：

```json
{
  "operation": {
    "action": "done",
    "id": "T1",
    "event_summary": "恢复 calculate_total，新增 3 个边界测试，7 个测试全部通过"
  }
}
```

```json
{
  "role": "tool",
  "tool_call_id": "call_fb7b043f86914a409f688b9b",
  "content": "done → done"
}
```

**判断：** 既有明确步骤，也有真实的任务创建和完成状态，所以“存在计划并跟踪任务”有直接证据。但计划首次展示时，前两步已经被标为完成；这也直接支持“计划建立偏晚”的判断。六步自然语言列表与一个 Task 工作项不能混为六个独立创建的任务。

#### 4.4 自己的临时项目：路径证据及其边界

`[OBSERVED]` 上面首次测试和复测的 `workdir` 都是 `D:\project\self\test\w1-lab1`，两个 Edit 的 `file_path` 也位于该目录。它与存放本作业的 `D:\project\self\test\cs146s\modern-software-dev-assignments` 是不同路径。

[R007][R007] 的 `messages[6].content` 还保存了 `Get-ChildItem -Force` 的目录输出。以下只摘录目录行与三个文件行，移除了终端颜色控制码：

```text
    Directory: D:\project\self\test\w1-lab1
-a---          2026/10/13    20:52            597 pricing.py
-a---          2026/10/13    20:52            534 receipt.py
-a---          2026/10/13    20:52           1076 test_receipt.py
```

**判断：** 用户指定的目标、工具实际执行位置和修改文件位置相互吻合，足以确认工作发生在独立实验目录。关于 Git 仓库属性，应检查链接中的完整目录列表以及实际 Git 操作；不能仅用上面的节选证明。完整列表未见 `.git`，整个捕获也没有 Git 初始化或仓库状态命令，因此本报告只确认“独立实验项目”，保留“是否已建立独立 Git 仓库”的证据缺口。

### 5. mitmweb flows

| 请求 | 北京时间 | 消息数 | 可见工具数 | 请求体字节数 | 用途 |
|---|---|---:|---:|---:|---|
| R001 | 21:12:55.435 | 3 | 1 | 1,586 | 问候会话的标题生成 |
| R002 | 21:12:56.481 | 2 | 17 | 96,712 | hello 问候回复 |
| R003 | 21:13:12.555 | 4 | 0 | 766 | 预测下一条用户输入 |
| R004 | 21:17:26.722 | 3 | 1 | 2,377 | 修复任务的标题生成 |
| [R005][R005] | 21:17:27.681 | 2 | 17 | 97,504 | 列目录、尝试读取 README |
| [R006][R006] | 21:17:36.931 | 5 | 17 | 98,631 | 修正 PowerShell 命令、重试 README |
| [R007][R007] | 21:17:43.088 | 8 | 17 | 99,924 | 搜索 README、读取三个源文件 |
| [R008][R008] | 21:17:51.736 | 13 | 17 | 104,938 | 继续搜索、首次运行测试 |
| [R009][R009] | 21:18:06.602 | 16 | 17 | 115,016 | 收到测试失败，定位示例来源 |
| [R010][R010] | 21:18:17.824 | 19 | 17 | 121,816 | 读取原示例 README 和代码 |
| [R011][R011] | 21:18:24.120 | 23 | 17 | 130,173 | 创建任务 T1 |
| [R012][R012] | 21:18:36.594 | 25 | 17 | 132,933 | 启动 T1 |
| [R013][R013] | 21:18:41.597 | 27 | 17 | 133,289 | 展示六步计划、恢复函数 |
| [R014][R014] | 21:18:53.834 | 29 | 17 | 135,306 | 新增三个边界测试 |
| [R015][R015] | 21:19:02.549 | 31 | 17 | 136,882 | 重新运行完整测试 |
| [R016][R016] | 21:19:07.906 | 33 | 17 | 138,145 | 收到 7 项通过结果，完成 T1 |
| [R017][R017] | 21:19:14.599 | 35 | 17 | 138,609 | 输出最终报告 |
| R018 | 21:19:26.420 | 4 | 0 | 2,976 | 预测下一条用户输入 |

### 6. 脱敏与证据边界

报告正文没有复制原始认证请求头或完整流量。另按提交需要，将 [R005][R005]—[R017][R017] 的请求体脱敏导出至 [requests 目录](requests/README.md)；这些导出保留消息索引和调用 ID，具体替换范围见目录说明。引文中的个人用户目录和会话记忆路径使用 `[REDACTED: ...]` 明确替代；与任务有关的实验路径和文件名予以保留，便于定位。搜索输出中与本任务无关的项目路径不作为报告摘录。

HTTP `200` 只说明模型接口请求成功，不代表模型随后要求执行的本地工具成功。首次测试失败、PowerShell 参数错误和文件不存在，都来自后续请求中的 `role: "tool"` 消息。

## 第二部分：注释系统提示词（25 分）

### 1. 结构与顺序

`[OBSERVED]` [R005][R005]—[R017][R017] 均只有一条 `role: "system"` 消息，位于 `messages[0]`，内容保持一致；没有 `role: "developer"`。主要章节顺序如下。右栏是对设计目的的 `[INFERRED]` 分析，不等同于已经观察到指令被完整执行。

| 顺序 | 章节或内容 | 希望促成的行为与防范的问题 |
|---|---|---|
| 1 | MiMoCode 身份、授权安全测试边界、URL 规则 | 先限定角色和全局边界，减少能力描述被误当成无限授权，以及编造链接。 |
| 2 | `System` | 定义输出可见性、权限规则、工具名和数据边界；防范把工具内容当成新指令、把历史记忆当成实时事实。 |
| 3 | `Doing tasks` | 将软件工程请求落到实际代码修改，约束过度设计、额外功能和不必要抽象。 |
| 4 | `Executing actions with care` | 根据可逆性和影响范围处理删除、推送、共享状态等操作，防止“修复问题”扩大成未授权操作。 |
| 5 | `Using your tools` | 要求准确工具名、控制单轮调用数量、跟踪多步骤任务，并区分 Task 与 Actor 的职责。 |
| 6 | `Skills` | 说明技能的发现与加载方式，要求使用当前已暴露能力，防止凭记忆编造工具名。 |
| 7 | `Tone and style` | 控制回复长度、导航格式及过程更新，使用户能跟进任务，同时减少无关叙述。 |
| 8 | `Memory system` 及其子节 | 区分项目记忆、会话检查点、任务进度和全局记忆，明确读写责任，避免重复拉取上下文或覆盖系统维护的状态。 |
| 9 | `<available_skills>` | 提供 20 项技能的名称、触发描述和位置，供按需选择；这些是技能目录，不是 20 个额外工具。 |

`[INFERRED]` 这种顺序先确定边界，再给出执行原则和工具纪律，最后附加记忆与技能目录，便于模型把后面的具体能力放入前面的约束中使用。但本次轨迹也表明“写在系统提示词中”不保证模型执行正确：Bash 描述已标明 PowerShell，模型仍先发出了 `ls -la`。

### 2. 语气与详略程度

`[OBSERVED]` [R005][R005].messages[0] 的 `Tone and style` 包含以下摘录：

> Match responses to the task: a simple question gets a direct answer, not headers and sections. Keep responses short and concise.

> Before your first tool call, state in one sentence what you're about to do.

> While working, give short updates at key moments (found something, changed direction, hit a blocker). Brief is good — silent is not.

`[INFERRED]` 这些指令同时约束“过度解释”和“长时间无反馈”两种失效模式。花费少量固定提示 token，可以让长任务保持可跟踪，而不需要用户反复询问状态。

`[OBSERVED]` [R005][R005] 响应先说“我先读取 README 和项目结构，再跑测试确认失败原因。”；[R008][R008]、[R009][R009] 又说明 README 的搜索方向。最终 [R017][R017] 给出修改文件、故障原因和测试结果，符合任务所需的汇报范围。

### 3. 何时不应行动

`[OBSERVED]` [R005][R005].messages[0] 中的关键原文包括：

> If the user denies a tool you call, do not re-attempt the exact same tool call — adjust your approach.

> Match the scope of your actions to what was actually requested.

> When you encounter an obstacle, do not use destructive actions as a shortcut to simply make it go away.

系统还列出删除文件或分支、覆盖未提交修改、强制推送、发送消息及修改共享基础设施等高影响操作；开头也要求拒绝恶意破坏、DoS 和供应链攻击等请求。

`[INFERRED]` 这些规则分别防范重复绕过拒绝、把一次授权无限扩大，以及通过删除或跳过检查掩盖根因。本次故障恢复采用补回函数和增加测试，没有出现删除导入或放宽原有断言；但没有发生权限拒绝或破坏性请求，不能据此证明相应拦截机制已经实际触发。

### 4. 环境上下文出现在哪里

| 上下文 | 捕获中的位置 | 解释 |
|---|---|---|
| Windows 与 PowerShell | [R005][R005].tools[1].function.description：`Be aware: OS: win32, Shell: pwsh` | 客户端注入到 Bash 的工具描述中。工具名称叫 Bash，不代表实际执行的是 Bash Shell。 |
| 目标项目路径 | [R005][R005].messages[1] 的用户指令 | 来自用户，不应归因于模型自行发现或系统环境块。 |
| 测试工作目录 | [R008][R008]、[R015][R015] 响应中的 Bash 参数 `workdir` | 模型显式指定为 `D:\project\self\test\w1-lab1`。 |
| 文件内容、目录与 Python 环境路径 | [R007][R007]—[R011][R011] 的工具结果，例如 [R009][R009].messages[15] 的回溯 | 是执行后反馈到上下文的数据，首次请求不包含这些读取结果。 |
| 记忆、技能位置 | [R005][R005].messages[0]，以及 [R012][R012].messages[1].content[1] | 前者提供通用规则和目录，后者补充本次会话的实际记忆入口。 |

`[OBSERVED]` 系统提示词虽提到 `AGENTS.md` 可承载持久授权，但本次捕获没有加载某个 `AGENTS.md` 正文的证据；也没有独立的 `<env>` 块、明确的默认工作目录值或当前 Git 分支。HTTP 时间戳用于报告定位，不表示该时间被作为模型指令注入。

### 5. 运行时提醒与动态上下文

`[OBSERVED]` 本次确实出现了 `<system-reminder>`，但它不在新增的 system 消息中。[R005][R005]—[R011][R011] 的 `messages[1].content` 是字符串；从 **[R012][R012]** 开始，它变为两个文本块：`content[0]` 保留用户任务，`content[1]` 追加以下提醒。个人目录和会话路径已脱敏：

```text
<system-reminder>
This session has memory at [REDACTED: session memory path]. Recall content
not in your context with:
- memory({ operation: "search", query: "<keyword>" })
- read(file_path="[REDACTED: session memory path]/...")
- task({ operation: "list" })
- actor({ operation: "status", actor_id: "<id>" })

Don't ask the user about something memory may already record.
</system-reminder>
```

该提醒支持两个不同用途：

1. **历史信息召回。** `[OBSERVED]` 它给出本次会话的记忆位置，以及搜索、读取入口；`[INFERRED]` 目的是在历史不全时先查已有信息，减少重复向用户询问。
2. **工作状态查询。** `[OBSERVED]` 它提示查询任务列表和 Actor 状态；任务状态又通过真实工具结果动态回灌：[R012][R012].messages[24] 为 `Created T1 (open)`，[R013][R013].messages[26] 为 `start → in_progress`，[R017][R017].messages[34] 为 `done → done`。`[INFERRED]` 这种设计用于把当前工作状态交还给模型，避免只依赖先前的自然语言计划。

本次只观察到这一种提醒文本，没有观察到权限拒绝、计划模式切换或压缩恢复提醒。提醒提供了查询方法，并不意味着模型真的调用过 Memory 或 Actor；调用统计中两者均为 0。

`[INFERRED]` 会话路径和任务状态具有时效性，中途注入能让它们在相关阶段进入上下文。[R012][R012] 恰好紧接首次 Task.create，但时间上的相邻不足以证明 Task.create 就是注入的内部触发条件。另一个接口细节是提醒使用小写调用示意，实际注册工具名为 `Memory`、`Read`、`Task`、`Actor`；执行时应以真实 schema 为准。

## 第三部分：注释工具设计（25 分）

### 1. 工具清单与变化

统计单位是当前请求 `tools[].function` 中按名称去重的工具。[R005][R005]—[R017][R017] 的完整工具定义逐项相同，没有发现中途加载新工具。

| 范围 | 内置工具 | 可见 MCP 工具 | 可见插件／自定义工具 | 去重总数 | 变化 |
|---|---:|---:|---:|---:|---|
| 正式任务 [R005][R005]—[R017][R017] | 17 | 0 | 0 | **17** | 无 |

17 个名称按请求中的顺序为：`Question`、`Bash`、`Read`、`Glob`、`Grep`、`Edit`、`Write`、`NotebookEdit`、`Actor`、`WebFetch`、`SkillSearch`、`Skill`、`PlanExit`、`Memory`、`History`、`Task`、`Cron`。来源分类依据这些已暴露的 MiMo 内置工具名称与描述；“可见 MCP 为 0”不等于已核查机器上所有 MCP 配置。

正式任务共发起 **21 次工具调用请求**：Bash 8 次、Read 8 次、Task 3 次、Edit 2 次。其中一次 Read 被客户端取消，不能把 21 次都理解为成功执行。全部 21 个调用 ID 都能在后续请求中找到对应工具结果或取消说明。

辅助请求的集合不同：R001、R004 仅暴露 `StructuredOutput`；R003、R018 没有 tools 字段。若计算整个文件的工具名称并集，是 **18 个**，但正式编程智能体每次可见的仍为 17 个。这里的集合差异源于标题与输入建议两类辅助调用，不能写成主会话触发了动态工具加载。

### 2. 延迟加载与技能搜索

`[OBSERVED]` 未发现延迟工具搜索接口，也没有工具集合扩展事件。`SkillSearch` 本身是已暴露的一个工具，其描述是搜索技能；`Skill` 用于将技能指令注入对话。[R005][R005].messages[0] 明确写有：

> Skills overlay *behavior* and *guidance*; they do not change the tool set.

因此不能把 20 项可用技能加到 17 个工具上，也不能把 `SkillSearch` 当作额外 MCP 工具的搜索入口。本次两个技能工具都未被调用；系统文本提到的 `Workflow` 也没有出现在真实工具列表中。

### 3. 工具一：Edit

证据：[R005][R005].tools[5].function。以下为参数 schema 的结构摘录，仅省略说明文字和 `$schema`：

```json
{
  "type": "object",
  "properties": {
    "file_path": {
      "type": "string"
    },
    "old_string": {
      "type": "string"
    },
    "new_string": {
      "type": "string"
    },
    "replace_all": {
      "type": "boolean"
    }
  },
  "required": [
    "file_path",
    "old_string",
    "new_string"
  ],
  "additionalProperties": false
}
```

三个必填参数指定目标文件、待匹配原文和替换文本；可选 `replace_all` 默认 false。`additionalProperties: false` 限制额外字段。接口没有提供模糊匹配阈值或自动挑选某个重复匹配项；其描述规定原文不存在或出现多次时应失败。

描述中一条很具体的约束是：

> Never include any part of the line number prefix in the old_string or new_string.

`[INFERRED]` 这防范了模型把 Read 返回的 `14: ` 等展示前缀当成源文件内容，导致匹配失败或把行号写入文件。不能仅凭这句话证明开发团队过去发生过多少次同类错误，但可以明确识别它针对的错误行为。

`[OBSERVED]` [R008][R008].messages[10] 中的源码带行号前缀；[R013][R013] 的 Edit 参数只提交原来的两行注释，不含行号，随后 [R014][R014].messages[28] 返回 `Edit applied successfully.`。这里既有 schema，也有实际使用证据。

`[INFERRED]` Edit 只负责精确文本变更，不负责判断业务逻辑正确或运行测试。因此周边系统仍需要 Read 获取上下文、Bash 执行测试，以及模型判断该改动是否解决问题。

### 4. 工具二：Task

证据：[R005][R005].tools[15].function。顶层参数要求 `operation`；它通过 `anyOf` 列出不同 action 的 schema。以下摘录其中的 **create 分支**，其余操作仍存在：

```json
{
  "type": "object",
  "properties": {
    "action": {
      "type": "string",
      "const": "create"
    },
    "summary": {
      "type": "string",
      "minLength": 1
    },
    "parent_id": {
      "type": "string",
      "minLength": 1
    },
    "session_id": {
      "type": "string",
      "minLength": 1
    }
  },
  "required": [
    "action",
    "summary"
  ],
  "additionalProperties": false
}
```

`create` 必填 `action` 和非空 `summary`，可选 `parent_id` 与 `session_id`；任务 ID 由工具创建后返回。`start`、`done` 等动作必填 `action`、`id`，可选 `event_summary` 和 `session_id`。这样的操作接口表达受控状态转换，而非允许模型任意覆盖一个状态对象。

描述中的原文为：

> Only mark `done` when the work is FULLY accomplished. If tests fail, the
> implementation is partial, or you hit an unresolved error, keep it
> in_progress or `block` it — never `done`.

`[INFERRED]` 这针对“代码已经改过，所以任务就算完成”的过早结束行为。状态机让完成、阻塞与放弃可区分，但描述本身并不等于自动执行了测试验证。

`[OBSERVED]` 本次 T1 先创建、再进入 `in_progress`，收到七项测试通过后才调用 `done`。Task 没有运行代码或委派子智能体；后者由单独的 Actor 提供。它也没有把用户的六步计划自动拆成六个任务，本次只创建了一个 T1。

选择 Edit 和 Task，是因为它们分别控制**文件内容变更**和**工作状态转换**。两者都采用结构化参数，但失败条件、成功含义和对周边系统的依赖明显不同。

## 第四部分：基于证据的行为分析（25 分）

### 1. 错误恢复

**主故障：缺失函数导致测试无法导入。 `[OBSERVED]`**

[R008][R008] 响应发出 Bash 调用 `call_07252762a57849d9a9bcc26e`，命令为 `python -m unittest -v`，`workdir` 指向实验目录。结果在 [R009][R009].messages[15] 中出现。以下为两段逐字摘录，仅统一换行显示：

```text
ImportError: cannot import name 'calculate_total' from 'pricing' (D:\project\self\test\w1-lab1\pricing.py). Did you mean: 'calculate_subtotal'?
```

```text
Ran 1 test in 0.000s

FAILED (errors=1)
```

其后的恢复过程如下：

| 模型轮次 | 实际行为 | 结果证据 |
|---|---|---|
| [R009][R009] | 根据目录搜索结果定位原示例目录 | [R010][R010].messages[17]、[18] |
| [R010][R010] | 读取原示例 README、pricing.py 和测试，确定接口约定 | [R011][R011].messages[20]—[22] |
| [R011][R011] | 创建 T1 | [R012][R012].messages[24] |
| [R012][R012] | 将 T1 标为进行中 | [R013][R013].messages[26] |
| [R013][R013] | 用 Edit 恢复 calculate_total，复用 calculate_subtotal | [R014][R014].messages[28]，调用 ID `call_a877bcafb2bc4c5eba51ffad` |
| [R014][R014] | 用 Edit 保留原有测试并增加三个边界用例 | [R015][R015].messages[30]，调用 ID `call_2b9ea07931be4f87bca8a48f` |
| [R015][R015] | 再次运行完整测试 | [R016][R016].messages[32]，调用 ID `call_78f94d7a38e5464d8077554f` |

[R016][R016].messages[32] 的结果逐字摘录：

```text
Ran 7 tests in 0.000s

OK
```

从模型在 [R009][R009] 首次收到测试错误，到 [R015][R015] 发出成功复测命令，共 **7 轮模型响应**，其中包括定位文档、建立任务和修复；成功结果在下一请求 [R016][R016] 中进入模型上下文。若只统计代码动作，则是两次 Edit 加一次复测，没有出现复测失败后的第二轮代码修订。

**额外故障：Shell 参数与缺少 README。 `[OBSERVED]`**

[R005][R005] 先调用 `ls -la`，[R006][R006].messages[3] 报错。以下摘录移除了终端颜色控制码，文字保持原样：

```text
Get-ChildItem: A parameter cannot be found that matches parameter name 'la'.
```

同一响应里的 Read 调用没有正常执行；[R006][R006].messages[4] 的原文是：

```text
Tool call cancelled because an earlier tool call in this response failed.
```

[R006][R006] 随后改用 `Get-ChildItem -Force` 并重试 Read。目录读取成功，但 [R007][R007].messages[7] 返回：

```text
File not found: D:\project\self\test\w1-lab1\README.md
```

模型随后扩大搜索范围，最终在 [R011][R011].messages[20] 读到原示例 README。这说明同一模型响应中发出多个工具调用，并不保证它们都被执行；也说明报告必须记录工具结果，不能只数模型发出的调用。

### 2. 规划来自哪里

`[OBSERVED]` 用户在 [R005][R005].messages[1] 明确要求列计划；[R005][R005].messages[0] 也要求：

> Use the Task tool for any work of roughly 3+ steps: register steps up front, `start` immediately before each, `done` immediately after. Never batch completions.

Task 描述进一步要求跟踪多步骤工作。实际执行中，[R011][R011] 创建任务，[R013][R013] 展示六步自然语言计划。因此有证据表明规划受到**用户指令、系统指令和工具接口**的共同约束，不能把它描述成完全自发行为。

`[OBSERVED]` 遵循并不完整：模型已经发起 15 次工具调用请求之后才在 [R011][R011] 创建 T1，首次测试也早于完整计划展示。它满足“存在明确计划”的会话要求，但没有严格遵守“先规划再执行”的顺序，也没有为每一步分别建立 Task。

`[INFERRED]` 这些指令各自对模型行为的因果贡献无法由单次轨迹分离；需要对照实验，才能判断去掉某条指令后是否还会规划。

### 3. 计划与任务状态如何推进

`[OBSERVED]` 三个状态调用形成完整链条：

| 调用所在响应 | operation | 后续请求中的工具结果 |
|---|---|---|
| [R011][R011] | `{"action":"create","summary":"恢复 calculate_total 并补充边界测试"}` | [R012][R012].messages[24]：`Created T1 (open): 恢复 calculate_total 并补充边界测试` |
| [R012][R012] | `{"action":"start","id":"T1"}` | [R013][R013].messages[26]：`start → in_progress` |
| [R016][R016] | `{"action":"done","id":"T1","event_summary":"恢复 calculate_total，新增 3 个边界测试，7 个测试全部通过"}` | [R017][R017].messages[34]：`done → done` |

模型通过后续请求的历史消息看到这些状态结果。[R013][R013] 的六步计划随后保留在 [R014][R014].messages[27] 中，并继续进入后面的请求；[R017][R017] 的最终文本将六步标为完成。

需要区分：**T1 是真实工具维护的一个工作项，六步列表是助手生成的文本计划。** 本次没有调用 Task.list 或 Task.get，也没有证据表明每轮都注入一个完整任务数据库快照。[R012][R012] 起追加的提醒只提供查询入口，不包含完整任务状态表。

### 4. 子智能体

`[OBSERVED]` [R005][R005]—[R017][R017] 中 Actor 始终可用，但 21 次工具调用请求里没有 Actor。Task 的三次调用都是状态管理；标题生成和输入建议请求也有独立的明确用途，不能当作委派证据。因而本次没有可观察到的子智能体接收信息、执行过程或返回结果。

`[INFERRED]` 根据 [R005][R005].tools[8].function 的 Actor schema 与描述，若需要委派，`spawn` 分支必填 `description`、`prompt`、`subagent_type`，后者可为 `explore` 或 `general`；可选 `task_id` 将工作关联到已存在的 Task。描述称 spawn 返回 `actor_id`，结果可通过完成通知或 wait/status 获取。工具还提醒子智能体只能看到所写的 prompt，因此不能假设它自动拥有父对话的全部历史。

上述是从捕获到的接口定义推断的使用方式，不是本次会话中实际发生的行为。

### 5. 上下文管理

`[OBSERVED]` 主任务请求逐步积累历史：

| 请求 | messages 数量 | 请求体字节数 | 响应 usage 报告的 prompt_tokens |
|---|---:|---:|---:|
| [R005][R005] | 2 | 97,504 | 23,961 |
| [R009][R009] | 16 | 115,016 | 28,939 |
| [R012][R012] | 25 | 132,933 | 33,822 |
| [R017][R017] | 35 | 138,609 | 34,981 |

**一次具体的上下文追加。** [R015][R015] 只有 `messages[0]`—`messages[30]`。其模型响应要求复测；在下一次请求 [R016][R016] 中，增加了助手调用 `messages[31]` 和工具结果 `messages[32]`。下面摘录新增助手消息的 `role`、`tool_calls`，省略其余字段；工具结果消息则完整保留：

```json
{
  "role": "assistant",
  "tool_calls": [
    {
      "id": "call_78f94d7a38e5464d8077554f",
      "type": "function",
      "function": {
        "name": "Bash",
        "arguments": "{\"command\":\"python -m unittest -v\",\"description\":\"Re-run full unit tests\",\"workdir\":\"D:\\\\project\\\\self\\\\test\\\\w1-lab1\"}"
      }
    }
  ]
}
```

```json
{
  "role": "tool",
  "tool_call_id": "call_78f94d7a38e5464d8077554f",
  "content": "test_discount_equal_to_subtotal_yields_zero (test_receipt.ReceiptTests.test_discount_equal_to_subtotal_yields_zero) ... ok\r\ntest_discount_exceeding_subtotal_is_rejected (test_receipt.ReceiptTests.test_discount_exceeding_subtotal_is_rejected) ... ok\r\ntest_empty_receipt (test_receipt.ReceiptTests.test_empty_receipt) ... ok\r\ntest_negative_discount_is_rejected (test_receipt.ReceiptTests.test_negative_discount_is_rejected) ... ok\r\ntest_negative_quantity_is_rejected (test_receipt.ReceiptTests.test_negative_quantity_is_rejected) ... ok\r\ntest_receipt_with_discount (test_receipt.ReceiptTests.test_receipt_with_discount) ... ok\r\ntest_receipt_without_discount (test_receipt.ReceiptTests.test_receipt_without_discount) ... ok\r\n\r\n----------------------------------------------------------------------\r\nRan 7 tests in 0.000s\r\n\r\nOK\r\n"
}
```

`tool_calls[0].id` 与后一条消息的 `tool_call_id` 相同，因此可确定这段 `OK` 回应的是该次复测。也正因为调用及结果被加入下一请求，R016 的模型才有直接证据决定把 T1 标记为完成。这个例子具体展示了“模型输出 → 客户端执行 → 结果进入下一轮上下文”的过程。

逐条比较相邻请求：除 [R011][R011]→[R012][R012] 将原用户消息改为“原文加提醒”的两个文本块外，先前消息都原样保留，后续追加助手消息和工具结果。助手消息中同时可见 `content`、`reasoning_content` 和 `tool_calls` 等字段；较早的失败结果也仍存在于 [R017][R017] 的历史中。

`[OBSERVED]` 系统提示词和 tools 定义保持一致；没有观察到主任务历史被摘要替换、删除或截断。系统提示词声称接近上下文限制时会压缩历史，但这只证明存在相应指令，不能写成本次已发生压缩。R018 只传四条消息，是用途明确的输入建议请求，同样不能拿它来证明主会话进行了压缩。

[R017][R017] 的 usage 中 `cached_tokens` 为 34,816，`prompt_tokens` 为 34,981。`[OBSERVED]` 这是服务端报告的缓存统计；`[INFERRED]` 它与大量稳定前缀可以复用相符，但不能据此推断客户端减少了 HTTP 上传内容——请求体仍完整携带了这些消息和定义。

## 第五部分：反思（10 分）

**我会借鉴的两个设计决策。** 第一，采用 Edit 的精确匹配和可诊断失败，而不让文件编辑默默猜测目标。本次模型从带行号的 Read 输出构造不含行号的替换文本，修改范围清楚；这有利于发现陈旧内容和重复匹配。第二，将任务状态做成有 ID 的结构化生命周期。本次 T1 的 create、start、done 都留下可引用结果，且完成发生在测试通过之后，便于区分“已经动手”和“有验证的完成”。

**我会采用不同做法的一个决策。** 我会让终端接口更明确地体现实际 Shell，并优先提供结构化的目录枚举入口。现有工具叫 Bash，却执行 PowerShell；虽然描述已经写明 `Shell: pwsh`，模型仍先用了 `ls -la`，还连带取消了另一个调用。统一名称可能便于跨平台复用工具接口，但仅靠长描述提醒并没有避免本次错误。显式 Shell 字段或更少歧义的工具名可以降低这种误用。

**这次轨迹改变了我的引导方式。** 我会在正式会话前准备完整的独立项目，包含 README，并确认仓库状态；提示词中要求先建立任务，再运行故障基线测试，最后用真实测试结果结束任务。报告会检查实际顺序，而不只复述最后的完成总结：本次最终汇报看起来完整，但调用记录揭示了计划建立偏晚、额外目录搜索和一次被取消的读取。

## 附录：原始记录定位

以下 ID 只用于在本地 `session.flows` 中定位，不包含认证信息。原始捕获文件保留在仓库之外，报告无需附带它。

| 请求 | mitmproxy flow ID |
|---|---|
| R001 | `c16d3050-fec7-4b27-b36a-e1e472c2a20f` |
| R002 | `2ed14ab1-29d9-4bcd-b20a-0cd398dd5bdf` |
| R003 | `9c82b511-2687-404b-b2cd-f34f0341c99c` |
| R004 | `12578390-5fce-4d14-9a36-5a6a1407cd40` |
| [R005][R005] | `ee0941b2-3977-4f17-bb79-ec0f958f2427` |
| [R006][R006] | `bea26f28-9c96-4e2b-94ac-9749e1ba8fba` |
| [R007][R007] | `b3e117bc-e15d-465f-9684-4e85c0b7ac48` |
| [R008][R008] | `518443e4-f311-42e1-b51e-307d09b69a23` |
| [R009][R009] | `48716de2-5832-4d77-b8ee-eb433b8f3b14` |
| [R010][R010] | `9891c000-8408-4a68-b63f-9578bb5e9875` |
| [R011][R011] | `23412bc0-b05d-4e40-b3f3-64980a519336` |
| [R012][R012] | `71b1134a-9c6d-48c2-93e3-19df35751c66` |
| [R013][R013] | `4684f106-2467-4025-a454-f7d7e3046126` |
| [R014][R014] | `891ee31d-00e9-43dd-8fb5-ff2b41bb24ec` |
| [R015][R015] | `8dd834ec-2277-49eb-9acb-b261de2bf497` |
| [R016][R016] | `50af20b9-7f55-421b-a717-0e05e90711e6` |
| [R017][R017] | `056140a0-f31c-4ab2-a1ca-a2c03c44e29b` |
| R018 | `8ad655a0-dd27-44ad-97b5-1fbff1755217` |

<!-- JSON 请求体引用 -->
[R005]: requests/R005.json
[R006]: requests/R006.json
[R007]: requests/R007.json
[R008]: requests/R008.json
[R009]: requests/R009.json
[R010]: requests/R010.json
[R011]: requests/R011.json
[R012]: requests/R012.json
[R013]: requests/R013.json
[R014]: requests/R014.json
[R015]: requests/R015.json
[R016]: requests/R016.json
[R017]: requests/R017.json
