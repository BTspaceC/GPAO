# Case State Patch 3.1

每条工作流在回答末尾输出一个 JSON 代码块。不要重写完整 Case State；只声明本次实际变化。

```json
{
  "schema_version": "3.1",
  "case_id": "CASE_001",
  "workflow": "/诊断",
  "base_state_available": false,
  "operations": [
    {
      "op": "append",
      "field": "sources",
      "value": {"source_id": "SRC_001", "kind": "provided_material"},
      "reason": "用户在当前请求中提供",
      "evidence_ids": ["SRC_001"]
    },
    {
      "op": "append",
      "field": "findings",
      "value": {"finding_id": "F_001", "text": "缺少评分标准"},
      "reason": "输入未包含正式 rubric",
      "evidence_ids": ["SRC_001"]
    }
  ]
}
```

## 操作

- `append`：向列表字段追加一个真实存在的新项目。需要 `value`。
- `set`：只设置 `stage/scope`。需要 `value`。授权状态只能通过独立授权状态机转换，State Patch 无权改变。
- `update_item`：更新已有列表项目。必须有真实的基础状态，并提供 `item_id/before/updates`。

所有操作都必须给出非空 `reason/evidence_ids`。没有基础状态时：

- 只能追加新事实，或初始化 `stage/scope`；
- 禁止 `update_item`；
- 禁止虚构 `before` 值或声称旧状态已经改变；
- 没有需要更新的字段时输出空 `operations`，不得制造伪更新。

所有 `evidence_ids` 必须已经存在于基础状态的 `sources`，或由同一补丁先以 `append sources` 登记；不存在的 ID 会被验证器拒绝。

模块化模式可运行：

```text
python tools/case_state.py validate-patch patch.json
```

Bundle 模式不能运行本地工具，仍必须严格输出同一 JSON 结构。
