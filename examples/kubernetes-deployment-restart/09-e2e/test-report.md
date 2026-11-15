# E2E Test Report

> **Real Execution Status: SKIPPED — no application or test environment。** 没有真实浏览器、集群、截图或 trace。
> Example Outcome: PASS 为教学占位，不是执行结果。

## 预期 Workflow

登录 → Deployment Detail → Restart → 核对目标/确认 → 提交中 → 请求已提交（不表示 rollout 完成）→ 同一操作 ID 的记录。

## 待验证场景

| 场景 | 预期行为 | 真实执行 |
|---|---|---|
| 有权用户确认 | Submitted 仅在 API 接受且最终审计确认时显示 | SKIPPED |
| 取消／未授权 | 不 mutation；拒绝记录不泄漏凭证 | SKIPPED |
| API 超时 | Unknown、保留占用、不重试，显示核验指引 | SKIPPED |
| 同 ID 重放／同目标新 ID | 返回已有记录或冲突，不再发送 PATCH | SKIPPED |
| 意图存储失败 | 不调用 Kubernetes，明确未发送及证据限制 | SKIPPED |
| API 接受后最终审计未确认 | 分开说明观测与持久化，不显示普通成功 | SKIPPED |
| 原进程崩溃／人工更正失败 | 不恢复发送、不盲目解锁 | SKIPPED |
| 查询／核验交接 | 授权范围、ID、证据、批准和维护事务可追溯 | SKIPPED |

真实项目的报告必须有批准 Test Plan、实际步骤/时间/对象版本/环境、原始输出、截图或 trace 及限制。上述表格不是证据。

任何真实 mutation、维护、故障注入都需明确目标、影响范围、恢复方案和授权。本例未执行这些操作。

下一步：[Human Acceptance](../10-acceptance/human-acceptance.md)。实际产品的完整流程仍未验证。
