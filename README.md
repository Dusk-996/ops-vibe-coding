# Ops Vibe Coding v3.3

> 面向**不会写代码的运维工程师**、专为 **Codex**（兼顾 Antigravity）设计的**生产级 Web 运维平台 Vibe Coding 方法论与确定性门禁系统**。

核心理念：**阶段内让机器与机器靠固定路径和硬门禁全自动闭环，阶段间强制停手由人类用大白话验收拍板；先起前端验收通过，再写后端与联调。**

---

## 一、全流程 6 阶段总览（P1 → P5）

| 阶段 | 核心目标 | 串联 Skill（Codex `$<name>`） | 强制人工确认点 |
|---|---|---|---|
| **P1 意图、风格与原型** | 定边界（含 Non-Goals）→ 3 套风格对比选定 → 可交互高保真原型 | `devops-brainstorming` → `ui-ux-pro-max` → `frontend-design` | 打开原型确认界面与交互 → `approve p1` |
| **P2 技术栈与核心机制** | 逐项拍板前后端语言框架 + **核心运维采集/执行机制** + 存储/部署 | `stack-selector` → `grilling` → `stack-selector` | 确认技术栈与核心机制 → `approve p2` |
| **P3 规格、骨架与用例** | 输出 OpenAPI、规格、P4a/P4b 任务书、空工程骨架（含容器红线预扫） | `to-spec` → `project-init` → `devops-writing-plans` | 确认目录骨架、逻辑流与用例 → `approve p3` |
| **P4a 前端实机验收** | 保真实现前端（禁原生 `<select>`、左表右抽屉、无后端双态预览）并启动 | `html-to-mui-react` → `prototype-parity-review` | 浏览器实机点验前端 → `approve p4a` |
| **P4b 后端采集与互检** | 实现真实核心引擎 + 安全测试（401/403/409/504 不重试）+ 双审查 | `test-driven-development` + `verification-before-completion` → `code-review` + `ops-readiness-review` | 验收联调效果与实测证据 → `approve p4b` |
| **P5 真环境联调放行** | 真实前后端全链路探活、收集证据、生成 `05-release-gate.json` | `playwright-cli` / `playwright-e2e-debug-report`（或实机联调） | 最终上线放行拍板 → `approve p5` |

---

## 二、5 分钟快速上手（新运维 Web 项目）

### 1. 初始化项目（一键生成受保护的 `AGENTS.md` 与 `.vibe/state.json`）
```bash
# 含写操作/巡检触发/邮件发送的运维平台选 --mode mutating；纯只读看板选 --mode readonly
python ../ops-vibe-coding/scripts/vibe_gate.py init \
  --project ./my-ops-platform \
  --name my-ops-platform \
  --mode mutating
```

### 2. 在 Codex 中按阶段驱动（每步机器校验 + 人工拍板）
```bash
# 阶段完成由 Agent 自动运行硬校验（退出码 0 才算通过；连续失败 3 轮自动熔断交人类）
python ../ops-vibe-coding/scripts/vibe_gate.py check p1 --project .

# 人类验收满意后显式放行（严禁 Agent 代签）
python ../ops-vibe-coding/scripts/vibe_gate.py approve p1 --project . --by ops-user --note "原型确认通过"

# 随时查看全阶段状态与命令配置
python ../ops-vibe-coding/scripts/vibe_gate.py status --project .
```

---

## 三、方法论核心文档与标杆案例

- **执行流程**：[workflow/pipeline.md](workflow/pipeline.md) — P1–P5 固定产物路径、P2 反向校准 P1 闭环与 P4a/P4b 分段规范
- **人工门禁与熔断**：[workflow/human-gates.md](workflow/human-gates.md) — 阶段末三段大白话汇报模板、3 轮熔断与严禁代签规则
- **运维与安全红线**：[workflow/risk-boundaries.md](workflow/risk-boundaries.md) — `readonly` vs `mutating`、401/403/409/504、生产 Fail-Fast、动态凭据加密热配与 SMTP/SSH 实践
- **生产前端 UI 基线**：[workflow/frontend-ui-baseline.md](workflow/frontend-ui-baseline.md) — 禁原生 `<select>`、去源码预览、左表右抽屉、10s 悬浮通知与运维人话文案
- **配套 Skill 路由与锁文件**：[references/skills.md](references/skills.md)、[references/skill-lock.json](references/skill-lock.json)
- **端到端标杆案例**：[examples/ops-inspect-platform/](examples/ops-inspect-platform/) — **智能服务器巡检与定时邮件推送平台**（React 18 + Vite + FastAPI + SQLite + 真实 `local`/`ssh`/`mock` 采集 + Fernet 加密多发件箱 + QQ/标准 SMTP 实测通过）
- **K8s 生产护栏模板**：[templates/k8s-guardrails/deployment.yaml](templates/k8s-guardrails/deployment.yaml)
