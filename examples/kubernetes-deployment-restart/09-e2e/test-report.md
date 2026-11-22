# S13 Restart 浏览器测试报告

**本地 Mock 已执行，七条已批准的用例全部通过。** 目标为 `lab / staging / checkout`；实现修订 `dbfd4fa`。2026-11-22 10:30:39–10:30:46 UTC，Windows、Node `v26.13.1`、Chrome `157.0.8103.79`、Playwright Core `1.56.1`。各用例使用独立的 127.0.0.1 随机端口、内存服务和浏览器上下文。初版计划由维护者答复“批准本地 Mock 测试计划”；双窗口和原型刷新经第二次答复“修复两处并批准补充测试（推荐）”加入。[获批计划](test-task.md)

| 用例和实际步骤 | 预期及实际观测 | 结果 |
|---|---|---|
| cancel · 打开确认框并取消 | 回到详情、无结果；API 请求 0，模拟变更 0 | PASS |
| accepted · 选择接受、确认、查记录 | POST 200，页面“请求已提交”，rollout 尚未验证；同一 ID 的 GET 200，记录 SUBMITTED，模拟变更 1 | PASS |
| timeout · 选择超时、确认、查记录、刷新、再查 | POST 504；显示“结果待核验”，原 ID 保留，两次查询及刷新只发 GET，重启禁用，模拟变更 1 | PASS · [截图](evidence/timeout.png) |
| rejected · 选择明确拒绝、确认、查记录 | POST 422；页面“请求被拒绝”，同一 ID 的 GET 返回 REJECTED，模拟变更尝试 1 | PASS |
| audit-unconfirmed · 选择最终审计未确认、确认、查记录、刷新 | POST 503；UI 单列“最终审计待核验”，原记录 SUBMITTING / accepted / unconfirmed，重启禁用，模拟变更 1 | PASS · [截图](evidence/audit-unconfirmed.png) |
| conflict-windows · 两个标签打开同一目标，先超时、再从另窗确认并刷新 | 两次 POST 分别返回 504 和 409，仅一次模拟变更；第二窗显示“本次未提交”及两个不同 ID。刷新和查看记录均按占用 ID 只读查询 | PASS · [截图](evidence/conflict.png) |
| prototype-reload · 静态原型超时后刷新同一标签并查记录 | 恢复同一原型 ID、维持 UNKNOWN 和阻重；未发 HTTP API 请求，模拟服务计数 0 | PASS · [截图](evidence/prototype-reload.png) |

**证据**包括[每条请求的方法、ID、响应码与计数](evidence/run.json)、[逐步浏览器断言](../02-react-mock/browser-test.mjs)和[S04 两个视口的原型／React 对照](../03-parity/prototype-parity.md)。官方 `@playwright/cli 0.1.25` 另在同一修订执行了 [CLI 脚本](cli-check.js)，确认取消零 API、一次 POST、一次 GET，服务计数为 1。[CLI 回执](evidence/cli-run.json)

**复现**按 [Mock 运行说明](../02-react-mock/contract.md)安装后运行 `npm run build`、`npm test` 与 `npm run e2e`（本轮均退出 0）。新运行生成独立的 `dist/e2e-*/run.json` 与截图；某项失败会记录已观察到的调用并标 FAIL，尚未执行的项目列为 SKIPPED 和对应原因。经批准修复前的[双窗失败](../07-implementation/red-conflict-windows.json)和[原型刷新失败](../07-implementation/red-prototype-reload.json)保留原状。若已安装相同版本 CLI，也可启动服务后运行以下三条命令复核其独立路径（从 Mock 目录执行）。

```sh
playwright-cli -s=restart-proof open http://127.0.0.1:4173 --browser=chrome
playwright-cli -s=restart-proof run-code --filename=../09-e2e/cli-check.js
playwright-cli -s=restart-proof close
```

本地已批准的七项无跳过。实际 SSO、真实 Kubernetes RBAC 与 PATCH、rollout 结果、数据库审计持久化、进程崩溃及有权人员恢复均未在此次授权和环境内验证；这些决定仍需等价环境与责任人证据。[运维风险](../08-review/ops-readiness.md) · [S14 人工验收](../10-acceptance/human-acceptance.md)
