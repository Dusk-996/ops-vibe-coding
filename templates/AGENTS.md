# {{PROJECT_NAME}} — Ops Vibe Coding v3.3 执行中枢

- **项目名称**：`{{PROJECT_NAME}}`
- **风险模式**：`{{MODE}}`（`readonly` 仅只读查询 / `mutating` 含变更写操作）
- **门禁引擎**：`{{GATE_SCRIPT}}`
- **机器状态文件**：`.vibe/state.json`（唯一机器通信与命令配置源）
- **固定产物目录**：`docs/vibe/`（上下游 Skill 按固定路径直接读写）

<!-- VIBE-GUARD-START -->
## 1. 不可篡改的安全红线、生产 UI 基线与全阶段确认协议

> 本区块受 `vibe_gate.py` SHA-256 校验保护。禁止任何 Agent 或初始化脚本删除、弱化本区块内容。

### 核心执行原则：阶段内机器闭环，阶段间强制人工确认验收
- **严禁跨阶段抢跑**：每个阶段（`p1` / `p2` / `p3` / `p4a` / `p4b` / `p5`）完成后，必须先跑 `python {{GATE_SCRIPT}} check <stage> --project .` 拿到退出码 0，然后**立即停手**，严禁未经用户确认顺手进入下一阶段。
- **前后端严格分段验收（#12）**：先在 `P4a` 完成并真实启动前端，等用户打开页面验收通过（`approve p4a`）后，才允许进入 `P4b` 编写后端与联调。
- **上游反向校准闭环（#13）**：若在 `P2` 确认核心运维机制后发现 `P1` 原型字段或流程存在偏差，必须先同步回改 `01-design.md` 与 `01-prototype/index.html` 并复跑 `check p1`、`check p2`。
- **阶段末固定三段汇报（大白话，不甩源码）**：
  1. **本阶段完成了什么 + 机器检查证据**（实测输出/退出码，未测项如实单列；P3 必须醒目声明“当前仅空骨架，尚无代码可启动”）；
  2. **请你确认与验收的核心点**（P1 原型 / P2 技术栈与核心机制 / P3 骨架、逻辑流与验收用例 / P4a 启动后的前端实机页面 / P4b 后端实测与双审查 / P5 真环境终验）；
  3. **下一步计划做什么**（预告下一阶段动作，等待用户明确确认并执行 `approve <stage>`）。
- **严禁 Agent 代签**：禁止自行执行 `vibe_gate.py approve` 或手工篡改 `.vibe/state.json` 的 `approved` / `status` 字段。

### 生产级前端 UI 与文案基线（P1 / P4a 硬约束，#14–#18 / #21）
- **禁原生 `<select>`（#14）**：全站筛选栏与表单严禁裸用系统原生 `<select>`，统一封装圆角白底浮层、柔和悬停与右侧勾选态的自定义下拉组件（`check p4a` 自动扫描阻断）。
- **去源码符号展示（#15）**：底层可按契约存储/导出 Markdown，但前端页面阅读与推送确认预览必须渲染为可视化排版视图，禁止向用户直接裸露 `#`、`|---|` 等原始语法。
- **左表 + 右抽屉范式（#16）**：发送记录、收件箱、操作审计等日志类视图禁用手风琴折叠，统一采用“单行高密度列表 + 点击右侧滑出详情抽屉（Drawer）”。
- **悬浮通知与运维人话文案（#17）**：操作反馈采用右上角悬浮卡片 + **10 秒自动隐藏（鼠标悬停暂停倒计时）**；正文只讲运维人话结论、点名异常主机与建议动作，不把 `[200 OK]` / `INSPECT_ALL` 等技术码直出正文（追踪号降级放淡灰角标）；全站采用生产业务术语，模拟通道必须明确标注“未操作真实环境 / 未发真实外部邮件”。
- **P4a 无后端双态验收模式（#18）**：生产构建强制锁定 `VITE_USE_MOCK=false`（绝不含模拟兜底）；仅在开发态自动探测 `/health` 不可达时启用本地预览交互供 P4a 实机点验，待 P4b 后端启动后零改动无缝切回真实 `/api/*`。
- **生产信息架构克制原则（#21）**：页面顶栏不堆砌列表增导按钮；列表主触发放板块头，增/导按钮归位至筛选行右侧并合并多格式导出；去掉“说明书式”冗长副标题与顶栏多余数字胶囊；登录页用标准“账号/密码”，登录后仅显示用户名不重复角色括注。

### 运维与安全红线（含 #19 / #20）
- 禁止硬编码密钥、Token、私钥或默认弱密码；生产环境（`APP_ENV=production`）缺失关键密钥/密码必须 Fail-Fast 拒启。
- **动态通道凭据加密热配（#19）**：平台级发信/通知账号支持管理员 Web 热配并经主密钥（Fernet/AES-GCM）加密多账号存档，前端下拉直选切换、永不回显明文、留空保留原密文、免重启热生效，并保留环境变量/K8s Secret 兜底。
- **通知报告“总—分”原则（#20）**：巡检/告警邮件先给全局总览 KPI，**仅详细展示异常及需关注主机**，正常运行主机省略明细；SMTP 发信须使用 RFC 标准中文头、`Date`/`Message-ID`、`ehlo()` 并隔离 `quit()` 短超时防假报错。
- 禁止容器镜像使用 `:latest` 标签；Dockerfile 必须以非 root `USER` 运行（P3 即提前拦截）。
- 禁止生产/部署代码启用 `reload=True`、`CORS *` 通配来源、或保留 `VITE_USE_MOCK=true`。
- Kubernetes 工作负载清单必须声明 `livenessProbe`、`readinessProbe` 与 `resources.limits`。
- **禁止偷换核心概念**：需求中要求的主动巡检/采集/控制动作，必须有真实可执行的实现模块与对应测试（不得退化为纯手工填写表单的静态台账）。
- **`mutating` 模式附加红线**：
  - 所有写接口必须具备认证与细粒度授权（RBAC），并记录可追溯的审计日志。
  - 写操作必须防重/冲突保护（`409`）且对下游超时严禁盲目自动重试（`504`）。
  - P4b 自动化测试必须真实覆盖并跑通 4 类负面安全用例：`401` 未认证、`403` 越权、`409` 冲突防重、超时不重试。
  - 严禁未经人类明确授权对生产集群、生产数据库或真实基础设施执行写操作或破坏性命令。

### 自动打回与 3 轮熔断
- 每阶段内部遇到测试、构建、扫描或 `vibe_gate.py check` 失败时，自动根据错误修复并重试；
- **同一阶段连续失败达 3 轮触发熔断（退出码 2）**，必须立即停手向人类汇报失败证据，严禁绕过门禁。
<!-- VIBE-GUARD-END -->

## 2. P1–P5 技能路由与固定产物

> **双工具调用约定**：Codex 使用 `$<skill>` 触发；Antigravity 通过 `.agents/skills.json` 自动发现或直接读取对应 `SKILL.md` 执行。

| 阶段 | 串联 Skill | 固定输出路径 | 门禁与人工确认点 |
|---|---|---|---|
| **P1 意图、风格与原型** | `devops-brainstorming` → `ui-ux-pro-max`（3 套风格对比）→ `frontend-design` | `docs/vibe/01-design.md`、`docs/vibe/01-prototype/style-picker.html`、`docs/vibe/01-prototype/index.html` | `check p1` → **人工验收原型 + `approve p1`** |
| **P2 技术栈与核心机制** | `stack-selector`(草案) → `grilling`（必问：核心运维机制、前后端语言/框架、存储/实例、部署）→ `stack-selector`(定稿) | `docs/vibe/02-architecture.draft.md`、`docs/vibe/02-grill.md`、`docs/vibe/02-architecture.md` | `check p2` → **人工确认技术栈与核心机制 + `approve p2`** |
| **P3 规格、骨架与逻辑** | `to-spec` → `project-init` → `devops-writing-plans` | `docs/vibe/03-spec.md`、`docs/vibe/03-openapi.yaml`、`docs/vibe/03-tasks.md`、空目录骨架、`docker-compose.yml`、填好 `.vibe/state.json` 命令 | `check p3`（含骨架安全红线）→ **人工确认骨架、逻辑与用例 + `approve p3`** |
| **P4a 前端实现与实机启动** | `html-to-mui-react`（保真还原原型，遵守生产 UI 基线）→ `prototype-parity-review` | `frontend/` 可构建可启动前端工程 | `check p4a`（含构建 + 禁 Mock + 禁原生 `<select>`）→ **人工打开前端验收 + `approve p4a`** |
| **P4b 后端实现、实测与互检** | `test-driven-development` + `verification-before-completion` → `code-review` + `ops-readiness-review` | `backend/`（含核心采集/执行模块 + 全量安全测试）+ `docs/vibe/04-code-review.md`、`docs/vibe/04-ops-readiness.md` | `check p4b` → **人工验收后端实测与审查证据 + `approve p4b`** |
| **P5 真环境验收与放行** | `playwright-e2e-debug-report` + `playwright-cli`（或测试环境联调验证） | `docs/vibe/05-e2e-report.md`、证据文件、`docs/vibe/05-release-gate.json` | `check p5` → **人工终验拍板 + `approve p5`** |

## 3. 前后端合体规范

- 统一目录布局：`frontend/`（前端源码，直连 `/api/*` OpenAPI 接口）+ `backend/`（后端源码）+ 根目录 `docker-compose.yml`。
- 遵循 **P4a 无后端双态验收模式**：生产构建必须锁定 `VITE_USE_MOCK=false`；仅在 `import.meta.env.DEV` 且 `/health` 不可达时启用本地验收适配，P4b 启动后端后自动零改动切真联调。
- `P3` 结束前必须在 `.vibe/state.json` 的 `commands` 中填写真实可执行的 `frontend_build` 与 `backend_test`。

## 4. 项目补充规则（供 `project-init` 与团队追加）

> 在此处补充项目专属的技术栈约定、目录说明与领域词汇；请勿改动上方 `VIBE-GUARD` 区块。
