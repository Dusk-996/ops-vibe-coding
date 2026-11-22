# 阶段产物与 Restart 验收清单 · 2026-11-22

本次覆盖的是工作流和本机教学交付。评分约定见[规则 1.0](../../references/stage-rubrics.md)，生产与复查技能分工见 [Skill Map](../../references/skills.md)。下表“核验方式”说明实际检查到哪一步，门禁由相应角色判断。S02 未获实际使用者批准，后续本地材料在教学范围独立运行，整条业务流程仍待验收。

| 节点 | 实物与核验方式 | 当前结论或交接 |
|---|---|---|
| S00 | [Restart 简报](../../examples/kubernetes-deployment-restart/README.md#s00-从想法到原型目标)，按新 Skill [实际试评](restart-artifact-scores.md) | 教学选定单目标；真实使用者的选择待核对。风险摘要和正式设计另有[校准样本](calibration/stage-artifacts-v1.md)。 |
| S01 | [HTML](../../examples/kubernetes-deployment-restart/01-prototype/index.html)，浏览器核对 | 能实际体验目标确认和结果状态。 |
| S02 | [对应原型的决定记录](../../examples/kubernetes-deployment-restart/01-prototype/approval.md)，静态核对 | 待真实使用者确认。 |
| S03 | [React + Mock](../../examples/kubernetes-deployment-restart/02-react-mock/contract.md)，构建、启动、请求回执 | 本地可运行。 |
| S04 | [对照报告](../../examples/kubernetes-deployment-restart/03-parity/prototype-parity.md)，浏览器与两种视口截图 | 技术预检 PRECHECK；正式一致性结论待 S02 批准后再核对。 |
| S05 | [草案](../../examples/kubernetes-deployment-restart/04-architecture/stack-selection.draft.md)，静态核对 | Q1–Q3 追问提交语义、解锁和持久存储。 |
| S06 | [Q1–Q3 记录](../../examples/kubernetes-deployment-restart/04-architecture/grill-decisions.md)，静态核对 | 教学回答；生产运行责任人待确认。 |
| S07 | [定稿样本](../../examples/kubernetes-deployment-restart/04-architecture/stack-selection.md)，由问题号反查草案及 S06 | 定稿描述目标架构。 |
| S08 | [Spec](../../examples/kubernetes-deployment-restart/05-spec/deployment-restart.spec.md)，静态核对 R1–R3 和失败边界 | 可分别追到本地行为与真实系统待验证项。 |
| S09 | [T01](../../examples/kubernetes-deployment-restart/06-tickets/ticket-01.md)、[T02](../../examples/kubernetes-deployment-restart/06-tickets/ticket-02.md)，静态核对验收与依赖 | T01 提供操作 ID，T02 消费和核验同一条记录。 |
| S10 | [TDD 记录](../../examples/kubernetes-deployment-restart/07-implementation/tdd-evidence.md)，实际红灯、实现与复验 | 本地模拟提交计数、重放、占用与状态可断言。 |
| S11 | [固定差异双轴审查](../../examples/kubernetes-deployment-restart/08-review/code-review.md)，两名审查者分别看规范与 Spec | 首轮发现、修订范围和复核结论见报告。 |
| S12 | [就绪审查](../../examples/kubernetes-deployment-restart/08-review/ops-readiness.md)，检查源文件、测试与生产证据缺口 | 生产门禁 FAIL，真实 RBAC、审计持久化和恢复缺验证。 |
| S13 | [批准计划](../../examples/kubernetes-deployment-restart/09-e2e/test-task.md)、[实际报告](../../examples/kubernetes-deployment-restart/09-e2e/test-report.md)与[产物复查](restart-artifact-scores.md) | 在获准的本机环境执行，按用例核对网络事件与模拟变更计数。 |
| S14 | [待验收材料](../../examples/kubernetes-deployment-restart/10-acceptance/human-acceptance.md)，静态核对 | 业务决定和风险接受均待相应责任人。 |

## 评分与复评的实测

两名复查者分别评五个固定样本，五个合格/不合格判断相同。D5 恰好 8 分；D2 得 0 分；D3 的原始 8 分因错误标 PASS 封顶 7；D4 如实记录产品失败得 10 分。D1 的证据项相差 1 分，已据此明确“设计者选择”和“使用者现状”的举证要求。保留了[两组原始分](calibration/results-v1.md)。

显式运行 `$stage-artifact-review` 检查了同版复评、换版规则、材料未改变、整份缺件、节点未到达和无法读取。逐项报告、扣分和复验建议见[实际调用记录](calibration/skill-invocations.md)。固定技能提交为 `9dad86743b470bf1cb2f3d5de907239d85104003`。[技能 PR #3](https://github.com/Dusk-996/skills-manager-backup/pull/3)

## 生产技能与实际执行

本次在 Restart 的 S00 简报和 S13 测试包上实际执行了评分 Skill；另有校准用例。S01/S03 的交付以浏览器、构建和本地接口回执为据。S10 可追到 TDD 的失败/通过提交。S11 实际按 code-review 分两轴审查，S12 按 ops-readiness-review 检查适用风险。S13 用 Playwright Core 执行可复跑的整套用例，并用官方 playwright-cli 独立操作取消和提交。S05–S09 的 Restart 材料以交接、语义和静态核对为据。S02 和 S14 由真人决定。Skill Map 的推荐入口本身不计作调用证据。

## 图稿与静态范围

draw.io 源与 SVG 同步，导出尺寸 1058 × 2650。交互总图从同版 JSON 生成，浏览器检查通过；实际按“评分报告”定位节点并放大到 125% 核对文字、回退和人工决定。交互 HTML 的 SHA-256 为 `a5498c01d8ed83a2ccf0301b705940d2ea6b078a5bfa2e1051ef75ea8e847d46`。架构与持久状态以案例的表和契约表达，本轮调整落实到对应表格。全图只画一次“交付→评分→人工决定”的通用回路。[SVG](../diagrams/ops-vibe-coding-workflow.svg) · [交互 HTML](../ops-vibe-coding-workflow.html)

README、Full/Lite、可复制指令、主题文章、Harness、阶段锚点和产物链接共同指向同一套判据。技能索引固定 17 个入口，89 项目录资源、6 项许可或归属记录按 Git blob 原始字节核对。替换了 Restart 旧版“无应用”、模拟批准、示例 PASS 和未运行占位。本地运行和人的批准各有独立出处。先前的[只读发布巡检演练](2026-11-22-s00-workflow.md)保留原版本，其结果未计入上表。

## 本地复跑

对代码 `dbfd4fa` 在 `examples/kubernetes-deployment-restart/02-react-mock` 依次核对构建、Node 单元与真实浏览器。独立复跑于 2026-11-22 10:32 UTC 完成，`npm run build`、`npm test`、`npm run e2e` 均退出 0。6 项单元测试、7 条浏览器用例、2 项视口比较分别通过。Chrome 157.0.8103.79；与库内[同修订原始回执](../../examples/kubernetes-deployment-restart/09-e2e/evidence/run.json)的逐项结果一致。取消为零变更，双窗口获取 409 时有两次客户端 POST、仅一次模拟变更；两个视口的确认截图各自字节一致。
