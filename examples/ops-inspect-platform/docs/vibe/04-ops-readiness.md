# 运维就绪审查报告（Ops Readiness Review — P6 Docker Compose 终审）

**总体结论：** `PASS_WITH_RISKS`（全 12 域 **0 BLOCKER / 0 MAJOR / 0 MINOR**；应用代码、双端测试、Compose 配置校验与 WSL 真机 SQLite 热备恢复均已通过；仅保留 2 项因本机环境限制导致的明确 `NOT_VERIFIED` 项交由用户上线前按操作手册补验：Docker Daemon 实际构建/拉起验证、真实远程 SSHD 靶机实网验证）

> **审查说明**：本次依据 `ops-readiness-review` 12 大风险领域清单（A~L）补全了 **P6 阶段 K 域（Deployment）与 L 域（Failure/Recovery）** 的部署审查，严格遵守“不伪造未运行的 Docker 构建结果”的实证原则。

## 审查范围与风险画像

- **系统与修订版本**：智能服务器巡检与定时邮件推送平台（`ops-inspect-demo`，P6 Docker Compose 完整交付版 `v1.0.0`）
- **用户与信任边界**：内网运维团队双角色（`admin` / `viewer`），除 `/health` 与 `/api/auth/login` 外全部读/写接口均强制 HMAC-SHA256 Bearer Token 鉴权。
- **管理目标与爆炸半径**：管理内部服务器静态清单，通过只读 `local` / `ssh` 驱动采集内存/CPU，通过加密存档多发件箱 SMTP 推送总—分报告；属于 `mutating` 风险模式。
- **P6 部署形态**：单实例 Docker Compose 双非 root 容器（前端 `nginxinc/nginx-unprivileged:1.27.3-alpine` 仅暴露 `8080` 反代 `/api/` 与 `/health`；后端 `python:3.11.11-slim-bookworm` 仅在内部 `ops_net` 监听 `8000`，数据卷 `ops_inspect_data:/data`，只读挂载 `ssh_keys:/run/ssh_keys:ro`）。
- **证据限制**：
  1. 本机未启动 Docker Desktop Daemon，因此容器镜像实际构建（`docker compose build`）与 `docker compose up -d` 实机拉起标为 `NOT_VERIFIED`（已完成官方 `docker compose config` Schema 校验与 `vibe_gate.py check p6` 硬扫描）；
  2. 远程 SSH 采集已完成单测与真 Linux 严格 `known_hosts` 拒连验证，真实远程 SSHD 靶机实网采集标为 `NOT_VERIFIED`；
  3. 外部扫描器（`gitleaks`、`ruff`、`bandit`、`hadolint`）未在本机安装，由 `vibe_gate.py` 硬扫描与逐文件实审兜底。

---

## 检查领域覆盖（12 域全量核查）

| 检查领域 | 状态 | 证据摘要 | 说明 |
|---|---|---|---|
| A. 破坏性操作 | `ASSESSED` | `STATIC` + `TESTED` + `RUNTIME_VERIFIED` | 写/删/覆盖强制 `require_admin` + 审计 + `X-Op-Id`；批量导入限 `2MB/2000行`；删除与推送二次确认；P6 已补齐数据库热备与版本回滚路径。 |
| B. 认证与授权 | `ASSESSED` | `STATIC` + `TESTED` + `RUNTIME_VERIFIED` | 全部 7 个读接口强制 `require_authenticated`（`401`），全部写接口强制 `require_admin`（`401`/`403`）；前端未登录门面引导、退出/401 清敏感内存态。 |
| C. 审计 | `ASSESSED` | `STATIC` + `TESTED` + `RUNTIME_VERIFIED` | 写操作、登录、关键敏感读拒访、调度异常与 `401/403/409/500/502/504` 全入 `audit_logs` 且带 `op_id`，不落明文凭据。 |
| D. Secret 与凭证 | `ASSESSED` | `STATIC` + `TESTED` + `RUNTIME_VERIFIED` | 源码与镜像层（`.dockerignore` 排除 `.env`/`*.db*`/`ssh_keys/`）0 明文凭据；生产 Fail-Fast 校验全部密钥与独立 `CREDENTIAL_MASTER_KEY`；发件箱授权码 Fernet 加密存库永不回显；SSH 仅存别名并只读挂载 `:ro`。 |
| E. 远程执行 | `ASSESSED` | `STATIC` + `TESTED` + 局部 `RUNTIME_VERIFIED` | 生产默认 `SSH_STRICT_HOST_KEY=true` 缺 `known_hosts` 拒连；`stdout` 限 64KB、`stderr` 限 4KB；硬编码只读白名单命令防注入；5s/8s 超时不重试；5 并发隔离。 |
| F. Kubernetes 操作 | `NOT_APPLICABLE` | `DOCUMENTED` | 本项目选定 Docker Compose 单实例交付，不访问或操作 Kubernetes API。 |
| G. 异步任务 | `ASSESSED` | `STATIC` + `TESTED` + `RUNTIME_VERIFIED` | 调度异常落 `logger.exception` + `500` 审计不吞错；定时与手动共享 `inspect_lock`（`409`）；同分钟 SQLite 原子幂等；容器强制单 worker 避免多副本重复调度。 |
| H. API 可靠性 | `ASSESSED` | `STATIC` + `TESTED` + `RUNTIME_VERIFIED` | Pydantic 校验、`413` 限流、Nginx `client_max_body_size 3m`、CSV 防公式注入、SMTP 报错脱敏与全链路 `X-Op-Id`。 |
| I. 可观测性 | `ASSESSED` | `STATIC` + `TESTED` + `RUNTIME_VERIFIED` | 全模块标准 `logging`（`ops_inspect.*`）输出至 stderr，Docker Compose 配置 `json-file` 日志轮转（20MB×5 / 10MB×3）；有 `/health` 探针与全量审计。 |
| J. 数据生命周期 | `ASSESSED` | `STATIC` + `TESTED` + `RUNTIME_VERIFIED` | `outbox_messages`（500）与 `audit_logs`（2000）自动裁剪；SQLite WAL 命名卷持久化；`deploy/backup-db.sh` 已在 WSL 真机实测 WAL 热备 + 误删归零后 100% 校验恢复（保留 14 份）。 |
| K. 部署 | `ASSESSED`（容器实机拉起 `NOT_VERIFIED`） | `STATIC` + `TESTED` + 局部 `RUNTIME_VERIFIED` | 配置与 Secret 经 `.env` 分离（脚本预检拒占位符与 `*`）；双非 root 固定版本镜像（0 `:latest`）、`cap_drop: ALL`、`no-new-privileges`、CPU/内存限额、优雅退出 `SIGTERM`（15s）、健康检查编排（`service_healthy`）、单 worker 约束与按版本 Tag 回滚脚本均已落盘并通过 `docker compose config` 与 `vibe_gate.py check p6`。仅缺 Docker Daemon 实机拉起验证。 |
| L. 失败与恢复 | `ASSESSED` | `STATIC` + `TESTED` + `RUNTIME_VERIFIED` | 单台超时隔离、SMTP `504` 不重试、调度异常可诊断、`SIGTERM` 重启持久化、SQLite 热备与误删灾难恢复已在 WSL 真机演练通过，且提供按镜像版本 Tag 一键回滚脚本。 |

---

## 阻断 / 主要 / 次要问题

- **阻断问题（BLOCKER）**：无（0）。
- **主要问题（MAJOR）**：无（0）。
- **次要问题（MINOR）**：无（0）。

---

## 未验证项与上线前建议动作

1. **Docker Daemon 实机构建与容器启动验证（`NOT_VERIFIED` — 首次上线必做）**：
   - 原因：当前开发宿主机 Docker Desktop Daemon 未启动。
   - 关闭动作：在已启动 Docker 的宿主机或目标 Linux 服务器执行 `bash deploy/build-and-deploy.sh build 1.0.0 && bash deploy/build-and-deploy.sh up 1.0.0`，验证 `/health -> 200` 与登录后核心巡检流程。
2. **真实远程 SSHD 靶机实网采集（`NOT_VERIFIED` — 纳管远程主机前建议补测）**：
   - 关闭动作：将只读私钥与 `known_hosts` 放入 `ssh_keys/`，对一台测试 Linux 主机执行单台检测核验。

---

## 证据

- **P4b / P5 应用测试证据**：Windows `pytest` 20/20 PASSED（`3.19s`）、WSL Linux `pytest` 20/20 PASSED（`docs/vibe/05-pytest-linux.log`）、WSL 8 大域真 Linux E2E 32/32 PASSED（`docs/vibe/05-e2e.log`）。
- **P6 部署验证证据**：`docs/vibe/06-deploy.log`（官方 `docker compose config` 退出码 `0`、`bash -n` 通过、防 `latest` 拦截实测通过、WSL 真机 SQLite WAL 热备与误删灾难恢复 100% 还原）、`docs/vibe/06-deploy-report.md`、`docs/vibe/06-release-gate.json`。
