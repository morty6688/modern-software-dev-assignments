# 第 4 周：让杂乱的仓库适合智能体使用

## 作业概述

选择一个你不熟悉的开源仓库，为它补上缺少的智能体配置文件：`AGENTS.md` 或 `CLAUDE.md`，任选其一。重点是练习一份优秀配置文件应有的**结构与内容**：哪些信息该写，哪些不该写，以及要具体到什么程度才能真正发挥作用。

### 学习目标

- **熟悉**一个陌生的代码库，达到能够准确描述它的程度。
- **将这些知识固化**为持久可用、可据以执行操作的仓库上下文。
- **判断**哪些内容应写入智能体配置文件，哪些只是干扰信息。

## 学习材料

- **[AGENTS.md 格式](https://agents.md/)**
- **[如何编写优秀的 CLAUDE.md](https://www.hlyr.dev/blog/writing-a-good-claude-md)**
- **[Claude Code 最佳实践](https://code.claude.com/docs/en/best-practices)**

## 示例仓库

| 仓库 |
|---|
| [bigskysoftware/htmx](https://github.com/bigskysoftware/htmx) |
| [iamkun/dayjs](https://github.com/iamkun/dayjs) |
| [slidevjs/slidev](https://github.com/slidevjs/slidev) |
| [pixijs/pixijs](https://github.com/pixijs/pixijs) |
| [yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp) |
| [AUTOMATIC1111/stable-diffusion-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui) |
| [TheAlgorithms/Python](https://github.com/TheAlgorithms/Python) |
| [vuejs/vue](https://github.com/vuejs/vue) |
| [react/react](https://github.com/react/react) |

你也可以自行选择其他仓库，只要它**不是**你编写的即可。

## 第一部分：探索仓库（20 分）

先 Fork 该仓库，再弄清楚它实际如何运作：

- 如何构建、测试、检查代码规范和运行？找出**确切的**命令。
- 主要目录和入口点有哪些？
- 代码遵循了哪些没有明确写出来的约定？
- 哪些内容是自动生成的、随仓库附带的第三方代码，或因其他原因不应手动编辑？

使用智能体协助探索，这是最快的方法。

## 第二部分：编写文件（55 分）

在你 Fork 的仓库根目录编写 `AGENTS.md` 或 `CLAUDE.md`，至少涵盖以下内容：

- **项目是什么**：用几句话介绍，让智能体了解项目所属领域。
- **架构**：关键目录、入口点，以及各部分之间的关系。
- **命令**：构建、测试、代码规范检查和运行命令。必须准确且可以直接复制粘贴执行，例如 `pixi run pytest tests/`，而不是“运行测试”。
- **约定**：仓库实际采用的测试惯用方式、代码风格规则和命名模式。
- **操作边界**：哪些内容不能改动，以及哪些看似合理、实际却错误的命令或目录值得特别提醒。

质量标准是：每一行都应该**针对这个仓库**。一个合格模型本就会遵循的通用建议属于凑字数，重复 README 的内容也是如此。这个文件会被载入每一次上下文，因此篇幅本身就是成本。将长度控制在一页左右。

## 第三部分：实际试用（25 分）

将文件放到位后，让智能体在仓库中执行两个小任务，例如运行测试套件和做一处小修改。

报告你的观察结果：智能体是否使用了你提供的命令，并遵循了你写下的约定？然后，根据实际使用情况，指出你会对该文件做出的**一项改进**。

## 交付内容

在 `week4/` 中提交：你编写的 `AGENTS.md` 或 `CLAUDE.md`、填写完整的 `writeup.md`，以及指向你 Fork 的仓库的链接。

## 评分标准（总分 100 分）

| 部分 | 分值 | 满分要求 |
|---|---|---|
| 第一部分：探索 | 20 | 准确描述构建、测试、代码规范检查命令，以及仓库结构和约定 |
| 第二部分：配置文件 | 55 | 涵盖全部五个方面，内容针对该仓库，命令准确，表述简洁 |
| 第三部分：试用 | 25 | 执行两个任务并如实报告，提出一项有实际依据的改进 |

## 提交说明

1. 确保已将所有更改推送到远程仓库，以便评分。
2. **确保已将 `mihail911`、`isaackann` 和 `vdaita` 添加为你的作业仓库的协作者。**
3. 通过 Gradescope 提交。
