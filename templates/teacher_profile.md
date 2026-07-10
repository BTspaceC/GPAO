# 教师画像结构模板 (Teacher Profile)

`schema_version: 3.0`

**用途声明**：本模板用于结构化记录教师在评分中表现出的偏好、习惯与红线要求。禁止将单次个例、学生猜测或无事实支撑的主观判断升级为中高可信度偏好。

## 画像合并与防止覆盖规则
- 当多次运行 `/画像` 时，必须比对 `claim_id`。如果同类主张已存在，则**必须更新旧记录的证据、支持/反驳次数与最后验证时间**，而不是直接覆盖丢失旧数据。
- 每次更新后必须自增或保持 `schema_version` 不降级。

## 画像元数据
- **教师姓名/代号**：[例：张老师 / TCH_001]
- **所属院系/学科**：[例：心理学系]
- **档案建立日期**：[YYYY-MM-DD]
- **最后更新日期**：[YYYY-MM-DD]

## 偏好注册表

| claim_id | claim | course_scope | evidence_ids | support_count | contradiction_count | authority | verification | confidence | last_verified_at | transfer_state | transfer_reason |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- | :---: | :--- |
| P_TCH_01 | 反馈中重视正文对附录的明确引用 | 实验心理学 | F_FB_02, F_SC_04 | +2 | -0 | direct_feedback | supported | high | 2026-07-10 | false | 当前只在一门课程中验证 |

### 字段硬约束说明：
1. **evidence_ids**: 每项画像必须引用具体的证据 ID，禁止使用“根据之前交流”等模糊描述。
2. **support_count / contradiction_count**: 必须严格由 `evidence_ids` 中的证据条目推算，禁止模型凭印象填写。
3. **transfer_state**: 默认 `false`。至少两个不同课程、两条直接证据、非同一模板重复、语义一致且无反驳时才能标记为 `candidate`；获得用户或人工明确确认后才可标记为 `confirmed`。
4. `confidence` 只表示系统对当前主张判断正确性的把握，不代表来源权威、重要性或迁移资格。
5. 任务书、评分表和学院模板中的正式要求属于课程约束，不得登记为教师个人偏好。
