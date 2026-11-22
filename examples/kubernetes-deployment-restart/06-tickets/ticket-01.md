# Ticket 01 — 提交一次已授权的 Restart 请求

> 本地已交付 R1/R2 与 R3 的提交端，见[实现与测试](../07-implementation/tdd-evidence.md)。目标固定为 `lab / staging / checkout`。生产身份、真实 PATCH 和数据库事务为待实现及验证项。

依赖已定义的目标/接口与状态契约。验收本地切片时核对取消的 POST 数量和 accepted/timeout 返回的操作 ID、状态与模拟提交计数。[浏览器原始记录](../09-e2e/evidence/run.json)

## 用户价值与输入

用户确认一个目标，获得“已提交／明确拒绝／待核验”的准确结果；输入为 [Spec](../05-spec/deployment-restart.spec.md)、[Architecture Final](../04-architecture/stack-selection.md)。本任务不承诺工作负载已恢复。

## 范围

后端身份和 Namespace 授权、确认框、操作 ID 绑定、持久意图/目标占用、单次 PATCH、最终审计、结果反馈与关联记录。数据库、API、UI 和对应测试共同交付，不拆成无法独立验收的横向层。

## 验收

- Cancel 不发起请求；身份/授权拒绝不调用 Kubernetes。
- 意图及占用确认成功才发送至多一次 PATCH；客户端隐含重试关闭。
- 同 ID 重放不重发，改绑拒绝；不同 ID 同活动/未知目标冲突。
- 明确接受且最终审计确认后显示 Submitted，仅表示提交；明确未变更才 Rejected。
- 超时为 Unknown；最终审计未确认分开说明远端观测，不臆造落库状态。
- 进程中断、数据库故障不导致自动重发/解锁；证据不足持续阻断。
- 错误和记录脱敏；允许目标/身份/请求与结果可关联。

## 验证及非目标

真实项目记录后端事务/并发/故障测试、前端交互、build 和真实 Workflow 证据，不能用替身测试证明实际 RBAC。示例形态见 [TDD](../07-implementation/tdd-evidence.md)。

不包含批量、定时、rollout 跟踪、生产部署或审计管理页面。人工核验与记录查看由 [Ticket 02](ticket-02.md) 衔接；它未完成前，完整恢复路径不能标已交付。
