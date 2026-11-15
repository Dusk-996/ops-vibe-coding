# Prototype Approval

> 教学批准记录，不是实际人员对产品的批准。

## Gate Record

- Gate：S02 Human Prototype Review
- Example Status：APPROVED（illustrative）
- 实际人工评审：NOT_PERFORMED
- 范围：Deployment Detail 的单目标 Restart 请求与审计查看；不承诺 rollout 完成。

## 产品意图

Deployment Detail → Restart → 显示目标的确认框 → Confirm → 提交中 → 请求已提交／明确拒绝／结果待核验 → 对应操作记录。
Cancel 不发送变更。未知结果提示“请求可能已执行，请勿重复提交，保存操作 ID 并联系核验人员”。

只对已授权 Namespace 内一个 Deployment 操作。页面按钮不是后端授权；“请求已提交”不是“服务恢复”。集群、Namespace、Deployment 必须在确认框可辨认。

## 排除与门禁

批量、定时、回滚、自动重试、rollout 自动跟踪均排除。后台持久化与防重由后续架构确认；这里不决定数据库或 Worker。
真实项目记录实际审核人、日期、原型版本、viewport、允许范围及下一步；未知约束不由 Agent 填为批准。

下一步：[React Mock Contract](../02-react-mock/contract.md)。
