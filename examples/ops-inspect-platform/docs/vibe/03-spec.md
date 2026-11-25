# P3 核心技术规格说明书（Spec）：ops-inspect-demo

- **项目模式**：`mutating`（含目标写入、批量导入、主动巡检触发、定时修改与外部邮件发送）
- **上游依据**：`docs/vibe/01-design.md`（Rev 3）、`docs/vibe/01-prototype/index.html`（Rev 4）、`docs/vibe/02-architecture.md`（FINAL）
- **接口契约**：`docs/vibe/03-openapi.yaml`
- **实施拆分**：`docs/vibe/03-tasks.md`（严格先 `P4a` 前端启动验收，后 `P4b` 后端采集与联调）

---

## 1. 数据模型（SQLite `/data/ops_inspect.db`）

严格区分**静态目标配置字段**（人工登记或 IP 批量导入维护）与**动态巡检快照字段**（仅由采集引擎写入，用户不可手改）：

### 1.1 `targets`（纳管服务器与最新巡检快照）
| 字段 | 类型 | 分类 | 约束与说明 |
|---|---|---|---|
| `id` | INTEGER PK | 系统 | 自增主键 |
| `host` | TEXT UNIQUE NOT NULL | 静态 | 唯一主机名（如 `prod-k8s-node-01`） |
| `address` | TEXT NOT NULL | 静态 | 服务器 IP 或内网域名（如 `10.10.2.11`） |
| `type` | TEXT NOT NULL | 静态 | `物理机` / `虚拟机` / `容器节点` |
| `vendor` | TEXT NOT NULL | 静态 | 厂商标识（如 `戴尔 Dell` / `华为 TaiShan` / `阿里云 ECS` / `浪潮 Inspur` / `本地宿主机`） |
| `collector_type` | TEXT NOT NULL | 静态 | 采集驱动：`ssh` / `local` / `mock` |
| `ssh_port` | INTEGER NULL | 静态 | `ssh` 驱动必填（`1..65535`，默认 `22`） |
| `ssh_user` | TEXT NOT NULL DEFAULT '' | 静态 | `ssh` 只读账号（如 `ops-ro`） |
| `ssh_credential_ref` | TEXT NOT NULL DEFAULT '' | 静态 | SSH 私钥别名（仅别名，严禁存明文密钥/密码） |
| `mem_total` | REAL NULL | 动态只读 | 物理总内存（GB，保留 1 位小数） |
| `mem_free` | REAL NULL | 动态只读 | 真实可用剩余内存 `MemAvailable`（GB，保留 1 位小数） |
| `cores` | INTEGER NULL | 动态只读 | 逻辑 CPU 核数 |
| `cpu` | REAL NULL | 动态只读 | 实时 CPU 使用率（`0.0..100.0`，保留 1 位小数） |
| `probe_status` | TEXT NOT NULL DEFAULT 'PENDING' | 动态只读 | `PENDING` / `OK` / `WARN` / `HIGH_LOAD` / `TIMEOUT` / `UNREACHABLE` |
| `last_checked_at` | TEXT NOT NULL DEFAULT '' | 动态只读 | 最近采集时间（`YYYY-MM-DD HH:MM:SS`） |
| `probe_error` | TEXT NOT NULL DEFAULT '' | 动态只读 | 脱敏失败摘要（不含凭据与私钥路径） |
| `created_at` / `updated_at` | TEXT NOT NULL | 系统 | 创建与最后更新时间 |

### 1.2 `schedule_config`（每日定时推送规则，固定单行 `id = 1`）
- `enabled`（INTEGER `0/1`）、`push_time`（TEXT `HH:MM`）、`recipients_json`（TEXT JSON 字符串数组）、`last_triggered_minute`（TEXT `YYYY-MM-DD HH:MM`，同分钟幂等防重发）、`updated_at`（TEXT）。

### 1.3 `outbox_messages`（邮件发送记录 / 本地模拟收件箱）
- `id`、`op_id`、`delivery_mode`（`smtp` / `mock`）、`status_code`（`200` / `504` / `500`）、`recipients`、`subject`、`body_md`、`error`、`created_at`。

### 1.4 `audit_logs`（全量操作与异常审计）
- `id`、`op_id`、`actor`、`role`、`action`、`http_status`、`detail`、`created_at`。

---

## 2. 核心逻辑流

### 2.1 多驱动主动采集引擎（`backend/app/collector.py`）
1. **`local` 驱动（本机真实采集，纯 Python 标准库零外部依赖）**：
   - **Linux**：读取 `/proc/meminfo` 的 `MemTotal` 与 `MemAvailable`（老内核缺失时回退 `MemFree + Buffers + Cached`）；两次间隔 `0.5s` 读取 `/proc/stat` 首行，计算 `cpu = (total_delta - idle_delta) / total_delta * 100`；`os.cpu_count()` 获取核数。
   - **Windows**：通过 `ctypes` 调用 `kernel32.GlobalMemoryStatusEx` 获取物理总内存与可用内存；两次间隔 `0.5s` 调用 `kernel32.GetSystemTimes` 计算 `(kernel_delta + user_delta - idle_delta) / (kernel_delta + user_delta) * 100`；`os.cpu_count()` 获取核数。
2. **`ssh` 驱动（远程 Linux 只读采集，基于 `paramiko`）**：
   - 凭据加载：根据 `ssh_credential_ref` 查询 `SSH_KEY_MAP_JSON` 或只读目录 `SSH_KEYS_DIR/<ref>`（严禁路径穿越 `..`），找不到凭据直接判 `UNREACHABLE` 并脱敏报错；
   - 连接超时 `5s`，执行超时 `8s`，超时直接判 `TIMEOUT`，**绝不自动重试**；
   - 仅执行硬编码在后端常量中的只读白名单命令（绝不拼接任何前端输入）：
     ```sh
     awk '/^(MemTotal|MemAvailable|MemFree|Buffers|Cached):/{print $1,$2}' /proc/meminfo
     echo "---CORES---"; nproc 2>/dev/null || grep -c ^processor /proc/cpuinfo
     echo "---STAT1---"; head -n 1 /proc/stat
     sleep 0.5
     echo "---STAT2---"; head -n 1 /proc/stat
     ```
3. **`mock` 驱动（离线测试替身）**：
   - 依据主机名/IP 确定性生成指标或模拟异常（例如地址以 `.timeout` 结尾或 `host` 含 `timeout` 触发 `TIMEOUT`，含 `unreachable` 触发 `UNREACHABLE`），用于自动化回归测试与离线演示。
4. **健康状态判定规则**：
   - `cpu >= 80` 或 `mem_free / mem_total < 0.15` → `HIGH_LOAD`
   - `cpu >= 60` 或 `mem_free / mem_total < 0.25` → `WARN`
   - 其余 → `OK`
5. **批量巡检并发与故障隔离**：
   - `POST /api/inspect/run` 使用非阻塞锁防重入（并发中直接返回 `409 Conflict`），内部通过 `ThreadPoolExecutor(max_workers=5)` 并发采集全部目标；
   - 单台异常（`TIMEOUT` / `UNREACHABLE`）捕获后仅写入该台状态与 `probe_error`，不影响其余主机与后续报告生成。

### 2.2 静态目标批量导入与导出
- **导入**：采用 JSON Body `{ "format": "csv" | "json", "content": "...", "policy": "skip" | "overwrite" }`（单次限 `2 MB` 且最多 `2000` 行，零额外 multipart 依赖）：
  1. `POST /api/targets/import/preview`：校验必填 `host`/`address`、枚举 `collectorType`、`sshPort` 范围及文件内重复，统计已存在重名数，不写库；
  2. `POST /api/targets/import/commit`：在单个 SQLite 事务内按 `skip`（默认跳过重名）或 `overwrite`（仅覆写静态连接字段，保留原快照或重置为待检）落库；新增目标初始状态恒为 `PENDING`。
- **导出**：`GET /api/targets/export?format=csv|json` 支持同筛选条件导出；CSV 头部输出 UTF-8 BOM，并以 `'` 转义 `= + - @` 开头字段，防止电子表格公式注入。

### 2.3 每日定时巡检推送与邮箱双模式
- **定时调度**：单实例进程内后台守护线程每 `20s` 轮询一次；当 `enabled = true`、当前 `HH:MM == push_time` 且 `last_triggered_minute != YYYY-MM-DD HH:MM` 时：
  1. 先写 `last_triggered_minute`（同分钟幂等防重复触发）；
  2. 执行一次全量巡检（失败单台隔离）；
  3. 生成最新 Markdown 报告并推送到收件人列表，写入 `outbox_messages` 与 `audit_logs`。
- **手动立即推送（`POST /api/reports/push`）**：
  - 推送前非阻塞获取 `push_lock`：已被占用立即返 **`409 Conflict`**；
  - 未配置 `SMTP_HOST` 时自动走 `mock` 模式写入 `outbox_messages`；配置了 `SMTP_HOST` 时连接真实 SMTP（`timeout=10s`）；
  - SMTP 超时捕获 `TimeoutError` / `socket.timeout` 后记审计并立即返 **`504 Gateway Timeout`**，**严禁任何自动重试**。

---

## 3. 认证鉴权与生产安全基线

- **鉴权机制**：`POST /api/auth/login` 验证账号密码后签发 HMAC-SHA256 Token（`Authorization: Bearer <token>`）；
- **角色矩阵**：
  - 除 `GET /health` 与 `POST /api/auth/login` 外，全部读接口需 `viewer` 或 `admin` 登录（匿名一律 `401`）；
  - 未携带或无效 Token 访问受保护接口 → **`401 Unauthorized`**；
  - `viewer` 角色访问任意写接口（增删改、导入、巡检、改定时、推邮件） → **`403 Forbidden`**；
  - `GET /health` 免鉴权，供进程存活探活使用。
- **生产 Fail-Fast**：当 `APP_ENV=production` 时，若 `AUTH_SECRET`、可选独立 `CREDENTIAL_MASTER_KEY`、`ADMIN_PASSWORD`、`VIEWER_PASSWORD` 任一缺失/长度不足 12 位/含占位符，或 `CORS_ORIGINS` 含 `*`，应用启动时立即抛错拒启。
- **应用安全红线**：无 `reload=True`、无 `CORS *`、生产前端 `VITE_USE_MOCK=false`（生产部署打包、容器/服务权限与备份回滚红线留待 P6 部署阶段设计与校验）。

---

## 4. 验收用例清单（P4a / P4b / P5 共同基准）

| 编号 | 场景类别 | 输入 / 操作 | 预期结果 | 验证阶段 |
|---|---|---|---|---|
| **TC-01** | 前端双页与原型保真 | 启动前端并访问 `#/servers` 与 `#/schedule` | 风格 C + ≥14px、静态目标表单无内存/CPU手填项、4×6/2×6 网格时间选择器、无常驻大块 Markdown 展开 | P4a |
| **TC-02** | 目标登记与 IP 导入 | 下载 CSV 模板、上传预览、按 `skip`/`overwrite` 提交 | 新增目标初始状态为 `PENDING`（待检测），重名按策略处理，导出 CSV 含 UTF-8 BOM 且转义 `=HYPERLINK(...)` | P4a / P4b |
| **TC-03** | 本机 `local` 真实采集 | 对 `collectorType=local` 目标执行单台检测 | 返回真实的 `memTotal > 0`、`memFree > 0`、`cores >= 1`、`0 <= cpu <= 100`，状态更新为 `OK/WARN/HIGH_LOAD` | P4b |
| **TC-04** | `ssh` 驱动解析与超时隔离 | 全量巡检混合正常主机 + `ssh` 超时主机（8s） | 正常主机指标刷新成功，超时主机被隔离标记 `TIMEOUT` 且不自动重试、不拖垮整批巡检 | P4b |
| **TC-05** | 定时与手动推送报告 | 修改定时时间并手动确认推送 | `outbox_messages` 写入含汇总与明细表的 Markdown 报告，支持下载 `.md` | P4b / P5 |
| **TC-06** | 安全用例：`401` 未认证 | 不带 Token 调用登记、巡检、改定时、推送接口 | 统一返回 `401`，不产生任何状态变更并写入审计日志 | P4b |
| **TC-07** | 安全用例：`403` 越权 | `viewer` Token 调用登记、导入、巡检、推送接口 | 统一返回 `403`，不产生任何状态变更并写入审计日志 | P4b |
| **TC-08** | 安全用例：`409` 防并发重入 | 持有推送锁（或巡检锁）时并发发起第二次 `POST /api/reports/push` | 第二次请求立即被防重锁拦截返回 `409 Conflict` | P4b |
| **TC-09** | 安全用例：`504` 超时不重试 | 模拟 SMTP 连接/发送超时 | 返回 `504 Gateway Timeout`，断言底层发送函数仅调用 **1 次（不自动重试）** 并记录审计 | P4b |
| **TC-10** | 生产 Fail-Fast | `APP_ENV=production` 且缺 `AUTH_SECRET` / 弱密码启动 | 配置校验直接抛出异常拒启 | P4b |
