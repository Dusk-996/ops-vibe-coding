# Gates and Evidence

> A gate is not a conversation result. A gate is an artifact.

门禁不是 AI 说"通过了"，而是一份可以检查、引用和追溯的工程制品。

## 这一篇解决什么问题

流程里每一步都有门禁（Prototype Review、Parity、Architecture Confirmation、Code Review、Ops Readiness、E2E、Human Acceptance）。但如果没有证据，门禁就退化成"AI 口头说通过"——不可核对、不可追溯、出了事没人说得清当时为什么放行。

## 门禁的通用形态

结合 Ops Vibe Coding 流程，典型门禁：

```text
Prototype Review       产品意图是否获批
Prototype Parity       转换是否改变已批准设计
Architecture Confirmation  关键约束是否确认
Code Review            实现是否符合规范与 Spec
Ops Readiness          运行风险是否可接受
E2E                    真实用户流程是否通过
Human Acceptance       是否解决最初的问题
```

## Gate Record 最小结构

每个门禁至少留下：

```text
Gate        门禁名称
Status      结论（使用对应 Workflow 定义的状态）
Scope       被检查的版本、环境和范围
Evidence    可定位的证据（命令、报告路径、截图路径、提交版本）
Findings    发现的问题
Risks       已接受的风险
Decision    决定（放行 / 退回 / 补充）
Next Step   下一步行动或下一阶段
Reviewer    谁做的判断
```

状态不由 Harness 重新定义。使用对应阶段的权威定义，例如：

```text
Prototype Parity   → PASS / PASS_WITH_NOTES / FAIL
Ops Readiness      → PASS / PASS_WITH_RISKS / FAIL
E2E                → PASS / FAIL / SKIPPED
```

允许 `SKIPPED`、`NOT_APPLICABLE` 或其他非通过状态时，必须记录原因、影响和下一步。具体状态以 [Full Track](../workflows/full.md) 和对应阶段文档为准。

## 怎么执行

1. 为门禁留下 Markdown Artifact；文件位置遵循 [Artifact Map](../references/artifacts.md)，小项目可以合并文件；
2. 记录检查对象、环境、命令和证据路径，确保结论可以复现；
3. AI 可以执行检查并起草报告。自动测试、build、lint 等技术结论由证据决定；产品意图、架构约束、风险接受和最终验收由人决定；
4. 未达到 Workflow 的通过条件时，按其回退规则修复或补充证据，不能由 Harness 自行降级。

## 机器可读契约门禁

Markdown Gate Record 记录判断与证据；机器可读契约负责阻止可确定的漂移。多服务项目可以按需增加：

```text
IDL validation          IDL 能解析并符合规范
Compatibility check    接口变更满足兼容策略
Service matrix check   producer / consumer / contract 引用有效
Impact evidence        受影响服务已列出并完成相应验证
```

这不是新的 Workflow 阶段，也不要求实现 Gate Engine。先复用 OpenAPI、Protobuf 等生态已有的 lint、diff 和兼容性工具，把命令及结果记录进现有 Code Review 或对应 Gate Artifact。

Service Matrix 不能取代 IDL：IDL 定义接口，矩阵定义服务之间的关系。示例见 [service-matrix.example.yaml](examples/service-matrix.example.yaml)。

示例见 [examples/gate-record.example.md](examples/gate-record.example.md)。

## 与 Workflow 的关系

门禁的位置、输入和通过条件由 [Full Track](../workflows/full.md) 定义，产物位置由 [Artifact Map](../references/artifacts.md) 定义。本目录只规定"门禁如何留下证据"，不复制或覆盖流程定义。

## 常见错误（Anti-patterns）

- **AI 说"通过了"但没有文件**：不可核对，等于没有门禁；
- **门禁结论只有一句 PASS**：没有证据和发现，后人无法判断当时依据；
- **门禁结果存在聊天记录里**：会话一丢，审计线索就丢；
- **把所有状态强行统一**：覆盖各阶段的权威语义，制造新的真相源；
- **用 YAML 重复描述整个 API**：矩阵与 IDL 双写，必然漂移；
- **SKIPPED / NOT_APPLICABLE 不说明理由**：跳过变成逃避，不是受控决策。

## 门禁与下一步

- **门禁**：每个流程门禁都有带 Evidence 的 Gate Record，FAIL 有对应修复记录；
- **下一步**：[05-feedback-and-self-refinement.md](05-feedback-and-self-refinement.md)，把门禁和纠错中发现的教训沉淀为团队资产。

## 可追溯证据与人工决定

每项主张记录：对象提交/未提交差异、规则与 Skill 修订、环境/范围、时间与时区、执行者/来源、方法与原始结果位置。命令另记退出码与原始输出；人工步骤记检查人、依据及实际确认。

区分 DOCUMENTED（仅声明）、STATIC（源文件可见）、实际工具执行及产品 RUNTIME_VERIFIED。语义相称优先于标签强弱：字段齐全、文件摘要或退出0均不证明整个领域有效。报告与来源冲突时保持冲突，复核后再判断；旧证据沿用需影响分析。

教学记录、构造反例、草案与实际证据分开。无执行结果写 NOT_EXECUTED；有执行失败保存失败；不把 SKIPPED 或缺输入转成 PASS。反例的原始冲突证据对执行者可见，只有反例位置索引和判定答案放复核包。

风险接受记录必须含风险编号、批准人和授权角色、依据、适用目标/环境/条件、残余影响、复审触发条件；临时豁免另有期限。范围备注不等于生产风险接受。状态条件引用 [Ops Readiness](../docs/06-ops-readiness.md#状态判定)，Harness 不另立状态语义。

当前进度与原始门禁状态写入 [交接记录](examples/handoff.example.md)。遇到输入、证据、权限或责任人缺失，记录所缺内容、下一步及求助角色；不得让新会话凭记忆补齐批准。

## 关联阶段评分

在同一条交接中分别记产物及规则版本、评分报告、原始分与最终分，以及门禁状态和决定来源。规则见[阶段判据](../references/stage-rubrics.md)。同一个失败可以同时对应一份合格的测试报告和一个退回修复的产品。
