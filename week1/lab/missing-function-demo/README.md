# Week 1 实验：恢复被删除的函数

这是一个**故意无法通过测试**的小项目，使用 Python 3.10+ 和标准库，无需安装额外依赖。

## 初始状态

- `pricing.py`：保留了 `calculate_subtotal`，但删除了 `calculate_total`。
- `receipt.py`：仍然导入并调用 `calculate_total`。
- `test_receipt.py`：包含 4 个回归测试，当前会在导入阶段失败。

在本目录运行：

```powershell
python -m unittest -v
```

预期报错包含：

```text
ImportError: cannot import name 'calculate_total' from 'pricing'
```

## 函数应有的行为

需要恢复的接口是 `calculate_total(items, discount_cents=0)`：

- `items` 是 `(单价分, 数量)` 元组组成的列表，金额均为整数分。
- 折前金额等于每项单价乘以数量后求和；已有 `calculate_subtotal` 可复用。
- 实付金额等于折前金额减去优惠金额。
- 单价、数量或优惠金额为负数时，抛出 `ValueError`。
- 优惠金额超过折前金额时，抛出 `ValueError`；恰好等于折前金额时，实付金额为 0。
- 空订单在优惠金额为 0 时返回 0。

本实验假定输入类型符合接口约定，无需扩展为复杂的订单系统。

## 正式捕获前：复制到独立仓库

作业要求使用自己的临时仓库。本目录位于作业仓库中，正式捕获时请先复制出去。在**作业仓库根目录**运行以下 PowerShell 命令：

```powershell
# 创建唯一目录，避免覆盖已有实验。
$demoDir = Join-Path $env:TEMP ("mimo-missing-function-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $demoDir | Out-Null
Copy-Item -Path .\week1\lab\missing-function-demo\*.py -Destination $demoDir
Copy-Item -LiteralPath .\week1\lab\missing-function-demo\README.md -Destination $demoDir
Copy-Item -LiteralPath .\week1\lab\mimocode.json -Destination $demoDir

# 从现有 .env 加载凭证，只复制配置文件到实验目录。
$env:MIMO_API_KEY = (Get-Content .\week1\lab\.env -Raw | ConvertFrom-StringData).MIMO_API_KEY
Set-Content -LiteralPath (Join-Path $demoDir '.gitignore') -Value @('__pycache__/', '*.py[cod]', '.env', '.mimocode/', '*.flows', '*.har') -Encoding utf8
Set-Location -LiteralPath $demoDir
git init
```

然后按 [MiMo 作业说明](../../chinese/assignment-mimo.md)启动代理并验证请求。复制出去后，上述相对链接不再适用，请在原作业仓库中查看说明。`session.flows` 应放在这个实验仓库以外的目录。

在实验目录启动新会话：

```powershell
mimo --model mimo-capture/mimo-v2.6-pro
```

将下面的任务提示词发给 MiMo。正式会话内的首次失败才是后续分析所需的证据；之前手动运行的失败只能用于确认环境。

## 发给 MiMo 的任务提示词

```text
这个独立实验仓库的订单收据功能坏了：pricing.py 中的 calculate_total 函数被删除了，其他模块仍然依赖它。

请先阅读 README.md 并列出明确的任务计划，执行过程中更新计划状态。
在修改任何代码前，先运行 python -m unittest -v，记录并解释实际错误。
然后检查 pricing.py、receipt.py 和 test_receipt.py，恢复 calculate_total 的完整行为。
保留现有测试，并在 test_receipt.py 中增加至少三个边界测试，覆盖负数优惠、优惠超过折前金额、优惠恰好等于折前金额。
复用已有的金额计算逻辑，不要通过删除导入、跳过测试或放宽断言来绕过故障。
最后重新运行完整测试，汇报修改的文件、失败原因和测试结果。
```

## 四项要求如何对应

| 要求 | 会话中应保留的证据 |
|---|---|
| 至少操作两个文件 | 恢复 `pricing.py`，在 `test_receipt.py` 增加测试 |
| 至少失败一次并恢复 | 首次测试的导入错误、修复过程、最终通过的测试结果 |
| 明确计划 | 首次计划及后续状态更新 |
| 自己的临时仓库 | 复制出去后的实验路径及 `git init` 记录 |

以实际捕获为准，任务提示词本身不能证明智能体完成了这些行为。实验结束后，按照作业说明清理代理配置和临时凭证环境变量。
