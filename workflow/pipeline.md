# P1–P6 端到端流水线规范（Ops Vibe Coding v3.4）

> 机器间通信仅依赖两处单一事实源：**固定产物路径 `docs/vibe/`** + **机器状态文件 `.vibe/state.json`**，彻底消除人工复制搬运。
> **核心边界**：**只有 P6 阶段才涉及生产部署设计、部署交付物与部署评估**；P1–P5 绝不提前编写任何容器/服务编排文件。

## 1. 全 7 阶段执行表

| 阶段 | 阶段内自动执行动作 | 必填产物（固定路径） | 硬门禁命令 | 停手人工验收内容 |
|---|---|---|---|---|
| **P1 意图、风格与原型** | `P1a` 需求与 Non-Goals 落盘 → `P1b` `$ui-ux-pro-max` 生成 3 套真实 CSS 风格对比页供选型并写入 `state.json.selected_style` → `P1c` 生成高保真交互 HTML 原型（`mutating` 内置身份/401/403/409/504 体验） | `docs/vibe/01-design.md`<br>`docs/vibe/01-prototype/style-picker.html`<br>`docs/vibe/01-prototype/index.html` | `check p1` | 浏览器打开原型，确认页面结构、字段与核心流程 |
| **P2 技术栈与核心机制** | 出架构草案 → `$grilling` 逐项压测并**强制确认：前后端语言框架、核心运维采集/执行机制（严禁退化为静态手工台账）、存储与单/多实例形态**（**不提前锁定 P6 部署编排**）→ 出 FINAL 定稿 | `docs/vibe/02-architecture.draft.md`<br>`docs/vibe/02-grill.md`<br>`docs/vibe/02-architecture.md` | `check p2` | 确认语言框架、真实采集/执行原理与运行边界 |
| **P3 规格、骨架与用例** | 产出接口契约、规格与 **P4a/P4b 分段任务书** → 建干净空应用目录骨架（`frontend/`、`backend/`、`.env.example`，**严禁提前生成部署文件或业务代码**）→ 填好 `.vibe/state.json` 的 `commands` 与 `core_test_pattern` | `docs/vibe/03-spec.md`<br>`docs/vibe/03-openapi.yaml`<br>`docs/vibe/03-tasks.md`<br>`frontend/`、`backend/` | `check p3`（应用红线 + 防抢跑部署 `[EARLY-DEPLOY]`） | 确认目录骨架、业务逻辑流、验收用例（醒目说明尚无代码可启动） |
| **P4a 前端实机验收** | 保真还原原型并遵守 [frontend-ui-baseline.md](frontend-ui-baseline.md) → 生产锁死 `VITE_USE_MOCK=false` + 开发态无后端双态预览 → 实读 `prototype-parity-review` 核对 → 验证构建并启动前端 | `frontend/src/` 可构建可运行前端<br>`docs/vibe/04-parity-review.md` | `check p4a`（`frontend_build` + 禁 Mock + 禁原生 `<select>` + 防抢跑部署） | 浏览器直连前端逐项点验 UI、筛选、弹窗与反馈 |
| **P4b 后端实现与互检** | 实现真实核心运维模块 + OpenAPI 路由 → 亲跑全量单测 + `mutating` 四大安全用例 → 实读 `code-review` + `ops-readiness-review`（逐项核查应用/运行安全，K 域部署留待 P6） | `backend/app/`、`backend/tests/`<br>`docs/vibe/04-code-review.md`<br>`docs/vibe/04-ops-readiness.md` | `check p4b`（亲跑 `backend_test` + 核心正则 + 4 类安全用例 + 应用扫描 + 双审查 0 BLOCKER） | 实机联调验收真采集、真发信与权限审计 |
| **P5 全面真环境测试** | 在真实运行环境（如 Linux/WSL 非 root 隔离测试目录 `/opt/<app>-test`）跑全量单测 + 多域端到端回归（认证/RBAC、CRUD、导入导出、并发隔离、加密落库、结构化日志、`SIGTERM` 重启持久化等），留存真实日志 | `docs/vibe/05-e2e-report.md`<br>`docs/vibe/05-*.log`（或截图证据） | `check p5`（校验测试报告、实证日志、应用红线与防抢跑部署） | 核对真环境实测证据，确认测试全面通过后拍板进入 P6 |
| **P6 生产部署与放行** | **仅在此阶段设计与实施部署**：由人类选定部署形态（Linux `systemd`+Nginx / Docker Compose / K8s）→ 产出部署包、SQLite/DB 备份恢复与回滚脚本、**生产部署与运维交付手册（`deploy/DEPLOY.md` & `README.md`）** → 真机部署演练留存 `06-deploy.log` → 关闭 `ops-readiness-review` K 域终审 → 签发 `06-release-gate.json` | `deploy/DEPLOY.md`、`README.md`<br>`deploy/`（或 `docker-compose.yml` / `k8s/`）<br>`docs/vibe/06-deploy-report.md`<br>`docs/vibe/06-deploy.log`<br>`docs/vibe/06-release-gate.json` | `check p6`（部署红线扫描 + 交付手册校验 + 签发发布门禁） | 核对交付手册、部署产物、演练日志、备份回滚与最终发布门禁，拍板上线 |

---

## 2. 上游反向校准闭环（#13）

当 **P2 细化核心运维机制** 后，若发现 **P1 原型字段或交互与真实机制不符**（例如：原本手工填写内存/CPU 的表单，应改为仅录静态 IP/连接信息、由引擎主动检测动态指标）：
1. **立即回退校准 P1**：同步修订 `docs/vibe/01-design.md` 与 `docs/vibe/01-prototype/index.html`；
2. 复跑 `vibe_gate.py check p1` 与 `check p2`；
3. 请用户重新确认校准后的原型与 P2 定稿，再继续进入 P3。

---

## 3. 关键跨平台实操经验（#22）

- **Windows 沙盒下运行 FastAPI `TestClient`**：Windows 沙盒默认限制回环 `socketpair()` 导致 Python `ProactorEventLoop` 挂死；执行 `pytest` 与 `vibe_gate.py check p4b` 时须在宿主机/沙盒外环境执行，而静态构建与文档检查仍在沙盒内运行。
- **前端本地开发服务供浏览器访问**：Windows 沙盒内启动的端口无法从宿主机浏览器访问，交付 P4a / P4b 人工验收时须在沙盒外启动前端 `vite` 与后端 `uvicorn`。
- **WSL2 Ubuntu 真 Linux 隔离测试（P5 最佳实践）**：Windows 宿主机开发时，推荐在本地 WSL2 Ubuntu 创建独立非 root 测试目录（如 `/opt/<app>-test/`）执行 P5 真 Linux 全面测试；若 WSL 无外网直连 PyPI，可在宿主机用 `pip download --only-binary=:all: --platform manylinux2014_x86_64` 离线缓存 wheel 后安装。
