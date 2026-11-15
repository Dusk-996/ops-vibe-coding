# React Mock Contract

> 教学契约；仓库没有 React 应用，未执行 build 或浏览器验证。

## 输入与交互

输入：[Prototype Approval](../01-prototype/approval.md)。页面为 Deployment Detail。
Restart 打开目标确认框，Cancel 返回 Idle，Confirm 才发一个 Mock 请求。显示的身份/权限不是实际后端权限证据。

| UI 状态 | 用户应看到什么 |
|---|---|
| Idle／Confirmation | 核对目标，允许取消 |
| Running | 提交中，不重复发送同一操作 |
| Submitted | 重启请求已提交；未验证 rollout 完成，可查看操作记录 |
| Rejected | 本次确定未形成变更，显示脱敏类别 |
| Unknown | 可能已执行，禁止重复提交，保存操作 ID，联系核验人员 |
| 审计未确认 | 分开显示远端观测与记录未确认；不显示普通成功 |

Mock API：`POST /api/deployments/{namespace}/{name}/restart`；`GET /api/audit?operation_id={id}`，仍按授权资源范围筛选。

## 输出与限制

本契约为 [Parity](../03-parity/prototype-parity.md) 提供页面、状态和流程。UI Running 不等于数据库的持久 SUBMITTING；持久状态、占用和恢复由 [Spec](../05-spec/deployment-restart.spec.md)定义。刷新仅查询记录，不授权自动重新执行。
