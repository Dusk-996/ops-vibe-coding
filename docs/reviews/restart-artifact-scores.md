# Restart 阶段产物实评

2026-11-22 · 首次评价 · Full Track 教学案例。复查按技能库 [stage-artifact-review @ 9dad867](https://github.com/Dusk-996/skills-manager-backup/blob/9dad86743b470bf1cb2f3d5de907239d85104003/stage-artifact-review/SKILL.md) 的报告格式执行。规则为[阶段细则 1.0](../../references/stage-rubrics.md)，Git blob 为 `5d4801fb68c1661c89cf051b85992787b34e4291`。评审只读产物及原始依据。

## S00 · 原型目标简报

本次出口是单目标、本地模拟的原型目标。产物为 [Restart README 的 S00 节](../../examples/kubernetes-deployment-restart/README.md#s00-从想法到原型目标)，本次读取的 README Git blob 为 `2774613b46868195ab0bcfab5413ca98204f322c`。可与[上一版案例的问题与范围](https://github.com/Dusk-996/ops-vibe-coding/blob/daee2c0db3b5871cd36d763491f0914ab1e63de7/examples/kubernetes-deployment-restart/README.md#s00-从想法到原型目标)对照。这里评的是教学设定下的可用性；人的实际决定见阶段状态。

| 维度 | 分数 | 判据和证据位置 | 缺口与处置 |
|---|---:|---|---|
| C1 输入与范围 | 2 | 原版目标为在详情页发起一次重启并辨认提交结果。新版首段固定 `lab / staging / checkout`，S00 的“候选方向”保留单目标并排除批量、自动重试和 rollout 跟踪。 | 无扣分。 |
| C2 结论依据 | 2 | “使用者与痛点”明确把命令操作和重发风险标为教学设定、待实际使用者核对。“候选方向”说明选页面的理由，结尾指回真实体验决定。 | 无扣分。 |
| C3 下游接手 | 2 | “可观察的成功标准”明确 S01 做确认框及结果面板，还给出只做风险评估时的结束条件。 | 无扣分。 |
| A 使用者与问题 | 2 | 值班人对单个 Deployment 发起 Restart，当前靠命令及人工查结果，超时无法确认是否已执行。这些信息足以还原练习情境。 | 无扣分。 |
| B 可核验的出口 | 2 | 在同一目标切换三个样本，分别观察取消后零请求、接受且记账后的“请求已提交”、超时后保留 ID 并阻止重发。每条都有能观察到的反例。 | 无扣分。 |

**原始 10/10，最终 10/10，产物合格。** B 有可观察的验证情境，原文标明教学选择，未触发 S00 封顶。教学样例可以沿此目标制作 S01；真实项目中的场景选择仍需需求提出人决定，原型体验和转换批准另由实际使用者在 [S02](../../examples/kubernetes-deployment-restart/01-prototype/approval.md) 确认。

## S13 · 本地浏览器测试报告与证据

本次交付的是[测试计划](../../examples/kubernetes-deployment-restart/09-e2e/test-task.md)、[测试报告](../../examples/kubernetes-deployment-restart/09-e2e/test-report.md)以及报告引用的浏览器记录。评审固定在工作流仓库提交 `79650dbaec42aa2ff9f15a405a56058487819a94`，对应受测实现 `dbfd4faee855737ce14d81524da10c313e40df5a`。上游范围是计划中的单目标、回环地址、合成 ID 和模拟变更，含维护者补充批准的两项回归。

| 维度 | 分数 | 判据和证据位置 | 缺口与处置 |
|---|---:|---|---|
| C1 输入与范围 | 2 | 计划明确 `lab / staging / checkout`、模拟环境和两次授权。报告首段给出同一目标、获批用例、实现修订和运行时间，末段列明真实 RBAC、审计、恢复等未验证项。 | 无扣分。 |
| C2 结论依据 | 2 | 核对 [run.json](../../examples/kubernetes-deployment-restart/09-e2e/evidence/run.json)：`cancel` 的调用列表为空、计数为 0；`accepted` 同一 ID 的 POST 200 和 GET 200、计数为 1。`conflict-windows` 两笔不同 ID 分别返回 504、409，计数仍为 1。[独立 CLI 回执](../../examples/kubernetes-deployment-restart/09-e2e/evidence/cli-run.json)给出另一条实际路径的 ID 和结果。 | 无扣分。 |
| C3 下游接手 | 2 | 报告“复现”给出构建、单测、浏览器命令、证据位置和退出码，还给出两条修复前的失败记录。末段将遗留验证交给运维风险审查和 S14 的相应责任人。 | 无扣分。 |
| A 执行边界 | 2 | 逐项对照计划与报告可匹配取消、已提交、超时、拒绝、审计未确认及两项新增回归。[浏览器断言](../../examples/kubernetes-deployment-restart/02-react-mock/browser-test.mjs)中的 fixture 将服务绑定在回环地址并检查外部请求；静态原型刷新用例的 API 事件为空。 | 无扣分。 |
| B 结果可追溯 | 2 | 报告七行给出操作、预期、实际和结果，均能对应原始 JSON 的同名用例。超时后原 ID 连续只读查询，[冲突截图](../../examples/kubernetes-deployment-restart/09-e2e/evidence/conflict.png)与对应断言区分两笔 ID。[修复前的失败记录](../../examples/kubernetes-deployment-restart/07-implementation/red-conflict-windows.json)保留当时的 FAIL 和未执行项的 SKIPPED，最终修订七项均已执行。 | 无扣分。 |

**原始 10/10，最终 10/10，产物合格。** 所评证据均在批准范围内，七个本地用例的状态可核对，未触发 S13 封顶。测试结果为本机七项通过。范围已由维护者批准，报告可交实际业务使用者及风险负责人审阅；[S14 的业务验收与风险决定](../../examples/kubernetes-deployment-restart/10-acceptance/human-acceptance.md)仍待确认。
