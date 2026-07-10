# 教师画像结构模板 (Teacher Profile)

`schema_version: 2.0`

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

| claim_id | claim | course_scope | evidence_ids | support_count | contradiction_count | confidence_level | verification_status | last_verified_at | cross_course_transfer | transfer_reason |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- | :---: | :--- |
| P_TCH_01 | 极度反感未被正文引用的附录 | 实验心理学 | F_FB_02, F_SC_04 | +3 | -0 | HIGH | 已验证 | 2026-07-10 | false | - |
| P_TCH_02 | 偏好结构方程模型(SEM) | 社会心理学 | F_FB_05 | +1 | -0 | MEDIUM | 待更多验证 | 2026-07-10 | false | - |
| P_TCH_03 | APA 7th 格式强制要求 | (全部课程) | F_REQ_01, F_FB_09 | +4 | -0 | FACT | 官方标准 | 2026-07-10 | true | 在多门课程的任务书中出现，属于底层学术规范 |

### 字段硬约束说明：
1. **evidence_ids**: 每项画像必须引用具体的证据 ID，禁止使用“根据之前交流”等模糊描述。
2. **support_count / contradiction_count**: 必须严格由 `evidence_ids` 中的证据条目推算，禁止模型凭印象填写。
3. **cross_course_transfer**: 默认必须设为 `false`。只有出现多门课程的重复证据后，才能标记为 `true` (候选可迁移)，且必须在 `transfer_reason` 说明理由，但这不能使其自动升级为 FACT。
