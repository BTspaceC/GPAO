# GPAO

GPAO（Grading Preference Alignment Optimizer）是一个面向大学课程作业的 Agent Skill，可以在 Claude Code 和 Codex 中使用。它根据任务书、评分标准和你已有的材料，帮你规划作业、检查评分项覆盖、在提交前找出风险，并在不编造任何事实的前提下做最小修改。

它围绕三个问题工作：

1. 你做了很多，老师能不能一眼看见？
2. 你认为重要的内容，老师是否也认为重要？
3. 作品是否规范，但又不像模板批量生成？

当前版本：`V3.2.0`（候选版，尚未完成冻结行为评测，见“验证状态”）

## 指令一览

| 指令 | 英文别名 | 什么时候用 | 你会得到 |
|---|---|---|---|
| `/诊断` | `/diagnose` | 刚拿到作业，或手上材料很散 | 作业类型、主要风险、材料缺口、建议下一步 |
| `/规划` | `/plan` | 有任务书和评分表，要安排怎么做 | 要求清单、评分点矩阵、P0–P3 任务排序、最小可交付版本 |
| `/审计` | `/audit` | 写完了，提交前完整检查 | 30 秒/3 分钟可见性检查、合规与事实复核、方法边界、风险排序 |
| `/速审` | `/quick` | 马上要交，只想知道最该改哪几处 | 一屏以内：最多 3 个最小动作 |
| `/修改` | `/revise` | 根据审计结果改文本 | 带原文定位的最小 Diff，默认只预览不写文件 |
| `/画像` | `/profile` | 有老师的评语或历史反馈 | 有证据、有作用域的老师偏好记录 |
| `/复盘` | `/postmortem` | 成绩出来后 | 结果与证据是否一致、下次改进策略 |

不用记指令也可以：直接说“今晚要交，帮我快速看一眼”“成绩出来了帮我复盘”，GPAO 会选择最接近的工作流，并在回答开头说明选了哪一个。

## 安装

### 推荐：只安装运行时文件

```bash
git clone https://github.com/BTspaceC/GPAO.git
cd GPAO
python tools/install_skill.py --target claude
```

- `--target claude`：安装到 `~/.claude/skills/gpao`（Claude Code）
- `--target codex`：安装到 `$CODEX_HOME/skills/gpao`，未设置时为 `~/.codex/skills/gpao`（Codex）
- `--target <目录>`：安装到任意目录
- `--dry-run`：只列出会复制的文件

安装脚本只复制 `SKILL.md`、工作流、适配器、模板和三个运行时工具，不会把测试、评测数据和开发文档放进 skills 目录。以后更新时，`git pull` 后再运行一次同样的命令即可。

安装后重新打开 Claude Code 或 Codex。

### 其他方式

- **直接克隆到 skills 目录**：`git clone https://github.com/BTspaceC/GPAO.git ~/.claude/skills/gpao`（会带上开发文件，但不影响使用）。
- **单文件模式**：把 `dist/GPAO.bundle.md` 整个提供给不支持 Skill 目录的平台。这种模式不能运行本地工具，但规则完全相同。

## 使用方法

### 典型流程

```text
拿到作业  →  /诊断  →  /规划  →  写作  →  /审计（或赶时间用 /速审）  →  /修改  →  提交
成绩出来  →  /复盘  →  （有老师评语时）/画像
```

每个工作流都会在回答末尾输出一个“状态补丁”，下一个工作流会接着用。你不需要读它，可以直接跳过。

### 示例

提交前快速检查：

```text
/速审 这是我的课程论文 paper.docx，任务书在 brief.pdf，今晚 12 点截止。
```

从任务书开始规划：

```text
/规划 这是社会调查课的期末作业任务书和评分表（附件），我已经收完了问卷，还有两周。
课程允许用 AI 润色语言，但需要在文末声明。
```

根据审计结果修改，先预览：

```text
/修改 按刚才审计的 P0 和 P1 改结论段，先给我看 Diff，不要直接改文件。
```

确认后写入文件：

```text
批准执行：把 MOD_001 和 MOD_002 应用到 paper.md。
```

成绩出来后复盘：

```text
/复盘 期末论文 80 分，没有分项分数。老师评语是“分析比较表面”。这是我交的版本。
```

### 怎么读输出

每个回答分三层：

1. **结论速览**：最前面几行，告诉你现在的判断和最该做的 1–3 件事。时间紧只看这里就够了。
2. **详细分析**：按工作流展开的表格和依据。
3. **状态补丁**：最后的 JSON，给工具和后续工作流用，可以跳过。

正文中的徽标表示每个判断的可信程度：

| 徽标 | 含义 |
|---|---|
| 【已证实】 | 有任务书、评分表、老师原话或作业原文直接支持 |
| 【推断】 | 有一定依据，但来自二手信息、你的猜测或系统推理 |
| 【待确认】 | 证据不足，需要你补充材料 |
| 【已反驳】 | 已有证据与该判断矛盾 |

### 为了拿到更好的结果

- **提供评分标准**：没有评分标准时，GPAO 不会编造权重，只能检查硬性要求和真实性。
- **告诉它作业类型**：例如“这是一份实验报告”。类型一旦确定，缺少其他材料也不会被降级为通用处理。
- **告诉它课程的 AI 使用政策**：禁止、限定用途、需要声明还是允许。未提供时，GPAO 会提醒你确认；如果课程禁止生成文本，它只指出问题、不给替换文本。
- **给真实数据和过程**：GPAO 不会替你补数据、补实验步骤或补引用，缺什么会标成“待补充”。

## 附带工具

在仓库根目录或安装目录下运行（需要 Python 3.10+）：

| 工具 | 用途 | 示例 |
|---|---|---|
| `tools/skim_view.py` | 生成作业的“30 秒视图”：标题、摘要、各级标题、图表标题、结论、附录引用；传入项目目录时汇总 README、测试和依赖清单 | `python tools/skim_view.py paper.docx` |
| `tools/case_state.py` | 校验和合并状态补丁 | `python tools/case_state.py validate-patch patch.json` |
| `tools/student_voice_auditor.py` | 提示空洞、绝对化的模板表达（不做 AI 文本判断，结果不阻断） | `python tools/student_voice_auditor.py draft.txt` |
| `tools/install_skill.py` | 安装运行时文件 | `python tools/install_skill.py --target codex` |

`tools/skim_view.py` 支持 `.md`、`.txt`、`.docx` 和项目目录，只用标准库；读取 `.pdf` 需要先 `pip install pypdf`。加 `--json` 可输出结构化结果。

## 作业适配

作业类型按 `SKILL.md` 第七节的路由表确定，内置四个适配器：

- 实证论文（`adapters/empirical_paper.md`）
- 编程项目（`adapters/programming_project.md`）
- 实验报告（`adapters/experiment_report.md`）
- 通用与混合（`adapters/general.md`）：只在类型确实未知，或存在两种以上不同类型的主要交付物时使用

## 安全边界

- 不编造数据、引用、教师反馈、评分权重或未完成的操作过程。
- 不代写整份作业；遵守课程的 AI 使用政策。
- 不判断文本是否由 AI 生成，不承诺规避任何检测系统。
- 没有你的明确授权时，`/修改` 只预览，不覆盖原文件。
- 教师画像默认只在当前会话中使用；只有你指定私有本地路径时才保存，且不写入公开仓库。
- 不承诺具体分数。

## 开发与验证

```bash
python tools/ci_checker.py          # 编码、链接、JSON、隐私文件检查
python -m unittest discover tests   # 确定性单元测试
python tools/build_bundle.py        # 修改源文件后重新生成 dist/
```

CI 在 Ubuntu 和 Windows、Python 3.11 和 3.13 上运行以上三步，并检查提交的 Bundle 是否最新。

### 真实模型评测

`evals/run_live_eval.py` 用本机的模型 CLI 实际运行评测案例（默认 `claude -p`，也可用 `--backend codex` 或 `--command` 指定其他命令）：

```bash
# 1. 用 Bundle 运行盲化案例，原始输出保存到 evals/raw/（已被 .gitignore 排除）
python evals/run_live_eval.py generate --out evals/raw/v32-run1

# 2. 用评委模型把原始输出归一化为评分记录
python evals/run_live_eval.py judge --raw-dir evals/raw/v32-run1 --out evals/raw/v32-run1/runs.jsonl

# 3. 评估技能描述的触发准确率（24 个正反例）
python evals/run_live_eval.py triggers --out evals/raw/triggers.json
```

第 2 步的输出可以直接交给 `evals/behavior_eval.py` 计分。完整的发布门禁、盲化和溯源要求见 `evals/evaluation_protocol.md`。

## 验证状态

- V3.2.0 通过仓库检查和全部确定性单元测试。V3.2 新增的输出分层、统一路由表、`/速审` 和 AI 使用政策规则**尚未经过冻结行为评测**，因此是候选版，不是 RC 或 Stable。
- 说明：V3.1.0-RC2 中修复的适配器路由问题，当时只做了两项定向验证，没有按 `evals/evaluation_protocol.md` 用新的未见案例重跑完整门禁。V3.2 把路由规则集中到一处，正是为了从根上解决这个问题，但效果仍需评测确认。
- 有限测试中没有观察到违规，不代表系统永远不会违规。

## 许可证

MIT，见 `LICENSE`。
