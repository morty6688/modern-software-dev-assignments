# 实际命令与复跑说明

这是操作摘要，不是自动完整 shell transcript。除路径明确写出者外，以下工作目录是 `week3/lab`。以上是迁移前的历史工作目录；验证文件现位于 `week3/lab/validation`，下方复跑命令已更新。原始测试输出位于本目录的 `evidence/`；日志中的旧绝对路径保留不改。

| 实际命令/操作 | 结果 |
|---|---|
| `node --version`; `npm.cmd --version` | v20.11.1；10.2.4 |
| 从仓库根运行 `git clone --depth 1 --branch v1.11.23 https://github.com/iamkun/dayjs.git week3/lab/vendor/dayjs` | 失败：Could not read from remote repository |
| `Invoke-WebRequest https://codeload.github.com/iamkun/dayjs/zip/refs/tags/v1.11.23 -OutFile week3/lab/vendor/dayjs-v1.11.23.zip`（仓库根） | 首次套接字访问失败；权限审核后同命令成功 |
| `Expand-Archive week3/lab/vendor/dayjs-v1.11.23.zip week3/lab/vendor -Force`（仓库根） | 成功 |
| `Get-Content vendor/dayjs-1.11.23/package.json`；`Get-Content vendor/dayjs-1.11.23/babel.config.js` | 识别测试脚本、Jest、Babel、开发版占位字段 |
| `rg -n 'diff\|Diff' vendor/dayjs-1.11.23/test/display.test.js`（实际使用正则 `diff|Diff`）及读取 163–224 行 | 检查 Difference 测试分组 |
| `npm.cmd install --ignore-scripts --no-audit --no-fund` | added 1 package in 2s，退出 0 |
| `npm.cmd ls --depth=0` | dayjs@1.11.23 |
| `node reproduce.cjs` | day NaN；month 0，退出 0 |
| `node investigate.cjs > evidence/matrix.txt` | 182 表征检查，54 预期违例，退出 0 |
| `node investigate.cjs --expect-nan > evidence/expected-contract.txt` | 同样结果，退出 1（已单独记录） |
| `rg -n 'diff\(|monthDiff|absFloor|Utils.m|case C.Y|case C.Q|case C.M' vendor/dayjs-1.11.23/src/index.js vendor/dayjs-1.11.23/src/utils.js`，随后读取实现 | 在矩阵执行之后定位单位分支和月份差辅助函数 |
| `node trace.cjs` | 首次诊断包装 TypeError；修正包装分号后通过，退出 0 |
| `$env:TZ='UTC'; node investigate.cjs > evidence/matrix-utc.txt` | 182/54，退出 0 |
| `$env:TZ='America/New_York'; node investigate.cjs > evidence/matrix-new-york.txt` | 182/54，退出 0；随后移除临时 TZ 环境变量 |
| `Get-FileHash`（归档、index.js、utils.js、dayjs.min.js） | SHA-256 保存到 evidence/sha256.txt |
| `git diff --check`；`git status --short` | 已有跟踪文件无差异；新增 lab 产物 |

## 在新检出中复跑

```powershell
cd week3/lab/validation
npm.cmd ci --ignore-scripts --no-audit --no-fund
node reproduce.cjs
node investigate.cjs
node investigate.cjs --expect-nan
# 上一条预期退出 1，表示缺陷仍存在。
```

可选：下载只读源码以重跑源函数诊断（前两个脚本无需源码）：

```powershell
New-Item -ItemType Directory -Force vendor | Out-Null
Invoke-WebRequest https://codeload.github.com/iamkun/dayjs/zip/refs/tags/v1.11.23 -OutFile vendor/dayjs-v1.11.23.zip
Expand-Archive vendor/dayjs-v1.11.23.zip vendor -Force
node trace.cjs
```

npm 依赖锁及归档哈希分别提供发布包和源码来源的复核依据；下载可能需要网络权限。不要将 `--expect-nan` 的退出 1 当成安装失败或修改断言以掩盖缺陷。
