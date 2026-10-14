# Task: Build self-github-issue-manager

## 补充约定（2026-10-14，优先于下文）

- 这是个人学习项目，使用 Codex 即可，不强制 Claude Code/Cursor，不要求课程协作者或 Gradescope 提交。
- 实现前阅读至少一个参考 MCP Server，记录参考来源与借鉴点。
- 真实 `.mcp.json` 必须 gitignore，只提交示例。
- writeup 为 Schema 约束、输出裁剪、结构化错误、串联 docstring、写入保护提供实际 `file:line` 和理由。
- 记录实际 Agent 误用、由此做出的改进及复测；未观察到误用时如实说明，不编造。
- 真实 transcript 包括 prompt、工具名、完整调用参数、request_id、结果摘要，失败后还须记录 Agent 的下一步行为。Mock 与协议测试不能冒充真实演示。
- MCP 调用边界生成 request_id，覆盖工具参数校验失败；协议级错误和业务级错误分别说明。畸形 JSON-RPC 不属于已识别的工具调用。
- 刷新采用跨进程锁，锁内重新读取凭证，将轮换后的完整 token bundle 一次保存；避免 CLI/IDE 多实例重复刷新。
- 写请求超时或服务端错误返回 WRITE_OUTCOME_UNKNOWN、retryable=false，并建议先查询核实，禁止盲目重复创建。
- 分页过滤 PR 后可能空页，仍返回 has_next/next_page；详情及标签工具也拒绝 PR 编号。
- GitHub App 最小权限：Issues read/write、Metadata read；仅安装至目标仓库。使用过期用户令牌并验证刷新，不以 PAT/Installation Token 替代。
- 真实授权、远程写入及推送需用户参与；独立本地实现和 Mock 测试直接执行。

实现一个 Python GitHub Issue Manager MCP Server，作为 CS146S Week 2 的实践项目。

## 1. 项目信息

- Project name: `self-github-issue-manager`
- Project directory: `./week2/lab/self-github-issue-manager`
- GitHub App: `cs146s-w2-issue-manager-test-app`
- Target repository: `morty6688/cs146s-w2-issue-manager-test`
- Repository URL: https://github.com/morty6688/cs146s-w2-issue-manager-test
- OAuth callback: `http://localhost:18765/callback`（如实际配置不同，先确认）
- OS: Windows
- Python: 3.12
- MCP framework: FastMCP
- MCP transport: stdio
- MCP client: Codex CLI / VS Code Codex

项目代码必须位于 `./week2/lab/self-github-issue-manager`，不要放到 `week2` 根目录，也不要写入 GitHub 测试仓库。

参考：
- CS146S Week 2 Assignment: https://github.com/mihail911/modern-software-dev-assignments/blob/master/week2/assignment.md
- GitHub App OAuth: https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-user-access-token-for-a-github-app

## 2. 实现 MCP Server

使用 FastMCP，提供至少 4 个工具。

### list_issues

- 查询目标仓库 Issues。
- 支持状态过滤（open、closed、all）和分页。
- 返回精简的结构化数据：issue_number、title、state、labels、url 等。
- 排除 GitHub Issues API 返回的 Pull Requests。
- 明确告诉 Agent，issue_number 可以传给其他工具。

### get_issue

- 根据 issue_number 获取 Issue 详情。
- 返回标题、正文、状态、标签、创建者、创建时间、URL。
- 对不存在的 Issue 返回结构化错误。

### create_issue

- 创建 Issue，支持 title、body、labels。
- `dry_run` 默认为 true。
- dry_run 仅返回预览，不产生真实写操作。
- 真实创建后返回 issue_number、url 等。

### add_issue_labels

- 为指定 Issue 追加标签，不替换原有标签。
- `dry_run` 默认为 true。
- 处理不存在的 Issue、无效标签等错误。

所有工具必须严格限制在 `morty6688/cs146s-w2-issue-manager-test`，不提供让 Agent 任意指定 owner/repo 的参数。

要求：

- 清晰的 Tool 名称、docstring 和参数 Schema。
- 使用类型约束及适当的 tool annotations。
- 使用 FastMCP instructions 说明工具间的调用关系。
- 不直接向 Agent 返回冗长的 GitHub 原始 JSON。
- 错误响应包含 error code、message、retryable，必要时包含 retry_after 或 suggested_action。
- 正确处理 HTTP 401、403、404、422、429、5xx、网络超时。
- 配置合理的超时与重试策略，避免对非幂等写操作盲目重试。

## 3. GitHub App OAuth 2.0

使用 GitHub App User Access Token，实现 Authorization Code Flow。

功能要求：

1. 生成 Authorization URL。
2. 生成随机 state，防止 CSRF。
3. 使用 PKCE S256。
4. 启动仅监听 localhost 的临时 HTTP Callback Server。
5. 验证回调 state。
6. 用 Authorization Code 交换 Access Token 和 Refresh Token。
7. 安全持久化 Token 和过期时间。
8. Access Token 即将过期时自动刷新。
9. 正确处理 Refresh Token Rotation 和并发刷新。
10. Refresh Token 失效时提示重新授权。
11. 提供 `auth login` 和 `auth status` 命令。

OAuth 应作为独立命令执行，MCP Tool 调用中不要突然打开浏览器要求登录。

安全要求：

- Client ID、Client Secret 从配置或环境变量加载。
- 优先使用 Windows Credential Manager 存储 Token，或采用有明确安全边界的本地凭证存储实现。
- 不持久化 Authorization Code。
- 禁止把 Secret 或 Token 写进日志、工具响应和 Git 仓库。
- `.env`、真实凭证文件、日志文件加入 `.gitignore`。
- GitHub App 使用细粒度权限，不使用 Personal Access Token 或 Installation Access Token 替代 OAuth。
- 验证 App 对目标仓库的访问权限，失败时给出明确提示。

## 4. MCP 调用日志与可观测性

这一部分是项目的明确要求，不能省略。

目标：我能够通过查看 MCP Server 的日志，确认 Codex 确实调用了我自己的 MCP Server，而不是现成的 `codex_apps.github.*` 工具。

### 4.1 Request ID

- 每次 MCP Tool 调用都由服务端生成一个唯一 `request_id`，建议使用 UUID v4。
- 同一次调用内部的开始事件、GitHub API 请求和结束事件共享同一个 request_id。
- 正常及错误的 MCP Tool 响应中都包含 request_id，便于关联。
- 每次调用的日志必须由实际 MCP Tool 入口触发，而不是只在底层 GitHub Client 中生成。
- 不要依赖模块导入、Server 启动等事件作为工具被调用的证据。

### 4.2 结构化日志

使用 Python logging，日志推荐保存为：

`./logs/mcp.jsonl`

采用 JSON Lines 格式，每行一条完整 JSON 记录。

每次工具调用至少记录：

- timestamp：UTC ISO 8601 时间戳。
- request_id：本次工具调用唯一 ID。
- event：tool_start / github_api / tool_end / tool_error。
- server：self-github-issue-manager。
- tool：工具名称。
- repository：目标仓库。
- parameters：脱敏后的工具参数摘要。
- status：success / error / dry_run。
- duration_ms：执行耗时。
- error_code：失败时的错误代码。
- result_summary：精简的结果摘要。

日志示例（仅作格式参考）：

```json
{"timestamp":"2026-10-14T11:20:01Z","request_id":"a1b2c3","event":"tool_start","server":"self-github-issue-manager","tool":"list_issues","repository":"morty6688/cs146s-w2-issue-manager-test","parameters":{"state":"open","per_page":20}}
{"timestamp":"2026-10-14T11:20:01Z","request_id":"a1b2c3","event":"github_api","method":"GET","endpoint":"/repos/morty6688/cs146s-w2-issue-manager-test/issues","http_status":200}
{"timestamp":"2026-10-14T11:20:02Z","request_id":"a1b2c3","event":"tool_end","tool":"list_issues","status":"success","duration_ms":820,"result_summary":{"count":5}}
```

实际实现应生成真正的 UUID，而不是使用示例中的简短 ID。

### 4.3 日志安全与健壮性

- 禁止记录 Access Token、Refresh Token、Client Secret、Authorization Code。
- 不完整记录 Issue 正文、评论内容或可能包含敏感信息的请求头。
- 参数和结果只记录必要的元数据。
- 日志默认写入文件，支持日志大小限制和轮转。
- 日志文件不能提交到 Git。
- stdio 模式下，普通日志不得写入 stdout，避免破坏 MCP JSON-RPC。
- 确保失败、异常及 dry_run 操作同样有日志。
- 并发调用不能混淆不同 request_id。
- 日志写入失败不应导致正常的 GitHub API 操作意外失败。

### 4.4 日志测试

通过 pytest 验证：

- 不同 Tool 调用具有不同 request_id。
- 同一次调用的不同日志事件共享 request_id。
- 成功、失败、dry_run 都会记录日志。
- duration_ms 合法。
- 返回给 Agent 的 request_id 能与日志对应。
- 日志不会泄露 Token、Secret 等敏感数据。
- 真实 MCP 协议调用能触发工具日志。

在 README 中说明 Windows PowerShell 实时查看日志的方法：

```powershell
Get-Content .\logs\mcp.jsonl -Tail 20 -Wait
```

## 5. Codex MCP 集成

提供：

- 单命令启动方式。
- Codex `config.toml` 配置示例。
- `.mcp.json.example`。
- Windows PowerShell 完整操作说明。

当前 Codex 已接入 `codex_apps`，其中包含现成的 GitHub 插件。

测试时优先明确要求 Codex 调用 `self-github-issue-manager` 的 MCP 工具，不使用 `codex_apps.github.*`、gh CLI 或 curl 等替代路径。

不必默认禁用整个 `codex_apps`。

以自己 MCP Server 的调用日志以及 request_id 为主要验证依据。

日志能证明自己的 Server 被调用，但不能单独证明 Codex 没有同时调用其他工具，应在文档中说明这个边界。

## 6. 自动化与集成测试

使用 pytest。

测试覆盖：

- OAuth state、PKCE。
- Code 交换与 Token 保存。
- 自动刷新、Refresh Token Rotation。
- Token 失效与授权撤销。
- GitHub API 错误处理。
- Repository allowlist。
- MCP Tool 输入校验。
- dry_run 行为。
- MCP 协议级工具调用。
- Request ID 和结构化日志。

普通测试 Mock 外部 HTTP 请求，避免依赖真实 GitHub API。

真实集成测试流程：

1. list_issues 查询开放 Issues。
2. get_issue 获取详情。
3. create_issue 执行 dry_run。
4. 经用户确认后创建真实测试 Issue。
5. add_issue_labels 执行 dry_run。
6. 经用户确认后添加真实标签。
7. 再次查询并验证结果。
8. 检查 MCP 日志中的对应 request_id 和结果。

真实远程写操作必须先得到用户确认。

## 7. Agent Ergonomics

这是作业的重要部分。

重点考虑：

- Agent 能否正确选择工具。
- 工具名称和描述是否明确。
- 参数约束是否足够清楚。
- 工具返回值是否简洁。
- 工具之间是否容易串联。
- 失败后 Agent 能否合理恢复。
- dry_run 是否帮助 Agent 避免意外写操作。

设计两个完整测试场景：

### 成功场景

搜索开放 Issues → 获取详细信息 → 判断是否需要标签 → dry_run → 用户确认后写入。

### 失败场景

查询不存在的 Issue，验证 Agent 能否根据结构化错误作出合理反应，避免无意义的重复调用。

记录测试使用的 Prompt、MCP 工具调用、request_id、结果及评价。

## 8. 项目结构

使用 Python package 和 `pyproject.toml` 管理依赖。

建议结构：

```text
week2/
└── lab/
    └── self-github-issue-manager/
        ├── pyproject.toml
        ├── README.md
        ├── writeup.md
        ├── .env.example
        ├── .mcp.json.example
        ├── .gitignore
        ├── src/
        │   └── self_github_issue_manager/
        │       ├── __init__.py
        │       ├── server.py
        │       ├── tools.py
        │       ├── github_client.py
        │       ├── oauth.py
        │       ├── token_store.py
        │       ├── config.py
        │       ├── logging_config.py
        │       └── cli.py
        ├── tests/
        │   ├── test_tools.py
        │   ├── test_oauth.py
        │   ├── test_logging.py
        │   └── test_mcp_protocol.py
        └── logs/
            └── mcp.jsonl
```

这是建议结构，可以在保证职责清晰的前提下合理调整。

README 必须包括：

- 环境安装与配置。
- GitHub App 的权限和安装方法。
- OAuth 登录。
- 启动 MCP Server。
- Codex 配置。
- 查看日志。
- 运行测试。
- 常见错误排查。

writeup.md 必须包括：

- 工具设计理由。
- OAuth 认证架构。
- GitHub App 权限模型。
- Token 管理和刷新机制。
- Agent 成功与失败场景。
- MCP 调用日志验证。
- 已知限制和改进方向。

## 9. 执行要求

请按顺序完成：

1. 检查当前目录，确认项目应位于 `./week2/lab/self-github-issue-manager`。
2. 阅读 CS146S Week 2 原始作业及相关官方文档。
3. 简述架构和实施计划。
4. 创建项目并实现 MCP Server。
5. 实现 OAuth 2.0。
6. 实现 request_id 和结构化日志。
7. 完成 Mock 自动化测试及 MCP 协议级测试。
8. 配置 Codex 并验证自己的 MCP 工具可以被调用。
9. 在需要凭证、浏览器授权或真实写操作时请求用户参与。
10. 完善 README 和 writeup.md。
11. 汇报实际完成情况、测试结果及剩余事项。

可以自主执行本地开发、安装依赖和 Mock 测试。

真实 GitHub 写操作、Git Push、远程仓库配置变更必须先获得用户确认。

如果缺少 OAuth 凭证，不能伪造授权成功或声称完成真实集成测试。先完成可独立验证的代码，再提示我进行必要的手动操作。

最终目标是一个可运行、可维护、具备安全认证、结构化日志及完整测试的 GitHub Issue Manager MCP Server。

请开始执行。
