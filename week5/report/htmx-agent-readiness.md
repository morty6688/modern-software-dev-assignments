# htmx Agent Readiness 审计报告

**结论：本地快照具有简洁的开发入口、静态校验和浏览器测试。主要缺口是 CI 与跨浏览器验证指引不一致、发行构建未进入 CI，以及开发环境和生成产物说明尚未集中。**

> **本报告不是 Factory 官方评分。** 未安装或运行 Droid，仅沿用 [Factory 八个维度](https://factory.com/news/agent-readiness)进行独立静态审计，不给出官方分数或成熟度等级。

- 审计日期：2026-11-01。
- 目录：`D:\project\self\test\cs146s\htmx`。
- HEAD：`fa978b24e75fb03c137bf2cdae4fef0e711cf8a1`；package.json 版本：`2.0.11`。
- `git --no-optional-locks status --short` 成功且无输出；审计时未发现 Git 报告的工作树变更。不证明文件来源可信或远程状态一致。
- 方法：只读检查本地源码、配置、工作流、文档和代表性测试。未安装依赖、下载浏览器、运行测试/构建、启动服务器或修改被审计仓库；只保存报告。
- **通过**表示存在静态证据，不等于执行成功；**缺失**限于指定范围；**Unknown**表示无法验证。P1 为优先解决，P2 为计划改进，P3 为按需完善。

## 1. Style & Validation

| 状态 | 项目与证据 |
|---|---|
| 通过 | [package.json:28](D:/project/self/test/cs146s/htmx/package.json:28)提供 `lint`、`format`、`types-check`；`npm test` 依次执行 ESLint、TypeScript checkJs 和 Chrome 测试。 |
| 通过 | ESLint 配置继承 `standard` 和 `plugin:mocha/recommended`；类型检查命令为 `tsc src/htmx.js --noEmit --checkJs ...`，无需把源码迁移到 TypeScript。 |
| 缺失 | 根目录未见 pre-commit/Husky 配置，静态检查主要依赖手动命令和 CI。不能排除开发者自设 Git hook。 |
| 缺失 | ESLint 多个质量规则未启用：[package.json:62](D:/project/self/test/cs146s/htmx/package.json:62)附近将 `no-undef`、`eqeqeq`、`no-unused-vars`、`no-eval` 等设为 0。checkJs 可提供部分补充，不能直接宣称存在对应缺陷。 |
| Unknown | 当前 lint 与 checkJs 是否通过，本次未执行。 |

**P2：**解释关闭规则的兼容性理由，优先恢复对新增代码有价值的规则；如加入提交钩子，应复用 `npm run lint` 与 `npm run types-check`。

## 2. Build System

| 状态 | 项目与证据 |
|---|---|
| 通过 | [package.json:28](D:/project/self/test/cs146s/htmx/package.json:28)的 `dist` 串联分发构建、类型声明和编辑器元数据生成；`files` 明确发布文件集合。 |
| 通过 | [scripts/dist.sh:3](D:/project/self/test/cs146s/htmx/scripts/dist.sh:3)使用 `set -euo pipefail`，从源码生成 IIFE、压缩、gzip、AMD、CJS 和 ESM 产物。 |
| 通过 | 根目录有 [package-lock.json](D:/project/self/test/cs146s/htmx/package-lock.json)，[ci.yml:18](D:/project/self/test/cs146s/htmx/.github/workflows/ci.yml:18)使用 `npm ci`。 |
| 缺失 | [ci.yml](D:/project/self/test/cs146s/htmx/.github/workflows/ci.yml)仅执行 `npm ci` 和 `npm test`，没有 `npm run dist`、npm 打包内容或最终 ESM/CJS 消费验证。 |
| 缺失 | 版本元数据不一致：package.json 为 `2.0.11`，package-lock.json 第 3、9 行仍为 `2.0.10`。这是已确认差异，但不能仅据此断定 `npm ci` 会失败。 |
| Unknown | 当前构建是否成功、dist 是否与源码一致、npm 包是否完整可用；未执行构建或打包。 |

**P1：**CI 增加隔离的构建和包消费检查。**P2：**在版本更新流程同步清单与 lockfile 元数据，检查实际发布内容。

## 3. Testing

| 状态 | 项目与证据 |
|---|---|
| 通过 | [web-test-runner.config.mjs:60](D:/project/self/test/cs146s/htmx/web-test-runner.config.mjs:60)收集 `test/attributes/**/*.js` 和 `test/core/**/*.js`。 |
| 通过 | [test/core/ajax.js:1](D:/project/self/test/cs146s/htmx/test/core/ajax.js:1)在 beforeEach/afterEach 建立并恢复模拟服务器、清理 DOM；测试点击、响应及内容替换。 |
| 通过 | [package.json:36](D:/project/self/test/cs146s/htmx/package.json:36)提供 Chromium、Firefox、WebKit 和全部浏览器入口；[配置:56](D:/project/self/test/cs146s/htmx/web-test-runner.config.mjs:56)启用源码覆盖率。 |
| 缺失 | CI 只调用 `npm test`，该命令只执行 Chromium；已存在的 `test:ci` / `test:all` 没有接入当前工作流。 |
| 缺失 | 覆盖率配置未设置最低门槛，CI 未显式上传覆盖率产物。实际覆盖率为 Unknown。 |
| 缺失 | 随机测试条件不可直接重放：[配置:18](D:/project/self/test/cs146s/htmx/web-test-runner.config.mjs:18)用 `Math.random()` 选择 nonce，第 24 行随机设置 onpopstate；未见种子或选择结果记录机制。 |
| Unknown | 当前测试通过率、偶发失败及浏览器兼容结果；未执行浏览器测试。 |

**P1：**让 CI 执行跨浏览器测试，或明确默认与完整测试的差别。**P2：**将随机条件改为可枚举组合或记录可重放输入；建立覆盖率基线并保存结果。

## 4. Documentation

| 状态 | 项目与证据 |
|---|---|
| 通过 | [README.md:70](D:/project/self/test/cs146s/htmx/README.md:70)、[CONTRIBUTING.md:13](D:/project/self/test/cs146s/htmx/CONTRIBUTING.md:13)、[TESTING.md](D:/project/self/test/cs146s/htmx/TESTING.md)分别说明开发、贡献及测试。 |
| 通过 | [CONTRIBUTING.md:38](D:/project/self/test/cs146s/htmx/CONTRIBUTING.md:38)明确格式化、PR 目标分支、不提交 dist，以及测试与文档位置。 |
| 通过 | [netlify.toml](D:/project/self/test/cs146s/htmx/netlify.toml)配置 `zola build`、网站目录和预览构建；不能因此断言部署成功。 |
| 缺失 | [TESTING.md:74](D:/project/self/test/cs146s/htmx/TESTING.md:74)称 `test:ci` 可模拟 CI，但实际 CI 执行只测 Chromium 的 `npm test`，`test:ci` 则包含三种浏览器。 |
| 缺失 | 贡献指南要求系统 Chrome 和 `CHROME_PATH`，而 npm 测试脚本使用 Playwright 下载浏览器；入口没有清楚区分这些前提分别适用哪些模式。根目录也未发现 AGENTS.md/CLAUDE.md。 |
| Unknown | 全部网站文档、链接及安装步骤的当前有效性；没有逐一执行验证。 |

**P1：**先统一 `test:ci` 与实际 CI 的语义。**P2：**提供简洁的智能体/贡献者入口，说明源文件、生成文件、各测试模式和浏览器安装前提。

## 5. Dev Environment

| 状态 | 项目与证据 |
|---|---|
| 通过 | [CONTRIBUTING.md:17](D:/project/self/test/cs146s/htmx/CONTRIBUTING.md:17)要求 Node 20.x 或以上；CI 指定 Node `20.x`；package.json 集中声明开发依赖。 |
| 通过 | 测试脚本明确执行 `playwright install chromium/firefox/webkit`，依赖获取有直接入口；这也意味着测试前可能联网下载。 |
| 缺失 | 检查的 package.json 未声明 `engines`/`packageManager`，根目录未见 `.nvmrc` 或 `.node-version`；本地版本约束主要依赖文档。 |
| 缺失 | 构建使用 Bash、`cp`、`gzip` 等，开发前提段仅列 Node 和 Chrome，没有说明 Windows 构建所需 Shell/工具。 |
| Unknown | 新机器或离线环境安装成功率、Windows 构建可用性、浏览器系统依赖是否齐全；未创建环境。 |

**P2：**记录受支持的 Node/npm 组合及 Windows 构建方式；推荐用 `npm ci` 复现 lockfile，区分安装浏览器和执行测试步骤。

## 6. Code Quality

| 状态 | 项目与证据 |
|---|---|
| 通过 | [src/htmx.js:59](D:/project/self/test/cs146s/htmx/src/htmx.js:59)等位置通过 JSDoc 描述 API 类型，配合 `checkJs`；test/core 及 test/attributes 对应核心与属性行为。 |
| 通过 | [CONTRIBUTING.md:49](D:/project/self/test/cs146s/htmx/CONTRIBUTING.md:49)明确不接受未经请求的无行为重构，有助于智能体限制改动范围。 |
| 缺失 | 检查的 ESLint 配置未声明复杂度或函数长度门槛；大量逻辑位于 `src/htmx.js`。单文件布局本身不是缺陷，也不足以证明需要拆分。 |
| Unknown | 实际复杂度、重复率、缺陷数量及所有 JSDoc 的完整性；未进行全仓度量。 |

**P3：**先为高变更区域建立导航和行为测试，再决定是否增加局部复杂度约束；遵循仓库明确的重构边界。

## 7. Observability

| 状态 | 项目与证据 |
|---|---|
| 通过 | [src/htmx.js:65](D:/project/self/test/cs146s/htmx/src/htmx.js:65)暴露 `logger`；第 889 行 `logAll()` 安装日志回调，`logNone()` 可关闭。 |
| 通过 | [src/htmx.js:3163](D:/project/self/test/cs146s/htmx/src/htmx.js:3163)向 logger 传递元素、事件和 detail；请求路径提供 sendError、timeout、responseError 等错误事件。 |
| 通过 | [TESTING.md:54](D:/project/self/test/cs146s/htmx/TESTING.md:54)说明浏览器控制台、断点和手动调试；测试 runner 配置输出测试错误。 |
| 缺失 | 测试随机初始化条件没有诊断记录，失败后难以重建同样的 nonce/onpopstate 组合；对应证据见测试维度。 |
| Unknown | 下游应用是否捕获错误事件、接入日志和告警，以及是否正确过滤敏感 detail；不在本仓库静态审计范围。 |

**P2：**失败报告记录浏览器版本及随机组合。**P3：**给出带字段过滤的错误事件接入示例。作为浏览器库，不要求内置服务器日志收集、生产仪表盘或 SLO。

## 8. Security & Governance

| 状态 | 项目与证据 |
|---|---|
| 通过 | [SECURITY.md:5](D:/project/self/test/cs146s/htmx/SECURITY.md:5)列明支持版本，第 14 行指向私密漏洞报告；package.json 声明 0BSD，并有 LICENSE。 |
| 通过 | [README.md:35](D:/project/self/test/cs146s/htmx/README.md:35)的 CDN 示例包含 integrity 和 crossorigin 属性；本次未验证哈希是否匹配远程文件。 |
| 通过 | [src/htmx.js:241](D:/project/self/test/cs146s/htmx/src/htmx.js:241)默认 `selfRequestsOnly: true`，第 4171 行按该配置检查请求；也提供 allowEval/allowScriptTags 开关。 |
| 缺失 | [ci.yml](D:/project/self/test/cs146s/htmx/.github/workflows/ci.yml)未显式声明最小 `permissions`，Actions 使用 `@v4` 标签而非完整 SHA。实际默认 token 权限为 Unknown。 |
| 缺失 | 根目录及 `.github/` 未发现 CODEOWNERS、Dependabot 配置；所检查唯一 CI 未见专门 SAST/依赖漏洞扫描步骤。这不排除托管平台功能。 |
| Unknown | `allowEval: true`、`allowScriptTags: true` 的默认值是否在具体应用中形成风险，取决于响应信任、输入过滤与 CSP；不能仅凭默认值断言存在可利用漏洞。 |
| Unknown | 分支保护、强制评审、托管扫描、依赖漏洞和实际发布权限；本次未查询远程状态。 |

**P2：**显式限制 CI 权限、固定 Actions SHA，补充开发依赖扫描及评审责任说明。**P2：**面向使用者说明脚本/eval 开关与 CSP、可信响应的关系，保持兼容性决策可审阅。

## 优先顺序与范围限制

1. **P1：对齐跨浏览器 CI 与文档。** 已有完整命令，接入成本相对低，可直接扩大智能体修改后的验证范围。
2. **P1：在 CI 构建并检查最终分发包。** 测试源码通过不能替代分发产物验证。
3. **P2：记录随机测试输入，补充环境前提，修正 lockfile 版本元数据。**
4. **P2：完善 CI 权限、依赖扫描和诊断产物。**
5. **P3：按实际需要完善代码导航与局部质量门禁。**

本报告不推断当前 CI 通过，不将 coverage 配置当作实测覆盖率，不把浏览器库缺少服务端监控认定为缺陷。审计未修改 htmx；只新增本报告。
