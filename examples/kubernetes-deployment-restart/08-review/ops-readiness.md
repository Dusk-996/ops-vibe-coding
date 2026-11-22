# S12 运维就绪报告 · Deployment Restart

**生产门禁：FAIL。** 真实 RBAC、审计持久化和进程重启后的恢复是 Restart 的关键控制，当前只提交了设计和本机模拟，三项均缺目标环境证据。业务风险尚无人签收。

审查对象为 [React + 本机内存服务](../02-react-mock/contract.md)、[行为与失败契约](../05-spec/deployment-restart.spec.md)、[S11 比较范围](code-review.md) 及 [S13 批准计划与实际结果](../09-e2e/test-report.md)。单用户操作一个目标 `lab / staging / checkout`。当前运行在回环地址，没有真实集群客户端。生产设计另有 SSO、后端、Kubernetes 与 PostgreSQL 的信任边界。[架构定稿样本](../04-architecture/stack-selection.md)

| 风险领域 | 依据和结论 | 责任角色与下一步 |
|---|---|---|
| 危险操作与 API 可靠性 | 本地 ASSESSED。确认/取消、请求次数、超时后的阻重、明确拒绝和审计未确认，可查 [浏览器事件](../09-e2e/evidence/run.json) 与[单元测试](../02-react-mock/mock.test.mjs)。真实 PATCH、跨进程占用和网络重试为 NOT_VERIFIED。 | API 维护者在获准等价环境验证每次意图至多发起一次变更，保留请求/审计关联。 |
| 认证授权、Kubernetes 及凭证 | **B1 / BLOCKER，NOT_VERIFIED**。当前仅检查固定目标和本地输入。真实身份、服务端资源授权、凭证隔离/轮换、最小 RBAC 和越界读取拒绝尚无证据。[本地服务](../02-react-mock/server.mjs) | 身份和集群维护者提供受控配置与获准的授权/拒绝回执。 |
| 审计与数据生命周期 | **B2 / BLOCKER，NOT_VERIFIED**。Mock 可按操作 ID 查记录；状态保存在进程内。生产意图与占用的原子性、审计留存、备份、同目标并发及最终写入的故障行为都需持久层验证。[模拟存储](../02-react-mock/mock.mjs) | 服务和数据维护者提交事务、并发及审计追溯证据。 |
| 故障与恢复 | **B3 / BLOCKER，NOT_VERIFIED**。浏览器刷新仅证明客户端可再次查询。本例未执行进程重启后的接管或数据库恢复事务。[受控维护契约](../05-spec/deployment-restart.spec.md#人工核验与受控维护) | 平台和数据维护者在获准环境演练中止、取证、审批、事务补记与失败仍阻断。 |
| 可观测性与部署 | 本地事件能区分 POST 与 GET；生产监控告警、部署配置、资源限额、发布及回滚尚待核对。 | 服务维护者、变更负责人提交部署和回滚验证；待 B1–B3 关闭后复核。 |
| 远程执行与异步任务 | NOT_APPLICABLE。本地应用没有 Shell/SSH 执行入口、批量队列、调度任务或 Worker。 | 增加这些能力时重新定范围。 |

**风险接受：无。** 当前材料可用于复现教学交互，S13 的本地测试授权有效。只有取得适用的生产证据、责任人决定及正式变更授权后，才进入实际发布流程。[S14 待确认事项](../10-acceptance/human-acceptance.md)
