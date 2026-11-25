# P1–P5 端到端流水线规范（Ops Vibe Coding v3.3）

> 机器间通信仅依赖两处单一事实源：**固定产物路径 `docs/vibe/`** + **机器状态文件 `.vibe/state.json`**，彻底消除人工复制搬运。

## 1. 全 6 阶段执行表

| 阶段 | 阶段内自动执行动作 | 必填产物（固定路径） | 硬门禁命令 | 停手人工验收内容 |
|---|---|---|---|---|
| **P1 意图、风格与原型** | `P1a` 需求与 Non-Goals 落盘 → `P1b` `$ui-ux-pro-max` 生成 3 套真实 CSS 风格对比页供选型并写入 `state.json.selected_style` → `P1c` 生成高保真交互 HTML 原型（`mutating` 内置身份/401/403/409/504 体验） | `docs/vibe/01-design.md`<br>`docs/vibe/01-prototype/style-picker.html`<br>`docs/vibe/01-prototype/index.html` | `check p1` | 浏览器打开原型，确认页面结构、字段与核心流程 |
| **P2 技术栈与核心机制** | 出架构草案 → `$grilling` 逐项压测并**强制确认：前后端语言框架、核心运维采集/执行机制（严禁退化为静态手工台账）、存储/实例、部署形态** → 出 FINAL 定稿（跳过假 React Mock 二次返工） | `docs/vibe/02-architecture.draft.md`<br>`docs/vibe/02-grill.md`<br>`docs/vibe/02-architecture.md` | `check p2` | 确认语言框架、真实采集/执行原理与简化边界 |
| **P3 规格、骨架与用例** | 产出接口契约、规格与 **P4a/P4b 分段任务书** → 建干净空目录骨架与容器配置 → 填好 `.vibe/state.json` 的 `commands` 与 `core_test_pattern`（**严禁提前写业务代码**） | `docs/vibe/03-spec.md`<br>`docs/vibe/03-openapi.yaml`<br>`docs/vibe/03-tasks.md`<br>`docker-compose.yml`、`frontend/`、`backend/` | `check p3`（含容器/配置提前红线扫描） | 确认目录骨架、业务逻辑流、验收用例（醒目说明尚无代码可启动） |
| **P4a 前端实机验收** | 保真还原原型并遵守 [frontend-ui-baseline.md](frontend-ui-baseline.md) → 生产锁死 `VITE_USE_MOCK=false` + 开发态无后端双态预览 → 验证构建并启动前端 | `frontend/src/` 可构建可运行的完整前端工程 | `check p4a`（含 `frontend_build` + 禁 Mock + 禁原生 `<select>`） | 浏览器直连前端逐项点验 UI、筛选、弹窗与反馈 |
| **P4b 后端采集与互检** | 实现真实核心运维模块（如 `local`/`ssh` 采集、加密凭据、SMTP）+ OpenAPI 路由 → 亲跑全量测试 + `mutating` 四大安全用例 → 双审查（代码审查 + 运维就绪审查） | `backend/app/`、`backend/tests/`<br>`docs/vibe/04-code-review.md`<br>`docs/vibe/04-ops-readiness.md` | `check p4b`（亲跑 `backend_test` + 核心正则 + 4 类安全用例 + 内置/外部扫描 + 双审查 0 BLOCKER） | 实机联调验收真采集、真发信与权限审计 |
| **P5 真环境联调放行** | 对真实运行中的前后端做全链路探活、收集日志/截图证据、产出发布门禁 JSON | `docs/vibe/05-e2e-report.md`<br>证据文件（如 `05-e2e.log` / 截图）<br>`docs/vibe/05-release-gate.json` | `check p5` | 核对实测证据与未覆盖项，最终拍板上线 |

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
