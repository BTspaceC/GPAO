# `/审计` 工作流示例输出

> 本文件是人工编写的示范输出，用于展示 V3.2 的输出分层和证据规则。输入材料为虚构教学案例，不对应真实课程。

## 输入材料

- **[S1] 作业摘要节选**：“综上所述，不可否认的是，本次研究取得了极为显著的良好效果。在宏大的时代背景下，网络素养扮演了至关重要的角色……因此全国大学生普遍存在网络素养不足的问题。”
- **[S2] 评分标准**：要求数据支撑、结论可靠。
- **[S3] 方法章节节选**：调查对象为某省两所高校的在校本科生。
- **[S4] 附录 A**：调查问卷原文；正文中没有任何位置提到附录 A。
- **[S5] 用户声明**：这是一篇课程实证论文。
- 未提供任务书全文、格式要求和课程 AI 使用政策。

---

## 示例输出

### 结论速览

- **判断**：主要风险是结论范围超出样本，其次是摘要看不到具体结果【已证实】（S1、S3）。
- **P0**【已证实】把“全国大学生普遍存在”改为限定在调查对象范围内的表述（S1、S3）。
- **P1**【已证实】摘要用一两句写出实际调查了谁、主要发现是什么，替换空泛评价（S1、S2）。
- **P2**【已证实】在方法章节加一句指向附录 A 的引用（S4）。
- **无法判断**：硬性格式要求；AI 使用政策未确认，请核对课程规定。

### 0. 类型与适配器

- **类型**：实证论文；命中路由规则第 1 条（S5 用户明确声明）。
- **适配器**：`adapters/empirical_paper.md`
- **识别置信度**：high。任务书缺失只降低硬性合规检查的结论，不改变类型。

### 1. 30 秒可见性启发式检查

| 读者能否快速看到 | 结果 | 依据 |
| :--- | :---: | :--- |
| 研究对象和目标 | 否 | S1 摘要没有说明调查对象 |
| 主要结果 | 否 | S1 只有“极为显著的良好效果”这类评价，没有具体发现 |
| 附件索引 | 否 | S4 附录 A 未被正文引用 |

该检查只近似评估信息可见性，不代表真实教师一定如何阅卷。

### 2. 3 分钟结构启发式检查

结论和样本之间断链：S3 的样本是某省两所高校本科生，S1 的结论推广到“全国大学生”。

### 3. 硬性合规与事实复核

| 检查项 | 结果 | 依据 |
| :--- | :---: | :--- |
| 文件、格式、字数和提交要求 | 无法判断 | 未提供任务书 |
| 表格数值与正文一致 | 无法判断 | 未提供结果表格 |
| 引用可核实 | 无法判断 | 未提供参考文献 |
| 附件完整且命名清楚 | 部分通过 | S4 附录存在但未被引用 |
| 符合课程 AI 使用政策 | 无法判断 | 政策未提供 |

### 4. 方法正确性与结论边界

S1 的“全国大学生普遍存在”超出了 S3 样本能支持的范围。结论最多写到“在本次调查的两所高校本科生中……”。
authority: official（作业原文） / verification: verified / confidence: high。

### 5. Rubric 覆盖与证据链

S2 要求“数据支撑”，但 S1 摘要没有引用任何具体数据，评分项“数据支撑”在摘要中不可见。
authority: official / verification: supported / confidence: medium（只看到摘要节选，正文其他部分未提供）。

### 6. 具体性与作者表达

S1 中“极为显著的良好效果”“扮演了至关重要的角色”只有评价，没有说明具体发现。建议改写方向：`本次调查发现，[填入你的实际统计结果]。` 数值必须来自你自己的分析结果，这里不提供示例数字。

这是表达具体性的问题，不是对文本来源的判断。

### 7. 冲突检查

未发现课程要求、方法前提和偏好之间的冲突。

### 8. 总体风险

| 优先级 | 风险 | 来源 | 三维标签 | 最小动作 |
| :---: | :--- | :--- | :--- | :--- |
| P0 | 结论推广超出样本范围 | S1、S3 | official/verified/high | 把结论范围限定到调查对象 |
| P1 | 摘要缺少具体发现 | S1、S2 | official/supported/medium | 用实际结果替换评价性语句 |
| P2 | 附录 A 未被正文引用 | S4 | official/verified/high | 方法章节加一句“问卷见附录 A” |

### 状态补丁（供工具与后续工作流使用，可跳过）

```json
{
  "schema_version": "3.1",
  "case_id": "CASE_AUDIT_EXAMPLE",
  "workflow": "/审计",
  "base_state_available": false,
  "operations": [
    {"op": "append", "field": "sources", "value": {"source_id": "S1", "kind": "draft_excerpt"}, "reason": "用户提供摘要节选", "evidence_ids": ["S1"]},
    {"op": "append", "field": "sources", "value": {"source_id": "S2", "kind": "rubric"}, "reason": "用户提供评分标准", "evidence_ids": ["S2"]},
    {"op": "append", "field": "sources", "value": {"source_id": "S3", "kind": "draft_excerpt"}, "reason": "用户提供方法章节节选", "evidence_ids": ["S3"]},
    {"op": "append", "field": "sources", "value": {"source_id": "S4", "kind": "appendix"}, "reason": "用户提供附录 A", "evidence_ids": ["S4"]},
    {"op": "append", "field": "claims", "value": {"claim_id": "CLM_001", "text": "摘要结论推广到全国大学生，超出某省两所高校样本的支持范围", "source_ids": ["S1", "S3"], "authority": "official", "verification": "verified", "confidence": "high"}, "reason": "摘要结论与方法章节样本描述对照", "evidence_ids": ["S1", "S3"]},
    {"op": "append", "field": "findings", "value": {"finding_id": "F_001", "priority": "P0", "text": "结论范围超出样本"}, "reason": "见 CLM_001", "evidence_ids": ["S1", "S3"]},
    {"op": "append", "field": "findings", "value": {"finding_id": "F_002", "priority": "P2", "text": "附录 A 未被正文引用"}, "reason": "正文中没有指向附录 A 的引用", "evidence_ids": ["S4"]},
    {"op": "append", "field": "open_questions", "value": {"question_id": "Q_001", "text": "AI 使用政策未确认"}, "reason": "用户未提供课程 AI 使用政策", "evidence_ids": ["S1"]}
  ]
}
```
