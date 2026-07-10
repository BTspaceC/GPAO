# 教师偏好证据账本 (Teacher Evidence Ledger)
`schema_version: 3.0`

- `evidence_id`: 证据编号
- `claim`: 偏好主张（例如：喜欢复杂的图表）
- `authority`: 来源权威性 (`official/direct_feedback/observed/secondhand/user_hypothesis/unknown`)
- `verification`: 验证状态 (`verified/supported/contradicted/evidence_insufficient`)
- `confidence`: 系统对当前判断正确性的把握 (`high/medium/low/unknown`)，不代表权威性或重要性
- `source_id`: 原始材料索引或出处
- `source_type`: 证据来源类型（任务书/评语/课堂录音等）
- `quote`: 原文摘录（必须包含具体的话语或要求截图说明，不能只写总结）
- `date`: 收集日期
- `course`: 课程名称
- `assignment`: 对应作业
- `notes`: 备注
- `legacy_label`: 旧版标签；仅在导入旧记录时保留

## 证据列表示例
| evidence_id | claim | authority | verification | confidence | source_id | source_type | quote | date | course | assignment | notes | legacy_label |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E001 | 在本次高等数学课程中可能重视展示推导过程 | direct_feedback | supported | medium | S_001 | 课堂录音 | "公式推导不要直接贴图，我希望看到你们一步步自己打出来或者手写扫描。" | 2026-05-01 | 高等数学 | 期中作业 | 当前课程中的一次直接反馈，不等于跨课程稳定偏好 | - |
