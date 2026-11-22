# S10 单目标 Restart 实现与 TDD 证据

实际运行覆盖 [Ticket 01](../06-tickets/ticket-01.md) 的提交、占用及结果语义和 [Ticket 02](../06-tickets/ticket-02.md) 的本地记录查询。实物为[内存状态机](../02-react-mock/mock.mjs)、[HTTP 服务](../02-react-mock/server.mjs)、[React 交互](../02-react-mock/app.jsx)、[单元测试](../02-react-mock/mock.test.mjs)与[浏览器断言](../02-react-mock/browser-test.mjs)。

## RED → GREEN → REFACTOR

| 轮次及修订 | 实际命令与结果 |
|---|---|
| RED · `0a6bc82` | 在 Mock 目录执行 `node --test --test-reporter=spec mock.test.mjs`，退出 1，6 条中 4 失败。只会返回成功的初始实现分别将预期 504/403/503 返回为 200，又将明确拒绝写成 SUBMITTED。[原始单测输出](unit-red.txt) |
| GREEN · `f99380a` | 同一组预期在内存状态机实现后执行 `npm test`，退出 0，6/6。验证同 ID 重放、其他目标拒绝、未知占用、审计未确认与明确拒绝。取消的 UI 行为由浏览器验证。 |
| 重构、补充 RED · `2be32a1` | 前后端共用 [target.mjs](../02-react-mock/target.mjs)，修正初始计数用例名称。审查后经批准分别执行 `npm run e2e -- conflict-windows` 与 `npm run e2e -- prototype-reload`，分别退出 1。双窗口还把原操作状态当作本次结果，原型刷新时结果面板消失。[双窗口失败回执](red-conflict-windows.json) · [原型刷新失败回执](red-prototype-reload.json) |
| 修复、最终复验 · `dbfd4fa` | 修复后的完整运行 `npm run build` 退出 0、`npm test` 退出 0、`npm run e2e` 退出 0。六条单测、七条浏览器用例及两个视口的选定对照全部完成。[最终单测输出](unit-green.txt) · [浏览器回执](../09-e2e/evidence/run.json) |

2026-11-22 在 Windows、Node `v26.13.1`、Chrome `157.0.8103.79` 复验。两个文本文件来自固定实现版本的 Node spec reporter；RED 堆栈仅将本机绝对路径缩成文件名。从干净检出依[本地运行说明](../02-react-mock/contract.md)安装依赖即可复验当前修订；旧 RED 可在独立检出相应提交后运行表中命令。

模拟变更次数来自本地计数器。真实 SSO/RBAC、数据库事务、进程崩溃后的占用、审计留存和恢复规程分别留给[运维就绪](../08-review/ops-readiness.md)。[S11](../08-review/code-review.md)使用实际变更与 Spec 审查。
