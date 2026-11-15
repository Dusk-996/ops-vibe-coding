# Stack Selection Draft

> DRAFT — 完成 Grill 后才能 Finalize。本教学草案不构成已批准架构。

输入：[Mock](../02-react-mock/contract.md)、[Parity](../03-parity/prototype-parity.md)。

## 能力与最小候选

- 单 Deployment 提交、确认、已提交/拒绝/未知反馈及记录查看。
- 浏览器不能持有集群凭证，候选为 React + FastAPI + Kubernetes client。
- 操作记录需持久化；UI 不决定数据库、队列或 Worker。
- 未知结果、防重和审计失败不能仅靠禁用按钮处理。

## 必须追问

部署与规模、认证及 Namespace 权限、集群凭证、调用超时、客户端隐含重试、持久意图及目标占用、审计失效窗口、同 ID 重放、原进程崩溃、核验/更正的授权路径、保留策略及残余可用性风险。

排除无依据的 Redis、MQ、Worker、微服务和自动重试。结果未知时是否允许强制重发、何时释放占用，必须确认，不能由 UI 推断。

下一步：[Grill Decisions](grill-decisions.md)。
