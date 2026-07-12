# GPAO (Grade Point Alignment Optimizer)

[![CI](https://github.com/BTspaceC/GPAO/actions/workflows/ci.yml/badge.svg)](https://github.com/BTspaceC/GPAO/actions/workflows/ci.yml)

这是一套帮助大学生在课程大作业中**将高价值工作展示在老师最容易看到的位置**的工作流系统。

它不是论文生成器，不是 AI 代写工具，也没有所谓的“去 AI 味”伪装功能。它解决的核心问题是：缓解“评分可见性不足”——即你花了大量精力做的数据清洗、代码复现等工作，在老师快速翻阅阅卷时被忽略。

> **当前版本状态**: `V2.1.0-RC1`
> 本系统强制执行完全的事实证据等级基线。

> **V3 状态（2026-07-13）**：`V3.1.0` 候选完成一次冻结的 48 次评测，严重违规为 0，但因 3 次适配器路由错误未通过 RC 门禁，未发布。当前公开版本仍为 `V2.1.0-RC1`。详见 `evals/reports/v3.1.0-candidate-failed.md`。

## 使用方法

本系统分为 **模块化版** 与 **单文件 Bundle 版** 两种分发形式。

### 方式一：单文件版 (推荐)
最简单的使用方式是直接加载打包好的单文件版本。该文件已自包含 `SKILL`、所有工作流契约以及所有作业类型适配器：
1. 提取文件 `dist/GPAO.bundle.md`。
2. 将其作为完整的 System Prompt 输入给兼容超长上下文的 AI (如 GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro)。

### 方式二：模块化执行
如果您作为开发者希望针对自己学校的特点补充特定适配器，可按目录结构单独加载：
将 `SKILL.md` 作为主路由配置，AI 将根据对话阶段按需读取 `workflows/` 与 `adapters/`。

## 隐私与安全约束

在将真实作业交由 AI 分析时，请务必建立本地隔离环境。
本项目默认通过 `.gitignore` 保护以下可能包含您个人信息的隐私目录，请将真实作业放在这些目录下以防止误上传：
- `private_assignments/` (您的个人作业原始文件)
- `user_data/` (作业脱敏前中间数据)
- `profiles/private/` (未脱敏的真实教师画像表)
- `*.raw.csv / *.raw.xlsx` (原始受访样本)

## 开发者指令

如果您在本地修改了工作流或规则，必须确保未破坏内部一致性：

1. **运行发布检查器 (CI Checker)**：
   检查是否存在非法的 UTF-8 BOM 字符或 Markdown 路径断链：
   ```bash
   python tools/ci_checker.py
   ```
2. **运行单元测试 (Unit Tests)**：
   验证是否错误地硬编码了分值或引入了未经验证的造数行为：
   ```bash
   python -m unittest discover tests
   ```
3. **重新构建 Bundle (Build Bundle)**：
   每次修改源文件后，必须重新打包 `dist/GPAO.bundle.md` 才能生效：
   ```bash
   python tools/build_bundle.py
   ```

## 适用范围

目前内置了针对以下作业类型的差异化适配：
- 实证论文 (Empirical Paper)
- 编程项目 (Programming Project)
- 实验报告 (Experiment Report)

## 核心指令

1. **`/诊断`** (Diagnose)
   初步识别未知作业的类型与致命结构风险，推荐下一步行动路线。
2. **`/画像`** (Profile)
   从确凿的历史证据中，建立带有置信度和跨课程追踪的结构化教师偏好档案。
3. **`/规划`** (Plan)
   根据任务书和已知的教师画像，按决定性 P0-P3 规则拆解任务，协助你放弃低收益修饰。
4. **`/审计`** (Simulate Grading)
   完稿后进行“3分钟扫视”和“可见性诊断”，通过排版、索引将隐性工作量显性化。
5. **`/修改`** (Modify)
   基于审计结果，输出带有严格事实核验的局部 Diff 修改，拒绝失控的全文重写。
6. **`/复盘`** (Postmortem)
   成绩发布后客观比对证据与分数，更新客观事实，抛弃主观臆想。

## 局限性与免责声明

- 本工具**不能**承诺特定分数或确保高分。
- V3 候选将证据拆分为 `authority/verification/confidence`，但该候选尚未通过 RC1 行为门禁；当前发布状态仍为 V2.1.0-RC1。
- 本工具没有任何学术剽窃规避功能，仅供格式化展示研究成果之用。
