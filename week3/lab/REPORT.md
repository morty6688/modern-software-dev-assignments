# Phase 1：Day.js 无效日期 diff 基线调查

日期：2026-10-15（Asia/Shanghai）。本阶段未使用任何 bug-reproduction Skill，未读取已有 issue、讨论或已发表修复，未修改 Day.js 生产代码。这里只完成 Phase 1，作为后续编写通用 Skill 的原始证据；不声称已完成 Skill 编写、触发测试或整个 Week 3 作业。

## 结论

在实际安装的 **dayjs 1.11.23** 中，无效日期参与 `diff()` 时，`month`、`quarter`、`year` 返回正零；`millisecond`、`second`、`minute`、`hour`、`day`、`week` 返回 `NaN`。两种参数方向、整数/浮点模式、三种无效输入均如此。

原因定位到 `src/utils.js:24-25` 的月份差计算：算术结果本来为 `NaN`，但 `|| 0` 将其替换为零。`src/index.js:350-388` 未提前拒绝无效日期，并让月/季度/年共用这个辅助函数。源码原函数、发布包内部辅助函数和公开 API 的执行结果互相印证。

## 环境与版本证据

- Windows，win32/x64；Node.js v20.11.1，npm 10.2.4；PowerShell，禁用 profile 后执行。
- 默认运行时区 Asia/Shanghai；另在新 Node 进程中通过 `TZ` 测试 UTC 和 America/New_York。
- `validation/package.json` 精确依赖 `1.11.23`；`validation/package-lock.json` 保存 npm tarball URL 和 SHA-512 integrity；`validation/evidence/package-version.txt` 为实际 `npm ls` 输出。
- 无插件；固定有效输入 `2024-01-15`，不依赖当前日期。
- 源码来自 [v1.11.23 归档](https://codeload.github.com/iamkun/dayjs/zip/refs/tags/v1.11.23)。该标签源码 `package.json` 的版本是 `0.0.0-development`，不能拿它代替发布包版本证明。
- `validation/evidence/sha256.txt` 保存下载归档、两个相关源文件、实际执行的 npm bundle 的 SHA-256；`validation/evidence/environment.json` 保存运行时信息。

## 仓库与测试约定

阅读了标签中的 `package.json`、`babel.config.js`、`test/display.test.js`，并搜索相关文件。仓库使用 Jest 22、Babel preset-env，测试位于 `test/`，使用 `it/describe/expect`，从 `../src` 导入实现，并经常与 Moment 对比。Difference 分组位于 `test/display.test.js:163-224`，覆盖单位、浮点选项和正常月份差。其全量 `npm test` 包含多个时区及覆盖率要求。

本调查使用独立 Node/assert 脚本直接测试精确版本的发布包，避免为一个小复现引入整个旧构建工具链。**没有运行上游 Jest 全量测试，也没有声称它们通过**。保存的源码摘录见 `validation/evidence/source-excerpts.txt`；不能仅凭这个分组断言整个仓库不存在其他相关测试。

## 最小复现

在 `week3/lab/validation` 目录执行（Windows 使用 `npm.cmd`，其他平台用 `npm`）：

```powershell
npm.cmd ci --ignore-scripts --no-audit --no-fund
node reproduce.cjs
```

五行脚本只需要 Day.js 核心包，用原生 `new Date(NaN)` 排除字符串解析歧义。实际输出（`validation/evidence/reproduction.txt`）：

```text
day: NaN
month: 0
```

预期：只要任一操作数为无效日期，所有单位都应返回 `NaN`，而不是给出看似有效的零时间差。这是本调查采用的一致性要求，依据是无效时间戳不能表示可计算的间隔、同一 API 的其他单位已传播 `NaN`；**不将其冒充为已核对的官方无效输入契约**。正常相同日期返回零仍然合理。

## 先提出假设，再区分

最小复现后、阅读 `diff` 实现前，已写入 `validation/evidence/hypotheses-before-source.md`：

| 假设 | 区分实验及预测 | 实测与判断 |
|---|---|---|
| H1 默认整数截断把无效结果变零 | `float=true` 应恢复 NaN | 浮点仍为零；后续源函数和发布包的 `absFloor(NaN)` 都是 NaN，排除该解释 |
| H2 日历单位采用不同路径，吞掉无效中间值 | 月/季度/年在浮点模式下也成组异常 | 三者始终返回零；源码和执行追踪进一步支持 |
| H3 特定解析方式或参数方向导致异常 | 换原生无效 Date、数值 NaN、坏字符串；交换双方 | 三种输入均 `isValid() === false`、时间戳 NaN；交换后分组不变，未支持此解释 |

`validation/investigate.cjs` 执行 3 种输入 × 3 种方向（无效/有效、有效/无效、无效/无效）× 2 种模式 × 9 个单位，共 **162 个无效输入案例**；另有 18 个有效同日对照、2 个正负月份差对照，共 **182 个表征检查**，且额外检查输入有效性。54 个案例违反“应返回 NaN”的预期，均为三个日历单位。

```powershell
node investigate.cjs
node investigate.cjs --expect-nan
```

第一个命令退出 0，表示它准确确认了当前缺陷的形态，**不代表实现正确**；第二个命令按预期正确性判定，实际退出 1。完整结果见 `validation/evidence/matrix.txt`、`validation/evidence/expected-contract.txt` 和 `validation/evidence/expected-contract-exit.txt`。

UTC 和 America/New_York 分别重跑同一矩阵，均为 182 个表征检查通过、54 个预期违例，退出 0，见 `matrix-utc.txt`、`matrix-new-york.txt`、`timezone-exits.txt`。这降低了该结果依赖默认时区的可能性，不等于测试了所有时区或 DST 边界。

## 源码与动态证据

1. `src/index.js:350-355` 规范化单位、构造另一个 Day.js 对象，计算时间戳差，并定义调用 `Utils.m` 的 `getMonth()`；没有有效性保护。
2. `359-367`：年用月份差除以 12，月直接用月份差，季度除以 3。
3. `368-388`：其余单位使用时间戳算术；浮点直接返回，整数经过 `Utils.a`。
4. `src/utils.js:17-25`：无效日期使 `wholeMonthDiff` 和两个锚点时间戳为 NaN；返回表达式在 `|| 0` 前为 NaN。JavaScript 中 NaN 是 falsy，因此这里变成正零。
5. `src/utils.js:28` 的整数处理对 NaN 走 `Math.floor(NaN)`，保持 NaN，不是这次转换的来源。

`validation/trace.cjs` 从归档源码读取原样的 `monthDiff`/`absFloor` 函数，隔离执行并注入其需要的月份常量；同时调用 npm 包自身的 `$utils().m`/`$utils().a` 交叉核验。另行计算中间值用于展示，不修改或替换生产函数。

```powershell
node trace.cjs
```

实际输出（两个参数方向均如此，完整记录见 `validation/evidence/trace.txt`）：

```text
wholeMonthDiff=NaN; anchor=NaN; anchor2=NaN; beforeFallback=NaN; afterFallback=0; sourceHelper=0; publishedHelper=0
absFloor(NaN)=NaN in tagged source and published package
PASS: source helper, published helper, floating diff and diagnostic intermediate agree
```

这使 H2 从分组推测提升为有具体转换点的源码与执行证据。`|| 0` 可能也承担消除负零的功能，但其历史意图未经调查，不将意图当事实。

## 建议的最小修复（仅建议，未实施）

在 `diff()` 构造 `that = dayjs(input)` 后、开始计算偏移和月份差之前加入：

```javascript
if (!this.isValid() || !that.isValid()) return NaN
```

这是针对公开 API 的两侧输入保护，保留正常月份计算及其零值处理。不要未经验证直接删除辅助函数的 `|| 0`，因为需要考虑正常同日差的正负零语义及其他调用者。

如果以后获准修复，应把本矩阵转为仓库 Jest 回归测试，先观察无效输入测试失败，再实施保护，随后验证正常正负月份差、同日零、浮点、月底/闰年及上游时区测试。此次未应用补丁，也未运行“修复后”验证。

## 实际操作、障碍与限制

`validation/COMMANDS.md` 记录实际执行命令及结果摘要；`validation/evidence/` 内测试输出由实际命令写入，不是手工模拟终端记录。

- HTTPS Git 克隆失败，提示无法读取远端；未确定具体原因。首次 PowerShell 下载被沙箱套接字权限拒绝，随后经工具权限审核成功下载指定标签归档。
- GitHub 标签网页工具读取出现 Internal Error，未把它当作源码证据，改用下载归档。
- 一次合并 PowerShell 命令因直接管道连接 `foreach` 块产生 ParserError，整段未执行；改为 `& { ... } | Out-File` 后执行成功。
- 首次 `validation/trace.cjs` 的 VM 包装缺少语句分隔符，导致提取结果 undefined。错误输出保留在 `validation/evidence/trace-first-attempt.txt`；只在诊断包装中增加分号后重新执行成功，未改源函数。
- 归档及 `node_modules` 由本地 `.gitignore` 排除；精确 npm 锁文件、来源、校验值和相关源码摘录保留。没有 Git checkout 的 commit 身份证明，也未做完整源码到 bundle 的重构建等价性验证。
- `$utils()` 是内部诊断接口，不应作为通用 Skill 的固定步骤；独立复现只用公开 API。

## 后续通用 Skill 可提取的判断

这些是本次基线产生的经验，并非已实现的 Skill：

- 先证实运行的是目标发布版本；标签源码的版本字段可能只是占位值。
- 把最小复现与诊断矩阵分开；前者便于复用，后者负责区分竞争假设。
- 在阅读实现前记录假设及可证伪预测，避免根据已知代码倒写推理。
- 更改一个维度或使用结构化矩阵，加入正常对照；必要时验证输入本身确实异常。
- 区分表征断言通过与行为正确，给正确性预期提供真正的失败退出码。
- 只有实验缩小范围后才追踪对应路径，用运行证据定位信息在哪一步丢失。
- 环境工具出错时保存失败与绕行理由，避免把脚本错误算成产品错误。
- 未获得修复任务时停在可验证的最小修复建议，明确未跑的验证范围。

作业上下文：[assignment](https://github.com/mihail911/modern-software-dev-assignments/blob/master/week3/assignment.md)、[writeup template](https://github.com/mihail911/modern-software-dev-assignments/blob/master/week3/writeup.md)。本次保留原有中英文作业材料，产物独立存放于 `week3/lab`。
