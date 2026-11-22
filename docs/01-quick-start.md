# 新人使用指引（Quick Start）

手里只有一句想法时，从 [S00](#s00) 开始，例如“值班同事想从详情页安全地发起一次重启”。已经接手项目时，先看交接记录中的阶段和未决事项，再从下表跳到相应指令。

## 先选路径，再准备输入

- **本地 Mock、低风险体验**：选 [Lightweight Track](../workflows/lightweight.md)，先看其中的升级条件。
- **团队长期维护、真实基础设施变更或敏感操作**：选 [Full Track](../workflows/full.md)。如制作真正重启 Deployment 的工具，按完整流程评审权限、审计和恢复。

下面六组对应 S00–S14。详细放行与回退条件见 Full Track，项目的运行风险和实际验证范围分别查 [Ops Readiness](06-ops-readiness.md) 与 [证据规则](../harness/04-gates-and-evidence.md)。

| 组 | 去哪里 | 人需要决定什么 |
|---|---|---|
| 1. 表达意图 | [S00 澄清](#s00) → [S01 原型](#s01) → [S02 人工确认](#s02) | 哪个问题值得验证，体验后接受哪些流程和状态 |
| 2. 固定产品契约 | [S03 React + Mock](#s03) → [S04 Parity](#s04) | 转换偏差能否接受 |
| 3. 确认架构约束 | [S05 Draft](#s05) → [S06 Grill](#s06) → [S07 Final](#s07) | 部署、安全、可靠性等事实 |
| 4. 实现一个切片 | [S08 Spec](#s08) → [S09 Tickets](#s09) → [S10 TDD](#s10) | 范围、风险、验收及测试边界 |
| 5. 分别审查 | [S11 Code Review](#s11) → [S12 Ops Review](#s12) | 阻断是否关闭，谁有权接受风险 |
| 6. 验证与收口 | [S13 E2E](#s13) → [S14 人工验收](#s14) | 批准测试范围并判断业务价值 |

指令中的路径指你的目标项目。如果使用本仓库的 [Restart 练习](../examples/kubernetes-deployment-restart/README.md)，可以从本地 HTML 和 React Mock 开始。先读目标项目 `AGENTS.md` 及其索引，写下谁遇到什么问题、现在如何处理、怎样算有价值。首次术语可查 [FAQ](08-faq.md)，卡住时去[问题定位](09-troubleshooting.md)。

## 每个新会话先贴一次公共约束

先替换所有 `{{参数}}`，再复制公共指令和当前步骤的 AI 指令。`{{项目根目录}}` 用绝对路径，`{{允许范围}}` 写具体目录和允许动作，`{{审核人}}` 写实际姓名或已指定角色，`{{记录目录}}` 是项目内已允许写入的证据目录。各步骤的其余参数换成真实文件、URL、版本或待确认问题；不要把示例路径当成已存在的输入。

```text
项目根目录：{{项目根目录}}；当前阶段：{{S编号}}。
先读 AGENTS.md、其索引及本步骤列出的输入。允许范围：{{允许范围}}。
仅做当前步骤；修改前说明影响范围，保留用户改动，优先最小改动并加必要中文注释。
本轮只使用本地或已授权测试环境；不直接操作生产，不自动安装或升级到最新版。
依赖必须先确认项目锁定版本、批准来源和安装范围；获取失败时保存错误，不绕过校验。
输出列出产物路径、输入修订、实际动作、命令/原始输出/退出码、未验证项及下一步，写到 {{记录目录}}；未执行的命令写明未执行。
教学样例、静态检查、实际调用、运行验证和人工决定分别记录；不伪造批准、测试或 PASS。
关键输入、权限、原始证据或所需 Skill 缺失/冲突时停手，说明缺口和应找的 {{审核人}}。
到本步骤规定的交接点停止；只有有权的人可作人工确认和风险接受。
```

Skill 是完成某一任务的执行说明，Workflow 是阶段与门禁。按 [Skill Map](../references/skills.md) 核对需要的 Skill、来源与固定修订；未发现就按 [T01](09-troubleshooting.md#t01) 定位，不能用一个名字相似的版本静默替代。国内网络获取失败见 [T02](09-troubleshooting.md#t02)，不要反复安装最新版。

需要换会话时，使用现有 [handoff 模板](../harness/examples/handoff.example.md) 在目标项目保存当前阶段、Ticket、输入修订、原始证据、未通过门禁、阻断、指定核验人和下一步。新会话先读交接及证据，只续当前任务；具体协议见 [会话生命周期](../harness/03-task-and-session-lifecycle.md)。

<a id="artifact-review"></a>

## 交付后复查该版本

交付后复制下面的指令。在[产物索引](../references/artifacts.md)选择实际阶段和出口，提供已有材料即可。换会话时要带上原始阶段状态。

```text
使用 $stage-artifact-review 复查 {{阶段编号}}（{{Full/Lite及本次范围}}）。
规则是 {{工作流仓库固定修订}} 的 references/stage-rubrics.md#{{小写阶段编号}}，规则版本 {{规则版本}}。
产物是 {{实际文件、页面或关联文件组及修订}}；上游输入、授权及证据在 {{定位}}，阶段状态依据见 {{记录}}。
只交付评分报告到 {{输出位置}}：列出逐项分数、依据与扣分位置、原始分、封顶及最终分、阶段放行状态和可执行修改建议。
复评时引用 {{上次报告及产物版本}}；逐项核对缺口。规则有变化时另列基线。
```

低于 8 分的产物由负责人决定如何处理。有权人员仍按原阶段决定能否继续，产品测试失败和人工待审照实保留。[已评分的校准样例](reviews/calibration/results-v1.md)

## 第一组：澄清问题、做原型、体验确认

<a id="s00"></a>

### S00 澄清问题与原型目标

一句想法可以直接开始。用下面的指令整理四件事：当前痛点、可观察的成功标准、可行方向及取舍、值得验证的一个场景。已经讨论过的决定附上来源即可。

```text
沿用公共约束。我的想法或已有方案是：{{例如：值班同事想从详情页发起重启}}。
请先从材料中查找谁在什么时候做什么判断、当前如何处理、怎样算成功。只问会改变选择的问题，每次一个。
比较可行方向和取舍。已有候选方案需要找风险时，用 $devops-brainstorming 的 Grill 模式；范围过大时，用其 Refinement 模式收敛。
交付所选出口的一份材料。原型简报写目标用户、成功标准、核心流程、范围和待验证项，请 {{需求提出人}} 选择场景；已有 design.md 或 Grill 风险摘要时直接给出原件位置。仅做评估可记录风险后结束。
```

只有需求提出人选定了原型目标，才带简报进入 S01；没有答复就标待确认。若决定正式实施设计，请使用 [devops-brainstorming](../references/skills.md#devops-brainstorming) 的原生审批与 [writing-plans](../references/skills.md#writing-plans) 交接。S02 根据原型体验确认产品意图，S06 根据架构草案确认运行约束。 [复查 S00 产物](../references/stage-rubrics.md#s00)

<a id="s01"></a>

### S01 先做可体验原型（HTML Prototype）

- **目标**：让真实使用者看见流程，尽早发现意图偏差。
- **前置输入**：S00 已选定的用户、关键流程、成功标准、待验证项和允许的本地目录。

```text
沿用公共约束。读取 {{S00简报}}。有合适的现成原型就复用，从零设计时用 $frontend-design，仅在 {{原型目录}} 制作可点击 HTML Prototype。
围绕 {{关键流程}} 展示导航、操作入口、权限表现，以及相关的 Loading/Error/Empty/Success 状态。
使用 Mock 数据，不连接真实集群或服务；输出页面、流程说明、待人确认清单。完成后停在人工体验前，不写已批准。
```

- **产物与检查点**：打开 HTML，按给定样本从入口走到结果。可在本地直接打开 [Restart 原型](../examples/kubernetes-deployment-restart/01-prototype/index.html)，分别体验取消、已提交和结果未知。 [复查 S01 产物](../references/stage-rubrics.md#s01)
- **完成条件与审核角色**：按 [Full Track §1](../workflows/full.md#s01) 交付可体验原型，此阶段无批准门禁；需求提出人与真实使用者准备体验。
- **失败处理 / 下一步**：入口或状态缺失先补原型；意图不清找需求提出人，准备好后到 S02。

<a id="s02"></a>

### S02 由人批准产品意图（Human Prototype Review）

- **目标**：明确以后需要保留的页面、交互和屏幕尺寸（viewport）。
- **前置输入**：S01 原型、流程、目标 viewport，以及实际参与的真实使用者。

```text
沿用公共约束。只读 {{原型路径}}，为 {{关键流程}} 和 {{viewport列表}} 整理人工点击检查清单。
检查导航、操作入口、状态反馈、权限表现与响应式行为；仅在 {{批准记录路径}} 写待确认项。
等待 {{真实使用者}} 实际体验并给出决定，再准确记录批准范围、修订与剩余问题；未收到决定就停手，不代签。
```

- **产物与检查点**：如 `prototype/approval.md`；应定位到原型修订、页面、流程、viewport、转换模式、审核人与决定。仅写“看着可以”不足以固定范围。 [复查 S02 产物](../references/stage-rubrics.md#s02)
- **完成条件与审核角色**：沿用 [Full Track §2](../workflows/full.md#s02) 的 `Prototype Approved`；由真实使用者确认，AI 只整理记录。
- **失败处理 / 下一步**：未批准或流程不合理回 S01；获批后带同一记录进入 S03。

## 第二组：Mock 与原型一致性

<a id="s03"></a>

### S03 转成可运行产品契约（React + Mock）

- **目标**：用 React 界面与模拟接口（Mock）固定页面行为，尚不据此决定后端。
- **前置输入**：获批原型、批准记录、页面/路由/状态及 viewport 清单，已确认的项目依赖版本。

```text
沿用公共约束。用 $html-to-mui-react 读取 {{批准原型目录}} 与 {{批准记录}}，只在 {{前端目录}} 转换。
默认 fidelity 保真；仅有显式视觉重设授权时使用 mui-normalize。保留路由、布局、关键流程、数据/API Shape 与非默认状态。
按项目已确认依赖执行 {{build命令}}，在 {{本地或测试URL}} 用真实浏览器走 {{关键流程}}，保存输出与截图。
输出 React、Mock API/Data 和验证记录；环境或浏览器不可用就记录 NOT_VERIFIED，停在 Parity 前，不接真实资源。
```

- **产物与检查点**：可启动前端、Mock、build 输出和浏览器证据。见 [Restart Mock 运行说明](../examples/kubernetes-deployment-restart/02-react-mock/contract.md)与 [npm 入口](../examples/kubernetes-deployment-restart/02-react-mock/package.json)。 [复查 S03 产物](../references/stage-rubrics.md#s03)
- **完成条件与审核角色**：按 [Full Track §3](../workflows/full.md#s03) 检查关键流程实际可运行，未验证写 `NOT_VERIFIED`；实现者整理证据，原型审核人核对范围。
- **失败处理 / 下一步**：依赖失败见 [T02](09-troubleshooting.md#t02)，流程失败留在 S03 修复；证据齐后到 S04。

<a id="s04"></a>

### S04 比对转换前后（Prototype Parity）

- **目标**：确认视觉与交互没有偏离获批原型；Parity 就是一致性检查。
- **前置输入**：同一修订的批准原型、React、批准记录、流程/状态/viewport 清单及可用浏览器。

```text
沿用公共约束。单独使用 $prototype-parity-review，只读 {{HTML目录}}、{{React目录}}、{{批准记录}}。
在 {{原型URL}} 与 {{ReactURL}} 的相同 viewport/数据/身份下，实际比较 {{页面与流程清单}} 的视觉和交互。
只向 {{Parity报告路径}} 写覆盖、偏差和原始截图/步骤证据；证据不足如实标未验证，不推断一致。
停在报告和人工处理意见处；不修改产品或自动接受 PASS_WITH_NOTES。
```

- **产物与检查点**：如 `docs/reviews/*-prototype-parity.md`；报告须覆盖确认框、提交中、失败与成功等获批状态，而非只比首页截图。见 [Parity 教学报告](../examples/kubernetes-deployment-restart/03-parity/prototype-parity.md)。 [复查 S04 产物](../references/stage-rubrics.md#s04)
- **完成条件与审核角色**：沿用 [Full Track §4](../workflows/full.md#s04)：`PASS`，或由人接受 `PASS_WITH_NOTES`；`FAIL` 退回。原型审核人判断偏差，AI 不代替接受。
- **失败处理 / 下一步**：回 S03 修复后重跑 Parity；无法验证见 [T06](09-troubleshooting.md#t06)，通过后进入 S05。

## 第三组：先草案，再确认架构

<a id="s05"></a>

### S05 提取能力候选（Architecture Draft）

- **目标**：由 Mock 提取有证据的后端能力，先保留草案（Draft）。
- **前置输入**：React Mock、Parity 结论、已知运行约束、已有基础设施。

```text
沿用公共约束。第一次调用 $stack-selector，读取 {{ReactMock路径}}、{{Parity报告}} 与 {{已知约束文件}}。
只生成 {{Draft路径}}：列出 API/数据/外部操作证据、最小暂定组件、排除项、升级条件和 Grill 开放问题。
每个组件说明依据；UI 有进度条不能直接推出 Worker。写明“完成 Grill 后再 Finalize”，随后停手，不生成 Final 或 Spec。
```

- **产物与检查点**：如 `docs/plans/*-stack-selection.draft.md`；见 [Draft 示例](../examples/kubernetes-deployment-restart/04-architecture/stack-selection.draft.md)。检查每个技术建议有能力或约束依据，未知项没有被写成事实。 [复查 S05 产物](../references/stage-rubrics.md#s05)
- **完成条件与审核角色**：按 [Full Track §5](../workflows/full.md#s05)，Draft 明确需 Grill 后再 Finalize，不进入 SDD；架构/维护负责人核对问题清单。
- **失败处理 / 下一步**：缺 Mock 证据回 S03，约束缺口留给 S06，不能靠补组件掩盖未知。

<a id="s06"></a>

### S06 由人确认关键约束（Grill）

- **目标**：Grill 是追问并核实运行约束，把假设变成可追溯决定。
- **前置输入**：S05 同一 Draft 的开放问题，以及能回答部署、安全、可靠性问题的人员。

```text
沿用公共约束。读取 {{Draft路径}}，用 $grilling 询问 {{约束确认人}}。从会改变架构的一项 {{关键未知项}} 开始，每次一问，收到本人回答再继续。
引用已有决定，只追问与草案有关的部署、权限、重试或恢复等未知约束；需要沉淀项目术语或架构决策记录时再用 $domain-modeling。
只在 {{决策记录路径}} 区分已确认事实、来源、待确认项和架构影响。无人能确认就保留未知并停手，不代答、不进入 Final。
```

- **产物与检查点**：决策记录或 ADR（架构决策记录）；如 [Grill 示例](../examples/kubernetes-deployment-restart/04-architecture/grill-decisions.md)。检查谁确认、确认了什么、影响哪条架构建议。 [复查 S06 产物](../references/stage-rubrics.md#s06)
- **完成条件与审核角色**：按 [Full Track §6](../workflows/full.md#s06)，会改变架构的关键约束由人确认；部署/安全/业务负责人回答各自有权确认的问题。
- **失败处理 / 下一步**：事实不足保持 Draft，交给对应负责人；约束已确认才到 S07。

<a id="s07"></a>

### S07 用同一草案形成定稿（Architecture Final）

- **目标**：让组件、部署单元、安全与可靠性选择都能回指确认结果。
- **前置输入**：S05 同一 Draft、S06 决策及其确认记录。

```text
沿用公共约束。第二次调用 $stack-selector，只消费 {{同一Draft路径}} 与 {{Grill决策路径}}。
逐项映射决策，复查组件、部署、安全/可靠性基线、排除项和升级条件，写入 {{Final路径}}。
关键未知项仍存在则保持 Draft 并列缺口；不伪造 Final。输出供 {{架构负责人}} 复核后停手，不提前生成 Spec。
```

- **产物与检查点**：如 `docs/plans/*-stack-selection.md`；见 [Final 示例](../examples/kubernetes-deployment-restart/04-architecture/stack-selection.md)。核对是否消费同一 Draft，而非另起一套未经确认的架构。 [复查 S07 产物](../references/stage-rubrics.md#s07)
- **完成条件与审核角色**：沿用 [Full Track §7](../workflows/full.md#s07)，关键未知项存在时保持 Draft；架构负责人复核决策映射。
- **失败处理 / 下一步**：新增或矛盾约束回 S06 再 Finalize；输入齐全后到 S08。

## 第四组：Spec、Ticket 与单个切片实现

<a id="s08"></a>

### S08 写可测试规格（SDD / Spec）

- **目标**：SDD 是规格驱动开发，Spec 是明确行为、边界与验收的规格文档。
- **前置输入**：获批原型、Architecture Final、已确认决策、目标项目规范。

```text
沿用公共约束。用 $to-spec 读取 {{原型与批准记录}}、{{ArchitectureFinal}}、{{决策记录}}。先和 {{负责人}} 确认测试的公共接口，再只写 {{Spec路径}}。
仅在项目缺少任务跟踪配置时用 $setup-matt-pocock-skills 选择 Local Markdown，把这次练习留在已授权的本地目录。
定义范围/非目标、功能、API/数据、状态/错误、授权/审计/可观测性、失败行为、测试 seam 和逐条验收条件，并回指来源。
说明在哪个接口观察行为，以及测试时怎样隔离真实外部依赖。缺 Final、关键约束或权限就停手列缺口，不脑补。
交付待审 Spec，等待 {{范围风险与验收确认人}} 确认；不要自写“已批准”，不要实现代码。
```

- **产物与检查点**：Spec 草案及真实人工确认后形成的批准记录；参考 [Restart Spec](../examples/kubernetes-deployment-restart/05-spec/deployment-restart.spec.md)。检查“失败返回什么、是否可能已执行、如何核验”有明确验收，不只写 happy path（正常成功路径）。 [复查 S08 产物](../references/stage-rubrics.md#s08)
- **完成条件与审核角色**：按 [Full Track §8](../workflows/full.md#s08)，范围、风险与验收条件由人确认；需求负责人、维护负责人及相关风险负责人按职责审核。
- **失败处理 / 下一步**：缺输入见 [T03](09-troubleshooting.md#t03)；Spec 无法测试回到 seam 和验收条件，批准后到 S09。

<a id="s09"></a>

### S09 拆成纵向任务（Tickets）

- **目标**：一个 Ticket 交付一个能独立验证的用户价值，避免按数据库/API/页面横拆。
- **前置输入**：已批准 Spec、确认记录、项目任务格式和依赖。

```text
沿用公共约束。使用 $to-tickets 读取 {{已批准Spec}} 与 {{批准记录}}，沿用项目本地跟踪配置；如仍缺配置才调用 $setup-matt-pocock-skills 选择 Local Markdown。
每项列目标、Spec条款、输入、允许范围、非目标、依赖、验收与验证方式，保持一个 Ticket 一个主要上下文。
例如“用户提交一次操作并看到可解释结果”，而非单独“建表”。缺批准或契约不可测试就停手退回 Spec。
先展示拆分依据与依赖顺序；等 {{Ticket审核人}} 确认切片粒度及阻塞关系后，再将任务写入 {{Ticket目录}}，停在实施前。
```

- **产物与检查点**：本地 Markdown Ticket 或 GitHub Issue。参照 [Restart Ticket 1](../examples/kubernetes-deployment-restart/06-tickets/ticket-01.md) 和 [Ticket 2](../examples/kubernetes-deployment-restart/06-tickets/ticket-02.md)，逐项核对可见结果、依赖和可失败的验收步骤。 [复查 S09 产物](../references/stage-rubrics.md#s09)
- **完成条件与审核角色**：按 [Full Track §9](../workflows/full.md#s09)，每项可在独立上下文完成和验证；项目维护人与实现者核对切片及依赖。
- **失败处理 / 下一步**：Ticket 过大重拆，Spec 矛盾回 S08；选一个依赖满足的 Ticket 开新会话进入 S10。

<a id="s10"></a>

### S10 一个 Ticket 一个会话（TDD）

- **目标**：TDD 是测试驱动开发，用 RED → GREEN → REFACTOR → VERIFY（先失败、再通过、整理、复验）约束实现。
- **前置输入**：一个 Ticket、批准 Spec、必要 ADR、项目索引、已确认测试环境与命令。

```text
沿用公共约束。新会话读取 {{单个Ticket}}、{{Spec}}、{{必要ADR}} 与 AGENTS.md 索引，只修改 {{Ticket允许文件范围}}。
使用 $superpowers:test-driven-development，先写会因目标行为缺失而失败的测试并保存 RED 原始结果，再做最小实现。GREEN 后整理代码并复验，执行 {{验收测试/单元测试/lint/build命令}}。
测试外部操作使用 Spec 规定的 seam，不触达生产。记录每步命令、修订、输出和退出码，逐条映射 Ticket 验收。
关键条件未通过或环境不可用就记录失败/未验证并停手；完成当前 Ticket 后交接，不顺手做下一项，不代替人工验收。
```

- **产物与检查点**：可定位的[实现](../examples/kubernetes-deployment-restart/02-react-mock/mock.mjs)、[测试](../examples/kubernetes-deployment-restart/02-react-mock/mock.test.mjs)和 [RED / GREEN / 复验记录](../examples/kubernetes-deployment-restart/07-implementation/tdd-evidence.md)。确认断言会因同一目标行为的缺失而失败。 [复查 S10 产物](../references/stage-rubrics.md#s10)
- **完成条件与审核角色**：沿用 [Full Track §10](../workflows/full.md#s10)：验收测试、单元测试、lint/build 与 Ticket 条件通过；实现者保存证据，维护者核对验收映射。
- **失败处理 / 下一步**：区分产品、测试、环境与权限问题，不改弱验收使测试变绿；缺证据见 [T06](09-troubleshooting.md#t06)。完成后准备可定位的比较点进入 S11。

## 第五组：代码与运行风险分别审查

<a id="s11"></a>

### S11 审规范与规格符合度（Code Review）

- **目标**：沿 Standards（仓库规范）与 Spec（行为规格）两条轴审查。
- **前置输入**：有效固定比较点、明确目标修订、非空的已提交差异、规范、批准 Spec 及测试证据。若尚未提交，按项目已获授权的提交流程准备，不让审查替你提交。

```text
沿用公共约束。使用 $code-review，只读比较 {{固定base提交}} 到 {{目标head提交}}，读取 {{Spec}}、AGENTS.md索引与 {{测试证据}}。
先确认两端可解析、比较范围准确且已提交diff非空；工作区改动另列为未覆盖，不悄悄纳入或自动提交。
按 Standards/Spec 两轴，在 {{Review报告路径}} 写有文件位置、严重级别和证据的发现，并关联阻断问题。
基点无效、diff为空或输入不足就停手说明，不生成“无问题/通过”；报告完成即停，不修改代码。
```

- **产物与检查点**：[代码审查报告](../examples/kubernetes-deployment-restart/08-review/code-review.md)应注明固定基点、候选修订、规范与 Spec 两路检查的发现、影响和证据。 [复查 S11 产物](../references/stage-rubrics.md#s11)
- **完成条件与审核角色**：按 [Full Track §11](../workflows/full.md#s11) 解决阻断问题；代码审核人与维护者确认修复及必要复验，AI 不以空差异证明实现正确。
- **失败处理 / 下一步**：基点/空差异见 [T04](09-troubleshooting.md#t04)；设计问题回对应 Spec 或架构决定，修复后重审，阻断关闭后到 S12。

<a id="s12"></a>

### S12 检查运行与操作安全（Ops Readiness Review）

- **目标**：检查具体产品运行与操作风险，避免“代码能跑”替代生产证据。
- **前置输入**：架构、Spec、代码、部署配置、测试原始证据及 S11 报告。

```text
沿用公共约束。使用 $ops-readiness-review，只读 {{架构/Spec/代码/部署路径}} 与 {{原始验证证据}}。
按项目适用风险检查危险操作、鉴权、审计、Secret、远程执行/K8s、任务、API、可观测性、数据、部署与恢复；标明不适用及证据不足的理由。
仅在 {{Ops报告路径}} 输出有依据的结论、风险、核验建议及责任人；遵循 Full Track 和 Ops Readiness 的状态定义。
如建议需生产操作、真实变更或缺权限就停在方案，不执行；不得自己接受风险或把缺证据写成 PASS。
```

- **产物与检查点**：如 `docs/reviews/*-ops-readiness.md`；见 [Ops 教学报告](../examples/kubernetes-deployment-restart/08-review/ops-readiness.md)。检查危险操作的授权、审计、失败与恢复各有何种证据，而非只有设计承诺。 [复查 S12 产物](../references/stage-rubrics.md#s12)
- **完成条件与审核角色**：引用 [Full Track §12](../workflows/full.md#s12) 与 [Ops Readiness](06-ops-readiness.md)：无未修复且未获授权接受的主要风险，关键控制有足够证据；有权的风险负责人作风险决定。
- **失败处理 / 下一步**：失败拆有边界的修复 Ticket 后重审；结果与原始输出冲突见 [T05](09-troubleshooting.md#t05)，未知操作结果见 [T07](09-troubleshooting.md#t07)。满足该阶段门禁后到 S13。

## 第六组：端到端测试与人工验收

<a id="s13"></a>

### S13 先批计划，再做端到端测试（E2E）

- **目标**：E2E 在真实浏览器验证完整用户流程，不能仅检查按钮或文本存在。
- **前置输入**：Spec、Tickets、审查结果、可用环境、测试身份/数据，以及明确允许的操作边界。

```text
沿用公共约束。使用 $playwright-e2e-debug-report 读取 {{Spec/Tickets/审查路径}}，先只写 {{test-task路径}}。
列出 {{测试环境URL}} 的完整Workflow、身份/数据、正反例、影响范围、证据与停手条件；等待 {{测试批准人}} 明确批准范围和权限。
核对实际已有授权的来源和范围；有权后再用 $playwright-cli 执行计划的浏览器步骤，向 {{报告与证据目录}} 保存步骤、原始输出及 PASS/FAIL/SKIPPED、环境限制。
权限或环境不足即停；失败先分环境/测试/产品/数据/权限，修复另需授权。不要自批计划、直接生产变更或擅自修复。
```

- **产物与检查点**：[计划及批准范围](../examples/kubernetes-deployment-restart/09-e2e/test-task.md)、[实际步骤、环境和浏览器证据](../examples/kubernetes-deployment-restart/09-e2e/test-report.md)。按用例核对预期、观测与结果分类：取消后零提交、接受后显示已提交、结果未知时保留 ID 并阻止重复提交。 [复查 S13 产物](../references/stage-rubrics.md#s13)
- **完成条件与审核角色**：沿用 [Full Track §13](../workflows/full.md#s13)，破坏性或生产操作有明确权限，范围和结果由人确认；测试批准人和环境负责人确认边界及结果。
- **失败处理 / 下一步**：`SKIPPED` 不能当 `PASS`，见 [T06](09-troubleshooting.md#t06)；失败分类后按授权处理。带真实结果交 S14，由人决定是否补充或退回。

<a id="s14"></a>

### S14 由人关闭业务闭环（Human Acceptance）

- **目标**：确认解决了最初的问题，失败行为、风险与运行成本可接受。
- **前置输入**：所有产物及修订、审查和测试证据、未验证范围、待处理风险、原始问题说明。

```text
沿用公共约束。只读 {{产物与证据索引}}、{{原始问题说明}}，在 {{人工验收记录路径}} 整理给 {{业务与风险验收人}} 的待审材料。
逐项关联产品意图、用户价值、失败行为、风险、运行成本及未验证范围；明确教学或局部验证不能替具体产品放行。
等待人作“接受、补充或退回”的决定，再记录对象、范围、依据与真实审核人；没有决定则停在待审，不代签、不部署。
```

- **产物与检查点**：人工验收决定，示例 [验收记录](../examples/kubernetes-deployment-restart/10-acceptance/human-acceptance.md)。检查决定是否明确接受对象及范围，未验证项没有被“全部通过”遮住。 [复查 S14 产物](../references/stage-rubrics.md#s14)
- **完成条件与审核角色**：按 [Full Track §14](../workflows/full.md#s14)，只有人能关闭最终闭环；真实业务使用者与有权的风险负责人承担相应判断。
- **失败处理 / 下一步**：补充或退回按 Full Track 回退规则处理；业务接受不自动授权上线，发布和生产变更仍需目标项目规定的依据与权限，见 [T09](09-troubleshooting.md#t09)。

## 继续阅读与定位

- [问题定位](09-troubleshooting.md)：九类流程采用问题，只读检查、停手与求助人。
- [FAQ](08-faq.md)：术语、人工责任以及为何通过不等于可上线。
- [Prototype First](02-prototype-first.md)、[Architecture and SDD](03-architecture-and-sdd.md)、[Context Engineering](04-context-engineering.md)、[TDD](05-tdd-and-feedback-loop.md)：阶段深潜。
- [Lightweight Track](../workflows/lightweight.md)、[Full Track](../workflows/full.md)：路径、门禁与回退的权威定义。
- [Artifact Map](../references/artifacts.md) 与 [Skill Map](../references/skills.md)：产物及执行能力查表。
