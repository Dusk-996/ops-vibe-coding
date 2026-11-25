# P5 全面真环境测试报告（E2E Test Report）：ops-inspect-demo

- **测试日期**：2026-11-25（安全与可观测性加固复测版）
- **测试环境（真 Linux 内核，非 Root 独立部署）**：
  - 操作系统：`WSL2 Ubuntu (Linux 6.18.33.2-microsoft-standard-WSL2 x86_64)`
  - 运行用户：`administrator (uid=1000)`（全程非 root）
  - 测试根目录：`/opt/ops-inspect-test/`
  - 日志落盘目录：`/opt/ops-inspect-test/logs/`（含 `p5-e2e.log`、`pytest-linux.log`、`backend_prod.log`、`pip-install.log`）
  - 同步归档证据：[05-e2e.log](05-e2e.log)、[05-pytest-linux.log](05-pytest-linux.log)
- **测试结论**：**PASSED（Windows 单测 20/20 + WSL Linux 单测 20/20 + 真 Linux 8 大域生产 E2E 32/32 PASSED，0 BLOCKER / 0 FAIL）**

---

## 一、测试覆盖全景汇总

| 测试域 | 用例数 | 结果 | 核心验证点与真实产出证据 |
|---|---:|---|---|
| **Windows 单元测试（`pytest`）** | 20 | **PASSED** | Windows Python 3.11.9 实跑 20 项单测与安全加固回归（`3.19s` 全绿） |
| **Linux 内核单元测试（`pytest`）** | 20 | **PASSED** | WSL Linux 6.18 + Python 3.14.4 实跑全部 20 项单测（`2.23s` 全绿），含 7 读接口鉴权、严格 `known_hosts` 与 64KB 截断、调度异常日志+500 审计、共享 `inspect_lock`、弱主密钥 Fail-Fast、SMTP 报错脱敏与存储自动裁剪 |
| **D1 真实 Linux `/proc` 采集** | 1 | **PASSED** | 直采 Linux `/proc/meminfo`（`MemAvailable`）与 `0.5s` `/proc/stat`，与宿主机基准 `mem=7.0/7.8GB, cores=4` 精确一致 |
| **D2 生产模式 Fail-Fast** | 4 | **PASSED** | `APP_ENV=production` 弱密码/占位密钥拒启（`exit=1`）；`CORS_ORIGINS=*` 拒启（`exit=1`）；弱独立 `CREDENTIAL_MASTER_KEY` 拒启（`exit=1`）；强密钥真进程启动 `/health -> 200 (env=production)` |
| **D3 双角色认证与 RBAC** | 8 | **PASSED** | 错密 `401`、伪造 Token `401`、未登录访问全部 7 个读接口一律 `401`、未登录 5 类写接口全 `401`、`admin`/`duskk` 登录 `200`、`duskk` 访问全部 7 读接口一律 `200`、越权 5 类写接口全 `403` |
| **D4 主机资产 CRUD 与筛选** | 5 | **PASSED** | 新增静态目标恒 `PENDING` + `X-Op-Id`、重名 `409 Conflict`、编辑端口、多维组合筛选、删除 `200` 与二次删除 `404` |
| **D5 批量导入导出与防注入** | 4 | **PASSED** | CSV 预检识别合法行/非法端口 `99999`/文件内重名、`skip`/`overwrite` 策略、超 `2MB` 拦截 `413`、CSV 导出 UTF-8 BOM + 转义 `'=CMD_INJECT` |
| **D6 5 并发巡检与故障隔离** | 3 | **PASSED** | 生产严格模式缺 `known_hosts` 拒连 `502`（绝不静默降级 `AutoAddPolicy`）；8 台主机并发巡检：Linux 真采与正常节点成功、`.52` 单台隔离 `TIMEOUT`、SSH 路径穿越 `../../etc/passwd` 隔离 `UNREACHABLE`（0 宿主机路径泄漏）；单台超时直返 `504` |
| **D7 多发件箱加密、日志与报告** | 6 | **PASSED** | 非法时间 `400` / 合法 `08:30` 保存 `200`；SQLite 直查 2 套发件箱均为 `v1:` Fernet 密文且 API 0 泄漏；免重输热切换；总—分报告仅详展异常省略正常；审计 35 条覆盖 `[200,201,401,403,409,502,504]`；真进程 `backend_prod.log` 输出 `ops_inspect.scheduler / main / collector` 标准结构化日志 |
| **D8 生产进程重启持久化** | 1 | **PASSED** | 真发 `SIGTERM` 优雅停服再重启，验证 8 台主机、定时 `08:30`、发件记录与 2 套加密发件箱 100% 持久留存且重启后仍可正常解密 |
| **前端构建与人工真机点验** | 补充 | **PASSED** | `vite build` 43 modules `504ms` 通过（0 原生 `<select>`）；已补未登录门面引导与退出清态；前期人工实机点验 UI 交互与真实 QQ 465 SSL 发信成功 |

---

## 二、未覆盖 / 明确留待下一阶段（P6 部署）的项目（如实单列）
1. **自动化无头浏览器（Playwright）**：按用户规则跳过（本机无浏览器测试环境），由人工浏览器点验 + 32 项真 Linux API 回归替代。
2. **外部静态扫描器**：本机未安装 `gitleaks`、`ruff`、`bandit`、`hadolint`（由 `vibe_gate.py` 内置红线扫描与人工审查兜底）。
3. **最终生产部署形态交付与验证**：划归独立的 **P6（部署阶段）**，待用户拍板部署形态并确认 P5 放行后，在 WSL Ubuntu 执行实机部署、SQLite 在线备份恢复与回滚演练。
