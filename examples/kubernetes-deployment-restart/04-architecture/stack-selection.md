# Stack Selection Final

> FINAL — example。来自本例 [Draft](stack-selection.draft.md) 和 [Grill](grill-decisions.md)，不是实际系统已验证架构。

| 组件 | 职责 |
|---|---|
| React | 明确确认、提交反馈、Unknown 停手、记录查看 |
| FastAPI | 可信身份、后端范围授权、操作 ID 与目标绑定、单次提交 |
| Kubernetes client | 对允许目标发一次有超时的 PATCH；禁止隐含 mutation 重试 |
| 既有 PostgreSQL | 操作意图、持久占用、审计结果与核验更正 |
| 既有 SSO | 可信用户身份，不将 token 或集群凭证交前端 |

## 请求边界

认证和授权 → 检查重放/冲突 → 同一事务保存意图与目标占用 → 确认事务成功 → 一次 PATCH → 同一事务保存最终状态、审计及明确结果下的占用释放 → 返回分别标明远端观测和审计确认的结果。

若首次持久化未确认，不调用 Kubernetes。最终写入未确认时，数据库可能仍为 SUBMITTING，也可能已提交但响应丢失；不得谎称 UNKNOWN 已落库。保留占用并核验。只在最终结果与审计已确认时返回正常 Submitted/Rejected。

## 人工恢复

管理员只读取证；有权人员批准；有权维护者按 [Spec 恢复前提](../05-spec/deployment-restart.spec.md#人工核验与受控维护)事务化更正结果、补核验审计、释放占用。证据不足或维护事务未确认则继续阻断。此处不是可执行数据库操作功能。

## 限制

无 Redis、MQ、Worker、批量、定时、自动重试、强制解锁、自动 rollout 跟踪或记录清理。本例仅约束提交并发，不声称跨 PostgreSQL 与 Kubernetes 的 exactly-once。实际 HA、留存和上线另由风险责任人判断。
