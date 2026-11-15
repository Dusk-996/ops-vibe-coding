# Artifact Map

| 阶段 | 最小产物 | 下一阶段如何消费 |
|---|---|---|
| S01 Explore | `prototype/*.html` | 人工体验页面与流程 |
| S02 Prototype Review | `prototype/approval.md` | 固定页面、Flow、viewport 和模式 |
| S03 React + Mock | 可运行前端、Mock API/Data | Parity 检查并暴露能力候选 |
| S04 Parity | `docs/reviews/*-prototype-parity.md` | 决定是否进入架构阶段 |
| S05 Architecture Draft | `docs/plans/*-stack-selection.draft.md` | Grill 逐项确认开放约束 |
| S06 Grill | 决策记录或 ADR | Final 映射每项约束及确认人 |
| S07 Architecture Final | `docs/plans/*-stack-selection.md` | Spec 固定组件和部署边界 |
| S08 SDD / Spec | 已确认 Spec 及确认记录 | Tickets 提取纵向验收切片 |
| S09 Tickets | 本地 Markdown 或已获授权的 Issue | 每个新会话只消费一个 Ticket |
| S10 TDD | 代码、测试、原始验证结果 | Review 检查实现与契约 |
| S11 Code Review | 固定比较点、候选修订及两轴报告 | 修复阻断问题或进入 Ops Review |
| S12 Ops Review | `docs/reviews/*-ops-readiness.md` | 决定是否具备指定范围的运行验收基础 |
| S13 E2E | 获批 Test Plan、执行证据与报告 | 人执行最终业务和风险判断 |
| S14 Human Acceptance | 人工接受、补充或退回记录 | 记录业务结果；生产发布另外交接 |

产物传递已确认事实和证据。小项目可合并文件，但必须保留决策来源、对象修订、验证状态和人工门禁。S 编号对应 [Full Track](../workflows/full.md)，不增加新阶段。

## 生产发布交接

业务验收不自动授权上线。实际项目的发布记录至少指向：版本化产物、目标环境及范围、有效批准人、适用的部署/升级/回退验证、监控告警与维护责任，以及数据恢复依据。缺少适用关键证据时不得由 S14 推出生产放行；详见 [Ops Readiness](../docs/06-ops-readiness.md#生产发布交接)。

## 进行中与跨会话

使用 [交接模板](../harness/examples/handoff.example.md)记录当前 S 阶段、原始门禁状态、输入与产物路径、证据、阻断、下一步及审核角色。新会话先读此记录，再核对路径和修订；不要凭聊天记忆补写“已完成”。

## 练习材料

[Restart 示例](../examples/kubernetes-deployment-restart/README.md)为教学；其中“批准/PASS”不是实际项目的批准或执行证据。本轮验证包分别保存公开任务、原始结果及复核依据；维护者的验收索引见 [实施设计](../docs/plans/2026-11-15-reuse-design.md)。
