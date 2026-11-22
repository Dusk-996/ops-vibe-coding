# Ops Vibe Coding

面向熟悉运维、想借助 AI 开发工具的工程师。从一次值班遇到的问题开始，经过原型、架构、实现与验收，把一个想法做成可验证的软件。

## 从这里开始

| 你要做什么 | 从哪里起步 |
|---|---|
| **第一次做本地 Demo**，用假数据验证一个流程 | 打开 [Quick Start 的 S00](docs/01-quick-start.md#s00)，选一个有价值的场景，再按 [轻量路线](workflows/lightweight.md) 完成练习。 |
| **团队长期维护，或涉及真实基础设施变更** | 走 [完整路线 S00–S14](workflows/full.md#s00)。例如，真的修改 Deployment 涉及权限、审计与未知结果处理，参见 [Restart 教学案例](examples/kubernetes-deployment-restart/README.md)。 |

先说清楚谁遇到了什么问题、现在怎么做、怎样算解决。S00 可以停在风险清单；决定做原型时，由人选定一个目标。没有前端经验，可以从 [单页原型库](https://github.com/luozijian1990/Beautiful-Ops-Pages) 或 [平台原型库](https://github.com/luozijian1990/Beautiful-Ops-Platform) 选已有页面，用 Mock 数据替换成自己的场景。

## 完整流程

![Ops Vibe Coding 完整工作流，覆盖 S00–S14、人工门禁和反馈路径](docs/diagrams/ops-vibe-coding-workflow.svg)

[查看 SVG 大图](docs/diagrams/ops-vibe-coding-workflow.svg) · [编辑 draw.io 源文件](docs/diagrams/ops-vibe-coding-workflow.drawio) · [S00–S14 完整阶段说明](workflows/full.md)

图中蓝色实线表示主路径，黄色菱形标记判断或人工批准，红色虚线表示退回与修复。阶段编号与 Full Track 对应，具体放行条件及回退规则以阶段说明为准。

[Archify 交互版流程图](docs/ops-vibe-coding-workflow.html) 提供主题切换、缩放、搜索和阶段导览。请下载 HTML 后用浏览器打开，本次核验见[调整验证记录](docs/reviews/2026-11-22-s00-workflow.md)。

Parity、Review、Ops Readiness 或 E2E 发现问题后，都要回到对应阶段修正并重新提供证据。人工验收完成后，将验收记录交给实际项目的生产发布流程。

## 10 分钟理解每个阶段

| 阶段 | 回答的问题 | 关键产物 | 人工门禁 |
|---|---|---|---|
| 意图与 Prototype | 先验证哪个场景，用户如何使用？ | S00 简报、HTML Prototype、批准记录 | 人先选场景，再实际体验并确认原型 |
| React + Mock | 产品契约是否可执行？ | React App、Mock API/Data | Parity 报告通过 |
| Architecture | 系统由什么组成？ | Draft、Grill 决策、Final | 确认运行与风险约束 |
| Spec、Tickets 与 TDD | 一个可独立验收的任务怎样实现？ | Spec、Ticket、代码、测试结果 | 确认范围、验收条件和测试边界 |
| 代码与运维审查 | 实现满足规格吗，失败后能恢复吗？ | Code Review、Ops Readiness 报告 | 关闭阻断问题，由有权人员处理剩余风险 |
| E2E 与人工验收 | 真实流程是否解决最初的问题？ | 测试计划、浏览器证据、验收决定 | 批准测试范围，按实际证据接受或退回 |

前端只能暴露能力候选，不能直接决定 Redis、MQ、Worker、WebSocket 或微服务：

> UI 告诉我们系统需要做什么；Grill 告诉我们系统必须在什么约束下运行；两者共同决定架构。

## 按需查阅

- 换会话或接手 Ticket，先读[交接记录](harness/examples/handoff.example.md)；多会话协作见 [Harness](harness/README.md)。
- 在当前阶段查[产物索引](references/artifacts.md)、[技能与固定版本](references/skills.md)或[流程问题定位](docs/09-troubleshooting.md)。
- 按主题深入阅读：[原型](docs/02-prototype-first.md)、[架构与 Spec](docs/03-architecture-and-sdd.md)、[上下文](docs/04-context-engineering.md)、[TDD](docs/05-tdd-and-feedback-loop.md)、[运维就绪](docs/06-ops-readiness.md)、[E2E 与人工验收](docs/07-e2e-and-human-acceptance.md)。术语见 [FAQ](docs/08-faq.md)。

## 核心原则

### 采用范围与责任

本仓库提供工作流和教学产物；规范 M、模板及依赖接口 A、具体产品 P 的验证分开。流程或练习通过不自动证明某个产品可上线，也不保证新人无错误。

新人负责按任务生成/核对产物、记录证据并在缺输入、权限或结果未知时停手；维护者确认架构、Spec 和测试范围，资深人员复核技术与运行风险，有权发布人另行批准上线。每个采用项目须把这些角色绑定到实际人员，不能由 Agent 代签。

本次[工作流验证记录](docs/reviews/2026-11-22-s00-workflow.md)列出本地样本、实际调用和未验证范围。旧版本的采用与图稿检查见 [2026-11-15 记录](docs/reviews/2026-11-15-reuse-validation.md)。

### 工作原则

- **Prototype before expensive code**：尽量在低成本原型阶段发现产品问题。
- **Human approves intent, AI executes detail**：AI 执行细节，人决定需求、架构、风险和验收。
- **UI reveals capabilities, grilling reveals constraints**：不从 UI 直接脑补完整架构。
- **Evidence before complexity**：没有具体证据，不增加基础设施复杂度。
- **One ticket, one context**：一个 Ticket 使用一个新会话，降低上下文污染。
- **Specs are executable contracts**：Spec 必须能够指导实现与测试。
- **Tests are evidence**：不能用“应该可用”代替可复现验证。
- **Operations are part of software design**：权限、审计、Secret、恢复、部署和可观测性属于设计本身。
- **Human acceptance closes the loop**：最终由人确认软件是否解决最初的问题。

## 项目生态与仓库边界

| 项目 | 职责 |
|---|---|
| `ops-vibe-coding` | 维护方法论、工作流、教程、引用和示例，定义 Operations-first Golden Path |
| [Beautiful Ops Pages](https://github.com/luozijian1990/Beautiful-Ops-Pages) | 提供可直接体验和改写的单页功能原型 |
| [Beautiful Ops Platform](https://github.com/luozijian1990/Beautiful-Ops-Platform) | 提供可直接体验和改写的完整运维平台原型 |
| [skills-manager-backup](https://github.com/Dusk-996/skills-manager-backup) | 提供工作流引用的技能版本，具体入口及依赖见 [Skill Map](references/skills.md) |

本仓库引用现有原型和 Skills，但不复制它们的实现。首版也刻意不提供 CLI、Agent Framework、低代码平台或大量 Demo；目标是先让一条面向运维场景的完整路径清楚、可执行、可验证。
