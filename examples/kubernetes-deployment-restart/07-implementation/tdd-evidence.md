# TDD Evidence

> **Actual Status: NOT_EXECUTED。** 仓库无应用，以下为预期测试名称/证据类别，不是真实命令输出。

输入：[Ticket 01](../06-tickets/ticket-01.md)、[Ticket 02](../06-tickets/ticket-02.md)。

## RED → GREEN → REFACTOR

真实项目先保存为缺失行为而失败的测试输出，再最小实现，最后在不改变约束下重构。每轮绑定代码提交/未提交差异、环境、时间、实际命令、退出码与原始结果。不能把依赖错误当成业务 RED。

待实现用例包括：

- 未授权和取消不调用 Kubernetes；意图持久化先于 PATCH。
- 各层 mutation 至多发送一次；超时 Unknown 且不重试。
- 同 ID 重放/改绑、同目标不同 ID 并发与跨进程占用。
- 明确接受＋最终审计确认只表示 Submitted，不表示 rollout 完成。
- 意图事务未确认不发送；最终写入未确认保留占用及准确远端观测。
- 持久意图后崩溃不恢复发送；人工更正需证据/批准/版本条件，事务失败不解锁。
- 记录读取范围、脱敏、空/加载/查询失败和新会话核验交接。

## VERIFY

后端事务/并发/集成测试、前端交互、build/lint、真实 Workflow 与适用环境的权限/故障/维护验证分别留证。替身可以计数和注入失败，不证明真实 Kubernetes RBAC 或人工恢复路径有效。

实际结果仍为 NOT_EXECUTED。后续 [Review](../08-review/code-review.md) 或教学 PASS 不能将其升级为已执行。
