# 智能服务器巡检与定时邮件推送平台（ops-inspect-platform）

基于 **React 18 + Vite + Python FastAPI + SQLite WAL** 构建的轻量级生产服务器巡检与定时邮件推送平台，严格区分静态资产登记导入与多驱动主动采集（`local` / `ssh` / `mock`），支持多发件箱 Fernet 加密存档热切换、总—分巡检报告、双角色最小权限鉴权与全量操作审计。

## 快速入口

- **生产部署与运维交付手册（Docker Compose 打包、离线迁移、热备恢复与回滚）**：[deploy/DEPLOY.md](deploy/DEPLOY.md)
- **一键发布脚本**：[deploy/build-and-deploy.sh](deploy/build-and-deploy.sh)
- **SQLite 热备与恢复脚本**：[deploy/backup-db.sh](deploy/backup-db.sh)
- **生产编排与环境模板**：[docker-compose.yml](docker-compose.yml)、[.env.example](.env.example)

## 常用交付命令速览

```bash
# 1. 初始化生产配置（替换为强密钥与口令）
cp .env.example .env && mkdir -p ssh_keys && chmod 700 ssh_keys

# 2. 构建固定版本生产镜像（支持国内源加速，禁止 latest）
bash deploy/build-and-deploy.sh build 1.0.0

# 3. 启动上线并自动探活 /health
bash deploy/build-and-deploy.sh up 1.0.0

# 4. 数据库在线热备 / 恢复 / 按版本回滚
bash deploy/backup-db.sh backup
bash deploy/backup-db.sh restore deploy/backups/ops_inspect-YYYYMMDD-HHMMSS.db
bash deploy/build-and-deploy.sh rollback 1.0.0
```

## 目录结构

```text
├── backend/                # FastAPI 后端、多驱动采集引擎、加密存储、定时调度、Dockerfile 与单测
├── frontend/               # React 18 + Vite 前端、自定义组件、非 root Nginx 配置与 Dockerfile
├── deploy/
│   ├── DEPLOY.md           # 生产部署与运维交付手册（完整操作步骤与排障表）
│   ├── build-and-deploy.sh # 镜像打包、离线导出/导入、发布探活与回滚脚本
│   └── backup-db.sh        # SQLite WAL 一致性热备与校验恢复脚本
├── docker-compose.yml      # 双非 root 容器生产编排
├── .env.example            # 环境变量模板（含生产 Fail-Fast 说明）
└── docs/vibe/              # P1–P6 全阶段需求原型、架构、规格、审查、测试与部署门禁证据
```
