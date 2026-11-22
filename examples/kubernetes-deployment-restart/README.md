# Kubernetes Deployment Restart Golden Path

从一个值班问题追到一次可复现的浏览器运行。固定目标是集群 `lab`、命名空间 `staging`、Deployment `checkout`。先在本机打开 [HTML 原型](01-prototype/index.html)，或按 [React Mock 启动说明](02-react-mock/contract.md) 运行。操作记录和服务端变更计数均来自本地内存。

## S00 从想法到原型目标

**使用者与痛点。** 本教学设定中，值班人靠命令发起一次 Restart，再人工查结果。请求超时后无法从页面判断操作是否可能已执行，再试一次可能重复提交。这是练习前提，尚待实际使用者在 S02 核对。

**候选方向。** 操作手册成本较低，可以解释如何查证；单目标页面还可以在动作发生前核对目标，在响应不确定时保留操作 ID。此次教学选择页面，批量、自动重试和跟踪 rollout 均不在本轮范围。

**可观察的成功标准。** 使用同一目标逐一切换样本。取消后请求计数为零；服务接受并确认已记账后，看到“请求已提交”；模拟超时时能读到原操作 ID、刷新查回记录，同时不能再次发起重启。有了这三个可反证的预期，S01 可以直接做确认框和结果面板。若只需评估风险，到记录“单次超时后盲目重发可能造成两次变更”即可结束。实际业务方是否选择或批准这个页面，见 [S02 决定记录](01-prototype/approval.md)。

## Artifact Chain

| 阶段 | 可以打开的产物 | 接手时核对什么 |
|---|---|---|
| S00 | [本页原型简报](#s00-从想法到原型目标) | 使用者、取舍和三条可观察结果 |
| S01 | [可点击 HTML](01-prototype/index.html) | 在桌面或窄屏体验目标确认与状态样本 |
| S02 | [原型决定记录](01-prototype/approval.md) | 哪个版本等待使用者决定 |
| S03 | [React 页面](02-react-mock/app.jsx)、[模拟接口与启动方式](02-react-mock/contract.md) | 通过本机服务复现流程 |
| S04 | [原型一致性报告](03-parity/prototype-parity.md) | 同一视口、场景和实现下的对照依据 |
| S05 | [架构草案](04-architecture/stack-selection.draft.md) | 从 Mock 识别能力，列出待回答的问题 |
| S06 | [约束决定记录](04-architecture/grill-decisions.md) | 区分教学选择和需要项目责任人确认的约束 |
| S07 | [架构定稿样本](04-architecture/stack-selection.md) | 草案和约束如何落实到目标架构 |
| S08 | [行为 Spec](05-spec/deployment-restart.spec.md) | 取消、提交、未知与审计边界 |
| S09 | [提交 Ticket](06-tickets/ticket-01.md)、[查看记录 Ticket](06-tickets/ticket-02.md) | 单项可验收行为与依赖 |
| S10 | [可计数的实现](02-react-mock/mock.mjs)、[单元测试](02-react-mock/mock.test.mjs)、[运行证据](07-implementation/tdd-evidence.md) | 同目标占用、操作 ID 和已执行的复验 |
| S11 | [两轴代码审查](08-review/code-review.md) | 比较基点、规范与 Spec 发现 |
| S12 | [运维就绪报告](08-review/ops-readiness.md) | 本地可验证项和生产证据缺口 |
| S13 | [获批计划](09-e2e/test-task.md)、[逐项报告](09-e2e/test-report.md)、[浏览器原始记录](09-e2e/evidence/run.json) | 用例、事件、截图与剩余限制 |
| S14 | [业务验收记录](10-acceptance/human-acceptance.md) | 业务使用者和风险负责人尚需决定的事项 |

## Evidence Boundary

读者可从 [阶段细则](../../references/stage-rubrics.md) 评价任一已交付产物，在[验收清单](../../docs/reviews/2026-11-22-stage-artifacts.md)查它的证据状态。S13 的本地测试范围已由仓库维护者批准。S02 的原型批准、S14 的业务接受分别留给相应角色。

React、内存 Mock 和浏览器测试实际运行；FastAPI、SSO、PostgreSQL 和 Kubernetes 是目标系统的设计。发布前须在授权环境验证真实 RBAC、持久化审计、故障恢复与审批。只读发布巡检另有[历史演练](../../docs/reviews/2026-11-22-s00-workflow.md)，其数据和结论不计入 Restart。
