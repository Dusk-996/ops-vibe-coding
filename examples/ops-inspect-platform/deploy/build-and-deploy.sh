#!/usr/bin/env bash
# 智能服务器巡检与定时邮件推送平台 — P6 Docker Compose 打包、离线迁移、发布与回滚脚本
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_DIR}"

log_info()  { printf '[%s] [INFO] %s\n' "$(date '+%F %T')" "$*"; }
log_warn()  { printf '[%s] [WARN] %s\n' "$(date '+%F %T')" "$*" >&2; }
log_error() { printf '[%s] [ERROR] %s\n' "$(date '+%F %T')" "$*" >&2; }

usage() {
  cat <<'EOF'
用法: bash deploy/build-and-deploy.sh <command> [args]

子命令:
  build [VERSION]          构建带固定版本标签的前后端生产镜像（默认 1.0.0，禁 latest）
  save  [VERSION]          导出前后端镜像离线压缩包到 deploy/dist/（内网无外网机房用）
  load  <TAR_GZ_FILE>      在目标生产机导入离线镜像压缩包
  up    [VERSION]          前置安全检查 -> 若已有运行实例先热备 DB -> 启动并探活 /health
  rollback <PREV_VERSION>  按历史镜像版本标签一键回退并探活 /health
  status                   查看容器运行状态与最近健康检查
  logs  [SERVICE]          查看服务日志（默认 backend 与 frontend）
  down                     优雅停止并移除容器（保留持久化数据卷 ops_inspect_data）

可选加速环境变量:
  PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
  NPM_REGISTRY=https://registry.npmmirror.com
EOF
}

require_docker() {
  command -v docker >/dev/null 2>&1 || { log_error "未找到 docker 命令，请先安装 Docker Engine / Docker Desktop。"; exit 1; }
  docker compose version >/dev/null 2>&1 || { log_error "未找到 docker compose v2+ 插件。"; exit 1; }
  docker info >/dev/null 2>&1 || { log_error "Docker Daemon 未运行，请先启动 Docker 服务后再执行。"; exit 1; }
}

validate_version() {
  local ver="$1"
  if [[ -z "${ver}" || "${ver}" == "latest" ]]; then
    log_error "禁止使用空版本号或 latest 标签，请指定明确版本（例如 1.0.0 或 20261126.1）。"
    exit 1
  fi
}

preflight_env_check() {
  if [[ ! -f "${PROJECT_DIR}/.env" ]]; then
    log_error "未找到 .env 文件。请先执行: cp .env.example .env 并替换全部密钥与密码。"
    exit 1
  fi
  if grep -Eiq '^(AUTH_SECRET|CREDENTIAL_MASTER_KEY|ADMIN_PASSWORD|VIEWER_PASSWORD)=.*(changeme|placeholder|example|dummy)' "${PROJECT_DIR}/.env"; then
    log_error ".env 中仍包含占位弱密钥/弱口令（changeme/placeholder 等），已拦截启动。"
    exit 1
  fi
  if grep -Eq '^CORS_ORIGINS=.*\*' "${PROJECT_DIR}/.env"; then
    log_error ".env 中 CORS_ORIGINS 含通配符 *，已拦截启动。"
    exit 1
  fi
  local ssh_dir
  ssh_dir="$(grep -E '^SSH_KEYS_HOST_DIR=' "${PROJECT_DIR}/.env" | tail -n1 | cut -d= -f2- || true)"
  ssh_dir="${ssh_dir:-./ssh_keys}"
  mkdir -p "${ssh_dir}"
  chmod 700 "${ssh_dir}" 2>/dev/null || true
}

wait_health() {
  local port bind_ip url
  port="$(grep -E '^APP_PORT=' "${PROJECT_DIR}/.env" | tail -n1 | cut -d= -f2- || true)"
  bind_ip="$(grep -E '^APP_BIND_IP=' "${PROJECT_DIR}/.env" | tail -n1 | cut -d= -f2- || true)"
  port="${port:-8080}"
  bind_ip="${bind_ip:-127.0.0.1}"
  [[ "${bind_ip}" == "0.0.0.0" ]] && bind_ip="127.0.0.1"
  url="http://${bind_ip}:${port}/health"

  log_info "等待入口健康探活: ${url}"
  for _ in $(seq 1 20); do
    if command -v curl >/dev/null 2>&1; then
      if body="$(curl -fsS --max-time 3 "${url}" 2>/dev/null)"; then
        log_info "探活成功: ${body}"
        return 0
      fi
    elif command -v python3 >/dev/null 2>&1; then
      if body="$(python3 -c "import urllib.request; print(urllib.request.urlopen('${url}', timeout=3).read().decode())" 2>/dev/null)"; then
        log_info "探活成功: ${body}"
        return 0
      fi
    fi
    sleep 1
  done
  log_error "20s 内未能通过健康检查 ${url}，请执行: docker compose logs --tail=80"
  return 1
}

cmd_build() {
  local ver="${1:-1.0.0}"
  validate_version "${ver}"
  require_docker
  log_info "开始构建生产镜像（版本 ${ver}，固定基础镜像，非 root，VITE_USE_MOCK=false）..."
  APP_VERSION="${ver}" docker compose build --pull=false
  log_info "镜像构建完成："
  docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}" \
    | grep -E 'REPOSITORY|ops-inspect-(backend|frontend)' || true
}

cmd_save() {
  local ver="${1:-1.0.0}"
  validate_version "${ver}"
  require_docker
  mkdir -p "${PROJECT_DIR}/deploy/dist"
  local out_file="${PROJECT_DIR}/deploy/dist/ops-inspect-images-${ver}.tar.gz"
  log_info "导出离线镜像包至 ${out_file} ..."
  docker save "ops-inspect-backend:${ver}" "ops-inspect-frontend:${ver}" | gzip -c > "${out_file}"
  sha256sum "${out_file}" > "${out_file}.sha256"
  log_info "离线镜像包已就绪（附 SHA-256 校验文件）：${out_file}"
}

cmd_load() {
  local tar_file="${1:-}"
  if [[ -z "${tar_file}" || ! -f "${tar_file}" ]]; then
    log_error "请指定有效的离线镜像压缩包路径。"
    exit 1
  fi
  require_docker
  if [[ -f "${tar_file}.sha256" ]]; then
    log_info "校验离线包 SHA-256 ..."
    sha256sum -c "${tar_file}.sha256"
  fi
  log_info "导入离线镜像 ${tar_file} ..."
  gzip -dc "${tar_file}" | docker load
  log_info "离线镜像导入完成。"
}

cmd_up() {
  local ver="${1:-}"
  preflight_env_check
  require_docker
  if [[ -z "${ver}" ]]; then
    ver="$(grep -E '^APP_VERSION=' "${PROJECT_DIR}/.env" | tail -n1 | cut -d= -f2- || true)"
    ver="${ver:-1.0.0}"
  fi
  validate_version "${ver}"

  # 若已有运行中的后端容器，升级前自动热备 SQLite
  if docker compose ps --status running --services 2>/dev/null | grep -qx 'backend'; then
    log_info "检测到已有运行中实例，发版前先执行 SQLite 在线热备..."
    bash "${SCRIPT_DIR}/backup-db.sh" backup || log_warn "发版前热备跳过或失败，请确认数据卷状态。"
  fi

  log_info "启动 Docker Compose 生产服务（版本 ${ver}）..."
  APP_VERSION="${ver}" docker compose up -d --wait
  wait_health
  log_info "发布完成！当前运行版本: ${ver}"
}

cmd_rollback() {
  local prev_ver="${1:-}"
  if [[ -z "${prev_ver}" ]]; then
    log_error "回滚必须指定目标历史版本号，例如: bash deploy/build-and-deploy.sh rollback 1.0.0"
    exit 1
  fi
  validate_version "${prev_ver}"
  preflight_env_check
  require_docker

  docker image inspect "ops-inspect-backend:${prev_ver}" >/dev/null 2>&1 \
    || { log_error "本地不存在历史镜像 ops-inspect-backend:${prev_ver}"; exit 1; }
  docker image inspect "ops-inspect-frontend:${prev_ver}" >/dev/null 2>&1 \
    || { log_error "本地不存在历史镜像 ops-inspect-frontend:${prev_ver}"; exit 1; }

  log_warn "开始回滚至历史版本 ${prev_ver}（不删除持久化卷 ops_inspect_data）..."
  APP_VERSION="${prev_ver}" docker compose up -d --no-build --wait
  wait_health
  log_info "已成功回滚至版本 ${prev_ver}！"
}

main() {
  local cmd="${1:-}"
  shift || true
  case "${cmd}" in
    build)    cmd_build "$@" ;;
    save)     cmd_save "$@" ;;
    load)     cmd_load "$@" ;;
    up)       cmd_up "$@" ;;
    rollback) cmd_rollback "$@" ;;
    status)   require_docker; docker compose ps ;;
    logs)     require_docker; docker compose logs -f --tail=100 "$@" ;;
    down)     require_docker; docker compose down ;;
    -h|--help|"") usage ;;
    *)        log_error "未知子命令: ${cmd}"; usage; exit 1 ;;
  esac
}

main "$@"
