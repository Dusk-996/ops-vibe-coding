# ops-inspect-platform — Ops Vibe Coding v3.4 执行中枢

- **项目名称**：`ops-inspect-platform`
- **风险模式**：`mutating`（`readonly` 仅只读查询 / `mutating` 含变更写操作）
- **门禁引擎**：`../../scripts/vibe_gate.py`
- **机器状态文件**：`.vibe/state.json`（唯一机器通信与命令配置源）
- **固定产物目录**：`docs/vibe/`（上下游 Skill 按固定路径直接读写）

<!-- VIBE-GUARD-START -->
## 1. 不可篡改的安全红线、阶段隔离铁律与确认协议

> 本区块受 `vibe_gate.py` SHA-256 校验保护。禁止任何 Agent 或初始化脚本删除、弱化本区块内容。

### 核心执行原则：阶段内机器闭环，阶段间强制人工确认，部署专属 P6
- **严禁跨阶段抢跑**：每个阶段（`p1` / `p2` / `p3` / `p4a` / `p4b` / `p5` / `p6`）完成后，必须先跑 `python ../../scripts/vibe_gate.py check <stage> --project .` 拿到退出码 0，然后**立即停手**，严禁未经用户确认顺手进入下一阶段。
- **只有 P6 阶段才涉及部署（#23）**：**P1–P5 任何阶段绝不设计、编写或评估部署文件**（禁止提前生成 `docker-compose.yml`、`Dockerfile`、`nginx.conf`、`*.service`、`deploy/`、`k8s/`，也不在 P4b/P5 提前评估尚未进入的部署产物）；`vibe_gate.py` 在 `p5` 获批前会自动阻断 `[EARLY-DEPLOY]`。所有部署形态拍板、脚本打包、容器/服务权限扫描、备份恢复与回滚验证，一律在 **P5 全面真环境测试全部通过并放行后**，于独立的 **P6 部署阶段**完成。
- **Skill 实读防盲签铁律（#24）**：进入路由表标注的阶段（尤其是 `prototype-parity-review`、`code-review`、`ops-readiness-review`、`verification-before-completion` 等审查/验证环节）前，必须先**真实读取**对应 `SKILL.md` 及清单文件，按条款逐项以代码行号或实测输出举证，严禁凭感觉写结论或替人类擅自接受 `MAJOR` 风险；对简单文案/单文件小改遵循 KISS，不强套全套重 Skill。
- **前后端严格分段验收（#12）**：先在 `P4a` 完成并真实启动前端，等用户打开页面验收通过（`approve p4a`）后，才允许进入 `P4b` 编写后端与联调。
- **上游反向校准闭环（#13）**：若在 `P2` 确认核心运维机制后发现 `P1` 原型字段或流程存在偏差，必须先同步回改 `01-design.md` 与 `01-prototype/index.html` 并复跑 `check p1`、`check p2`。
- **阶段末固定三段汇报（大白话，不甩源码）**：
  1. **本阶段完成了什么 + 机器检查证据**（实测输出/退出码，未测项如实单列；P3 必须醒目声明“当前仅空骨架，尚无代码可启动”）；
  2. **请你确认与验收的核心点**（P1 原型 / P2 技术栈与核心机制 / P3 骨架、逻辑流与用例 / P4a 启动后的前端实机页面 / P4b 后端实测与双审查 / P5 真环境全面测试证据 / P6 生产部署形态、实机部署与回滚演练）；
  3. **下一步计划做什么**（预告下一阶段动作，等待用户明确确认并执行 `approve <stage>`）。
- **严禁 Agent 代签**：禁止自行执行 `vibe_gate.py approve` 或手工篡改 `.vibe/state.json` 的 `approved` / `status` 字段。

### 生产级前端 UI 与文案基线（P1 / P4a 硬约束，#14–#18 / #21）
- **禁原生 `<select>`（#14）**：全站筛选栏与表单严禁裸用系统原生 `<select>`，统一封装圆角白底浮层、柔和悬停与右侧勾选态的自定义下拉组件（`check p4a` 自动扫描阻断）。
- **去源码符号展示（#15）**：底层可按契约存储/导出 Markdown，但前端页面阅读与推送确认预览必须渲染为可视化排版视图，禁止向用户直接裸露 `#`、`|---|` 等原始语法。
- **左表 + 右抽屉范式（#16）**：发送记录、收件箱、操作审计等日志类视图禁用手风琴折叠，统一采用“单行高密度列表 + 点击右侧滑出详情抽屉（Drawer）”。
- **悬浮通知与运维人话文案（#17）**：操作反馈采用右上角悬浮卡片 + **10 秒自动隐藏（鼠标悬停暂停倒计时）**；正文只讲运维人话结论、点名异常主机与建议动作，不把 `[200 OK]` / `INSPECT_ALL` 等技术码直出正文（追踪号降级放淡灰角标）；全站采用生产业务术语，模拟通道必须明确标注“未操作真实环境 / 未发真实外部邮件”。
- **P4a 无后端双态验收模式（#18）**：生产构建强制锁定 `VITE_USE_MOCK=false`（绝不含模拟兜底）；仅在开发态自动探测 `/health` 不可达时启用本地预览交互供 P4a 实机点验，待 P4b 后端启动后零改动无缝切回真实 `/api/*`。
- **生产信息架构克制原则（#21）**：页面顶栏不堆砌列表增导按钮；列表主触发放板块头，增/导按钮归位至筛选行右侧并合并多格式导出；去掉“说明书式”冗长副标题与顶栏多余数字胶囊；登录页用标准“账号/密码”，登录后仅显示用户名不重复角色括注。

### 运维与安全红线（应用级 P3–P5 + 部署级 P6）
- **应用级红线（P3–P5 生效）**：
  - 禁止硬编码密钥、Token、私钥或默认弱密码；生产环境（`APP_ENV=production`）缺失或使用弱密钥/密码（含可选独立加密主密钥）或通配 `CORS *` 必须 Fail-Fast 拒启。
  - 除 `/health` 与登录入口外，涉及资产拓扑、凭据引用、邮件与审计的读接口亦须遵守最小权限认证，写接口强制 `admin` RBAC + 全量审计；退出或 401 时前端清空敏感内存态。
  - **动态通道凭据加密热配（#19）**：发信/通知账号支持管理员 Web 热配并经主密钥（Fernet/AES-GCM）加密多账号存档，下拉切换、永不回显明文或密文、留空保留原密文、免重启热生效，并保留环境变量兜底。
  - **通知报告“总—分”原则（#20）**：先总览 KPI，**仅详细展示异常及需关注主机**，正常主机省略明细；SMTP 失败向前端返回脱敏人话，完整堆栈进服务端日志。
  - 远程 SSH 只读命令硬编码常量防注入、凭据别名阻断路径穿越、生产态默认严格 `known_hosts`（不静默降级 `AutoAddPolicy`）、输出设字节上限（如 64KB）、超时绝不自动重试；后台调度禁止 `except: pass` 静默吞错，全模块输出标准 `logging` 并对日志/历史表设保留上限。
  - 禁止应用代码保留 `reload=True`、`CORS *` 通配来源、或 `VITE_USE_MOCK=true`；**禁止偷换核心概念**（主动巡检/采集/控制必须有真实可执行模块与对应测试）。
  - **`mutating` 模式附加红线**：写操作须 RBAC + 全量审计 + 并发防重（`409`）+ 下游超时不重试（`504`）；P4b 自动化测试必须覆盖 `401`/`403`/`409`/`504 超时不重试` 4 类负面安全用例；严禁未经人类授权对生产基础设施执行破坏性命令。
- **部署级红线（仅 P6 阶段生效，`check p6` 自动校验）**：
  - 容器镜像严禁 `:latest` 标签，Dockerfile 与 systemd unit 严禁以 `root` 用户运行；
  - Kubernetes 工作负载清单必须声明 `livenessProbe`、`readinessProbe` 与 `resources.limits`；
  - 必须交付并演练数据持久化备份恢复与版本回滚步骤。

### 自动打回与 3 轮熔断
- 每阶段内部遇到测试、构建、扫描或 `vibe_gate.py check` 失败时，自动根据错误修复并重试；
- **同一阶段连续失败达 3 轮触发熔断（退出码 2）**，必须立即停手向人类汇报失败证据，严禁绕过门禁。
<!-- VIBE-GUARD-END -->

## 2. P1–P6 技能路由与固定产物

> **双工具调用约定**：Codex 使用 `$<skill>` 触发；Antigravity 通过 `.agents/skills.json` 自动发现或直接读取对应 `SKILL.md` 执行。**进入审查阶段必须先真实读取对应 Skill 与清单原文。**

| 阶段 | 串联 Skill | 固定输出路径 | 门禁与人工确认点 |
|---|---|---|---|
| **P1 意图、风格与原型** | `devops-brainstorming` → `ui-ux-pro-max`（3 套风格对比）→ `frontend-design` | `docs/vibe/01-design.md`、`docs/vibe/01-prototype/style-picker.html`、`docs/vibe/01-prototype/index.html` | `check p1` → **人工验收原型 + `approve p1`** |
| **P2 技术栈与核心机制** | `stack-selector`(草案) → `grilling`（必问：核心运维机制、前后端语言/框架、存储与实例形态；**不提前锁 P6 部署编排**）→ `stack-selector`(定稿) | `docs/vibe/02-architecture.draft.md`、`docs/vibe/02-grill.md`、`docs/vibe/02-architecture.md` | `check p2` → **人工确认技术栈与核心机制 + `approve p2`** |
| **P3 规格、骨架与用例** | `to-spec` → `project-init`（仅应用骨架，**不生成部署文件**）→ `devops-writing-plans` | `docs/vibe/03-spec.md`、`docs/vibe/03-openapi.yaml`、`docs/vibe/03-tasks.md`、空目录 `frontend/` & `backend/`、填好 `.vibe/state.json` 命令 | `check p3`（应用红线 + 防抢跑部署）→ **人工确认骨架、逻辑与用例 + `approve p3`** |
| **P4a 前端实现与实机启动** | 按 P1 原型与 UI 基线实现（仅选 MUI 时用 `html-to-mui-react`）→ 实读 `prototype-parity-review` | `frontend/` 可构建可启动前端工程 + `docs/vibe/04-parity-review.md` | `check p4a`（构建 + 禁 Mock + 禁原生 `<select>` + 防抢跑部署）→ **人工打开前端验收 + `approve p4a`** |
| **P4b 后端实现、实测与互检** | `test-driven-development` + `verification-before-completion` → 实读 `code-review` + `ops-readiness-review`（K 域部署留待 P6） | `backend/`（核心模块 + 全量安全单测）+ `docs/vibe/04-code-review.md`、`docs/vibe/04-ops-readiness.md` | `check p4b` → **人工验收后端实测与双审查 + `approve p4b`** |
| **P5 全面真环境测试** | `verification-before-completion` + 真环境（推荐 Linux/WSL 隔离目录）全链路测试（有浏览器环境可选 `playwright-e2e-debug-report`） | `docs/vibe/05-e2e-report.md`、`docs/vibe/05-*.log`（测试实证日志/截图） | `check p5`（测透功能/安全/容错/持久化，防抢跑部署）→ **人工确认测试全过 + `approve p5`** |
| **P6 生产部署与上线放行** | 按目标环境设计部署形态 + 实读 `ops-readiness-review`（关闭 K 域部署/备份/回滚） | `deploy/DEPLOY.md`（交付运维手册）、`README.md`、`deploy/`（或 `docker-compose.yml` / `k8s/`）、`docs/vibe/06-deploy-report.md`、`docs/vibe/06-deploy.log`、`docs/vibe/06-release-gate.json` | `check p6`（部署红线扫描 + 交付手册校验 + 发布门禁签发）→ **人工终审上线放行 + `approve p6`** |

## 3. 应用目录规范（P3–P5）

- 应用源码目录：`frontend/`（前端源码，直连 `/api/*` OpenAPI 接口）+ `backend/`（后端源码）+ `.env.example`。
- 生产部署交付物（`deploy/`、`docker-compose.yml`、`Dockerfile`、`nginx.conf`、`*.service`、`k8s/` 等）**仅在 P5 放行后于 P6 阶段按需创建**。
- 遵循 **P4a 无后端双态验收模式**：生产构建必须锁定 `VITE_USE_MOCK=false`；仅在 `import.meta.env.DEV` 且 `/health` 不可达时启用本地验收适配，P4b 启动后端后自动零改动切真联调。
- `P3` 结束前必须在 `.vibe/state.json` 的 `commands` 中填写真实可执行的 `frontend_build` 与 `backend_test`。

## 4. 项目补充规则（供 `project-init` 与团队追加）

> 在此处补充项目专属的技术栈约定、目录说明与领域词汇；请勿改动上方 `VIBE-GUARD` 区块。
