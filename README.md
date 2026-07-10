# GPAO: 教师偏好导向型课程大作业优化器

## 这是什么

一套帮助大学生在课程大作业中**将高价值工作展示在老师最容易看到的位置**的工作流系统。

它不是论文生成器，不是AI代写工具，也不是检测对抗方案。它解决的核心问题是：你做了很多，但老师快速阅卷时没有看到。

## 适用范围

- 课程论文、问卷调查报告
- 数据分析报告
- 编程/系统设计项目
- 实验报告
- 案例分析
- PPT答辩与课程展示

## 目录结构

```
SKILL.md              → Agent执行规则（系统提示词）
README.md             → 本文件（用户说明）
CHANGELOG.md          → 版本变更记录

workflows/            → 各指令的工作流定义与输入输出契约
templates/            → 可填写的标准化模板
checklists/           → 分级审查清单
adapters/             → 不同作业类型的适配器
profiles/             → 独立的老师画像存储
examples/             → 实战案例
tools/                → 本地辅助脚本
tests/                → 验收测试用例
```

## 功能状态

| 模块 | 名称 | 状态 |
| :--- | :--- | :---: |
| workflows | plan_assignment (/规划) | stable |
| workflows | simulate_grading (/审计) | stable |
| workflows | postmortem (/复盘) | stable |
| workflows | diagnose (/诊断) | planned |
| workflows | profile_teacher (/画像) | planned |
| workflows | revise_assignment (/修改) | planned |
| adapters | empirical_paper | planned |
| adapters | programming_project | planned |
| adapters | experiment_report | planned |
| adapters | data_analysis | planned |
| adapters | case_study | planned |
| adapters | presentation | planned |
| tools | student_voice_auditor.py | planned |

## 使用方法

1. 将 `SKILL.md` 提供给 AI 助手作为系统规则
2. 填写 `templates/assignment_intake.md` 提交任务信息
3. 使用指令启动工作流：`/规划`、`/审计`、`/复盘`
4. 提交前依次通过 `checklists/` 中的三级审查

## 局限性

- 不能消除老师的主观评分因素
- 不能承诺特定分数或确保高分
- 不能鉴定文本是否由AI生成
- 老师偏好推断依赖证据质量，证据不足时存在不确定性
- 不同学校和课程的格式要求差异较大，需要使用者根据实际情况调整
