# Week 3 Write-up — Bug Reproduction Skill

**Skill name，以及目标仓库：**

`bug-reproduction`。以 `iamkun/dayjs` 的发布版本 **1.11.23** 完成未使用 Skill 的基线调查，再以 Day.js 和 Lodash 的独立调查验证 Skill 的端到端工作流。

技能源码：[SKILL.md](../lab/bug-reproduction/SKILL.md)。技能已安装到本机 `C:/Users/lijian/.codex/skills/bug-reproduction/`；作业中的可交付版本保留在 `week3/lab/bug-reproduction/`。

## Part I: The Workflow

### What the workflow is，以及为什么值得编码

将一个缺陷描述转化为可执行的最小复现，通过实际输出验证现象，提出竞争假设并运行区分实验，追踪最可能的原因，最后交付结构化报告和未自动应用的修复建议。

这是一类可跨仓库重复使用的工作：不同语言的命令和测试工具各异，但版本确认、输入缩减、假设排除、证据保存和授权边界相同。Skill 固化的是这些判断，而不是某个库的错误输入或修复答案。

### The decision point：需要判断什么

- **环境还是产品：** 安装、网络、命令启动或诊断脚本失败时，先验证前置条件，不能把这些错误算作产品缺陷。
- **最小入口还是集成环境：** 优先使用公开 API 的短脚本或已有聚焦测试；只有现象依赖服务、状态或集成链路时才扩大环境。
- **已复现还是暂未复现：** 暂未复现时检查实际加载版本、配置和缺失前提，报告已测试条件，而不是宣称没有问题。
- **证据是否能区分解释：** 多个假设仍成立时，选择预测结果不同的实验；无法排除时保留不确定性。
- **实验成功代表什么：** 表征断言通过可能恰好确认了缺陷；必须与预期正确性断言、修复验证区分。
- **是否有权修改：** 调查和提出修复建议不自动授权生产代码修改；保留无关变更。

### What you learned running it manually

在编写 Skill 前，先独立调查了 Day.js 1.11.23。完整基线见 [Phase 1 报告](../lab/REPORT.md)，脚本和实际输出见 [验证命令](../lab/validation/COMMANDS.md) 及 [最终复核输出](../lab/validation/evidence/final-verification.txt)。

最小复现只需无效日期、固定有效日期和两次 `diff()` 调用：按天返回 `NaN`，按月返回 `0`。随后对无效输入构造、参数方向、单位及浮点模式进行矩阵实验：182 个表征检查通过，其中 54 个案例违反“无效操作数应传播 NaN”的一致性预期。该预期在报告中明确标为调查假设，并未冒充已核实的上游契约。

实际调查带来了以下设计依据：

1. 标签源码的版本字段可能是开发占位值，因此必须独立确认运行时加载的发布包版本。
2. 起初合理的“整数截断导致零值”解释，被浮点模式实验和取整辅助函数的执行结果排除；不能先根据直觉写根因。
3. 月、季度、年共用计算路径，辅助函数的兜底表达式吞掉了无效中间值。单看最终输出不足以定位转换点，需要源代码和运行时证据交叉核验。
4. 复现成功与产品正确并不相同：预期正确性测试应保留真实的失败退出码。
5. 网络限制和一次诊断包装错误没有触及产品缺陷，应保存失败记录并单独解释；修正后不得把旧输出改写为成功。

这些经验被抽象为通用规则，Skill 中没有 Day.js 名称、特定根因或复现输入。

## Part II: The Skill

### Your description（逐字引用）

```text
Reproduce reported software defects, collect execution evidence, distinguish competing hypotheses, and produce a root-cause report with a proposed fix. Use when asked to reproduce a bug, build a minimal failing example, investigate unexpected behavior, or diagnose a reported test failure in a repository. Do not invoke for general code explanations, feature development, routine code review or refactoring, test writing without a reported defect, or standalone environment installation requests.
```

### Why it is worded that way

描述同时说明产物（复现、执行证据、根因报告与修复建议）和触发意图（复现 bug、最小失败示例、调查异常行为、诊断已报告的测试失败）。这对应用户实际会提出的任务，而不是用笼统的“帮助调试”扩大范围。

排除项明确覆盖通用代码解释、功能开发、常规 review/refactor、没有缺陷背景的测试编写以及独立环境安装。解释 JavaScript Date 虽然与基线领域相近，但没有复现具体缺陷的意图，因此应当不触发。

### Judgment encoded in the body

主体将九项要求组织为七个阶段：确认现象和预期；检查仓库及运行身份；构建并执行最小复现；提出假设；执行区分实验；追踪原因；提出修复并交付报告。构建与执行、修复建议与报告分别合并在相应阶段。

其中明确规定：

- 不可复现时调查版本、配置和前置条件；受阻时写出最小下一步。
- 环境损坏与产品错误分别归类，不为安装成功随意升级目标依赖。
- 假设需有预测和可证伪条件；已看过实现时如实披露顺序，不倒写“事先预测”。
- 证据不足时报告置信度、剩余解释和验证边界。
- 保存实际命令、工作目录、输出与退出状态；不得声称未执行的测试通过。
- 优先小复现和正常对照；诊断矩阵与最小复现分离。
- 不自动应用修复，不修改无关文件，不把隔离诊断当作生产修复验证。

主体提供 `git status --short`、`git rev-parse HEAD`、`git diff --stat` 等确定性命令，同时对归档调查保留替代路径。具体语言的运行器由目标项目决定。

### Supporting files

| 文件 | 内容 | 分离原因 |
|---|---|---|
| [references/report-template.md](../lab/bug-reproduction/references/report-template.md) | 结果、环境身份、最小复现、执行记录、假设实验、根因、修复建议及限制 | 交付报告时按需读取，避免模板挤占核心判断流程 |
| [references/execution-evidence.md](../lab/bug-reproduction/references/execution-evidence.md) | POSIX shell 和 PowerShell 的输出及退出码捕获方式，解释失败与证据保留 | 隔离 shell 差异，保持核心流程语言无关，并避免日志管道掩盖失败 |

格式验证实际返回 `Skill is valid!`；另检查了目录名与 frontmatter 一致、description 长度及两个参考文件路径。安装时也完成了文件哈希一致性核验。格式检查与安装校验不替代下面的行为测试。

## Part III: Testing

### Triggering

下表按用户提供的测试观察记录填写。测试名称是用户提供的场景摘要，**不是重建的逐字提示词**；没有把未提供的完整 prompt 或自动触发 trace 补写为真实记录。Issue 编号仅用于标识测试，本次汇总未检索其页面或讨论。

| 测试场景（用户提供） | Should fire? | Did it? | E2E result |
|---|---|---|---|
| Test 1: Day.js #3186 | Yes / Activation | Triggered | Passed |
| Test 2: Lodash #6167 | Yes / Activation | Triggered | Passed |
| Test 3: Spring Boot API | Yes / Activation | Triggered | 未提供 E2E 结果；此项用于触发测试 |
| Test 4: JavaScript Date explanation | No / No activation | Not triggered | 不适用，负向近似场景 |

三个正向场景和一个负向场景的观察均符合预期。Spring Boot 场景提供跨语言触发观察，但不构成 Java 端到端调查已验证的证据。

### End-to-end run：Day.js #3186

独立项目及 [调查报告](D:/project/self/test/cs146s/other-tests/w3-test/dayjs-1.11.23-investigation/REPORT.md) 位于 `D:/project/self/test/cs146s/other-tests/w3-test/dayjs-1.11.23-investigation/`。

- **运行环境：** Windows x64，Node.js 20.11.1，npm 10.2.4；精确锁定 `dayjs@1.11.23`，无插件。另在 UTC 下重复实验。
- **复现：** 整数和浮点模式下，年/季度/月返回 `0`，周到毫秒返回 `NaN`。
- **区分实验：** 覆盖三种无效输入、参数方向、单位别名与正常对照；浮点模式及取整辅助函数结果排除了整数截断解释。
- **根因证据：** 运行时辅助函数追踪与标签源码一致，共享月份差计算的 falsy fallback 将 `NaN` 转成 `0`。报告披露：记录假设前已经看过 `index.js`，而辅助函数的实现检查发生在假设记录之后。
- **交付：** 复现脚本、假设记录、精确依赖锁、执行记录、完整报告及未应用的无效操作数保护建议。未修改生产文件，未运行上游完整 Jest 套件。

核对的原始输出：

```text
PASS: 218 invalid-input characterization checks and 6 valid controls; timezone=Asia/Shanghai
18/54 assertions failed under the proposed NaN-propagation expectation.
```

第一项为诊断表征成功；第二项的退出码是有意保留的 **1**，证明缺陷仍在。证据见 [本地矩阵](D:/project/self/test/cs146s/other-tests/w3-test/dayjs-1.11.23-investigation/evidence/06-experiments-local.output.txt) 和 [正确性断言输出](D:/project/self/test/cs146s/other-tests/w3-test/dayjs-1.11.23-investigation/evidence/07-expected-regression.output.txt)。这组计数属于独立 E2E，不能与 Phase 1 的 182/54 混用。

### End-to-end run：Lodash #6167

独立项目及 [调查报告](D:/project/self/test/cs146s/other-tests/w3-test/lodash-es-4.18.0-investigation/REPORT.md) 位于 `D:/project/self/test/cs146s/other-tests/w3-test/lodash-es-4.18.0-investigation/`。

- **运行环境：** Windows x64，Node.js 20.11.1，npm 10.2.4；原生 ESM，无 bundler 或浏览器。受影响包为 `lodash-es@4.18.0`，对照为 `lodash-es@4.17.21` 和 `lodash@4.18.0`。
- **最小复现：** 导入 `lodash-es/template.js` 并编译简单模板。受影响版本在编译阶段抛出 `ReferenceError: assignWith is not defined`，退出 **1**；早期版本输出 `Hello Ada!`，退出 **0**。
- **竞争假设：** 分别调查分隔符/代码生成、运行时限制、模块依赖缺失、设置或辅助函数实现变化；通过多入口与跨版本对照缩小范围。
- **关键判断：** CommonJS 根 bundle 正常，但单独模块也失败，所以不能把原因简单归为 ESM。只补充一个内存绑定会暴露或保留另一错误；同时补充 `assignWith` 和 `arrayEach` 后八类模板均正常，支持缺失依赖绑定的解释。
- **证据与边界：** 已安装文件与发布归档及精确源码快照的字节比较排除了所检查产物的本地损坏。内存干预保留函数体并带有转换对照，没有改写安装包。具体发布生成流程的致错环节仍未验证。
- **交付：** 最小复现、对照与诊断脚本、产物校验、假设记录、证据、报告及未应用的 `proposed-fix.diff`。

最终 [诊断输出](D:/project/self/test/cs146s/other-tests/w3-test/lodash-es-4.18.0-investigation/evidence/targeted-experiments-final.output.txt) 为：

```text
Characterization complete: 84 assertions passed. Expected original failures count as reproduced behavior, not product correctness.
```

报告保留了两次中间断言失败：一次修正对 CommonJS 单模块行为的预期，一次修正验证规则测试的输入。这体现了根据证据更新假设，而不是删除不符合最初预期的结果。最终 84 个断言通过包括对原始错误的预期检查及隔离内存干预验证，不等同于生产补丁通过全量测试。

### 测试结论与证据范围

按用户的观察，两个 E2E 均 Passed；已有报告和执行日志支持“从复现到竞争假设、定位原因和提出建议的工作流已完成”。这里的 Passed 指 **Skill 调查流程完成**，不表示目标库正确或缺陷已修复。

本次填报读取并核对了既有报告和关键原始输出，没有重新运行 E2E，也没有取得四个触发测试的完整会话日志。两个已完成 E2E 都是 JavaScript 包调查；跨仓库复用已有证据，跨语言完整调查能力不能仅由 Spring Boot 触发观察推定。

## Submission

- 技能和 supporting files 位于本仓库 `week3/lab/bug-reproduction/`。
- Phase 1 报告和验证产物保留在 `week3/lab/`；本报告位于 `week3/report/report.md`。
- 两个 E2E 项目及原始证据位于上述外部本地路径，尚未作为本次修改复制进作业仓库；报告中的这些链接依赖本机路径，远端阅卷者无法仅靠本仓库访问。
- 填报阶段未执行 Git 提交或推送；后续交付以实际 Git 提交和远端核验结果为准。协作者设置和 Gradescope 提交不在本次操作范围内。
