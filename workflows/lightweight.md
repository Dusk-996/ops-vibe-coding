# Lightweight Track

适合第一次体验、Demo 和低风险小工具。它减少文档深度和审查层级，但保留会改变架构与风险的人工决定。

## 从一个可验证的问题开始

“值班同事取消重启后，能否确定请求没有发出？”在 [Restart 教学案例](../examples/kubernetes-deployment-restart/README.md)中，可以仅选用本地 Mock 做小练习。S00 先看当前如何核对请求，比较一份命令说明和一个确认页面，由需求提出人选定目标。若选页面，S01 交一份可点击 HTML，S02 请同事体验取消、已提交和结果未知。若已有设计文档或风险摘要，可从原文接手。只需评估风险时可以在 S00 结束。

## 最小执行方式

一个文件可以承载相邻阶段的材料。每次交付时固定版本与本轮范围，用[共用复查指令](../docs/01-quick-start.md#artifact-review)评分。各编号链接到对应阶段的细则；只评实际交付。尚未到达的阶段留空，已到达却缺件的阶段登记缺件。

| 阶段 | 本地练习交什么、谁来决定 |
|---|---|
| [S00](../references/stage-rubrics.md#s00) / [S01](../references/stage-rubrics.md#s01) / [S02](../references/stage-rubrics.md#s02) | 一段目标或风险摘要、一份可点击 HTML 和一条针对该版的真实体验记录。请使用者选择方向并确认体验；待答复时保留待确认。 |
| [S03](../references/stage-rubrics.md#s03) / [S04](../references/stage-rubrics.md#s04) | 做可运行的 React Mock，执行 build 并走关键流程。用同一视口与数据记录两侧对照及偏差，交人决定能否接受。 |
| [S05](../references/stage-rubrics.md#s05) / [S06](../references/stage-rubrics.md#s06) / [S07](../references/stage-rubrics.md#s07) | 从 Mock 提取最小架构与开放问题，逐项找人核实会改变选型的约束，沿用同版草案整理定稿。未决问题保留在草案。 |
| [S08](../references/stage-rubrics.md#s08) / [S09](../references/stage-rubrics.md#s09) / [S10](../references/stage-rubrics.md#s10) | 一份 Minimal Spec 说明核心行为、接口/数据、授权、错误与验收；按纵向任务交实现、测试或可复现验证步骤，保存实际结果。 |
| [S11](../references/stage-rubrics.md#s11) / [S12](../references/stage-rubrics.md#s12) | 按实际审查范围，在切片记录中简记比较基点、与 Spec 的符合度、本地运行风险与缺口。未开展的独立审查如实标注，涉及真实基础设施时转完整流程。 |
| [S13](../references/stage-rubrics.md#s13) / [S14](../references/stage-rubrics.md#s14) | 约定本地测试范围，记录实际浏览器操作、预期、观察结果、跳过原因与证据。请业务使用者确认该版本能否解决最初问题。 |

各阶段生产 Skill 及其调用条件在[完整流程](full.md)。评分者只写复查报告，低分时由负责人决定修订、何时复评；测试结果和人工门禁分别保留。

## 什么时候升级到 Full Track

出现任一条件就使用 [Full Track](full.md)：

- 操作生产基础设施、执行远程命令或修改 Kubernetes 资源；
- 涉及 Secret、客户数据、多租户、审批或细粒度权限；
- 存在长任务、自动重试、重启恢复、高并发或多实例；
- 工具由团队长期维护，或者失败会造成明显业务影响；
- 需要正式发布、生产就绪声明或审计证据。

## 已有演练

[只读发布巡检](../docs/reviews/2026-11-22-s00-workflow.md)单独保存该例的 S00 选择、Grill 结束决定及 S05–S07 交接。它的输入、人员答复和验证结果只对应巡检练习。
