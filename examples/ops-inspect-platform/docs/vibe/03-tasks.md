# P3 分阶段实施任务清单（P4a 前端验收 → P4b 后端采集与联调）

> **强制执行纪律**：必须先完成 `P4a` 并真实启动前端页面，等用户打开浏览器确认 **`P4a 通过`** 后，才允许执行 `approve p4a` 并进入 `P4b` 编写后端代码。

---

## 第一段：P4a — 前端实现与实机启动验收（禁止在此阶段写后端业务代码）

- [ ] **T-FE-01 还原双页结构与视觉基线**
  - 按 `docs/vibe/01-prototype/index.html`（Rev 4，风格 C + Refactoring UI ≥14px）使用 React 18 + Vite 拆分为清晰组件：
    - `src/App.jsx`（顶栏导航、双页 Hash 路由 `#/servers` & `#/schedule`、身份/登录态控制、全局 Toast）
    - `src/pages/ServersPage.jsx`（5 张 KPI 卡片、筛选栏、巡检列表、单台检测、登记/编辑弹窗、IP CSV/JSON 导入预览弹窗、CSV/JSON 导出）
    - `src/pages/SchedulePage.jsx`（4×6 小时 / 2×6 分钟网格弹层时间选择器、SMTP 模式展示、收件人配置、手动确认推送、收件箱 & 审计双 Tab、按需下载 `.md`）
    - `src/components/TimePicker.jsx`、`src/components/ServerModal.jsx`、`src/components/ImportModal.jsx`、`src/components/ConfirmModal.jsx`
- [ ] **T-FE-02 API 客户端与 P4a 实机演示模式**
  - 按 `docs/vibe/03-openapi.yaml` 实现 `src/api/client.js`，默认请求真实 `/api/*` 接口（`.env.production` 强制 `VITE_USE_MOCK=false`）；
  - 为便于 `P4a` 在后端尚未落地时就能让用户打开页面完整点验交互，开发态支持通过页面“演示模式 / 连接后端”本地状态体验全部流程（包含静态目标登记、IP 导入预览、主动巡检触发以及 `401`/`403`/`409`/`504` 反馈）。
- [ ] **T-FE-03 构建验证、门禁校验与实机启动**
  - 在 `frontend/` 安装依赖并实跑 `npm --prefix frontend run build` 通过；
  - 执行 `python ../ops-vibe-coding/scripts/vibe_gate.py check p4a --project .` 拿到退出码 `0`；
  - 启动本地 Vite 前端服务（宿主机浏览器可直达），**停手汇报并等待用户确认 `P4a 通过`**。

---

## 第二段：P4b — 后端多驱动采集引擎、API、安全用例与双审查（须在 `approve p4a` 后启动）

- [ ] **T-BE-01 配置 Fail-Fast 与 SQLite 持久化**
  - 实现 `backend/app/config.py`：环境变量加载、CORS 白名单校验、`APP_ENV=production` 强密钥/强密码 Fail-Fast 拒启；
  - 实现 `backend/app/storage.py`：初始化 `targets`、`schedule_config`、`outbox_messages`、`audit_logs` 4 张表，支持预置 `local` 本机目标与安全清理/查询方法。
- [ ] **T-BE-02 多驱动主动巡检采集引擎（核心业务，严禁退化为手工台账）**
  - 实现 `backend/app/collector.py`：
    - `local` 驱动：Windows `ctypes`（`GlobalMemoryStatusEx` + 0.5s `GetSystemTimes`）/ Linux `/proc/meminfo` + `/proc/stat` 真实指标采集；
    - `ssh` 驱动：`paramiko` 只读白名单命令采集（连接 5s / 执行 8s 超时隔离、绝不重试、凭据别名只读加载）；
    - `mock` 驱动：确定性状态与异常模拟；
    - 5 并发线程池 `inspect_all`，单台 `TIMEOUT`/`UNREACHABLE` 隔离不影响其余主机。
- [ ] **T-BE-03 Markdown 报告、邮箱双模式与定时调度**
  - 实现 `backend/app/mailer.py`：生成 Markdown 汇总与明细、标准 SMTP（10s 超时返 `504` 且**不自动重试**）+ 本地模拟收件箱双模式、非阻塞防重锁（并发冲突返 **`409`**）；
  - 实现 `backend/app/scheduler.py`：进程内定时线程，到点先巡检再推送，同分钟幂等防重发。
- [ ] **T-BE-04 FastAPI 路由、RBAC 鉴权与导入导出**
  - 实现 `backend/app/main.py`：完整对齐 `docs/vibe/03-openapi.yaml`，含 `/health`、HMAC Bearer 登录鉴权（`401` / `403`）、IP CSV/JSON 导入预检与事务提交、UTF-8 BOM 防公式注入导出、全量审计与 `X-Op-Id`。
- [ ] **T-BE-05 自动化业务测试与 `mutating` 必测安全用例**
  - 编写 `backend/tests/test_api.py` 并亲跑 `python -m pytest -c backend/pytest.ini backend/tests -v` 全绿：
    - **核心采集用例**（覆盖 `collect|inspect|probe`）：本机 `local` 真实内存/CPU 采集、SSH 只读输出解析、5 并发中单台超时隔离；
    - **导入导出与防注入用例**：CSV/JSON 预览提交、`skip`/`overwrite`、CSV 公式转义；
    - **安全用例（强制）**：
      1. `401 Unauthorized`：未登录调用写接口被拒并落审计；
      2. `403 Forbidden`：`viewer` 越权调用写接口被拒并落审计；
      3. `409 Conflict`：并发重复触发推送/巡检被防重锁拦截；
      4. `504 Gateway Timeout`：模拟 SMTP 超时后返 `504` 且断言发送函数仅调用 1 次（**超时不重试**）；
      5. 生产模式弱密码/缺密钥 Fail-Fast 校验。
- [ ] **T-BE-06 联调收口、双审查与 `check p4b`**
  - 产出 `docs/vibe/04-code-review.md` 与 `docs/vibe/04-ops-readiness.md`（0 BLOCKER / 0 FAIL）；
  - 实跑 `python ../ops-vibe-coding/scripts/vibe_gate.py check p4b --project .` 拿到退出码 `0`，**停手汇报并等待用户确认 `P4b 通过`**。
