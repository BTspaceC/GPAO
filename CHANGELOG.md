# CHANGELOG

## V2.0 (2026-07-10)
### 阶段 3-5 完成 (2026-07-10)
- **增加类型适配器 (阶段3)**：新建了 `empirical_paper.md` (实证论文)、`programming_project.md` (编程项目)、`experiment_report.md` (实验报告) 三个适配器，提供针对性的评分转换与亮点池。
- **重做听觉疲劳案例 (阶段4)**：在 `examples/hearing_fatigue_case/` 下重建了包含原始输入、质量诊断、可见性矩阵和修改策略的全套真实案例分析流程。
- **工具重构与验收测试 (阶段5)**：将原来的 `ai_tone_detector.py` 改写并重命名为 `student_voice_auditor.py`，去除了所有 AI 鉴定功能并加入免责声明。新建了 4 个验收测试用例 (缺少标准、低置信偏好、不可见性、冲突要求) 以约束 Agent 行为。

### 阶段 R 止损与稳定化 (2026-07-10)
- **事故记录**：阶段0使用 `Copy-Item -Recurse` 在项目内部备份时触发了无限递归，随后未能中止执行，错误地提前删除了 `checklists` 和 `examples` 的旧版文件。
- **恢复操作**：由于无法通过本地系统日志还原旧版文件，已被确认为永久丢失。通过建立全新的 `academic_survival_skill` 纯净目录和项目外 ZIP 归档，终止了深层路径递归的进一步破坏。
- **断链清理**：修改 `SKILL.md`，移除对 planned 文件的虚假路由；修改 `/审计` 流程，弱化对 Python 工具的强依赖，全项目扫描零断链。
- **建立示例**：在 `test_runs/` 下输出了三条核心工作流的实体模拟运行结果。

### 阶段1-2 完成 (阶段0失败)
- 旧版备份因递归复制错误而损坏，无法恢复。当前以实际文件系统为唯一事实来源

### SKILL.md 重写（路由器角色）
- 仅包含核心原则、证据分级、冲突优先级、材料安全规则和指令路由表
- 不复制子文件内容，每条规则只有一个权威来源
- 新增第七原则：最小必要修改（四维评估）
- 新增冲突处理优先级链
- 新增材料安全规则（防提示注入）

### 新增文件
- `README.md`：面向用户的说明，含功能状态表
- `CHANGELOG.md`：本文件
- `templates/assignment_intake.md`：纯采集表，移除画像推断
- `templates/rubric_visibility_matrix.md`：修正"附录厚度"为"证据链完整性与可检索性"
- `templates/teacher_evidence_ledger.md`：偏好证据账本（新增）
- `profiles/teacher_profile_template.md`：独立老师画像（新增）
- `workflows/plan_assignment.md`：/规划 工作流 + 输出契约 + 大纲生成辅助Prompt
- `workflows/simulate_grading.md`：/审计 工作流 + 三级模拟输出契约 + 去空洞化和局限性辅助Prompt
- `workflows/postmortem.md`：/复盘 工作流 + 输出契约

### 移除文件
- 旧版中文命名的 checklists（01_30秒扫视...、02_3分钟...、03_深度复核...）
- 旧版中文命名的 templates（01_作业信息采集与画像表、02_评分点与可见性追踪矩阵）
- 旧版 examples（01_耳机使用与听觉疲劳复盘案例）
- 旧版 `tools/ai_tone_detector.py`（待阶段5改名重建）

### 概念修正
- "附录厚度" → "附录证据链完整性与可检索性"
- "注入真实的调研挣扎" → "提取并呈现真实过程证据"
- "完整恢复原模板" → "根据已知功能重新构建等效模板"
- 最小必要修改公式改为四维分级（评分影响×可见概率×证据可信度÷时间成本），仅用于相对排序

### 待阶段3-5完成
- adapters/（实证论文、编程项目、实验报告）
- examples/hearing_fatigue_case/（案例重做）
- tools/student_voice_auditor.py（改名+重定位）
- tests/（验收测试用例）
- checklists/ 英文版文件

## V1.5 (2026-07-10)
- 引入 GPAO 概念重构，导致 V1 内容丢失（无备份）

## V1 (2026-07-10)
- 初始版本
