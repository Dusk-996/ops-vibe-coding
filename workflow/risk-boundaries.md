# 运维风险分级与生产安全红线（Ops Vibe Coding v3.3）

## 1. 风险模式划分（初始化 `init --mode` 锁定）

| 模式 | 适用场景 | 核心约束 |
|---|---|---|
| **`readonly`** | 纯监控看板、资产查询、日志检索 | 禁止暴露写接口；仍须遵守禁硬编码密钥、非 root 容器、受控 CORS、禁 `:latest` |
| **`mutating`** | 含资产增删改、批量导入、主动巡检触发、配置变更、邮件/告警外发 | 叠加全部 `mutating` 硬红线：RBAC 鉴权、全量审计、并发防重 `409`、下游超时 `504` 不重试、4 类负面安全用例必测 |

---

## 2. 强制生产安全红线（机器门禁 + 审查双重兜底）

### 2.1 凭据、密钥与动态通道热配（#9 / #19）
- **0 明文硬编码**：源码、配置文件模板、日志与数据库中严禁出现明文私钥、Token 或真实密码；本地运行凭据仅放 `.env`（必须加入 `.gitignore`）。
- **生产 Fail-Fast**：`APP_ENV=production` 启动时必须校验 `AUTH_SECRET`、管理员与只读口令非空、长度 `>= 12` 且非占位符，以及 `CORS_ORIGINS` 不含 `*`；任一不满足直接抛异常拒启，严禁静默回退弱默认密码。
- **动态平台凭据 Web 热配与多账号加密存档（#19）**：
  - 对于发件邮箱 SMTP 授权码等运维常用动态通道凭据，采用 **Web 热配 + 主密钥加密多账号存档** 模式（参考 Zabbix / JumpServer）：
    1. 仅 `admin` 可新增、切换、删除发件账号；
    2. 后端用环境变量主密钥（`CREDENTIAL_MASTER_KEY` 或 `AUTH_SECRET` 派生 Fernet / AES-GCM 密钥）加密后存库；
    3. API 响应**永不回显明文或密文**（仅返 `has_auth_code: true/false`），再次修改留空自动保留原密文；
    4. 前端通过下拉框一键选择已保存账号免重启热切换，全程不再反复接触授权码，同时保留环境变量 / K8s Secret 注入兜底。

### 2.2 远程采集与外部通知工程规范（#11 / #20）
- **禁止偷换核心能力**：需求要求主动采集/检测/控制的系统，必须具备真实可执行采集模块（如本机 `ctypes`/`/proc`、远程 `paramiko` 只读白名单命令），并在 `.vibe/state.json` 配置 `core_test_pattern` 由 `check p4b` 验证真实测试通过。
- **SSH 只读采集红线**：执行写死在后端常量中的固定只读命令（绝不拼接前端输入防命令注入）；私钥路径校验阻断 `..`/`/`/`\` 路径穿越；连接 `5s` / 执行 `8s` 超时即隔离记 `TIMEOUT` 且**绝不自动重试**；生产挂载只读 `known_hosts` 启用严格 `RejectPolicy`。
- **外部邮件/报告“总—分”原则与 SMTP 兼容（#20）**：
  - 巡检与告警邮件采用 **总览 KPI + 仅详展异常及需关注主机 + 正常主机省略明细** 结构，避免大集群刷屏掩盖真正故障；
  - Python `smtplib` 对接 QQ 邮箱（465 SSL）与企业邮箱（587 STARTTLS）须使用 RFC 规范中文 `Header`、`formataddr`、`Date`、`Message-ID`、显式 `ehlo()`，并在 `finally` 中收紧 `quit()` 短超时（2s）且捕获关闭异常，防止 `sendmail` 成功后因对端不回 `221` 误报失败；
  - 精准解包 `smtplib.SMTPServerDisconnected` 包装后的底层 `TimeoutError` / `timed out` 并返回 `504`，**严禁任何自动重试**。

### 2.3 `mutating` 必测 4 类负面安全用例（`check p4b` 硬校验）
1. **`401 Unauthorized`**：未携带有效 Token 调用写接口被拒、不产生数据变更且落审计；
2. **`403 Forbidden`**：只读角色（`viewer`）调用写接口被拒、不产生数据变更且落审计；
3. **`409 Conflict`**：持有并发锁时重复发起巡检或推送被立即拦截并落审计；
4. **`504` 超时不重试**：模拟下游超时后立即返 `504` 并断言底层调用 `call_count == 1`。

### 2.4 容器、编排与扫描基线
- 双 Dockerfile 均固定基础镜像版本（0 `:latest`）、非 root `USER` 运行；后端禁 `reload=True` 与 `CORS *`；前端生产 `.env.production` 与镜像构建锁死 `VITE_USE_MOCK=false`；
- K8s 工作负载参考 [templates/k8s-guardrails/deployment.yaml](../templates/k8s-guardrails/deployment.yaml)，强制声明 `livenessProbe`、`readinessProbe` 与 `resources.limits`；
- `vibe_gate.py` 自动探测并执行 `gitleaks`、`ruff`、`bandit`、`hadolint`，未安装项在 `05-release-gate.json` 的 `unverified_items` 如实单列。
