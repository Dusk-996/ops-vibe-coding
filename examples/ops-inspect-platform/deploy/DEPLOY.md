# 智能服务器巡检与定时邮件推送平台 — 生产部署与运维交付手册

> 交付模式：**Docker Compose 生产双容器编排**（前端非 root Nginx + 后端非 root FastAPI 单实例 + SQLite WAL 持久化卷）  
> 适用对象：负责上线部署、离线迁移、日常备份、升级与回滚的运维工程师

---

## 1. 交付架构与目录一览

```text
用户浏览器 / 内网网关
   │  HTTP :8080 (默认仅监听 127.0.0.1，可按需配置内网 IP)
   ▼
[frontend] nginxinc/nginx-unprivileged:1.27.3-alpine (非 root UID 101)
   ├── 静态托管 React 生产构建产物 (VITE_USE_MOCK=false)
   └── 内部反代 /api/* 与 /health ──▶ http://backend:8000 (仅内网 ops_net 可达)
                                          ▼
[backend] python:3.11.11-slim-bookworm (非 root opsuser UID 10001, 单 worker)
   ├── 数据卷：ops_inspect_data:/data (SQLite WAL: /data/ops_inspect.db)
   └── 只读卷：./ssh_keys:/run/ssh_keys:ro (SSH 只读私钥与 known_hosts)
```

核心交付文件：
- `docker-compose.yml`：生产编排（固定版本 Tag、健康检查、资源限额、日志轮转、`cap_drop: ALL`）
- `backend/Dockerfile`、`backend/.dockerignore`：后端多阶段非 root 镜像定义
- `frontend/Dockerfile`、`frontend/.dockerignore`、`frontend/nginx.conf`：前端编译与非 root Nginx 配置
- `.env.example`：生产环境变量模板（严禁把真实 `.env` 提交进代码库）
- `deploy/build-and-deploy.sh`：一键打包镜像、离线导出/导入、安全预检、发布探活与回滚脚本
- `deploy/backup-db.sh`：SQLite WAL 在线热备与校验恢复脚本

---

## 2. 上线前准备（必做）

### 2.1 运行环境要求
- Linux 宿主机（推荐 Ubuntu 22.04+ / Debian 12 / Rocky 9）或 Windows WSL2 + Docker Engine 24+ 与 `docker compose` v2+
- 宿主机内存建议 `>= 1 GB`（容器已设限额：backend `512m` / frontend `128m`）

### 2.2 生成生产 `.env`（严禁保留占位密码）
```bash
cp .env.example .env

# 生成 32 位以上随机密钥示例（将输出填入 .env 的 AUTH_SECRET）
openssl rand -hex 24
```

检查并修改 `.env` 以下必填项（`APP_ENV=production` 启动时会自动 Fail-Fast 强校验）：
- `APP_VERSION=1.0.0`（固定版本号，**严禁 `latest`**）
- `APP_BIND_IP=127.0.0.1`、`APP_PORT=8080`（如需内网直连可改为宿主机内网网卡 IP）
- `AUTH_SECRET`：长度 `>= 12` 位强随机串，不含 `changeme` 等占位词
- `ADMIN_USERNAME` / `ADMIN_PASSWORD`、`VIEWER_USERNAME` / `VIEWER_PASSWORD`：均须 `>= 12` 位强口令
- `CORS_ORIGINS`：填写实际浏览器访问来源（如 `http://10.10.1.50:8080`），**严禁 `*`**

### 2.3 准备 SSH 只读私钥与主机指纹白名单（采集远程 Linux 主机时）
```bash
mkdir -p ssh_keys && chmod 700 ssh_keys
# 将只读巡检私钥放入 ssh_keys/（例如 ssh_keys/prod-ro-key），权限设 600
# 收集受管主机公钥指纹写入 known_hosts（生产默认 SSH_STRICT_HOST_KEY=true 强制校验）：
ssh-keyscan -H 10.10.2.11 10.10.2.21 >> ssh_keys/known_hosts
chmod 644 ssh_keys/known_hosts
```

---

## 3. 打包镜像与首次部署

### 3.1 打包带版本标签的生产镜像（联网环境）
```bash
# 方式 A：脚本一键构建（推荐，内置防 latest 校验，支持国内加速源）
PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
NPM_REGISTRY=https://registry.npmmirror.com \
bash deploy/build-and-deploy.sh build 1.0.0

# 方式 B：原生 Docker Compose 命令等价构建
APP_VERSION=1.0.0 docker compose build \
  --build-arg PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
  --build-arg NPM_REGISTRY=https://registry.npmmirror.com
```

### 3.2 离线内网机房镜像迁移（可选）
```bash
# 1) 在有网构建机导出镜像压缩包与 SHA-256 校验文件（输出至 deploy/dist/）
bash deploy/build-and-deploy.sh save 1.0.0

# 2) 将 deploy/dist/ops-inspect-images-1.0.0.tar.gz(.sha256) 与本项目目录拷贝至离线生产机
# 3) 在生产机校验并导入镜像
bash deploy/build-and-deploy.sh load deploy/dist/ops-inspect-images-1.0.0.tar.gz
```

### 3.3 启动服务与上线验收
```bash
# 自动完成：.env 安全预检 -> 若已有旧实例先热备 DB -> docker compose up -d --wait -> /health 探活
bash deploy/build-and-deploy.sh up 1.0.0

# 查看容器状态与实时日志
bash deploy/build-and-deploy.sh status
bash deploy/build-and-deploy.sh logs
```

上线验收核对（3 项）：
1. `curl -fsS http://127.0.0.1:8080/health` 返回 `{"status":"ok",...,"env":"production"}`；
2. 浏览器访问 `http://<IP>:8080/` 未登录时弹出登录门面，匿名请求 `/api/targets` 返回 `401`；
3. 使用管理员账号登录后，在「服务器巡检」点单台检测并在「定时推送」配置发件邮箱与定时规则。

---

## 4. 日常运维、热备恢复与版本回滚

### 4.1 SQLite WAL 在线热备（建议配宿主机 crontab 每日执行）
```bash
# 执行一致性在线热备（含 SHA-256 与 PRAGMA integrity_check，自动保留最近 14 份，落盘 deploy/backups/）
bash deploy/backup-db.sh backup

# 宿主机每日 02:30 自动定时备份示例（crontab -e）
30 2 * * * cd /opt/ops-inspect-platform && bash deploy/backup-db.sh backup >> /var/log/ops-inspect-backup.log 2>&1
```

### 4.2 数据库灾难恢复
```bash
# 自动核对 SHA-256 -> 停 backend -> 替换 DB 并清理 wal/shm -> 拉起 backend
bash deploy/backup-db.sh restore deploy/backups/ops_inspect-YYYYMMDD-HHMMSS.db
bash deploy/build-and-deploy.sh status
```

### 4.3 滚动升级与一键回滚
```bash
# 升级至新版本 1.1.0（up 命令会在重启前自动做一次 DB 热备）
bash deploy/build-and-deploy.sh build 1.1.0
bash deploy/build-and-deploy.sh up 1.1.0

# 若新版本异常，按旧版本镜像 Tag 一键回滚（不删除持久化卷 ops_inspect_data）
bash deploy/build-and-deploy.sh rollback 1.0.0
```

### 4.4 优雅停服
```bash
# 停止并移除容器（数据卷 ops_inspect_data 完整保留）
bash deploy/build-and-deploy.sh down
```

---

## 5. 常见故障速查

| 现象 | 常见根因 | 排查与处理 |
|---|---|---|
| `backend` 启动立即退出并报 `Fail-Fast` | `.env` 密钥/密码不足 12 位、含 `changeme` 或 `CORS_ORIGINS` 含 `*` | 核对 `.env` 替换为强随机值后重新 `up` |
| 远程 SSH 检测报 `缺少 SSH known_hosts` | 生产默认 `SSH_STRICT_HOST_KEY=true`，未挂载 `ssh_keys/known_hosts` | 使用 `ssh-keyscan` 生成 `ssh_keys/known_hosts`（测试内网可显式设 `SSH_STRICT_HOST_KEY=false`） |
| 邮件推送返回 `504` | SMTP 服务器响应超时，系统已禁止自动重试防重复轰炸 | 先到邮箱收件箱确认是否已送达，排查宿主机出网 `465/587` 端口连通性 |
| 发件箱加密授权码重启后无法解密 | 变更了 `.env` 中的 `AUTH_SECRET` 或 `CREDENTIAL_MASTER_KEY` | 保持加密主密钥不变；若主动轮换密钥，请在 Web 端重新录入发件箱授权码 |
| 定时巡检未执行或报错 | 可通过 `docker compose logs backend` 搜索 `ops_inspect.scheduler` 或在前端审计抽屉查 `SCHEDULER_LOOP_ERROR` | 按 `op_id` 定位服务端日志堆栈 |
