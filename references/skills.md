# Skill Map

从 [Full Track](../workflows/full.md) 找当前阶段，从 [Quick Start](../docs/01-quick-start.md) 复制提示词。下表直达技能库的固定入口；S02 由真实使用者确认原型，S14 由业务使用者和风险负责人验收，这两个节点都可以由 AI 整理材料。

## 阶段与调用关系

| 使用时机 | 技能入口 | 输入、配合方式与交接 |
|---|---|---|
| S00 探索 | <a id="devops-brainstorming"></a>[devops-brainstorming](https://github.com/Dusk-996/skills-manager-backup/blob/cb43b9a4329fdda4b57c5323374ad1fc74c68b10/devops-brainstorming/SKILL.md) | 已有候选方向且有假设要质询时用 Grill，范围需收敛时用 Refinement。讨论可结束于风险清单。进入原型由人确认目标。 |
| S00 正式实施设计的后继 | <a id="writing-plans"></a>[writing-plans](https://github.com/Dusk-996/skills-manager-backup/blob/cb43b9a4329fdda4b57c5323374ad1fc74c68b10/external-skills/superpowers/skills/writing-plans/SKILL.md) | 面向实施的设计获批并按技能要求落盘后，原生出口交给 writing-plans 制定计划。原型探索路径见 [S00](../workflows/full.md#s00)。 |
| S01 原型 | <a id="frontend-design"></a>[frontend-design](https://github.com/Dusk-996/skills-manager-backup/blob/cb43b9a4329fdda4b57c5323374ad1fc74c68b10/frontend-design/SKILL.md) | 从零做 HTML 原型时使用。已有可复用原型则调整关键流程和 Mock 数据。 |
| S03 React + Mock | <a id="html-to-mui-react"></a>[html-to-mui-react](https://github.com/Dusk-996/skills-manager-backup/blob/cb43b9a4329fdda4b57c5323374ad1fc74c68b10/html-to-mui-react/SKILL.md) | 消费 S02 批准的页面、流程和视口；完成转换后单独发起 S04。 |
| S04 原型一致性 | <a id="prototype-parity-review"></a>[prototype-parity-review](https://github.com/Dusk-996/skills-manager-backup/blob/cb43b9a4329fdda4b57c5323374ad1fc74c68b10/prototype-parity-review/SKILL.md) | 在真实浏览器比较关键操作、视觉和状态；出现有条件通过的偏差时交给人决定。 |
| S05 / S07 架构 | <a id="stack-selector"></a>[stack-selector](https://github.com/Dusk-996/skills-manager-backup/blob/cb43b9a4329fdda4b57c5323374ad1fc74c68b10/stack-selector/SKILL.md) | 首次从 Mock 生成草案。取得 S06 人工决定后，第二次读取同一草案定稿。 |
| S06 运行约束 | <a id="grilling"></a>[grilling](https://github.com/Dusk-996/skills-manager-backup/blob/cb43b9a4329fdda4b57c5323374ad1fc74c68b10/grilling/SKILL.md) | 围绕草案的开放问题逐项询问。有权人员给出会影响架构的决定。此入口已整合旧的 grill-me 和 grill-with-docs。 |
| S06 记录术语或决策 | <a id="domain-modeling"></a>[domain-modeling](https://github.com/Dusk-996/skills-manager-backup/blob/cb43b9a4329fdda4b57c5323374ad1fc74c68b10/domain-modeling/SKILL.md) | 需要同步维护领域词汇表或架构决策记录（ADR）时，与 grilling 配合。 |
| S08 规格 | <a id="to-spec"></a>[to-spec](https://github.com/Dusk-996/skills-manager-backup/blob/cb43b9a4329fdda4b57c5323374ad1fc74c68b10/to-spec/SKILL.md) | 确认测试边界后形成 Spec；按项目约定登记，范围和验收条件由人确认。 |
| S09 任务 | <a id="to-tickets"></a>[to-tickets](https://github.com/Dusk-996/skills-manager-backup/blob/cb43b9a4329fdda4b57c5323374ad1fc74c68b10/to-tickets/SKILL.md) | 基于批准的 Spec 提出纵向任务，确认拆分与阻塞关系后写入项目跟踪系统。 |
| S08 / S09 / S11 首次配置 | <a id="setup-matt-pocock-skills"></a>[setup-matt-pocock-skills](https://github.com/Dusk-996/skills-manager-backup/blob/cb43b9a4329fdda4b57c5323374ad1fc74c68b10/setup-matt-pocock-skills/SKILL.md) | 缺少任务跟踪等必需配置时使用。现有配置优先；本地练习选 Local Markdown。 |
| S10 实现 | <a id="test-driven-development"></a>[test-driven-development](https://github.com/Dusk-996/skills-manager-backup/blob/cb43b9a4329fdda4b57c5323374ad1fc74c68b10/external-skills/superpowers/skills/test-driven-development/SKILL.md) | 在确认的 Ticket 上做红→绿→重构和复验。调用名用 Superpowers 命名空间，见下文。 |
| S11 代码审查 | <a id="code-review"></a>[code-review](https://github.com/Dusk-996/skills-manager-backup/blob/cb43b9a4329fdda4b57c5323374ad1fc74c68b10/code-review/SKILL.md) | 向两个并行审查者提供有效基点及非空的已提交差异，分别检查仓库规范、Spec 符合度。 |
| S12 运维就绪 | <a id="ops-readiness-review"></a>[ops-readiness-review](https://github.com/Dusk-996/skills-manager-backup/blob/cb43b9a4329fdda4b57c5323374ad1fc74c68b10/ops-readiness-review/SKILL.md) | 检查适用运行风险及证据，风险接受交给有权人员。 |
| S13 E2E | <a id="playwright-e2e-debug-report"></a>[playwright-e2e-debug-report](https://github.com/Dusk-996/skills-manager-backup/blob/cb43b9a4329fdda4b57c5323374ad1fc74c68b10/playwright-e2e-debug-report/SKILL.md) | 先组织待批测试计划；获准后编排浏览器操作、问题分流与报告。 |
| S13 浏览器执行 | <a id="playwright-cli"></a>[playwright-cli](https://github.com/Dusk-996/skills-manager-backup/blob/cb43b9a4329fdda4b57c5323374ad1fc74c68b10/playwright-cli/SKILL.md) | 获批测试计划中的实际浏览器操作使用此工具，保存原始证据。 |
| 各阶段交付后复查 | <a id="stage-artifact-review"></a>[stage-artifact-review](https://github.com/Dusk-996/skills-manager-backup/blob/cb43b9a4329fdda4b57c5323374ad1fc74c68b10/stage-artifact-review/SKILL.md) | 评一个版本的实物，读取[阶段评分细则](stage-rubrics.md)，返回分数、证据和建议。由人决定是否修订或发起复评。此项独立于各阶段生产技能。 |

Superpowers 包内条目的源名称分别是 `test-driven-development` 和 `writing-plans`。采用 Superpowers 命名空间的运行时显式使用 `$superpowers:test-driven-development` 和 `$superpowers:writing-plans`。S10 选择前者，因为它在绿色测试保护下重构。技能库另有 `tdd`，其重构约定在审查阶段。

## 固定来源与复核

技能来源为 [Dusk-996/skills-manager-backup 的固定提交](https://github.com/Dusk-996/skills-manager-backup/tree/cb43b9a4329fdda4b57c5323374ad1fc74c68b10)，修订为 `cb43b9a4329fdda4b57c5323374ad1fc74c68b10`。[skill-lock.json](skill-lock.json) 记录 17 个入口、对应目录内的 89 个资源文件，以及 6 个许可或归属条目。锁定范围包括模板、测试材料和说明文档。运行环境、浏览器二进制和人工批准需要在使用时另行核对。

按提交中 Git blob 的原始字节计算 SHA-256，避免 Windows 检出时的换行转换影响摘要。已有本地技能仓库时，可在其根目录用 **Bash / Git Bash** 抽查一个入口，和锁中同一路径的 `sha256` 对照：

```bash
git cat-file blob cb43b9a4329fdda4b57c5323374ad1fc74c68b10:grilling/SKILL.md | sha256sum
```

许可和归属按来源核对：

- `frontend-design` 附 Apache-2.0 文本，入口另记 ECC 检查表来源；Superpowers 包附 MIT 许可与作者署名。[Frontend 许可](https://github.com/Dusk-996/skills-manager-backup/blob/cb43b9a4329fdda4b57c5323374ad1fc74c68b10/frontend-design/LICENSE.txt) · [Superpowers 许可](https://github.com/Dusk-996/skills-manager-backup/blob/cb43b9a4329fdda4b57c5323374ad1fc74c68b10/external-skills/superpowers/LICENSE)
- `prototype-parity-review` 和 `ops-readiness-review` 的 README 保留了原作者的 MIT 声明，其指向原仓库根许可的相对路径在此备份里缺少目标。锁中保留两份声明的摘要，其他技能的适用条款按其原来源核实。[Parity 归属](https://github.com/Dusk-996/skills-manager-backup/blob/cb43b9a4329fdda4b57c5323374ad1fc74c68b10/prototype-parity-review/README.md) · [Ops 归属](https://github.com/Dusk-996/skills-manager-backup/blob/cb43b9a4329fdda4b57c5323374ad1fc74c68b10/ops-readiness-review/README.md) · [备份的恢复与许可说明](https://github.com/Dusk-996/skills-manager-backup/blob/cb43b9a4329fdda4b57c5323374ad1fc74c68b10/docs/RESTORE.md)

## 本地采用

1. 取得固定提交或对应的离线包，核对入口和资源摘要。显式点名所采用的技能，记录实际加载路径，以便识别同名的其他版本。
2. 本地练习使用 Local Markdown tracker。Spec 和 Tickets 分别放在 `.scratch/<feature>/spec.md` 和 `.scratch/<feature>/issues/<NN>-<slug>.md`。已有跟踪系统时依项目约定执行。
3. 记录实际命令、输出、人工决定和未验证项。S11 的三点 diff 覆盖比较基点与 HEAD 的已提交变更；S13 的浏览器环境和允许操作来自已批准的测试计划。
4. 对照版本阅读验证记录。[2026-11-15 的历史记录](../docs/reviews/2026-11-15-reuse-validation.md) 对应此前使用的技能库和修订。
