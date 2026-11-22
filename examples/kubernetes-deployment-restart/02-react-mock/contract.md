# S03 React Mock 运行与契约

修订 `dbfd4fa` 的 React 18 详情页与 Node 内存服务固定使用 `lab / staging / checkout`。输入为 [S00 原型目标](../README.md#s00-从想法到原型目标)和[当前原型及待确认项](../01-prototype/approval.md)。S02 尚待人工决定，本实现作为可复现的教学分支供对照。

## 本地运行

在此目录执行，需 Node.js 20+、npm。构建输出位于被 Git 忽略的 `dist/`。依赖版本及完整性摘要保存在 [package-lock.json](package-lock.json)。

```sh
npm ci --registry=https://registry.npmmirror.com
npm run build
npm test
npm start
```

React 页面为 `http://127.0.0.1:4173/`；同版静态原型为 `http://127.0.0.1:4173/prototype/`。服务只绑定回环地址。镜像不可达时，已有完整缓存可使用 `npm ci --offline`；需改用官方源时可使用 `npm ci --registry=https://registry.npmjs.org --replace-registry-host=always`。

`npm run e2e` 自动启动随机端口服务和无头浏览器。需本机已有 Chrome/Chromium，如路径不在常见位置，请将环境变量 `CHROME_PATH` 设为实际可执行文件。每次结果写入新的 `dist/e2e-*/`。可以用 `npm run e2e -- conflict-windows` 单独复验一项。已执行环境、退出状态和原始结果见 [S10](../07-implementation/tdd-evidence.md)、[S13](../09-e2e/test-report.md)。

## 输入与交互

点“重启 Deployment”先核对目标，取消不发 POST。确认后只发一次 `POST /api/deployments/staging/checkout/restart`，头为 `X-Operation-ID`，JSON 包含 `target` 和所选 `scenario`。查看操作记录和同标签页刷新调用 `GET /api/audit?operation_id={id}`。受控故障使用本地样本选择器。

| 样本 / 操作 | HTTP | 界面与记录（状态 / 远端观测 / 最终审计） |
|---|---:|---|
| 接受并记录 | 200 | 请求已提交；`SUBMITTED / accepted / confirmed`；rollout 尚未验证 |
| 提交超时 | 504 | 结果待核验；`UNKNOWN / unknown / confirmed`；保留操作 ID 和目标占用 |
| 明确拒绝 | 422 | 请求被拒绝；`REJECTED / rejected / confirmed`，允许新的独立确认 |
| 最终审计未确认 | 503 | 最终审计待核验；`SUBMITTING / accepted / unconfirmed`，保持占用 |
| 原操作占用时另窗新 ID 提交 | 409 | 本次未提交；分别显示本次请求 ID、占用操作 ID。刷新只查占用记录 |
| 同 ID 重放 | 原记录码 | 返回同一记录，模拟变更计数保持不变 |

[状态与服务实现](mock.mjs)保存于单进程内存；进程退出即丢失记录。刷新尝试读取旧 ID 失败时保留待核验状态。课件未实现 SSO、真实 Kubernetes 客户端、持久化审计或人工恢复事务。完整产品要求见 [Spec](../05-spec/deployment-restart.spec.md)。

**下游产物**为[可运行 React 页面源码](app.jsx)、[HTTP 服务](server.mjs)、[单元测试](mock.test.mjs)与[逐路径浏览器记录](../09-e2e/evidence/run.json)。
