# Skill Map

Skill 源码独立维护在 [personal-skill](https://github.com/luozijian1990/personal-skill)。本仓库只记录职责、固定依赖和使用边界，不复制实现。

## 固定来源

- 仓库修订：`dcce92018746c38a277ece323eef1347294df687`，不是浮动 main 或最新版。
- 入口与资源清单：[skill-lock.json](skill-lock.json)，15 个 Skill、86 个资源文件，另有7份许可证/归属文件索引。
- SHA-256 基于 Git blob 原始字节，先于 Windows CRLF 转换；部署/验证副本须按该字节取得，不能把换行差异误报为同一包已验证。
- 本清单证明已取得和核对源码，不证明已安装、已执行、兼容或安全审计通过；实际结果见 [验证记录](../docs/reviews/2026-11-15-reuse-validation.md)。

## 阶段与调用关系

下列路径均相对于上述固定仓库；每项入口为 `skills/<名称>/SKILL.md`。完整资源摘要在锁定清单。

| 阶段 | 名称 | 固定职责／依赖关系 |
|---|---|---|
| React + Mock | html-to-mui-react | 保真转换；交接 prototype-parity-review，交接不等于自动连跑 |
| Parity | prototype-parity-review | 真实浏览器比较，不能用构建成功代替 |
| Architecture | stack-selector | Draft 后停下；Grill 确认后才 Final |
| Grill | grill-me | 显式调用 grilling |
| Grill＋文档 | grill-with-docs | 显式调用 grilling 与 domain-modeling |
| Spec | to-spec | 先确认测试 seam，再向已配置 tracker 输出；缺配置条件调用 setup-matt-pocock-skills |
| Tickets | to-tickets | 消费批准 Spec，先确认拆分再输出；缺配置条件调用 setup-matt-pocock-skills |
| Implementation | tdd | 对已确认 Ticket 实施；审查属于后续阶段 |
| Review | code-review | 有效比较点＋非空已提交 diff；Standards、Spec 两个并行子 Agent；缺 tracker 配置条件调用 setup |
| Ops | ops-readiness-review | 检查适用运行风险与证据，不代替人的接受 |
| E2E | playwright-e2e-debug-report | 先批准任务和环境，执行依赖 playwright-cli |

## 四个间接／条件节点

| 名称 | 关系与边界 |
|---|---|
| grilling | Grill 的逐题确认，不把假设当人已确认 |
| domain-modeling | grill-with-docs 使用的领域术语及决策文档 |
| setup-matt-pocock-skills | 缺配置才运行；默认倾向远程 tracker，必须先选择 Local Markdown 才能用于本轮本地任务 |
| playwright-cli | E2E 执行能力；源码包含 npm 全局安装或 init 最新版的回退，本轮不触发；安装另需明确范围与版本 |

模板提及 triage、qa、wayfinder、codebase-design 不构成必调用依赖，不无限扩大闭包。未执行入口不列为已验证。

## 本地采用与副作用

1. 在全新或起点已记录的验证目录取得固定源码；保存获取命令、修订与摘要。失败时保存诊断，使用固定版本导出/离线包，不改用未知镜像或最新版。
2. 先配置 Local Markdown tracker：Spec 为 `.scratch/<feature>/spec.md`，Tickets 为 `.scratch/<feature>/issues/<NN>-<slug>.md`。只有本地允许路径可写，不创建 GitHub Issue。
3. 显式点名 `$to-spec`、`$to-tickets` 等；这些入口的元数据不允许隐式调用。记录实际加载路径，遇到同名全局 Skill 冲突先排除，不用“应该加载了”作证据。
4. seam、Spec 和拆分确认是人工检查点；本次执行授权不等于未来未知产物已被确认。未确认可以生成明确草案，不能发布成已批准。
5. code-review 的 `git diff <base>...HEAD`不包含未提交工作区；空 diff、无效 base 或缺必需双 Agent 能力是前置阻断，不能替换为人工阅读后仍记原生调用通过。
6. 不修改用户全局 Skill、不自动安装、不暴露凭证、不执行生产命令。本轮仅验证选定的三个入口，其余做静态来源核对。

Skill 是执行单元，Workflow 定义编排与门禁。角色或审批不明确时向采用项目维护者求助，不能让 Agent 代签。
