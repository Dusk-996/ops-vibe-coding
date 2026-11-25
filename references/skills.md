# 配套 Skill 路由、微调清单与使用边界（v3.4）

> 配套仓库：[skills-manager-backup](https://github.com/Dusk-996/skills-manager-backup)（微调分支：`codex-vibe-v2`），精确版本 SHA-256 锁定见 [skill-lock.json](skill-lock.json)。

## 1. 什么时候必须走 Skill，什么时候不该强套？

基于真实 `demo` 项目 A/B 实证对比结论：
- **必须实读并逐项执行清洗后 Skill 的场景（高风险 / 防盲区托底）**：
  - P1 原型边界定型、P2 技术栈压测、P4a 原型一致性核对（`prototype-parity-review`）、P4b 代码与 12 域运维就绪审查（`code-review`、`ops-readiness-review`）、P5/P6 实证验证（`verification-before-completion`）。
  - **价值本质**：大模型靠直觉容易漏掉长尾运维安全红线（如读接口裸奔、`known_hosts` 静默降级、调度 `except: pass` 吞错、日志表无限涨）；实读清单与 4 级证据标尺能稳定托住下限。
- **不建议强套重 Skill 的场景（遵循 KISS）**：
  - 单文件小改动、改文案/调样式、一次性排障脚本。
- **严禁“贴标签走过场”**：只要某个阶段路由了审查类 Skill，就必须真实读取其 `SKILL.md` 与 `references/*checklist.md` 并逐项拿代码行/命令输出举证，严禁凭感觉直接写 `PASSED`。

---

## 2. Codex / Antigravity 分阶段 Skill 路由表（P1–P6）

| 阶段 | 串联 Skill | 作用 | 微调状态 |
|---|---|---|---|
| **P1** | `devops-brainstorming` → `ui-ux-pro-max` → `frontend-design` | 需求与 Non-Goals 落盘 → 3 套风格对比页 → 高保真交互原型 | `devops-brainstorming` 已微调 |
| **P2** | `stack-selector` → `grilling` → `stack-selector` | 架构草案 → 压测技术栈、核心机制与单/多实例（**不提前锁 P6 部署编排**）→ FINAL 定稿 | `stack-selector` 已微调 |
| **P3** | `to-spec` → `project-init` → `devops-writing-plans` | OpenAPI 与规格 → 空应用骨架（**不生成部署文件**）→ P4a/P4b 分段任务书 | 全部 3 个已微调 |
| **P4a** | 按 P1 原型与 UI 基线实现（仅选 MUI 时用 `html-to-mui-react`）→ `prototype-parity-review` | 保真还原前端 → 原型一致性逐项核对（支持无自动化浏览器时用源码+构建+人工点验） | `html-to-mui-react`、`prototype-parity-review` 已微调 |
| **P4b** | `test-driven-development` + `verification-before-completion` → `code-review` + `ops-readiness-review`（可选 `devops-requesting-code-review`） | 核心采集/业务与安全单测 → 代码审查 + 12 域应用/运行就绪审查（K 域部署留待 P6） | `code-review`、`devops-requesting-code-review`、`ops-readiness-review` 已微调 |
| **P5** | `verification-before-completion`（有浏览器自动化环境时可选 `playwright-cli` / `playwright-e2e-debug-report`） | 真环境（推荐 WSL/Linux 隔离目录）全量单测与多域端到端回归，留存实测日志 | 原生适配 |
| **P6** | 按 P5 放行后拍板的部署形态交付 + `ops-readiness-review`（K 域部署终审） | 设计并演练生产部署包、权限、备份恢复与回滚，生成 `06-deploy-report.md` 与 `06-release-gate.json` | `ops-readiness-review` 已微调 |

---

## 3. 在 `skills-manager-backup`（`codex-vibe-v2`）完成的 10 处精准微调

1. **`devops-brainstorming`（含 2 份模板）**：解除 Web 原型禁止衔接 `frontend-design` 的死锁，清理 Java 遗留注释，对接 `docs/vibe/01-design.md`。
2. **`stack-selector`**：支持从 P1 已批准 HTML 原型直连 P2；在 Ops Vibe Coding 中将 P2 聚焦运行架构/技术栈，具体部署编排延后至 P6；输出路径对齐 `docs/vibe/02-architecture*.md`。
3. **`to-spec`**：删除不存在的 `/setup-matt-pocock-skills` 指引，默认本地落盘 `docs/vibe/03-spec.md`。
4. **`project-init`**：解除对外部脚本/profile 文件的硬依赖；保护根 `AGENTS.md` 的 `VIBE-GUARD`；在 Ops Vibe Coding P3 阶段**仅建应用空骨架，不提前生成 `docker-compose.yml` / `Dockerfile` 等 P6 部署文件**。
5. **`devops-writing-plans`**：清理 Java 专属示例，对接 `docs/vibe/03-tasks.md` 并强制拆分为 `P4a` 与 `P4b`，移除冲突的 `superpowers:executing-plans`。
6. **`html-to-mui-react`**：解除“先写 React+Mock 再选架构”旧顺序，明确仅 P2 选用 MUI 时在 P4a 可选使用。
7. **`prototype-parity-review`（含 `templates/report.md`）**：对接 P4a 与 `docs/vibe/04-parity-review.md`，明确无自动化浏览器环境时采用“源码核对 + 构建 + 人类实机点验”如实标注 `PASS_WITH_NOTES` 而不伪造截图。
8. **`code-review`**：删除废弃命令引导，兼容 Codex 单会话分两段独立审查，输出 `docs/vibe/04-code-review.md`。
9. **`devops-requesting-code-review`**：修正错误模板路径，去除 Claude 专属工具语法，兼容 `AGENTS.md`。
10. **`ops-readiness-review`**：适配 7 阶段流程——P4b/P5 审查应用与运行安全（尚未进入 P6 时 K 域标 `NOT_APPLICABLE` 留待 P6），P6 完成部署演练后再关闭 K 域终审。

---

## 4. 明确弃用的冲突 Skill

- **`superpowers:executing-plans`**：要求遇歧义自行拍板并跨阶段自动连续执行不停手，与 Ops Vibe Coding **“阶段间强制停手人工确认、P4a 前端验收后再写后端、P5 测试全过后再进 P6 部署”** 核心原则直接冲突，已永久移除。
