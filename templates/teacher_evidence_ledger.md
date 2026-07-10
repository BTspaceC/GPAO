# 教师偏好证据账本 (Teacher Evidence Ledger)
`schema_version: 1`

- `evidence_id`: 证据编号
- `claim`: 偏好主张（例如：喜欢复杂的图表）
- `level`: 证据等级 (FACT/HIGH/MEDIUM/LOW/UNKNOWN)
- `source_id`: 原始材料索引或出处
- `source_type`: 证据来源类型（任务书/评语/课堂录音等）
- `quote`: 原文摘录（必须包含具体的话语或要求截图说明，不能只写总结）
- `date`: 收集日期
- `course`: 课程名称
- `assignment`: 对应作业
- `verification_status`: 验证状态 (UNVERIFIED / SUPPORTED / CONTRADICTED / INSUFFICIENT_DATA)
- `notes`: 备注

## 证据列表示例
| evidence_id | claim | level | source_id | source_type | quote | date | course | assignment | verification_status | notes |
|---|---|---|---|---|---|---|---|---|---|---|
| E001 | 喜欢手写公式 | HIGH | S_001 | 课堂录音 | "公式推导不要直接贴图，我希望看到你们一步步自己打出来或者手写扫描。" | 2026-05-01 | 高等数学 | 期中作业 | SUPPORTED | 无 |
