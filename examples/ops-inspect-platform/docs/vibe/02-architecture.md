# P2 技术栈与核心机制定稿（FINAL）：ops-inspect-demo

- **阶段**：FINAL（全部 4 项核心决策与具体采集实现细节已确认，待用户验收后执行 `approve p2`）
- **上游基准**：`docs/vibe/01-design.md`、`docs/vibe/01-prototype/index.html`、`docs/vibe/02-architecture.draft.md`、`docs/vibe/02-grill.md`

## 一、技术栈与核心机制确认表

| 维度 | 最终确认方案 | 说明与边界 |
|---|---|---|
| **前端技术栈** | **React 18 + Vite**（原生 Hash 双页 `#/servers` & `#/schedule`） | 保真还原 P1 批准原型，生产构建 `VITE_USE_MOCK=false` |
| **后端技术栈** | **Python 3.11 + FastAPI**（模块化单体） | 认证鉴权、静态目标与导入导出、多驱动巡检采集引擎、定时调度、SMTP 双模式、审计 |
| **核心检测机制（Collector）** | **多驱动可插拔采集引擎（`ssh` / `local` / `mock`）** | 见下方第二节内核级实现明细；5 并发线程池、单台超时 8s、失败隔离不拖垮整批 |
| **持久化与实例形态** | **单实例 + 内置 SQLite 持久化挂卷**（`/data/ops_inspect.db`） | 进程内轻量调度器 + 非阻塞并发锁；代码层隔离存储访问，便于日后迁 PostgreSQL/MySQL |
| **邮箱推送通道** | **标准 SMTP（环境变量注入）+ 本地模拟收件箱双模式** | 未配 `SMTP_HOST` 自动安全走模拟收件箱；并发 `409`、超时 10s 返 `504` 且**不自动重试** |
| **交付与部署形态** | **Docker Compose**（双非 root `Dockerfile` + Nginx `/api` 反代 + `/health`） | 禁 `:latest`、禁 root、禁 `reload=True`、禁 `CORS *`；生产缺密钥 Fail-Fast 拒启 |
| **开发与验收顺序** | **先完成并启动前端 → 用户打开验收通过 → 再做后端与联调** | P4 拆为 `P4a 前端实机验收` 与 `P4b 后端采集与联调验收` |
| **显式排除** | 无 Redis、无 MQ、无独立 Worker、无微服务、无 K8s 清单 | 单实例内网巡检无引入证据 |

## 二、服务器 CPU 与内存的具体检测采集机制

### 1. `ssh` 驱动（远程 Linux 服务器，基于 `paramiko`）
- 连接超时 `5s`、命令执行超时 `8s`，超时不自动重试。
- 执行**写死在代码里的固定只读白名单命令**（严禁拼接用户输入，杜绝命令注入），一次 SSH 往返获取全部指标：
  - **内存口径**：解析 `/proc/meminfo` 的 `MemTotal` 与 **`MemAvailable`**（真实可用剩余内存；老内核缺 `MemAvailable` 时回退 `MemFree + Buffers + Cached`）。
  - **CPU 核数**：`nproc`（回退 `/proc/cpuinfo` 计数）。
  - **实时 CPU 使用率（%）**：两次间隔 `0.5s` 读取 `/proc/stat` 首行，按增量 `(total_delta - idle_delta) / total_delta * 100` 计算。
- **凭据安全**：数据库仅存凭据别名 `sshCredentialRef`，后端通过环境变量映射或只读密钥目录加载私钥文件；不存明文私钥/密码，不回传前端，不打入日志。

### 2. `local` 驱动（本机真实采集，Python 纯标准库，零额外依赖）
- **Linux**：直接读取本机 `/proc/meminfo` + 间隔 `0.5s` 读取 `/proc/stat` + `os.cpu_count()`。
- **Windows**：使用 Python 标准库 `ctypes` 调用 `GlobalMemoryStatusEx`（物理总内存 & 可用内存）与间隔 `0.5s` 的 `GetSystemTimes`（实时 CPU 使用率），不依赖 `psutil`。

### 3. `mock` 驱动（自动化测试与离线演练）
- 确定性模拟正常、高负载、超时（`TIMEOUT`）、不可达（`UNREACHABLE`），页面与报告中显式标注采集驱动来源。

### 4. 触发与失败隔离
- 支持单台检测、全量立即巡检（默认 5 并发）以及每日定时推送前自动全量巡检；
- 单台采集失败仅标记该台为 `TIMEOUT` 或 `UNREACHABLE` 并记录脱敏错误摘要，不影响其余主机检测与巡检报告推送。

## 三、静态登记字段 vs 动态检测字段边界
- **人工登记/导入（静态）**：`host`、`address`（IP/域名）、`type`、`vendor`、`collectorType`、`sshPort`、`sshUser`、`sshCredentialRef`。
- **采集引擎产出（动态只读）**：`memTotal`（GB）、`memFree`（GB）、`cores`、`cpu`（%）、`probeStatus`（`OK` / `HIGH_LOAD` / `TIMEOUT` / `UNREACHABLE` / `PENDING`）、`lastCheckedAt`、`probeError`。
