# P6 生产部署交付手册与验证报告（Docker Compose 模式）：ops-inspect-demo

- **部署阶段**：P6（在 P5 全面真环境测试全部通过并获 `approve p5` 后独立设计与交付）
- **交付模式**：**Docker Compose 生产级双容器编排**（前端非 root Nginx 反代 + 后端非 root FastAPI 单实例 + SQLite 命名持久化卷）
- **实测证据日志**：[06-deploy.log](06-deploy.log)
- **阶段结论**：**`PASSED_WITH_ENV_NOTE`（0 BLOCKER / 0 未解决缺陷；配置校验、脚本语法、防 `:latest`、门禁硬扫描与 WSL 真机 SQLite 热备恢复全部 PASSED；本机 Docker Daemon 未启动，实际镜像构建与容器拉起标为 `NOT_VERIFIED`，待在开启 Docker 的目标宿主机执行下方一键命令验证）**

---

## 一、P6 完整交付物清单

| 文件路径 | 核心职责与安全加固要点 |
|---|---|
| [backend/Dockerfile](../../backend/Dockerfile) | 多阶段构建；固定基础镜像 `python:3.11.11-slim-bookworm`（0 `:latest`）；非 root `USER opsuser (10001)`；内置 `/health` `HEALTHCHECK` 与 `STOPSIGNAL SIGTERM`；严格单 worker、禁 `--reload`；支持 `PIP_INDEX_URL` 国内源加速 |
| [backend/.dockerignore](../../backend/.dockerignore) | 排除 `.env`、`*.db*`、`ssh_keys/`、`tests/`、`__pycache__`，严防凭据与测试文件打入镜像 |
| [frontend/Dockerfile](../../frontend/Dockerfile) | `node:20.18.1-alpine3.20` 多阶段编译（强锁 `VITE_USE_MOCK=false`，支持 `NPM_REGISTRY` 加速）+ 官方非 root `nginxinc/nginx-unprivileged:1.27.3-alpine`（`USER 101`，端口 `8080`） |
| [frontend/.dockerignore](../../frontend/.dockerignore) | 排除 `node_modules/`、`dist/`、`.env*`，防本地环境污染构建产物 |
| [frontend/nginx.conf](../../frontend/nginx.conf) | 非 root `8080` 监听、`server_tokens off`、`client_max_body_size 3m`、安全响应头、屏蔽 `/.` 隐藏文件、`/api/` 与 `/health` 内部反代至 `backend:8000` |
| [docker-compose.yml](../../docker-compose.yml) | 带版本标签 `ops-inspect-backend:${APP_VERSION}` / `ops-inspect-frontend:${APP_VERSION}`（禁 `:latest`）；后端 8000 仅内网暴露；`ops_inspect_data:/data` 持久化卷 + `${SSH_KEYS_HOST_DIR}:/run/ssh_keys:ro` 只读挂载；`no-new-privileges` + `cap_drop: ALL` + CPU/内存限额 + JSON 日志轮转 + `service_healthy` 启动编排 |
| [.env.example](../../.env.example) | 全量生产环境变量模板（含版本、端口、强密钥/口令、受控 CORS、`SSH_STRICT_HOST_KEY=true`、表留存上限、SMTP 兜底） |
| [deploy/build-and-deploy.sh](../../deploy/build-and-deploy.sh) | 一键打包镜像、离线 `save`/`load` 迁移、前置安全预检（拒占位符/`*`）、发版前自动热备、启动探活与按版本 Tag 一键回滚 |
| [deploy/backup-db.sh](../../deploy/backup-db.sh) | 基于 Python 标准库 `sqlite3.backup()` 的 WAL 一致性在线热备、SHA-256 与 `PRAGMA integrity_check` 校验、恢复前现状留存与 14 份自动轮转 |
| [deploy/DEPLOY.md](../../deploy/DEPLOY.md) | 面向接手运维的正式生产部署与运维交付手册（架构拓扑、`.env` 安全准备、构建/离线导包/上线、热备恢复、回滚与常见故障速查表） |
| [README.md](../../README.md) | 项目根目录交付总入口（目录导航与常用部署命令速览） |

---

## 二、生产打包镜像与部署操作手册（开箱直接复制执行）

### 1. 首次准备环境配置与 SSH 凭据目录
```bash
cp .env.example .env
# 编辑 .env：必须把 AUTH_SECRET、ADMIN_PASSWORD、VIEWER_PASSWORD 替换为 >=12 位强随机值
# 并配置实际访问来源 CORS_ORIGINS（严禁使用 *）

mkdir -p ssh_keys && chmod 700 ssh_keys
# 如需采集远程 Linux SSH 主机，将只读私钥与 known_hosts 放入 ssh_keys/（容器内只读挂载）
```

### 2. 打包带版本号的生产镜像（支持国内源加速）
```bash
# 方式 A：使用脚本一键打包（推荐，自动校验禁止 latest）
PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
NPM_REGISTRY=https://registry.npmmirror.com \
bash deploy/build-and-deploy.sh build 1.0.0

# 方式 B：原生 docker compose / docker build 命令等价执行
APP_VERSION=1.0.0 docker compose build \
  --build-arg PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
  --build-arg NPM_REGISTRY=https://registry.npmmirror.com
```

### 3. （可选）无外网机房离线导出与导入镜像包
```bash
# 在有网构建机导出压缩包 + SHA-256 校验文件（输出到 deploy/dist/）
bash deploy/build-and-deploy.sh save 1.0.0

# 拷贝到离线生产机后校验并导入
bash deploy/build-and-deploy.sh load deploy/dist/ops-inspect-images-1.0.0.tar.gz
```

### 4. 启动发布与健康验收
```bash
# 自动执行：.env 安全预检 -> 升级前自动热备 DB -> 拉起双容器并等待健康 -> /health 实测探活
bash deploy/build-and-deploy.sh up 1.0.0

# 查看运行状态与实时日志
bash deploy/build-and-deploy.sh status
bash deploy/build-and-deploy.sh logs
```

### 5. 日常 SQLite 在线热备与灾难恢复
```bash
# 在线热备（WAL 安全一致，含 SHA-256 校验与 14 份轮转，落盘 deploy/backups/）
bash deploy/backup-db.sh backup

# 灾难恢复（自动核对 SHA-256 与 integrity_check，清理残留 wal/shm 后重启后端）
bash deploy/backup-db.sh restore deploy/backups/ops_inspect-YYYYMMDD-HHMMSS.db
```

### 6. 版本一键回滚（保留持久化数据卷）
```bash
# 无需重编，直接切回上一个已知稳定的镜像版本标签并探活验证
bash deploy/build-and-deploy.sh rollback 1.0.0
```

---

## 三、P6 实测验证矩阵（如实区分已验证与环境受限项）

| 验证项 | 证据等级 | 实测结果 |
|---|---|---|
| `docker compose config --quiet` 官方 Schema 解析校验（Docker Compose v5.7.0） | `STATIC` / `TESTED` | **PASSED**（退出码 `0`，成功解析 `backend`/`frontend` 服务、固定镜像标签、卷挂载、健康检查与资源限额） |
| `vibe_gate.py check p6` 部署安全硬扫描（禁 `:latest`、禁 root、禁 `VITE_USE_MOCK=true`、0 明文凭据） | `STATIC` / `TESTED` | **PASSED**（0 违规项） |
| `bash -n` 静态语法检查（`build-and-deploy.sh` & `backup-db.sh`） | `TESTED` | **PASSED**（Linux LF 换行，0 语法错误） |
| 脚本防 `latest` 标签拦截实测（`build latest`） | `RUNTIME_VERIFIED` | **PASSED**（实测返回 `exit=1` 并明确报错拦截） |
| WSL2 真 Linux SQLite WAL 在线热备 → 模拟误删清零 → SHA-256/完整性校验恢复演练 | `RUNTIME_VERIFIED` | **PASSED**（8 台主机 + 2 套加密发件箱误删归零后 100% 完整还原，`PRAGMA integrity_check=ok`） |
| Nginx 非 root 8080、反代 `/api/` & `/health`、安全响应头与 `client_max_body_size 3m` 核对 | `STATIC` | **PASSED** |
| **实际 `docker compose build` 镜像打包与 `docker compose up -d` 容器运行** | **`NOT_VERIFIED`** | **本机 Docker Desktop Daemon 未启动**（`npipe:////./pipe/dockerDesktopLinuxEngine` 不可达）；待你在开启 Docker 的本机或目标 Linux 服务器执行 `bash deploy/build-and-deploy.sh build 1.0.0 && bash deploy/build-and-deploy.sh up 1.0.0` 完成首次容器实机验证 |
| 外部 `hadolint` 扫描 | `NOT_VERIFIED`（`SKIPPED`） | 本机未安装 `hadolint`，已由 `vibe_gate.py` 内置 Dockerfile 规则与人工逐行复核兜底 |
