# `/复盘` 工作流示例输出

> 本文件是人工编写的示范输出，用于展示 V3.2 的输出分层和证据规则。输入材料为虚构教学案例，不对应真实课程。

## 输入材料

- **[S1] 成绩**：期末论文 80 分；没有逐项分数。
- **[S2] 老师评语原文**：“数据量尚可，但分析比较表面，未见到对核心变量的深层挖掘。”
- **[S3] 已提交作业概况**：实证论文，30 份问卷，正文使用频数图和均值对比；附录放了大量代码截图，正文没有引用附录。
- **[S4] 之前记录的假设**：“老师可能不看附件代码”（用户猜测）。

---

## 示例输出

### 结论速览

- **判断**：评语直接指出“分析比较表面”，与正文只展示频数图和均值对比的情况一致【已证实】（S2、S3）。扣分具体落在哪些评分项无法判断（S1 无逐项分数）。
- **P1**【已证实】下次在正文中展示围绕核心变量的分析，并说明为什么选这种分析（S2）。
- **P1**【已证实】正文中凡是依赖附录的工作，都加一句指向附录的引用（S3）。
- **待确认**：老师期望的“深层挖掘”具体指哪类分析，评语没有说明。

### 0. 类型与适配器

- **类型**：实证论文；命中路由规则第 3 条（S3 为问卷数据与统计分析，无其他主要交付物）。
- **适配器**：`adapters/empirical_paper.md`
- **识别置信度**：high

### 1. 总体判断

实际结果与现有证据一致：评语（S2）和提交稿（S3）都指向“分析深度在正文中不可见或不足”。无法区分这是分析本身不够，还是做过的分析没有写进正文。附录代码与此是否相关，老师没有提及。
authority: direct_feedback / verification: supported / confidence: medium。

### 2. Rubric 逐项分析

| 评分项 | 正式权重 | 正文可见证据 | 实际逐项得分 | 判断依据 | 证据状态 |
| :--- | :---: | :--- | :---: | :--- | :--- |
| 未提供 rubric | | 频数图、均值对比（S3） | 无法判断 | S1 只有总分 | official/evidence_insufficient/unknown |

没有逐项分数，不从 80 分反推任何分项得分。

### 3. 教师偏好验证

| 之前假设 | 本次是否支持 | authority | verification | confidence | transfer_state |
| :--- | :---: | :---: | :---: | :---: | :---: |
| 老师可能不看附件代码（S4） | 无法判断 | user_hypothesis | evidence_insufficient | low | false |
| 新增：评语指出“分析比较表面，未见到对核心变量的深层挖掘”（S2） | 支持 | direct_feedback | supported | high | false |

第二条按评语原有粒度记录，不收窄为“老师要求回归分析”之类的具体方法。如果要提出更具体的假设（例如“希望看到变量间的关系检验”），只能另列为待验证假设，`verification: evidence_insufficient`。这条偏好只来自一门课程的一次反馈，`transfer_state` 保持 `false`。

### 4. 下次改进策略

| 策略 | 类别 | 来源 | 预期影响 | 可见概率 | 时间成本 | 优先级 |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| 围绕核心变量做数据条件允许的分析，并在正文说明理由 | 建议修改 | S2 | 中 | 高 | 中 | P1 |
| 正文为附录内容建立引用 | 建议修改 | S3 | 中 | 高 | 低 | P1 |
| 在同一老师的下次作业中，确认“深层挖掘”的具体期望 | 需要更多证据 | S2 | 未知 | 未知 | 低 | P2 |

单次反馈不产生跨课程 P0。

### 5. 不确定性

- 没有逐项分数，扣分归因无法落到具体评分项。
- 老师是否查看附录代码无法确认。
- “深层挖掘”指哪类分析，评语未说明。

### 状态补丁（供工具与后续工作流使用，可跳过）

```json
{
  "schema_version": "3.1",
  "case_id": "CASE_POSTMORTEM_EXAMPLE",
  "workflow": "/复盘",
  "base_state_available": false,
  "operations": [
    {"op": "append", "field": "sources", "value": {"source_id": "S1", "kind": "grade"}, "reason": "用户提供成绩", "evidence_ids": ["S1"]},
    {"op": "append", "field": "sources", "value": {"source_id": "S2", "kind": "teacher_feedback"}, "reason": "用户提供评语原文", "evidence_ids": ["S2"]},
    {"op": "append", "field": "sources", "value": {"source_id": "S3", "kind": "submission_summary"}, "reason": "用户描述已提交作业", "evidence_ids": ["S3"]},
    {"op": "append", "field": "sources", "value": {"source_id": "S4", "kind": "prior_hypothesis"}, "reason": "用户提供旧假设", "evidence_ids": ["S4"]},
    {"op": "append", "field": "history", "value": {"event_id": "H_001", "text": "期末论文总分 80，无逐项分数"}, "reason": "记录实际成绩", "evidence_ids": ["S1"]},
    {"op": "append", "field": "claims", "value": {"claim_id": "P_TCH_001", "text": "评语指出分析比较表面，未见到对核心变量的深层挖掘", "source_ids": ["S2"], "authority": "direct_feedback", "verification": "supported", "confidence": "high", "transfer_state": "false"}, "reason": "按评语原有粒度登记", "evidence_ids": ["S2"]},
    {"op": "append", "field": "claims", "value": {"claim_id": "P_TCH_002", "text": "老师可能不看附件代码", "source_ids": ["S4"], "authority": "user_hypothesis", "verification": "evidence_insufficient", "confidence": "low", "transfer_state": "false"}, "reason": "本次反馈未涉及附件，无法验证", "evidence_ids": ["S4"]},
    {"op": "append", "field": "findings", "value": {"finding_id": "F_001", "text": "正文分析深度不足或不可见，与评语一致"}, "reason": "评语与提交稿对照", "evidence_ids": ["S2", "S3"]}
  ]
}
```
