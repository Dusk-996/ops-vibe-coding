# 配套 Skill 路由与微调清单（v3.3）

> 配套仓库：[skills-manager-backup](https://github.com/Dusk-996/skills-manager-backup)（微调分支：`codex-vibe-v2`），精确版本 SHA-256 锁定见 [skill-lock.json](skill-lock.json)。

## 1. Codex / Antigravity 分阶段 Skill 路由表

| 阶段 | 串联 Skill | 作用 | 是否已微调适配 v3 |
|---|---|---|---|
| **P1** | `devops-brainstorming` → `ui-ux-pro-max` → `frontend-design` | 需求与 Non-Goals 落盘 → 3 套风格对比页 → 高保真交互原型 | `devops-brainstorming` 已微调 |
| **P2** | `stack-selector` → `grilling` → `stack-selector` | 架构草案 → 逐项压测技术栈与核心运维机制 → FINAL 定稿 | 原生适配 |
| **P3** | `to-spec` → `project-init` → `devops-writing-plans` | OpenAPI 与规格 → 空工程骨架 → P4a/P4b 分段任务书 | `project-init`、`devops-writing-plans` 已微调 |
| **P4a** | `html-to-mui-react` → `prototype-parity-review` | 按生产 UI 基线还原前端 → 原型一致性核对 | 原生适配（须遵守 `frontend-ui-baseline.md`） |
| **P4b** | `test-driven-development` + `verification-before-completion` → `code-review` + `ops-readiness-review`（可选 `devops-requesting-code-review`） | 核心采集/业务与安全用例实测 → 双轴代码与运维就绪审查 | `code-review`、`devops-requesting-code-review` 已微调 |
| **P5** | `playwright-cli` / `playwright-e2e-debug-report` | 真环境端到端联调、留痕与放行报告（无浏览器环境走 API 实机探活 + 人工浏览器验收） | 原生适配 |

---

## 2. 本次在 `skills-manager-backup`（`codex-vibe-v2`）完成的 5 处精准微调

1. **`devops-brainstorming`（含 `design.template.md` / `proposal.template.md`）**：
   - 解除“结束后严禁调 `frontend-design`”的死锁，Web 平台需求在 P1 衔接 `ui-ux-pro-max` → `frontend-design` 并输出 `docs/vibe/01-design.md`；
   - 清理模板中遗留的 Java 历史业务注释（`CommonAuthorization`、`V1 店铺`、`继承链`）。
2. **`project-init`**：
   - 解除对跨目录相对路径 `../profile/ops-engineer-cn.yml` 和 `../scripts/devops-skillctl.ps1` 的强依赖（缺失时自动跳过）；
   - 优先维护根目录 `AGENTS.md` 并严禁篡改 `VIBE-GUARD` 保护区块。
3. **`devops-writing-plans`**：
   - 清理 Java 专属示例（`XxxEnum.java`、`BaseHandler`）；
   - 对接 `docs/vibe/03-spec.md` / `03-openapi.yaml` → 输出 `docs/vibe/03-tasks.md`，强制拆分为 `P4a` 前端验收与 `P4b` 后端实现两段，并移除对冲突技能 `superpowers:executing-plans` 的强制依赖。
4. **`code-review`**：
   - 删除废弃的 `/setup-matt-pocock-skills` 引导；
   - 兼容 Codex / 单会话分两段独立审查（不再绑定 Claude 专属 `Agent` 工具），输出直连 `docs/vibe/04-code-review.md`。
5. **`devops-requesting-code-review`**：
   - 修正 2 处写错的模板路径（`requesting-code-review/` → `devops-requesting-code-review/`）；
   - 去除 Claude 专属 `Task`/`general-purpose` 硬语法，兼容 `AGENTS.md` 与 `docs/vibe/`。

---

## 3. 明确弃用的冲突 Skill

- **`superpowers:executing-plans`**：该 Skill 要求遇歧义自行拍板并跨阶段自动连续执行不停手，与 Ops Vibe Coding **“阶段间强制停手人工确认、P4a 前端验收后再写后端”** 核心原则直接冲突，已从流水线永久移除。
