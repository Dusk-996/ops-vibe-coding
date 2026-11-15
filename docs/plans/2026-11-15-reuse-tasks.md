# 任务：生产复用与新人采用基线 v3

> 使用 executing-plans 逐项实施；设计：[reuse-design](2026-11-15-reuse-design.md)。
> 执行日期：2026-11-15。所有 [x] 只表示该行声明的产物已核对，不表示产品已通过生产验收。

## 执行协议

每项先读取对应源文件→按设计修改→检查 diff 与引用→记录验证→标记；只改允许文件，不复制外部 Skill 实现，不操作生产。
规范类任务依赖 D01–D05；示例依赖 D06–D09；Q 类执行前冻结输入。独立人工任务无参与者时保持未完成。
文件级复核：git diff --check；链接与阶段映射检查；对照设计逐项静态核对。最终结果写入 docs/reviews/，原始输出写 .scratch/reuse-validation/。

## 规范与新人入口

- [ ] N01 `README.md`：读取现状→目标用户、入口、验证范围→静态核对本文件语义及引用；产物为该文件，执行者为本轮 Agent，最终人工采用另记 Q03。
- [ ] N02 `workflows/full.md`：读取现状→十四阶段编号、判定与回退→静态核对本文件语义及引用；产物为该文件，执行者为本轮 Agent，最终人工采用另记 Q03。
- [ ] N03 `docs/06-ops-readiness.md`：读取现状→十二领域适用条件、控制、证据及责任→静态核对本文件语义及引用；产物为该文件，执行者为本轮 Agent，最终人工采用另记 Q03。
- [ ] N04 `references/artifacts.md`：读取现状→完整交接与最终验收→静态核对本文件语义及引用；产物为该文件，执行者为本轮 Agent，最终人工采用另记 Q03。
- [ ] N05 `references/skills.md`：读取现状→固定依赖与条件调用闭包→静态核对本文件语义及引用；产物为该文件，执行者为本轮 Agent，最终人工采用另记 Q03。
- [ ] N06 `harness/04-gates-and-evidence.md`：读取现状→证据来源、状态、风险接受→静态核对本文件语义及引用；产物为该文件，执行者为本轮 Agent，最终人工采用另记 Q03。
- [ ] N07 `harness/07-runtime-portability.md`：读取现状→环境起点及兼容证据→静态核对本文件语义及引用；产物为该文件，执行者为本轮 Agent，最终人工采用另记 Q03。
- [ ] N08 `harness/examples/handoff.example.md`：读取现状→阶段、原始证据、阻断与下一步→静态核对本文件语义及引用；产物为该文件，执行者为本轮 Agent，最终人工采用另记 Q03。
- [ ] N09 `harness/examples/gate-record.example.md`：读取现状→范围备注与风险接受分开→静态核对本文件语义及引用；产物为该文件，执行者为本轮 Agent，最终人工采用另记 Q03。
- [ ] N10 `harness/05-feedback-and-self-refinement.md`：读取现状→变更影响及证据适用→静态核对本文件语义及引用；产物为该文件，执行者为本轮 Agent，最终人工采用另记 Q03。
- [ ] N11 `docs/01-quick-start.md`：读取现状→六组十四步新人入口→静态核对本文件语义及引用；产物为该文件，执行者为本轮 Agent，最终人工采用另记 Q03。
- [ ] N12 `docs/08-faq.md`：读取现状→人工责任与术语→静态核对本文件语义及引用；产物为该文件，执行者为本轮 Agent，最终人工采用另记 Q03。
- [ ] N13 `docs/09-troubleshooting.md`：读取现状→九类流程采用问题定位→静态核对本文件语义及引用；产物为该文件，执行者为本轮 Agent，最终人工采用另记 Q03。

## Restart 教学产物链

- [ ] E01 `examples/kubernetes-deployment-restart/01-prototype/approval.md`：按 D06–D09 核对→修正相关叙述→保留教学/未执行声明；对照 Spec 的提交、未知、防重、审计、恢复语义，不以关键词批量替换代替检查。
- [ ] E02 `examples/kubernetes-deployment-restart/02-react-mock/contract.md`：按 D06–D09 核对→修正相关叙述→保留教学/未执行声明；对照 Spec 的提交、未知、防重、审计、恢复语义，不以关键词批量替换代替检查。
- [ ] E03 `examples/kubernetes-deployment-restart/03-parity/prototype-parity.md`：按 D06–D09 核对→修正相关叙述→保留教学/未执行声明；对照 Spec 的提交、未知、防重、审计、恢复语义，不以关键词批量替换代替检查。
- [ ] E04 `examples/kubernetes-deployment-restart/04-architecture/grill-decisions.md`：按 D06–D09 核对→修正相关叙述→保留教学/未执行声明；对照 Spec 的提交、未知、防重、审计、恢复语义，不以关键词批量替换代替检查。
- [ ] E05 `examples/kubernetes-deployment-restart/04-architecture/stack-selection.draft.md`：按 D06–D09 核对→修正相关叙述→保留教学/未执行声明；对照 Spec 的提交、未知、防重、审计、恢复语义，不以关键词批量替换代替检查。
- [ ] E06 `examples/kubernetes-deployment-restart/04-architecture/stack-selection.md`：按 D06–D09 核对→修正相关叙述→保留教学/未执行声明；对照 Spec 的提交、未知、防重、审计、恢复语义，不以关键词批量替换代替检查。
- [ ] E07 `examples/kubernetes-deployment-restart/05-spec/deployment-restart.spec.md`：按 D06–D09 核对→修正相关叙述→保留教学/未执行声明；对照 Spec 的提交、未知、防重、审计、恢复语义，不以关键词批量替换代替检查。
- [ ] E08 `examples/kubernetes-deployment-restart/06-tickets/ticket-01.md`：按 D06–D09 核对→修正相关叙述→保留教学/未执行声明；对照 Spec 的提交、未知、防重、审计、恢复语义，不以关键词批量替换代替检查。
- [ ] E09 `examples/kubernetes-deployment-restart/06-tickets/ticket-02.md`：按 D06–D09 核对→修正相关叙述→保留教学/未执行声明；对照 Spec 的提交、未知、防重、审计、恢复语义，不以关键词批量替换代替检查。
- [ ] E10 `examples/kubernetes-deployment-restart/07-implementation/tdd-evidence.md`：按 D06–D09 核对→修正相关叙述→保留教学/未执行声明；对照 Spec 的提交、未知、防重、审计、恢复语义，不以关键词批量替换代替检查。
- [ ] E11 `examples/kubernetes-deployment-restart/08-review/code-review.md`：按 D06–D09 核对→修正相关叙述→保留教学/未执行声明；对照 Spec 的提交、未知、防重、审计、恢复语义，不以关键词批量替换代替检查。
- [ ] E12 `examples/kubernetes-deployment-restart/08-review/ops-readiness.md`：按 D06–D09 核对→修正相关叙述→保留教学/未执行声明；对照 Spec 的提交、未知、防重、审计、恢复语义，不以关键词批量替换代替检查。
- [ ] E13 `examples/kubernetes-deployment-restart/09-e2e/test-report.md`：按 D06–D09 核对→修正相关叙述→保留教学/未执行声明；对照 Spec 的提交、未知、防重、审计、恢复语义，不以关键词批量替换代替检查。
- [ ] E14 `examples/kubernetes-deployment-restart/10-acceptance/human-acceptance.md`：按 D06–D09 核对→修正相关叙述→保留教学/未执行声明；对照 Spec 的提交、未知、防重、审计、恢复语义，不以关键词批量替换代替检查。
- [ ] E15 `examples/kubernetes-deployment-restart/README.md`：按 D06–D09 核对→修正相关叙述→保留教学/未执行声明；对照 Spec 的提交、未知、防重、审计、恢复语义，不以关键词批量替换代替检查。

## 验证与交付

- [ ] Q01 冻结候选及公开/复核包：保存源码修订、文件摘要、依赖修订、环境起点和预期结果；不得从执行输出反推答案。
- [ ] Q02 原生 Skill 实际执行：确认固定版本加载与执行前置条件→分别保存输入/实际输出/退出码→执行正常及反例检查。人工 seam/Spec/Ticket 批准不得代签；阻断逐项记录。
- [ ] Q03 目标新人独立采用：由未参与编写、符合画像的人完成入口判断、阶段练习、异常定位、新会话接续和生产边界判断；保存帮助、耗时及误判。未提供参与者时保持待验证。
- [ ] Q04 受控规则变更：在隔离副本改一项规则→列受影响要求与旧证据→执行必要复核；不假称人工升级采用已经发生。
- [ ] Q05 复评与交付：检查 RA-01–10/V-01–09 映射、引用、diff 与证据→输出当前通过/失败/待验证项；独立采用或关键确认未完成时不出具9.5+或生产放行结论。

