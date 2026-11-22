# Kubernetes Deployment Restart Golden Path

> Full Track documentation example. It shows how artifacts pass confirmed facts
> and constraints between stages. It is not a running Kubernetes platform or
> production test evidence.

## Problem

内部 Kubernetes Operations Platform 的用户需要安全地 Restart 一个
Deployment，并确认请求提交结果和审计记录，而不是依赖人工执行 `kubectl`。

## Why Full Track

Restart 会修改 Kubernetes 资源，并涉及授权、确认、凭证范围和审计，因此本案例
按照 [Full Track](../../workflows/full.md) 展示，不属于 Lightweight Track。

## S00 从想法到原型目标

值班同事希望从 Deployment 详情页发起一次重启，并能回答“请求提交了吗，去哪里核对记录”。候选方向有提供一份命令操作指引，或做一个带目标确认和结果反馈的页面。这里演示后一种取舍，重点验证目标能否核对，以及使用者能否区分请求已提交和 rollout 已完成。范围只含单个目标的模拟流程；批量、自动重试和真实操作均在范围外。

下一步由实际使用者选择场景。未收到决定时保存为待确认；若本次仅为评估，可带着“未知结果可能导致重复提交”的风险在这里结束。本案例后续展示假设选定页面后的教学产物。

## Artifact Chain

| 阶段 | Artifact | 提供给下一阶段的内容 |
|---|---|---|
| S00 意图 | [本页的原型目标](#s00-从想法到原型目标) | 将目标用户、成功标准和单目标范围交给 S01 |
| S01–S02 Prototype / Review | [approval.md](01-prototype/approval.md) | 已批准的 Workflow、范围和非目标 |
| S03 React + Mock | [contract.md](02-react-mock/contract.md) | 可执行页面、交互、状态和 Mock API 契约 |
| S04 Parity | [prototype-parity.md](03-parity/prototype-parity.md) | React Mock 是否保留已批准产品意图 |
| S05 Architecture Draft | [stack-selection.draft.md](04-architecture/stack-selection.draft.md) | UI 暴露的能力候选、未知约束和最小候选架构 |
| S06 Grill | [grill-decisions.md](04-architecture/grill-decisions.md) | 由人确认的部署、安全和可靠性约束 |
| S07 Architecture Final | [stack-selection.md](04-architecture/stack-selection.md) | 由产品能力与运行约束共同支持的最小架构 |
| S08 Spec | [deployment-restart.spec.md](05-spec/deployment-restart.spec.md) | 可测试的行为、授权、API、审计和失败契约 |
| S09 Tickets | [ticket-01.md](06-tickets/ticket-01.md)、[ticket-02.md](06-tickets/ticket-02.md) | 按用户价值拆分的纵向实现边界 |
| S10 TDD | [tdd-evidence.md](07-implementation/tdd-evidence.md) | RED、GREEN、REFACTOR、VERIFY 应留下的证据形态 |
| S11–S12 Review | [code-review.md](08-review/code-review.md)、[ops-readiness.md](08-review/ops-readiness.md) | 实现符合性和可接受的运行风险 |
| S13 E2E | [test-report.md](09-e2e/test-report.md) | 完整用户 Workflow 的示例测试记录 |
| S14 Human Acceptance | [human-acceptance.md](10-acceptance/human-acceptance.md) | 人工最终判断应消费的输入和记录格式 |

完整产物定义以 [Artifact Map](../../references/artifacts.md) 为准。本目录只展示一条
Artifact → Artifact 的具体链路，不重新定义 Workflow 或 Gate 状态。

## Evidence Boundary

本目录中的 `PASS`、`APPROVED`、命令和测试结果都是教学用 illustrative records，
不是对真实系统执行后的证据。真实项目必须替换示例版本、环境、命令输出、截图或日志，
并由有权限的人完成风险接受和最终验收。

## 本例的结果与恢复边界

Submitted 仅表示请求已被接受且最终审计持久化，不表示 rollout 完成。Unknown 可能已产生变更，禁止重复提交；意图和占用先持久化，未知/最终审计未确认时持续阻断。核验由现有管理员只读取证，再由有权人员批准、有权维护者事务补记与释放。详细状态和失败判据以 [Spec](05-spec/deployment-restart.spec.md) 为准。

本例不提供应用、可执行SQL、自动核验、强制解锁、记录清理或 exactly-once 保证。文档走查、Skill阶段练习、真实实现测试和生产恢复验证分别记录；仅练习部分阶段不能勾选整条Full Track。新人先读 [Quick Start](../../docs/01-quick-start.md)，卡住查 [流程定位](../../docs/09-troubleshooting.md)。
