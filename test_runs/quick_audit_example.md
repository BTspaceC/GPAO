# `/速审` 工作流示例输出

> 本文件是人工编写的示范输出，用于展示 V3.2 的输出分层和证据规则。输入材料为虚构教学案例，不对应真实课程。

## 输入材料

- **[S1] 任务书节选**：编程项目，提交源代码与 README；README 需说明运行方式；截止今晚 23:59。
- **[S2] `python tools/skim_view.py ./project` 输出摘要**：README 中没有安装/运行相关章节；测试文件数 0；没有依赖清单。
- **[S3] README 节选**：“系统支持 1000 名用户同时在线。”

---

## 示例输出

### 结论速览

- **判断**：可以提交，但 README 缺少任务书明确要求的运行说明，提交前必须补上【已证实】（S1、S2）。
- **P0**【已证实】README —— 缺少运行方式 —— 加一个“运行方式”小节，写明环境、安装命令和启动命令（S1、S2）。
- **P1**【待确认】README —— “支持 1000 名用户同时在线”没有测试证据 —— 删除或改为实际测过的情况（S3）。
- **P2**【已证实】项目根目录 —— 没有依赖清单 —— 导出一份依赖列表，方便老师复现（S2）。
- **AI 使用政策**：未确认，请核对课程规定。

### 三项检查结果

| 检查 | 结果 | 依据 |
| :--- | :---: | :--- |
| 可见性（30 秒视图） | 有风险 | S2：README 没有运行说明，没有测试 |
| 硬性要求 | 未通过 | S1 要求 README 说明运行方式 |
| 真实性高危项 | 发现 | S3 性能声明没有对应证据 |

类型：编程项目，命中路由规则第 2 条（S1 任务书明确写出）。

### 建议下一步

截止前只处理上面三项。之后如需检查代码质量和测试覆盖，再运行 `/审计`。

### 状态补丁（供工具与后续工作流使用，可跳过）

```json
{
  "schema_version": "3.1",
  "case_id": "CASE_QUICK_EXAMPLE",
  "workflow": "/速审",
  "base_state_available": false,
  "operations": [
    {"op": "append", "field": "sources", "value": {"source_id": "S1", "kind": "assignment_brief"}, "reason": "用户提供任务书节选", "evidence_ids": ["S1"]},
    {"op": "append", "field": "sources", "value": {"source_id": "S2", "kind": "skim_view_output"}, "reason": "skim_view 工具输出", "evidence_ids": ["S2"]},
    {"op": "append", "field": "sources", "value": {"source_id": "S3", "kind": "readme_excerpt"}, "reason": "用户提供 README 节选", "evidence_ids": ["S3"]},
    {"op": "append", "field": "findings", "value": {"finding_id": "F_001", "priority": "P0", "text": "README 缺少任务书要求的运行方式"}, "reason": "任务书要求与 skim_view 输出对照", "evidence_ids": ["S1", "S2"]},
    {"op": "append", "field": "findings", "value": {"finding_id": "F_002", "priority": "P1", "text": "README 中的并发性能声明没有测试证据"}, "reason": "未发现测试文件或性能测试结果", "evidence_ids": ["S2", "S3"]},
    {"op": "append", "field": "open_questions", "value": {"question_id": "Q_001", "text": "AI 使用政策未确认"}, "reason": "用户未提供课程 AI 使用政策", "evidence_ids": ["S1"]}
  ]
}
```
