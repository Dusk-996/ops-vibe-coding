# FAQ

第一次使用从 [新人使用指引](01-quick-start.md) 开始；遇到阻断先查 [问题定位](09-troubleshooting.md)。阶段及门禁以 [Full Track](../workflows/full.md) 为准，本页不另设通过条件。

## 为什么同一份测试报告可以得 10 分，流程却要退回？

分数回答“这份交付物写准了吗”。如果浏览器显示取消后仍发出请求，如实记录失败、证据与修复责任即可交付一份完整报告，产品仍要修复。两版报告和同一条失败证据见[显式复评样板](reviews/calibration/skill-invocations.md)。

## 一个阶段要调用几个 Skill？

按工作分工确定。S02 由使用者决定，S10 用一个 TDD 入口，S13 由计划与报告技能编排浏览器执行工具。产物形成后再点名评分技能。S00 已有设计文档或 Grill 摘要时直接评该版本，位置见[产物索引](../references/artifacts.md)。

## 不熟开发，需要先学会 React / Python / Go 吗？

不必先熟练这些语言。先能指出目标用户、看懂产物对应哪个阶段、核对原始证据，并知道哪些决定需要谁确认。代码由 AI 辅助生成；涉及你无法核验的行为或风险时，找项目维护者、开发审核人或指定风险负责人，不让 AI 用“已完成”代替证据。基础 Linux、容器与操作风险知识仍需要由你掌握。

## 不会 React 可以吗？

可以，转换可由 `html-to-mui-react` 的 fidelity 模式完成。人的责任覆盖全过程：确认原型、回答架构约束、批准 Spec 的范围/风险/验收、复核 Ticket 边界、核对验证证据、批准测试范围与操作权限，并由有权的人接受风险和最终验收。AI 可整理材料，不能代签。你不必独自承担所有角色，但必须明确谁来决定；见 [新人指引各步审核角色](01-quick-start.md) 与 [权限边界](../harness/06-tool-and-permission-boundaries.md)。

## 这些英文术语分别指什么？

| 术语 | 在本流程中的含义 |
|---|---|
| Prototype | 可点击、可体验的原型，用来确认产品意图 |
| Mock | 模拟的数据或接口，帮助验证界面行为；不证明真实系统已工作 |
| Parity | 获批原型与 React 的视觉、交互一致性 |
| viewport | 浏览器视口尺寸；比较前后使用同一尺寸与状态 |
| Draft / Grill / Final | 架构草案 / 追问并确认约束 / 消费同一草案后的架构定稿 |
| ADR | Architecture Decision Record，记录决定、理由与确认来源 |
| SDD / Spec | 规格驱动开发 / 可测试的行为规格；Spec 不是实现代码 |
| seam | 测试接缝，允许测试替换真实集群、数据库等外部依赖的边界 |
| Ticket / vertical slice | 一个任务 / 纵向切片，交付一个可独立验证的用户价值 |
| TDD | 测试驱动开发：RED → GREEN → REFACTOR → VERIFY |
| lint / build | 静态规范检查 / 构建；通过它们不能证明完整用户流程成功 |
| Code Review / Ops Readiness | 代码规范与 Spec 审查 / 运行及操作安全审查 |
| E2E / Workflow | 端到端测试 / 用户从入口到结果的一整条流程 |
| Gate / Evidence | 阶段门禁 / 支撑判断的可定位原始证据 |
| HITL | Human In The Loop，保留人对关键决定和权限的控制 |
| handoff | 会话交接记录，保存阶段、证据、阻断与下一步 |

## 一定要从 HTML 开始吗？

不强制。已有 PRD（产品需求文档）或正在改造现有系统时，可以按现有产物进入后续阶段，但要核对其前置输入及确认记录。首次做产品时，HTML 是直接、低成本的意图验证方式。见 [Prototype First](02-prototype-first.md)。

## Prototype 和 PRD 有什么区别？

Prototype 是可点、可看、可体验的契约，PRD 是文字描述。对非产品背景的运维工程师，前者表达意图更直接。两者不能替代架构、Spec 或测试证据。见 [Prototype First](02-prototype-first.md)。

## 一定要用 MUI 吗？

不是。组件库服从已批准的原型；只有明确说视觉无需保留时，才统一为 MUI 风格。见 [Prototype First](02-prototype-first.md)。

## 一定要用 Python / Go 吗？

不是。技术栈由 UI 暴露的能力加上 Grill 确认的约束共同决定。见 [Architecture and SDD](03-architecture-and-sdd.md)。

## React Mock 可以直接决定后端吗？

不能。UI 只暴露能力候选，部署、规模、安全、恢复等约束必须经 Grill 确认。第一次 `stack-selector` 只生成 Draft，第二次消费同一 Draft 和确认记录才能 Finalize。关键未知项还在，就保持 Draft。见 [Architecture and SDD](03-architecture-and-sdd.md)。

## 小项目需要完整 SDD 吗？

不需要相同文档深度。Lightweight Track 仍要求 Minimal Spec、原型与架构约束人工确认、Parity、验证和人工验收。涉及生产资源、敏感操作、长任务或团队长期维护等升级条件时改走 Full Track。见 [Lightweight Track](../workflows/lightweight.md)。

## 什么时候可以跳过 TDD？

纯一次性、用完即弃且无生产价值的小工具，可以按 Lightweight Track 保留较轻验证，但每个 Ticket 仍要有可失败的验收测试或可复现步骤。生产资源、敏感操作或长期维护按 Full Track 执行；不能把“AI 已生成”当验证。见 [TDD and Feedback Loop](05-tdd-and-feedback-loop.md) 与 [Lightweight Track](../workflows/lightweight.md)。

## 什么时候需要 Worker？

存在长时间运行、需要重启恢复、独立于请求的异步任务，且 Grill 确认了重试、并发、恢复约束时才需要。UI 有进度条不等于需要 Worker。见 [Architecture and SDD](03-architecture-and-sdd.md)。

## 什么时候需要 Redis？

有明确证据需要缓存、队列或分布式锁时才需要。默认能用数据库解决的问题，不要加组件。见 [Architecture and SDD](03-architecture-and-sdd.md)。

## 什么时候需要 Agent？

需要远程在目标主机执行任务且不能内嵌在服务里，同时确认了凭证隔离、命令白名单与审计时才需要。见 [Ops Readiness Review](06-ops-readiness.md)。

## 为什么每个 Ticket 开新会话？

减少上下文污染，让 Agent 从文档重建事实。新会话先读 `AGENTS.md` 索引、一个 Ticket、批准 Spec、必要 ADR 和 [handoff](../harness/examples/handoff.example.md)，核对当前阶段与原始证据后再续做；不靠聊天回忆推断已通过。见 [Context Engineering](04-context-engineering.md) 与 [T08](09-troubleshooting.md#t08)。

## AI 写了 PASS，为什么还不能说可上线？

先问“谁的什么范围通过了”：方法论与模板的审查不替具体产品放行；文档静态检查不证明代码运行；局部测试不证明完整流程；报告标题也不能推翻原始失败输出。按 [证据规则](../harness/04-gates-and-evidence.md) 核对对象、修订、环境、范围、命令和原始结果，再应用对应阶段门禁。产品最终验收与生产变更权限仍由有权的人确认。见 [T05](09-troubleshooting.md#t05) 与 [T09](09-troubleshooting.md#t09)。

## SKIPPED、NOT_VERIFIED、NOT_APPLICABLE 都能算通过吗？

不能。`SKIPPED` 表示该测试未执行；`NOT_VERIFIED` 表示相关范围尚无足够验证证据；`NOT_APPLICABLE` 需说明为什么不适用。各状态及对门禁的影响以 [Full Track](../workflows/full.md) 和 [阶段证据规则](../harness/04-gates-and-evidence.md) 为准。记录原因、影响、补证据动作与责任人，不能把它们改写为 `PASS`。见 [T06](09-troubleshooting.md#t06)。

## 为什么 AI 测试完还要人工验收？

AI 可以依据证据说明测试范围内的行为，“是否解决最初的问题、风险和成本是否可接受”仍是人的业务判断。测试计划、危险操作授权、架构约束和风险接受也都需要相应人员参与，人的职责不只在最后一步。见 [E2E and Human Acceptance](07-e2e-and-human-acceptance.md)。

## Ops Readiness 和 Code Review 有什么区别？

Code Review 查代码正确性、仓库规范与 Spec 符合度；Ops Readiness 查生产运行、操作安全与恢复证据，两者互补不替代。见 [Ops Readiness Review](06-ops-readiness.md)。

## Skill 找不到或依赖下载失败，能让 AI 自己换最新版吗？

先停在依赖核对：确认 Skill 是否被当前运行时发现、实际来源/修订是否与项目约定一致，区分网络、代理、权限与版本问题。使用批准的来源、固定版本或经确认的离线包；不要静默替换同名 Skill、绕过校验或改全局配置。见 [Skill Map](../references/skills.md)、[T01](09-troubleshooting.md#t01) 和 [T02](09-troubleshooting.md#t02)。

## Restart 显示 UNKNOWN，要不要再点一次？

不要。`UNKNOWN` 表示提交结果不确定，操作可能已执行；审计未确认也不能推断“肯定没执行”。保存操作 ID、目标、时间、原始响应和核验责任人，不换 ID 重试、不自动解锁。按项目指定角色先只读取证，再由有权人员决定后续处理；这里的文档是恢复责任契约，不代表仓库提供了恢复功能。见 [T07](09-troubleshooting.md#t07) 与 [Restart Spec](../examples/kubernetes-deployment-restart/05-spec/deployment-restart.spec.md)。

## 看完指南或验证一个片段，就算会用完整流程了吗？

练习结论只覆盖实际输入、运行环境及取得的证据。按 [调整验证记录](reviews/2026-11-22-s00-workflow.md) 查看哪些阶段实际演练过。目标项目仍需逐步验证，独立新人试用另记定位、停手、求助、误判与耗时。见 [新人指引](01-quick-start.md) 和 [问题定位](09-troubleshooting.md)。
