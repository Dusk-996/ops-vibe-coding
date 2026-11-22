# Artifact Map

每行给出交付内容和一个可打开的教学入口。点击阶段号查看输入、生产 Skill 与人工职责；点最后一列的细则，结合[共用判据](stage-rubrics.md#共用计分方法)复查本次交付的实际版本。示例里的待审材料按原状态交接。

| 阶段 | 最小产物 | Restart 实物 | 接手动作 | 复查 |
|---|---|---|---|---|
| <a id="s00"></a>[S00 澄清问题](../workflows/full.md#s00) | 按实际出口交原型目标简报、设计/提案或 Grill 风险摘要，使用现有文档和决定来源。 | [原型目标简报](../examples/kubernetes-deployment-restart/README.md#s00-从想法到原型目标) | 人选定目标交 S01，风险评估可结束，正式实施设计获批后交 `writing-plans`。 | [细则](stage-rubrics.md#s00) |
| <a id="s01"></a>[S01 制作原型](../workflows/full.md#s01) | 可打开的 HTML、可操作的关键流程和样本。 | [可点击 HTML](../examples/kubernetes-deployment-restart/01-prototype/index.html) | S02 体验入口、状态、结果与视口。 | [细则](stage-rubrics.md#s01) |
| <a id="s02"></a>[S02 确认原型](../workflows/full.md#s02) | 指向原型版本的体验、批准范围和决定来源，尚未确认时保留待审。 | [体验与决定记录](../examples/kubernetes-deployment-restart/01-prototype/approval.md) | 实际批准的页面、流程和视口作为 S03 转换依据。 | [细则](stage-rubrics.md#s02) |
| <a id="s03"></a>[S03 React + Mock](../workflows/full.md#s03) | 可构建的 React 界面、Mock 接口、样本、启动和验证记录。 | [运行说明与契约](../examples/kubernetes-deployment-restart/02-react-mock/contract.md) · [运行入口](../examples/kubernetes-deployment-restart/02-react-mock/package.json) | S04 据同版样本比较两端，S05 从运行界面提取能力。 | [细则](stage-rubrics.md#s03) |
| <a id="s04"></a>[S04 原型一致性](../workflows/full.md#s04) | 对应版本、视口、样本的两侧证据、偏差、影响及结论。 | [对照报告](../examples/kubernetes-deployment-restart/03-parity/prototype-parity.md) | 审核人确认可接受偏差，超出范围回 S03。 | [细则](stage-rubrics.md#s04) |
| <a id="s05"></a>[S05 架构草案](../workflows/full.md#s05) | 关联 Mock 的候选组件、依据和开放问题。 | [架构草案](../examples/kubernetes-deployment-restart/04-architecture/stack-selection.draft.md) | S06 按问题核对会改变架构的约束。 | [细则](stage-rubrics.md#s05) |
| <a id="s06"></a>[S06 运行约束](../workflows/full.md#s06) | 逐项对应草案问题的决定、来源、责任人和影响。 | [决定记录](../examples/kubernetes-deployment-restart/04-architecture/grill-decisions.md) | S07 把每条关键答复映射到选型。 | [细则](stage-rubrics.md#s06) |
| <a id="s07"></a>[S07 架构定稿](../workflows/full.md#s07) | 引用同版草案、S06 答复、定稿条件与遗留限制。 | [架构定稿示范](../examples/kubernetes-deployment-restart/04-architecture/stack-selection.md) | 确认后将组件、部署与运行边界交 S08。 | [细则](stage-rubrics.md#s07) |
| <a id="s08"></a>[S08 行为规格](../workflows/full.md#s08) | 可测试的行为、输入输出、失败与授权契约、范围确认记录。 | [Restart Spec](../examples/kubernetes-deployment-restart/05-spec/deployment-restart.spec.md) | S09 从已确认的条款提取可验收切片。 | [细则](stage-rubrics.md#s08) |
| <a id="s09"></a>[S09 纵向任务](../workflows/full.md#s09) | 关联 Spec 的任务、依赖、非目标和独立验收步骤。 | [Ticket 1](../examples/kubernetes-deployment-restart/06-tickets/ticket-01.md) · [Ticket 2](../examples/kubernetes-deployment-restart/06-tickets/ticket-02.md) | S10 一次消费一个就绪 Ticket。 | [细则](stage-rubrics.md#s09) |
| <a id="s10"></a>[S10 实现与测试](../workflows/full.md#s10) | 实现、测试、修订或内容标识、实际 RED/GREEN 与最终复验结果。 | [本地实现](../examples/kubernetes-deployment-restart/02-react-mock/mock.mjs) · [单元测试](../examples/kubernetes-deployment-restart/02-react-mock/mock.test.mjs) · [运行记录](../examples/kubernetes-deployment-restart/07-implementation/tdd-evidence.md) | S11 核验同版实现、规格与测试。 | [细则](stage-rubrics.md#s10) |
| <a id="s11"></a>[S11 代码审查](../workflows/full.md#s11) | 含固定基点、候选版本、规范和 Spec 两轴发现的报告。 | [代码审查](../examples/kubernetes-deployment-restart/08-review/code-review.md) | 修复阻断后重审，指定范围交 S12。 | [细则](stage-rubrics.md#s11) |
| <a id="s12"></a>[S12 运维就绪](../workflows/full.md#s12) | 适用风险、控制证据、未验证项及处置责任人。 | [就绪报告](../examples/kubernetes-deployment-restart/08-review/ops-readiness.md) | 风险接受由有权人员决定，按范围与证据处理后续验证。 | [细则](stage-rubrics.md#s12) |
| <a id="s13"></a>[S13 端到端验证](../workflows/full.md#s13) | 计划、获批范围、每条实际步骤、可定位证据及测试结果。 | [测试计划](../examples/kubernetes-deployment-restart/09-e2e/test-task.md) · [报告与浏览器证据](../examples/kubernetes-deployment-restart/09-e2e/test-report.md) | S14 依据实际环境、结果和缺口作判断。 | [细则](stage-rubrics.md#s13) |
| <a id="s14"></a>[S14 人工验收](../workflows/full.md#s14) | 原始目标、版本、证据、遗留风险与接受范围；实际决定或待审人。 | [人工验收记录](../examples/kubernetes-deployment-restart/10-acceptance/human-acceptance.md) | 记录接受、补充、退回或待定原因，生产发布另行交接。 | [细则](stage-rubrics.md#s14) |

## 生产发布交接

业务验收不自动授权上线。实际项目的发布记录至少指向：版本化产物、目标环境及范围、有效批准人、适用的部署/升级/回退验证、监控告警与维护责任，以及数据恢复依据。缺少适用关键证据时不得由 S14 推出生产放行；详见 [Ops Readiness](../docs/06-ops-readiness.md#生产发布交接)。

## 进行中与跨会话

使用 [交接模板](../harness/examples/handoff.example.md)记录当前 S 阶段、原始门禁状态、输入与产物路径、证据、阻断、下一步及审核角色。新会话先读此记录，再核对路径和修订；不要凭聊天记忆补写“已完成”。

## 练习材料

[Restart 示例](../examples/kubernetes-deployment-restart/README.md)贯穿各阶段。本地验证、教学假设和真人确认分别以对应记录为准。此前的[只读发布巡检演练](../docs/reviews/2026-11-22-s00-workflow.md)和[原版复用验证](../docs/reviews/2026-11-15-reuse-validation.md)保留其输入、日期和当时的证据。
