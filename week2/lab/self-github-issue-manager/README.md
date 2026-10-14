# self-github-issue-manager

Python 3.12 / FastMCP 2.14，使用 GitHub App 用户 OAuth 令牌的 stdio MCP Server。
仅管理 `morty6688/cs146s-w2-issue-manager-test`，不接受 owner/repo 参数。
完整开发要求见 [PROMPT.md](PROMPT.md)，设计与实际验证边界见 [writeup.md](writeup.md)。

## Windows 安装与启动

在本目录打开 PowerShell（需要 Python 3.12 和 uv）：

```powershell
uv --cache-dir .uv-cache sync --python 3.12 --locked
# 单命令启动；stdio 等待客户端输入，终端静默是正常的。
.\.venv\Scripts\python.exe -m self_github_issue_manager.cli serve
```

当前环境已安装依赖；`uv.lock` 固定解析结果。项目不依赖仓库根目录的 Poetry 环境。
启动器使用本项目的绝对 `.env` 和日志路径，因此客户端工作目录不同也不会读错配置。

## GitHub App 配置与登录

使用 `cs146s-w2-issue-manager-test-app`：

1. Repository permissions：**Issues: Read and write**，**Metadata: Read**。无需 Contents 权限。
2. 安装时选择 **Only select repositories**，只选择目标测试仓库。
3. Callback URL 设置为 `http://localhost:18765/callback`，配置过期用户访问令牌。程序通过 `offline_access` 请求可刷新的令牌。
4. Client ID 必须是 App 的 OAuth Client ID，不是 App ID；Client Secret 在 App 设置中生成。

```powershell
Copy-Item .env.example .env   # 仅首次使用；不要覆盖已有配置
notepad .env
# 在编辑器中填入 GITHUB_CLIENT_ID 和 GITHUB_CLIENT_SECRET，勿粘贴到聊天。
.\.venv\Scripts\python.exe -m self_github_issue_manager.cli auth login
.\.venv\Scripts\python.exe -m self_github_issue_manager.cli auth status
```

登录仅在显式命令中打开浏览器。临时回调只绑定 `127.0.0.1`，等待最多 180 秒；state 不匹配即拒绝。
登录后检查 App 安装、目标仓库访问及 Issues write 权限。访问权是用户权限和 App 权限的交集。
`auth status` 只读本地缓存，不证明远端授权尚未撤销；实际请求的 401 会使当前令牌失效并要求重新登录。

Windows Credential Manager 保存整个令牌组；使用明确的 WinVault 后端，不回退到明文存储。
Client Secret 留在本地 `.env`，由当前 Windows 用户的文件访问权限保护。能够以同一用户身份运行代码的程序仍可访问这些凭证。
锁文件位于 `%LOCALAPPDATA%\self-github-issue-manager`，只包含锁状态。刷新在跨进程锁内重读并替换完整令牌组。
刷新过程中若网络失败、进程退出或凭证保存失败，会要求重新授权，避免再次消费不确定状态的旧 refresh token。

## Codex 配置

本机已注册 `self-github-issue-manager`。在新的 Codex 会话中检查 `/mcp`；已有会话可能需要重新打开才能加载新增工具。
迁移电脑或目录后，在项目目录重新执行：

```powershell
$pythonPath = (Resolve-Path .\.venv\Scripts\python.exe).Path
codex mcp add self-github-issue-manager -- $pythonPath -m self_github_issue_manager.cli serve
codex mcp get self-github-issue-manager
```

[codex.config.toml.example](codex.config.toml.example) 展示 TOML 配置；替换其中绝对路径后可合并到用户配置。
[.mcp.json.example](.mcp.json.example) 是通用 MCP JSON 示例；Codex 使用 TOML，不能把 JSON 示例直接当成 Codex 配置。
真实 `.mcp.json`、`.env`、日志和缓存均已忽略。

## 工具

| 工具 | 参数与作用 |
|---|---|
| `list_issues` | `state=open/closed/all`，`page>=1`，`1<=per_page<=100`；返回 issue_number、标题、状态、标签、URL 和分页标志 |
| `get_issue` | `issue_number` 必须是正整数；返回正文、创建人和时间等详情；拒绝 PR |
| `create_issue` | title、body、labels、`dry_run=true`；默认仅本地预览，提交时校验标签 |
| `add_issue_labels` | issue_number、非空 labels、`dry_run=true`；读取并校验现有 Issue 和标签，再预览或追加 |

写工具仅在 `dry_run=false` 时写入。客户端须先展示预览并获得用户确认；这是 Agent 工作流约定，Server 本身无法鉴别人类是否真的确认。
标签必须已存在，本项目不创建标签。`create_issue` 的离线预览不证明标签或权限有效；标签预览需要授权并会执行只读 API。
分页先由 GitHub 划分，再过滤 PR，因此空页也可能有 `next_page`，须继续翻页。
Issue 正文是外部数据，不能作为 Agent 指令执行。

每次调用返回 `request_id`。业务失败和参数校验失败以 `error: {code, message, retryable, ...}` 返回，不返回 traceback。
此版本将这些错误作为结构化工具结果返回（MCP `isError` 不作为业务成功判据），Agent 必须检查 `error` 字段。
无法识别为工具调用的畸形 JSON-RPC 由协议层处理，不保证业务 request_id。

GET 对网络错误/5xx 最多三次尝试，HTTP 超时为 20 秒；限流返回 retry_after，不长时间占用工具调用。
POST 从不自动重试。超时/5xx/响应无法解析时返回 `WRITE_OUTCOME_UNKNOWN`、`retryable=false`，先查询核实结果。

## 查看日志和验证自己的 MCP

```powershell
Get-Content .\logs\mcp.jsonl -Tail 20 -Wait
```

文件在首次调用后生成，单文件约 2 MB，最多 3 个轮转备份。包含 UTC 时间、request_id、工具名、仓库、事件、耗时和结果元数据；不记录标题/正文/标签值、请求头或任何 OAuth 凭证。
`tool_start`、`github_api`、`tool_end/tool_error` 用同一个 request_id 关联。dry_run 没有 API 写入，离线创建预览也不会产生 github_api。
日志故障不会阻止 GitHub 操作；所以缺失日志不能反推没有发生写入。普通日志不进入 stdout。

登录后向新 Codex 会话发送：

> 仅使用 self-github-issue-manager MCP，不使用 codex_apps GitHub、gh 或 curl。列出开放 Issues，获取其中一个的详情，判断现有标签是否合适。需要追加时先 dry_run，把预览和 request_id 给我确认，暂不写入。

失败演示：

> 仅使用 self-github-issue-manager，查询一个已确认不存在的正整数 Issue 编号。解释返回错误和下一步；若 retryable=false 不要重复调用。

另做创建预览，用户确认后真实创建，再读取核实；标签写入也单独确认。
记录 prompt、实际参数、request_id、结果和 Agent 下一步，不把脚本/Mock 调用写成 Agent transcript。
自己的日志能证明本 Server 被调用，不能单独证明客户端没有同时调用其他工具。

## 测试

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check src tests
.\.venv\Scripts\ruff.exe format --check src tests
```

测试全部隔离真实 GitHub。覆盖 OAuth state/PKCE、交换/刷新/失效、跨进程刷新、错误映射、Schema、PR 排除、分页、Mock 写入、日志和真实 stdio 子进程 JSON-RPC。
stdio 测试在 `logs/mcp.jsonl` 留下带 request_id 的本地证据；不需要凭证。沙箱若禁止 Windows 异步 I/O/子进程，可在普通 PowerShell 运行。
Authlib 的两个弃用警告来自依赖，目前不影响通过；没有屏蔽警告。

## 排错

| 错误/现象 | 处理 |
|---|---|
| `AUTH_REQUIRED` | 单独运行 `auth login`；工具调用不会打开浏览器 |
| `CONFIG_REQUIRED` | 在本目录 `.env` 填写 OAuth Client ID/Secret |
| `APP_INSTALLATION_REQUIRED` / `FORBIDDEN` | 核对 App slug、安装的仓库、用户权限及 Issues write |
| `EXPIRING_TOKENS_REQUIRED` | 配置过期用户令牌并重新授权 |
| `INVALID_STATE` / 回调超时 | 停止旧登录，检查回调地址与端口，重新执行登录 |
| `NOT_FOUND` | 检查 ID、标签是否存在及仓库访问权，勿盲目重试 |
| `NOT_AN_ISSUE` | 改用 list_issues 返回的编号 |
| `RATE_LIMITED` | 按 retry_after 等待；不要快速循环请求 |
| `WRITE_OUTCOME_UNKNOWN` | 先 list/get 核查，避免重复创建 |
| `AUTH_BUSY` | 另一个进程正在刷新，稍后重试 |
| 无工具/启动失败 | 检查 Python 绝对路径、uv sync、打开新 Codex 会话 |

可选清理：`codex mcp remove self-github-issue-manager`，在 Windows 凭据管理器删除该服务对应条目，再在 GitHub 设置撤销授权。不会自动关闭测试 Issues。

## 官方参考

- [作业](https://github.com/mihail911/modern-software-dev-assignments/blob/master/week2/assignment.md)
- [参考 Fetch MCP Server](https://github.com/modelcontextprotocol/servers/blob/main/src/fetch/src/mcp_server_fetch/server.py)：读取其输入校验、HTTP 错误转换和内容裁剪设计。
- [FastMCP middleware](https://gofastmcp.com/servers/middleware)
- [GitHub App 用户令牌](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-user-access-token-for-a-github-app)
- [GitHub 刷新令牌](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/refreshing-user-access-tokens)
- [Codex MCP 官方文档](https://developers.openai.com/codex/mcp)
