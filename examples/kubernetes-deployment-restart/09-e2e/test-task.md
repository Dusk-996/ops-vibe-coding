# Restart 本地教学 E2E 计划

测试对象是同一目标 `lab / staging / checkout` 的 [静态原型](../01-prototype/index.html) 和 [React Mock](../02-react-mock/contract.md)。测试只使用随机端口的 127.0.0.1、本地内存服务、独立浏览器上下文和合成操作 ID。固定输入为 [Spec](../05-spec/deployment-restart.spec.md) 和 [Ticket 01](../06-tickets/ticket-01.md)、[Ticket 02](../06-tickets/ticket-02.md)。

| 路径 | 操作 | 可反证的预期 |
|---|---|---|
| 取消 | 打开确认框，核对集群、命名空间、Deployment，取消 | 首屏无结果，React 客户端未发 POST，模拟变更计数为 0 |
| 已接受且记账 | 选择“接受”，确认一次，查看操作记录 | 看到“请求已提交”，明确 rollout 尚未验证；关联 ID 与返回状态匹配；仅有一次模拟变更 |
| 结果未知 | 选择“超时”，确认一次，查看记录并刷新页面 | 操作 ID 保留、显示“结果待核验”，页面阻止重复提交；刷新只查记录，服务端计数仍为 1 |
| 明确拒绝／审计未确认 | 分别模拟明确拒绝、远端已接受但最终审计未确认 | 两种提示可区分，审计未确认不能显示普通成功 |

- 测试环境无需账号或凭证。使用 Node 单元测试和 Playwright 驱动本机 Chromium，各场景使用独立内存数据。对比桌面和窄屏的原型与 React，记录检查与截图。
- 测试停止条件：请求指向非回环地址、出现真实凭证或集群。失败保留记录并按环境、测试、实现分类。
- `auto_fix: false`、`cleanup_test_data: false`、`allow_destructive_flows: false`。测试过程不实施产品修复。退出测试进程自然释放内存样本。
- 2026-11-22，仓库维护者在本轮明确答复“批准本地 Mock 测试计划”。允许在 127.0.0.1 对上述目标、模拟条件和范围操作。执行结果及授权范围写入[测试报告](test-report.md)。产品真实身份、Kubernetes PATCH、数据库事务和生产恢复另行验证。
