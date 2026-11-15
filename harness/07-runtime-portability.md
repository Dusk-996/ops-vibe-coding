# Runtime Portability

> Tools are replaceable. Engineering context is durable.

## 这一篇解决什么问题

今天用 Claude Code，明天可能换 Codex、OpenCode、Gemini CLI 或 Cursor。如果流程、规则、知识和证据都存在某个 AI 产品的聊天历史里，换工具就等于从零开始。

## 核心资产应该驻留在 Repository

```text
Specs
Tickets
AGENTS.md
Docs
Gate Reports
Test Reports
Architecture
Ops Rules
Scoped Context
IDL（复杂契约项目按需）
Service Matrix（多服务项目按需）
```

这些全部是仓库里的版本化文件，而不是某个 AI 产品的会话记录。仓库在哪里，工程资产就在哪里。

## 换工具时什么不变

```text
Workflow 不变          流程定义在 workflows/
Artifacts 不变          产物定义在 references/artifacts.md
Rules 不变              规则在 AGENTS.md + docs/
Acceptance Criteria 不变 验收条件在 Spec 和 Ticket 里
Service Contracts 不变   采用时，接口在 IDL，关系在 Service Matrix
```

读取同一套仓库资产是迁移的前提；还需核对实际加载的规则、Skill 版本、可用工具、权限和调用结果。相同 Markdown 不证明不同运行时行为相同。

## 运行时差异的处理

不同工具读 AGENTS.md、Skills 的方式略有差异，第一版不做复杂 Runtime Adapter。建议：

1. 把规则和知识放在仓库（工具无关）；
2. 按当前工具的要求，在工具配置目录只放入口、引用或指向仓库资产的链接；
3. 如果运行时只能消费生成文件，将其标记为不可手工编辑，并从仓库权威来源重复生成。

示例：

```text
.claude/    ← 入口，指向仓库内的 AGENTS.md 与 docs/
.codex/     ← 入口，指向同一份
.opencode/  ← 入口，指向同一份
```

正文只有一份，入口可以有多个。

## 怎么执行

1. 所有规范、知识、门禁产物写进仓库，接受 code review 与版本控制；
2. 每个会话从仓库读取，不从记忆恢复；
3. 换工具时验证"新工具凭仓库资产能独立开工"，把验证记录写进仓库。

如果团队规范来自独立仓库或制品，项目必须记录其来源和版本。不同 Runtime 解析的是同一固定版本，不能各自读取不受控的“最新版”。

## 常见错误（Anti-patterns）

- **规则只存在 Cursor 的自定义指令里**：换工具，规则清零；
- **Spec 只写在聊天记录里**：会话一关，验收标准消失；
- **为某个工具写专属工作流**：绑定到特定产品，团队迁移成本高；
- **过早实现复杂 Runtime Adapter**：第一版用 Markdown + 仓库就够，工具适配按需再做。

## 门禁与下一步

- **门禁**：只对有采用证据的运行时、版本、入口及任务组合声明已验证；其他组合保留未验证；
- **下一步**：回到 [01-context-engineering.md](01-context-engineering.md) 检查上下文分层是否完整，或在 [examples/](examples/) 里找到可直接改写的模板。

## 首轮基线与环境起点

本次范围是 Windows + Codex CLI 0.169.0 的文档及 Skill 阶段采用；这是待验证目标，不是兼容通过声明。完整 TDD、构建、浏览器 E2E、应用部署/恢复，以及 Ubuntu/CentOS/Kylin 和其他运行时不因本次静态修订被认定已验证。实际状态看 [本轮验证记录](../docs/reviews/2026-11-15-reuse-validation.md)。

环境起点应记录：OS/终端/工具/运行时/模型标识，规则入口，预装与全局 Skill，允许缓存及网络条件。新建目录不等于干净环境。取得固定依赖并实际调用后，核对加载路径与摘要；模型无法固定的部分如实列限制。

[Skill Map](../references/skills.md)固定来源、传递依赖和副作用。原生 Skill 在隔离验证目录加载，不修改用户全局副本；显式点名调用。发现同名来源冲突、无法确认加载修订、缺少必需子 Agent 能力时，记录环境阻断，不静默换成全局或其他实现。

本地 tracker 在执行前配置好，避免触发 setup 的远程默认。只做本地文档任务，不自动安装 npm/Playwright 最新版。必要依赖获取失败时保存错误，使用有固定修订和摘要的手动/离线材料；不能改用未知镜像或浮动最新版后仍声称复现。
