# S04 原型与 React 一致性预检

**正式状态为 PRECHECK，等待 S02 的真实原型批准。** 2026-11-22 对修订 `dbfd4fa` 的[静态原型](../01-prototype/index.html)和[React Mock](../02-react-mock/app.jsx)做了本地浏览器比对。两边使用相同目标 `lab / staging / checkout`、同一 CSS、同版无头 Chrome、相同视口和操作顺序。

| 样本与操作 | 两边实际观测 | 证据 |
|---|---|---|
| 桌面 1280×800，打开确认框 | 三项目标和两个按钮可见，两张截图字节一致 | [原型截图](../09-e2e/evidence/desktop-prototype-confirm.png) · [React 截图](../09-e2e/evidence/desktop-react-confirm.png) |
| 窄屏 390×844，打开确认框 | 确认文案换行，操作按钮可见，两张截图字节一致 | [原型截图](../09-e2e/evidence/mobile-prototype-confirm.png) · [React 截图](../09-e2e/evidence/mobile-react-confirm.png) |
| 两种视口下取消、切换超时、提交、查看记录 | 两边均为“结果待核验”，提示保存 ID，记录 `UNKNOWN / unknown / confirmed`，重启禁用 | [双视口逐项结果](../09-e2e/evidence/run.json)及[实际执行断言](../02-react-mock/browser-test.mjs) |
| 未知后刷新 | 两边分别验证同一标签页保留本次操作 ID 和阻重；原型零 API，React 读取原记录 | [原型刷新](../09-e2e/evidence/prototype-reload.png) · [React 刷新](../09-e2e/evidence/timeout.png) |

原型在标签页内模拟记录，React 访问回环服务。两边产生不同的合成 ID；比对检查各自刷新前后的 ID 与记录关联。独立的 React E2E 也覆盖接受、明确拒绝、审计未确认和双窗口占用。这些 React 结果的全屏视觉尚未逐一对照原型；S02 如要求纳入正式保真范围，应补相同输入下的两侧证据。现阶段没有已获人接受的偏差。

**下一步**请业务使用者完成[体验和决定记录](../01-prototype/approval.md)，再按其批准的版本、视口和状态确定正式结论。[架构草案](../04-architecture/stack-selection.draft.md)沿用教学设定。
