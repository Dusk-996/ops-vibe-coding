# P4b 运维就绪审查报告（Ops Readiness Review）：ops-inspect-demo

- **风险模式**：`mutating`（含资产写入、批量导入、主动巡检触发、定时变更与外部邮件发送）
- **结论**：**PASSED（0 BLOCKER / 0 FAIL）**

## 1. 生产运维与安全红线逐项核验
| 检查维度 | 状态 | 实证与落点 |
|---|---|---|
| 密钥与凭据管理 | **PASSED** | 源码与库表 0 明文密钥/密码；SSH 仅存凭据别名；`APP_ENV=production` 缺失或弱口令/弱密钥直接 `RuntimeError` Fail-Fast 拒启 |
| 容器与编排安全 | **PASSED** | 双 Dockerfile 固定基础镜像版本（0 `:latest`），均声明非 root 运行用户（`appuser` / `101`）；`docker-compose.yml` 挂卷 `/data` 且声明 `/health` 健康探针 |
| 服务运行基线 | **PASSED** | `backend` 无 `reload=True`；受控 `CORS_ORIGINS` 白名单（无 `*`）；前端 `.env.production` 与镜像构建锁死 `VITE_USE_MOCK=false` |
| RBAC 鉴权与全量审计 | **PASSED** | 全部写接口强制校验 `admin` Bearer Token；`401` 未登录与 `403` `viewer` 越权全部阻断并写入 `audit_logs` |
| 并发防重与超时不重试 | **PASSED** | 巡检与推送均加非阻塞并发锁（冲突立即 `409`）；SSH 连接 5s/执行 8s、SMTP 10s 超时立即终止返 `504`，测试断言底层仅调用 1 次（绝不重试） |
| 邮箱双模式与 QQ/企业兼容 | **PASSED** | 未配 `SMTP_HOST` 自动安全走本地模拟收件箱；配置 `SMTP_HOST` 时自动兼容 `465 SSL`（如 QQ 邮箱）与 `587 STARTTLS`（如企业邮箱） |
| 定时任务幂等与持久化 | **PASSED** | `schedule_config` 持久化落库重启自动重载；`mark_schedule_triggered` 原子更新同分钟防重发 |

## 2. 生产上线前运维配置建议（非阻断）
1. 生产部署远程 SSH 巡检时，建议在只读目录 `/run/ssh_keys/` 预先挂载 `known_hosts`，后端将自动启用严格的 `paramiko.RejectPolicy()` 防止中间人攻击。
2. 生产发送真实邮件（如 QQ 邮箱）时，通过环境变量或 `.env` 注入 `SMTP_HOST=smtp.qq.com`、`SMTP_PORT=465`、`SMTP_USER` 与 **16 位 SMTP 授权码**（`SMTP_PASS`），严禁将真实 `.env` 提交进 Git。
3. **本机未安装的外部静态扫描器（如实记录）**：`ruff`、`bandit`、`gitleaks`、`hadolint` 未在本机安装，本次通过 `vibe_gate.py` 内置硬规则扫描与人工逐文件审查覆盖，建议在 CI 流水线补齐这 4 项工具。
