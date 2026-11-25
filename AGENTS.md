# Ops Vibe Coding 仓库维护中枢（AGENTS.md）

本仓库是面向运维工程师（非专职开发者）的 **生产级 Web 运维平台 Vibe Coding 方法论与确定性门禁引擎（v3.3）**，与 [skills-manager-backup](https://github.com/Dusk-996/skills-manager-backup) 深度配套。

## 仓库核心结构（保持精简，禁止重新膨胀）

| 路径 | 职责 |
|---|---|
| `scripts/vibe_gate.py` | 唯一确定性门禁脚本（纯 Python 标准库，无第三方依赖） |
| `templates/AGENTS.md` | 目标生产项目的 `AGENTS.md` 模板（含 `VIBE-GUARD` SHA-256 防篡改红线） |
| `templates/k8s-guardrails/` | 生产级 K8s 护栏清单模板（非 root、探针、限额、Secret 引用） |
| `workflow/` | 精简方法论文档：`pipeline.md`、`human-gates.md`、`risk-boundaries.md`、`frontend-ui-baseline.md` |
| `references/` | Skill 路由说明（`skills.md`）与真实 SHA-256 锁定清单（`skill-lock.json`） |
| `examples/ops-inspect-platform/` | 经端到端全流程实战验证的标杆案例（智能服务器巡检与定时邮件推送平台） |

## 维护硬规范

1. **改规则必同步脚本**：任何新增的机器可检规则必须同时写入 `templates/AGENTS.md`（`VIBE-GUARD` 内）与 `scripts/vibe_gate.py`，保持文档与机器校验单一事实源。
2. **严禁引入外部运行依赖**：`scripts/vibe_gate.py` 必须仅依赖 Python 3.10+ 标准库，确保任何运维终端开箱即跑。
3. **标杆案例防泄漏红线**：`examples/` 内严禁提交 `.env`、`*.db`、`node_modules/`、`dist/` 或任何真实密钥/授权码；每次修改门禁后须对 `examples/ops-inspect-platform/` 跑一次静态红线校验。
4. **同步 Skill 锁文件**：微调 `skills-manager-backup` 中的核心 Skill 后，必须重新计算并更新 `references/skill-lock.json` 的真实 SHA-256。
