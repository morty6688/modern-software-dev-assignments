# Week 2：GitHub Issue Manager

这是个人学习项目，使用 Codex；不要求课程协作者、指定客户端或课程提交手续。

## Part I：Server

选择 GitHub Issues，因为查询、读取详情和追加标签具有明确的 ID 串联关系，也便于验证写入结果。
代码仅位于此 lab 子目录。启动命令：`.\.venv\Scripts\python.exe -m self_github_issue_manager.cli serve`。

| 工具 | 读写 | 串联方式 |
|---|---|---|
| list_issues | 读 | 返回 issue_number，分页排除 PR |
| get_issue | 读 | 接受上述编号，提供分类所需详情 |
| create_issue | 写，默认预览 | 返回编号与 URL，随后 get_issue 验证 |
| add_issue_labels | 写，默认预览 | 接受编号和现有标签，保留原标签 |

## Part II：Agent Ergonomics

以下定位以本次交付版本为准，路径相对于本项目：

| 决策 | 代码定位 | 理由 |
|---|---|---|
| Schema 约束 | `src/self_github_issue_manager/server.py:13`、`:39` | 正整数 ID、枚举状态、分页上下界；禁止字符串/布尔值冒充 ID |
| 输出裁剪 | `src/self_github_issue_manager/github_client.py:169` | 列表只保留分类和后续调用所需字段，详情才返回正文 |
| 结构化错误 | `src/self_github_issue_manager/logging_config.py:75` | 在 MCP 边界保留业务错误及校验失败，关联 request_id，明确重试语义 |
| 串联 docstring | `src/self_github_issue_manager/server.py:55` | 明确编号来自 list_issues，PR/404 不应盲目重试 |
| 写入保护 | `src/self_github_issue_manager/server.py:67`、`:75` | 默认离线预览；真实写入须用户确认；工具 annotations 标明写性质 |

进一步的边界：create dry_run 只作本地校验；add labels dry_run 会读 API；分页过滤 PR 后不能按条目数判断结束；写入超时为结果不确定，不建议自动重复提交。

**已进行真实 Codex CLI 测试；用户未报告工具误用，不能编造误用案例。**
本地实现中发现 FastMCP 会包装业务异常并记录原始异常，已改为解包领域错误且关闭该框架 traceback logger；协议测试验证错误结构和敏感值不出现在日志。这属于开发发现，不冒充 Agent 误用记录。
后续如观察到误用，再记录修改及复测。此次检查另修正内部异常被误报为 INVALID_INPUT 的分类问题，并增加协议回归测试。

## Part III：OAuth

`oauth.py:41` 验证 state；`oauth.py:129` 独立启动回调并完成 Authorization Code + PKCE S256。
OAuth code 仅驻留内存，不持久化、不记录回调 URL。
`oauth.py:100` 在到期前 60 秒刷新，跨进程文件锁内重读缓存；完整令牌组一次写入 Windows Credential Manager。
刷新前持久化 invalid 标志，遇到中断时重新登录，不冒险重复消费旧 refresh token；此策略牺牲了瞬时网络故障后的自动恢复。

GitHub App 使用注册时的细粒度权限：Issues read/write 用于四个工具，Metadata read 用于仓库访问；不请求 Contents、用户邮箱等权限。
`offline_access` 用于请求过期令牌和刷新能力，不授予仓库权限。权限仍取用户与 App 的交集，App 仅安装到目标仓库。
`github_client.py:120` 验证目标 App 安装与 Issues write 权限。

Client ID/Secret 由 `.env` 或进程环境提供，真实配置、日志、缓存不入库。
401 会使被拒绝的当前令牌失效，但不会覆盖其他进程刚刷新的令牌。工具返回 AUTH_REQUIRED 及命令建议，不弹浏览器。
跨进程 Mock 测试使用纯虚构凭证与临时文件，生产存储没有明文 fallback。

## Part IV：Integration 与证据

Codex 注册已通过 `codex mcp add` 完成；配置示例为 `codex.config.toml.example` 和 `.mcp.json.example`。
本聊天使用脚本通过真实 stdio MCP 创建并读取 Issue；用户随后在 Codex CLI 直接调用，确认页面及调用日志符合预期。两类证据分别记录。

实际完成：38 项 pytest 通过，包括进程内 MCP 客户端和独立 stdio 子进程；Ruff 检查通过。
自动化测试中的 GitHub 请求全部使用 Mock。之后已完成真实 OAuth 登录、安装权限检查、创建和读取；用户完成 CLI 列表、标签追加、失败恢复及加速刷新测试。

### 实际 stdio 测试记录（不是 Agent transcript）

2026-10-14，`tests/test_mcp_stdio.py` 启动真实 Python CLI，经 MCP initialize、tools/list、tools/call 调用：

| 工具与参数 | request_id | 结果 |
|---|---|---|
| create_issue `{"title":"protocol smoke test"}` | `aee69e1a-2814-427e-bdab-3ee66cfc9e1f` | dry_run=true，无 API 请求 |
| get_issue `{"issue_number":"secret-invalid-value"}` | `e47d944a-44fe-4943-90bf-b1f7cd299b4b` | INVALID_INPUT，retryable=false |
| list_issues `{}` | `9867923f-f157-446c-a250-6286003e0359` | AUTH_REQUIRED，retryable=false |

对应本地 JSONL 中各有 tool_start 与 tool_end/tool_error。再次测试会生成新 ID。日志不提交。
另有 `tests/test_tools.py` 经 MCP 串联 Mock list→get，验证返回编号传递、PR 排除、分页与标签追加。

### 真实集成验证（2026-10-14）

- OAuth 浏览器授权成功，安装和 Issues write 权限检查通过；回调改用 18765，原 8765 被本机其他程序占用。
- 用户请求“新建一个 issue 看看”，脚本经本 Server 先预览，再 create_issue，随后 get_issue。Issue #1 创建 HTTP 201、读取 HTTP 200；创建 request_id 为 `84e70a61-da34-4fb4-a2c1-69b44f0fd6e9`，读取为 `442c0f68-093d-4e38-8dc5-29a457d65e4d`。用户确认页面及日志。
- 第二次 create_issue 参数：`{"title":"测试：Issue Manager dry run","body":"本次仅验证试运行预览，不创建真实 Issue。","labels":[],"dry_run":true}`。预览 request_id 为 `1a4dde06-3f4d-4e3c-83f4-dee633109067`，用户确认页面无变化；确认后仅将 dry_run 改为 false，创建 Issue #2，request_id 为 `d086e239-2f7c-450e-90ff-877b76fe7e53`。随后 get_issue `{"issue_number":2}` 验证，request_id 为 `53478aa0-2874-4138-8ad7-6da57411ceb7`。正文保留预览原文，虽描述试运行，此时确已真实创建。
- 用户在 Codex CLI 测试 list_issues，并确认新增日志。日志中成功列表调用 request_id 为 `c2644e1e-7e99-4012-b147-b31409ec66e3`。
- 用户报告标签追加测试通过；日志中预览 `06157d1a-28b3-42fc-8ea1-4e2a801f8390` 为 dry_run，真实追加 `cede9a8c-fe38-4d0d-9932-1f3ad91ce56a` 为 success。未获取 CLI 完整 transcript，不补写未知的标签参数。
- 提供给用户的失败测试 prompt：仅使用本 Server 的 get_issue 查询 `issue_number=999999999`，解释错误和下一步，不创建或修改内容。用户反馈得到预期结果；日志 `a5633766-87d7-4bd7-bfb2-67fdc8abc3ee` 为 HTTP 404 / NOT_FOUND。Agent 停止重复调用的行为依据用户反馈，不声称日志本身证明其推理。
- 加速刷新：在用户授权下，仅将缓存 expires_at 调至过去，保留令牌值；用户随后在 CLI 查询并检查 auth status，反馈测试通过。查询日志 `6a9510a9-6c10-4d65-aad2-c639df98a91c` 为 HTTP 200。验证了真实刷新路径，但不是等待 GitHub access token 自然过期；当前没有专门的刷新日志，刷新结论依据操作顺序和用户状态检查反馈。

Issue 链接：[#1](https://github.com/morty6688/cs146s-w2-issue-manager-test/issues/1)、[#2](https://github.com/morty6688/cs146s-w2-issue-manager-test/issues/2)。不提交原始日志、CLI 会话或任何令牌。

自己的日志证明本 Server 收到调用，不能单独证明其他工具未被同时调用。判断需结合客户端完整 transcript。
日志无法写入时操作仍可继续；此时日志缺失也不能作为未写入的证据。

## 已知限制与改进方向

- Windows 专用 Credential Manager；没有 Linux/macOS 存储实现。
- 真实功能验证已完成上述范围；完整 CLI transcript 未归档，令牌自然过期和真实多进程同时刷新尚未演练。
- dry_run/确认是客户端协作约定，不是服务端人类确认凭据；不提供跨调用确认票据。
- 结构化业务错误返回 MCP 正常结果内的 error 字段，Agent 须检查它；畸形 JSON-RPC 不保证 request_id。
- 只处理已有标签，最多每次 20 个；详情正文可能较长，未来可增加裁剪/分页。
- 网络 API 为同步实现，同一服务实例的调用可能串行等待；当前小规模用途可接受，未来可改为异步 HTTP。
- 依赖 Authlib 有两条弃用警告；未来升级 FastMCP 时复测协议和异常传播路径。
