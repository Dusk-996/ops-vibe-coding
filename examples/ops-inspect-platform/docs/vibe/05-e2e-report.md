# P5 真实联调验证报告（E2E Report）：ops-inspect-demo

- **验证时间**：2026-11-25
- **验证环境**：本机真实运行栈（后端 `http://127.0.0.1:8000` FastAPI + SQLite WAL，前端 `http://127.0.0.1:5173` Vite + React 18；前端交互由用户在本机浏览器全程亲自验证，跳过自动化无头浏览器）
- **日志证据**：`docs/vibe/05-e2e.log`
- **结论**：**PASSED（0 BLOCKER / 0 FAIL）**

## 1. 实机端到端验证矩阵
| 验证项 | 结果 | 实测证据 |
|---|---|---|
| 健康探活与通道热状态 | **PASSED** | `GET /health -> 200`，动态返回 `smtp_mode=smtp, smtp_source=database` |
| 双角色认证（`admin` / `duskk`） | **PASSED** | `admin` 与只读账号 `duskk` 登录均返回 `200` 及正确角色 Token |
| 未登录拦截（`401`） | **PASSED** | 未带 Token 调用 `POST /api/inspect/run` 返回 `401 Unauthorized` |
| 只读越权拦截（`403`） | **PASSED** | `duskk`（viewer）调用 `POST /api/inspect/run` 返回 `403 Forbidden` |
| 本机真实采集（`local`） | **PASSED** | `POST /api/inspect/1 -> 200`，实测采集 `mem=17.2/31.9GB, cpu=4.7%, cores=16, status=OK` |
| 并发防重（`409`）与超时不重试（`504`） | **PASSED** | 实机二次连点触发 `409` 拦截 + 自动化测试验证 `504` 仅调用 1 次不重试 |
| 真实 QQ SMTP 发信与多账号加密存档 | **PASSED** | 网页热配 QQ 465 SSL、Fernet 加密存库（`GET /api/smtp` 0 密文/明文泄漏），用户 QQ 邮箱实测收到排版报告 |
| 巡检报告“总—分”结构 | **PASSED** | `GET /api/reports/markdown -> 200`，先呈现巡检总览，仅详展异常主机，正常主机省略明细 |
| 前端界面与交互实机验收 | **PASSED** | 用户在本机浏览器全程验收通过（自定义下拉、左表右抽屉、10s 悬浮通知、工具栏归位与文案精修） |
