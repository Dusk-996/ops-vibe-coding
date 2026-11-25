# 运维风险分级与生产安全红线（Ops Vibe Coding v3.4）

## 1. 风险模式划分（初始化 `init --mode` 锁定）

| 模式 | 适用场景 | 核心约束 |
|---|---|---|
| **`readonly`** | 纯监控看板、资产查询、日志检索 | 禁止暴露写接口；仍须遵守禁硬编码密钥、认证保护敏感拓扑、受控 CORS，P6 部署须非 root / 禁 `:latest` |
| **`mutating`** | 含资产增删改、批量导入、主动巡检触发、配置变更、邮件/告警外发 | 叠加全部 `mutating` 硬红线：读写分层 RBAC 鉴权、全量审计、并发防重 `409`、下游超时 `504` 不重试、4 类负面安全用例必测 |

---

## 2. 应用级生产安全红线（P3–P5 生效，`builtin_app_scan` + `ops-readiness-review` 兜底）

### 2.1 认证、凭据与动态通道热配（#9 / #19）
- **最小权限认证**：除 `/health` 与登录接口外，涉及内网资产 IP、SSH 凭据别名、发件邮箱与操作审计的只读接口同样强制登录鉴权（`viewer`/`admin`），写接口强制 `admin` 权限；前端未登录展示门面引导，退出或 401 时立即清空内存中的敏感数据。
- **0 明文硬编码**：源码、配置文件模板、日志与数据库中严禁出现明文私钥、Token 或真实密码；本地运行凭据仅放 `.env`（必须加入 `.gitignore`）。
- **生产 Fail-Fast**：`APP_ENV=production` 启动时必须校验 `AUTH_SECRET`、可选独立 `CREDENTIAL_MASTER_KEY`、管理员与只读口令非空、长度 `>= 12` 且非占位符，以及 `CORS_ORIGINS` 不含 `*`；任一不满足直接抛异常拒启，严禁静默回退弱默认密码。
- **动态平台凭据 Web 热配与多账号加密存档（#19）**：
  - 仅 `admin` 可新增、切换、删除发件账号；
  - 后端用主密钥（`CREDENTIAL_MASTER_KEY` 或 `AUTH_SECRET` 派生 Fernet / AES-GCM 密钥）加密后存库；
  - API 响应**永不回显明文或密文**（仅返 `has_auth_code: true/false`），再次修改留空自动保留原密文；
  - 前端通过下拉框一键选择已保存账号免重启热切换，同时保留环境变量注入兜底。

### 2.2 远程采集、后台调度与外部通知工程规范（#11 / #20）
- **禁止偷换核心能力**：需求要求主动采集/检测/控制的系统，必须具备真实可执行采集模块（如本机 `ctypes`/`/proc`、远程 `paramiko` 只读白名单命令），并在 `.vibe/state.json` 配置 `core_test_pattern` 由 `check p4b` 验证真实测试通过。
- **SSH 只读采集红线**：执行写死在后端常量中的固定只读命令（防命令注入）；私钥路径校验阻断 `..`/`/`/`\` 路径穿越；生产态默认严格 `SSH_STRICT_HOST_KEY=true`（缺 `known_hosts` 直接拒连，严禁静默降级 `AutoAddPolicy`）；限制远程 `stdout`/`stderr` 读取字节上限（如 64KB/4KB）；连接 `5s` / 执行 `8s` 超时即隔离记 `TIMEOUT` 且**绝不自动重试**。
- **调度可观测与防重**：后端全模块接入标准 `logging`；后台定时调度循环**严禁 `except Exception: pass` 静默吞错**，异常必须记录堆栈日志并写入 `500` 审计；定时与手动巡检共享并发锁防撞车；审计与发件历史表设保留上限自动裁剪防磁盘膨胀。
- **外部邮件/报告“总—分”原则与脱敏（#20）**：
  - 巡检与告警邮件采用 **总览 KPI + 仅详展异常及需关注主机 + 正常主机省略明细** 结构；
  - Python `smtplib` 对接 QQ 邮箱（465 SSL）与企业邮箱（587 STARTTLS）须使用 RFC 中文 `Header`、`formataddr`、`Date`、`Message-ID`、显式 `ehlo()`，并在 `finally` 中收紧 `quit()` 短超时（2s）；
  - 精准解包底层超时返回 `504`（**严禁任何自动重试**）；其他 SMTP 失败向前端返回脱敏运维人话，完整异常堆栈仅写服务端日志。

### 2.3 `mutating` 必测 4 类负面安全用例（`check p4b` 硬校验）
1. **`401 Unauthorized`**：未携带有效 Token 调用受保护读/写接口被拒、不产生数据变更；
2. **`403 Forbidden`**：只读角色（`viewer`）调用写接口被拒、不产生数据变更并落审计；
3. **`409 Conflict`**：持有并发锁时重复发起巡检或推送被立即拦截并落审计；
4. **`504` 超时不重试**：模拟下游超时后立即返 `504` 并断言底层调用 `call_count == 1`。

---

## 3. 部署级生产安全红线（仅 P6 阶段生效，`check p6` 硬校验）

> **边界铁律**：本节所有规则与扫描器**只在 P5 全面测试通过、进入 P6 部署阶段后启用**；P1–P5 禁止提前生成部署文件。

- **容器与编排（若 P6 选用 Docker/Compose）**：固定基础镜像版本（0 `:latest`）、非 root `USER` 运行、镜像构建与编排禁 `VITE_USE_MOCK=true`；探测并执行 `hadolint`。
- **Linux 服务托管（若 P6 选用 `systemd` + Nginx）**：`systemd` unit 必须显式声明非 root `User=`；Nginx 仅反向代理 `/api/*` 与 `/health` 并不暴露 `.env`/SQLite 文件。
- **Kubernetes（若 P6 选用 K8s）**：参考 [templates/k8s-guardrails/deployment.yaml](../templates/k8s-guardrails/deployment.yaml)，强制声明 `livenessProbe`、`readinessProbe` 与 `resources.limits`。
- **持久化备份与回滚**：P6 必须交付并在目标等价环境实机演练数据库备份恢复（如 SQLite `.backup`）与版本回滚步骤，留存 `docs/vibe/06-deploy.log` 与 `docs/vibe/06-deploy-report.md`，最终由 `check p6` 签发 `docs/vibe/06-release-gate.json`。
