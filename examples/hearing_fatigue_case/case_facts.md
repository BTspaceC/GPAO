# 听觉疲劳案例：事实库 (Single Source of Truth)

本文件是该案例的**唯一事实源**。所有的案例衍生分析与陈述，必须直接引用对应的 `ID`。

## 数据与事实记录 (Data Facts)

| ID | 声明内容 (Claim) | 验证状态 (Verification) | 结果占位 (Result Status) | 来源与备注 |
| :--- | :--- | :---: | :---: | :--- |
| F_DATA_01 | 问卷实际回收数量 35 份。 | SUPPORTED | - | 原始问卷平台导出记录 |
| F_DATA_02A| 最终有效数据比回收数据少 3 份。 | SUPPORTED | - | 比较回收与有效数 |
| F_DATA_02B| 这 3 份废卷是因为“全部选 C”被剔除的。 | SUPPORTED | - | 参考学生输入描述 |
| F_DATA_03 | 最终有效问卷 32 份。 | SUPPORTED | - | Excel 汇总表行数 |
| F_DATA_04 | 皮尔逊相关系数 r, p 值。 | UNVERIFIED | PLACEHOLDER | 尚未实际在 SPSS 运行，结果不得虚构 |
| F_DATA_05 | 佩戴超2小时疲劳感激增。 | INSUFFICIENT_DATA| PLACEHOLDER | 数据尚未支持此明确阈值 |
| F_DOC_01 | 问卷设计与数据质量占比 25%。 | SUPPORTED | - | 任务书评分标准 |
| F_DOC_02 | 统计分析深度占比 35%。 | SUPPORTED | - | 任务书评分标准 |
| F_DOC_03 | 报告结构与图表规范占比 25%。 | SUPPORTED | - | 任务书评分标准 |
| F_DOC_04 | 结论建议占比 15%。 | SUPPORTED | - | 任务书评分标准 |
| F_SCORE_01| 最终作业得分为 80 分。 | SUPPORTED | - | 成绩发布结果 |
| F_FEEDBACK_01| 老师评价：“问卷设计基本合理，但数据分析仅停留在表面。没有深入挖掘变量之间的相关关系。附录截图过于冗长且无意义。” | SUPPORTED | - | 老师评语 |

## 教师偏好记录 (Teacher Preferences)

| ID | 偏好内容 (Preference) | 证据等级 (Level) | 验证状态 (Verification) | 来源与备注 |
| :--- | :--- | :---: | :---: | :--- |
| P_TCH_01 | 强调图表规范性和正文引用。 | HIGH | SUPPORTED | 课堂多次公开强调 |
| P_TCH_02 | 厌恶无意义凑字数的附录。 | HIGH | SUPPORTED | 往届低分案例评语 |

## 规范与推断原则
1. **强制引用**: 任何诊断、矩阵等衍生文档在陈述客观情况时，必须带上出处（如 `(参考 ID: F_DATA_01)`）。
2. **禁止过度推断**: 将 `UNVERIFIED` 或 `INSUFFICIENT_DATA` 伪装成事实是严重违规。
3. **主观推断标记**: 文档中自行衍生的主观判断，必须明确标记为 `[INFERENCE]`。
