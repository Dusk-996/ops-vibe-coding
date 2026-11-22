# Full Track

适用于团队工具、长期维护、生产使用、敏感数据或基础设施变更。用 S00–S14 定位输入、动作、产物和放行条件。每步列出可用技能及启用条件，固定来源见 [Skill Map](../references/skills.md)。第一次使用可从 [Quick Start](../docs/01-quick-start.md#s00) 复制本步指令。

<a id="s00"></a>

## S00. 澄清问题与原型目标

- **Why**：选一个真实使用者愿意验证的场景，判断是否值得制作页面。
- **Input**：一句想法、现有操作记录或已有方案。
- **Action**：① 了解使用者、现有做法和痛点；② 让使用者描述可观察的成功标准；③ 比较可行方向和取舍，包括复用已有工具；④ 收敛到一个核心流程，列出本轮范围和待验证问题。已有答案只需引用。
- **Skill**：模糊想法由工作流先引导。对已有候选方案找风险时，用 [devops-brainstorming](../references/skills.md#devops-brainstorming) 的 Grill 模式逐题质询；只想缩小范围时用其 Refinement 模式。明确转为实施设计时，按该技能的设计审批和 [writing-plans](../references/skills.md#writing-plans) 交接。
- **Output**：原型简报（目标用户、现状、成功标准、方向取舍、核心流程、范围和待验证项），或已达成共识的风险清单。可直接补在已有问题说明里。
- **Gate / Next**：需求提出人选定原型目标后，带简报进入 [S01](#s01)；只评估风险的工作可在风险清单处结束。缺决定时保留待确认。这个选择只确定原型要验证什么；[S02](#s02) 由使用者体验后确认产品意图，[S06](#s06) 根据架构草案确认运行约束。后续只重开受新证据影响的决定。

<a id="s01"></a>

## S01. Explore — HTML Prototype

- **Why**：以最低成本把模糊想法变成可体验产品。
- **Input**：S00 已选定的目标用户、核心流程、成功标准和待验证问题。
- **Skill**：从零设计页面时用 [frontend-design](../references/skills.md#frontend-design)。已有合适原型可直接改写。
- **Action**：选择或制作 HTML，覆盖导航、关键流程和重要状态。
- **Output**：Prototype 与初始流程说明。
- **Gate**：无；允许快速探索。
- **Next**：Human Prototype Review。

<a id="s02"></a>

## S02. Human Prototype Review

- **Why**：在正式工程化前确认产品意图。
- **Input**：可交互 Prototype。
- **Skill**：由真实使用者主持体验。AI 可准备点击清单，确认范围与决定由人记录或核实。
- **Action**：真实使用者检查信息架构、操作入口、状态反馈、权限表现与响应式行为。
- **Output**：批准的 Prototype、关键流程和 viewport 契约。
- **Gate**：`Prototype Approved`。
- **Next**：React + Mock。

<a id="s03"></a>

## S03. React + Mock

- **Why**：把批准的视觉与交互变成可运行产品契约。
- **Input**：Prototype 与批准记录。
- **Skill**：[html-to-mui-react](../references/skills.md#html-to-mui-react) 按批准范围转换；变更视觉方案须先向原型负责人确认。
- **Action**：默认保真转换；实现页面、路由、数据模型、API Shape、交互和 Loading/Error/Empty/Success。
- **Output**：React App、Mock API/Data、build 与浏览器验证记录。
- **Gate**：关键流程实际可运行；未验证标为 `NOT_VERIFIED`。
- **Next**：Prototype Parity Gate。

<a id="s04"></a>

## S04. Prototype Parity Gate

- **Why**：防止工程化转换改变已批准设计。
- **Input**：批准的 HTML、React App、关键流程。
- **Skill**：单独调用 [prototype-parity-review](../references/skills.md#prototype-parity-review)，原型审核人判断报告中的偏差能否接受。
- **Action**：在真实浏览器比较 Visual Parity 和 Interaction Parity。
- **Output**：`PASS`、`PASS_WITH_NOTES` 或 `FAIL` 报告。
- **Gate**：`PASS`，或人接受 `PASS_WITH_NOTES`；`FAIL` 必须退回修复。
- **Next**：Architecture Draft。

<a id="s05"></a>

## S05. Architecture Draft

- **Why**：把 UI 信号转成能力候选，而不是直接脑补技术组件。
- **Input**：React Mock 与已知运行约束。
- **Skill**：[stack-selector](../references/skills.md#stack-selector) 第一轮产生草案。维护者核对开放问题及其来源。
- **Action**：提取 API、数据、交互和外部操作；给出最小暂定架构、排除项、升级条件和 Grill 输入。
- **Output**：`stack-selection.draft.md`。
- **Gate**：Draft 明确写“完成 Grill 后再 Finalize”，不得进入 SDD。
- **Next**：Grill。

<a id="s06"></a>

## S06. Grill

- **Why**：补齐 UI 无法表达的运行约束。
- **Input**：Draft 的开放问题。
- **Skill**：[grilling](../references/skills.md#grilling) 针对草案中的关键未知项逐题询问负责人。需要同步项目术语或架构决策记录时搭配 [domain-modeling](../references/skills.md#domain-modeling)。
- **Action**：确认部署、规模、网络、认证、权限、审批、审计、凭证、任务时长、重试、恢复、留存和现有基础设施。
- **Output**：可追溯的决策记录或 ADR。
- **Gate**：会改变架构的关键约束已由人确认。
- **Next**：Architecture Final。

<a id="s07"></a>

## S07. Architecture Final

- **Why**：让组件、部署单元和技术选择同时受产品能力与运行约束支持。
- **Input**：同一 Draft 与 Grill 决策。
- **Skill**：[stack-selector](../references/skills.md#stack-selector) 第二轮用已确认的回答定稿，架构负责人核对每项回答与选择的对应关系。
- **Action**：映射每条决策，复查组件、部署、安全与可靠性基线、排除项和升级条件。
- **Output**：`stack-selection.md`。
- **Gate**：关键未知项仍存在时继续保持 Draft；不得伪造 Final。
- **Next**：SDD / Spec。

<a id="s08"></a>

## S08. SDD / Spec

- **Why**：把产品和架构变成精确、可测试的行为契约。
- **Input**：Prototype、Architecture Final、决策记录。
- **Skill**：[to-spec](../references/skills.md#to-spec) 与负责人先确认测试边界，再编写规格。缺少项目跟踪配置时，先用 [setup-matt-pocock-skills](../references/skills.md#setup-matt-pocock-skills) 选择项目约定的跟踪方式。
- **Action**：定义功能、边界、API、数据模型、状态机、错误、授权、审计、可观测性、失败行为、测试 seam 和验收条件。
- **Output**：已批准 Spec。
- **Gate**：范围、风险和验收条件由人确认。
- **Next**：Tickets。

<a id="s09"></a>

## S09. Tickets

- **Why**：把 Spec 变成可独立实现和验证的工作单元。
- **Input**：已批准 Spec。
- **Skill**：[to-tickets](../references/skills.md#to-tickets) 先向维护者展示切片和依赖，确认后再写入跟踪器。沿用 S08 的配置，如仍缺配置再用 [setup-matt-pocock-skills](../references/skills.md#setup-matt-pocock-skills)。
- **Action**：按用户价值拆纵向切片，声明依赖、非目标和验证方式。
- **Output**：本地 Markdown Ticket 或 GitHub Issue。
- **Gate**：每项能在一个独立上下文中完成并验证。
- **Next**：TDD。

<a id="s10"></a>

## S10. TDD

- **Why**：用反馈循环约束实现，而不是一次性生成大量代码。
- **Input**：一个 Ticket、必要项目文档和相关代码。
- **Skill**：[superpowers:test-driven-development](../references/skills.md#test-driven-development) 覆盖红、绿和保持绿色时的重构；维护者按 Ticket 核对最终验证范围。
- **Action**：RED → GREEN → REFACTOR → VERIFY；一个 Ticket 使用一个新会话。
- **Output**：实现、测试和可复现验证结果。
- **Gate**：验收测试、单元测试、lint/build 和 Ticket 条件通过。
- **Next**：Code Review。

<a id="s11"></a>

## S11. Code Review

- **Why**：分别检查仓库规范与 Spec 符合度。
- **Input**：固定比较点、Spec、代码和测试。
- **Skill**：[code-review](../references/skills.md#code-review) 比较固定基点与候选提交；代码审核人和维护者核对阻断项修复证据。
- **Action**：沿 Standards 与 Spec 两条轴审查。
- **Output**：带文件证据和严重级别的报告。
- **Gate**：阻断问题解决。
- **Next**：Ops Readiness Review。

<a id="s12"></a>

## S12. Ops Readiness Review

- **Why**：判断运维软件是否具备合理的生产运行和操作安全基础。
- **Input**：架构、Spec、代码、部署配置和测试证据。
- **Skill**：[ops-readiness-review](../references/skills.md#ops-readiness-review) 依证据审查适用的运行风险，由有权的风险负责人决定是否接受剩余风险。
- **Action**：按风险检查危险操作、授权、审计、Secret、远程执行、Kubernetes、异步任务、API、可观测性、数据生命周期、部署和恢复。
- **Output**：`PASS`、`PASS_WITH_RISKS` 或 `FAIL` 报告。
- **Gate**：按 [Ops Readiness 的状态判定](../docs/06-ops-readiness.md#状态判定)放行；关键控制未验证、阻断项未修复或重大风险未被有效接受时不得放行。
- **Next**：E2E Test Plan。

<a id="s13"></a>

## S13. E2E Test Plan → Playwright → Test Report

- **Why**：以真实用户 Workflow 验证系统，而不是只看元素存在。
- **Input**：Spec、Tickets、运行环境和允许操作边界。
- **Skill**：[playwright-e2e-debug-report](../references/skills.md#playwright-e2e-debug-report) 编制计划及报告。测试批准人确认身份、环境和允许操作后，使用 [playwright-cli](../references/skills.md#playwright-cli) 执行浏览器步骤。
- **Action**：先生成测试任务并等待人批准，再运行 Playwright；失败先分类，修复需要额外授权。
- **Output**：步骤、证据、`PASS / FAIL / SKIPPED` 和环境限制。
- **Gate**：破坏性或生产操作有明确权限；测试范围和结果由人确认。
- **Next**：Human Acceptance。

<a id="s14"></a>

## S14. Human Acceptance

- **Why**：AI 的测试结论不能代替业务和风险判断。
- **Input**：全部产物、审查和测试证据。
- **Skill**：业务使用者与有权的风险负责人作决定。AI 可汇总审核材料，结论以人的实际答复为准。
- **Action**：人确认产品意图、价值、失败行为、风险与运行成本。
- **Output**：可追溯的人工接受、补充或退回记录，含对象、范围、依据与决定人；业务验收结果另交实际项目的生产发布流程。
- **Gate**：只有有权人员可以关闭最终业务闭环；不自动授予发布或生产操作权限。实际发布还需满足 [生产发布交接](../docs/06-ops-readiness.md#生产发布交接)。

## 回退规则

| 失败 | 回退位置 |
|---|---|
| 原型体验显示目标用户或成功标准有误 | 回 S00 重新选定目标，再按需更新原型 |
| 原型流程不合理 | Prototype / Human Review |
| React 改变批准设计 | React + Mock，修复后重跑 Parity |
| 运行约束不足 | Grill，再 Finalize |
| Spec 无法测试 | Spec 的 seam 与验收条件 |
| Ticket 过大 | 重新拆纵向切片 |
| Review 发现设计问题 | 对应 Spec 或 Architecture 决策 |
| Ops Readiness 失败 | 有边界的修复 Ticket，完成后重审 |
| E2E 失败 | 先分环境、测试、产品、数据或权限问题再行动 |
