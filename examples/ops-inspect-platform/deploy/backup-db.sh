#!/usr/bin/env bash
# SQLite WAL 在线热备与校验恢复脚本（基于 Python 标准库 sqlite3.backup，零额外 CLI 依赖）
# 支持 Docker Compose 容器在线热备（默认）与本地 SQLite 文件直连演练（--local-db <path>）
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-${PROJECT_DIR}/deploy/backups}"
KEEP_COPIES="${KEEP_COPIES:-14}"
LOCAL_DB=""

log_info()  { printf '[%s] [INFO] %s\n' "$(date '+%F %T')" "$*"; }
log_error() { printf '[%s] [ERROR] %s\n' "$(date '+%F %T')" "$*" >&2; }

usage() {
  cat <<'EOF'
用法:
  Docker 生产模式:
    bash deploy/backup-db.sh backup
    bash deploy/backup-db.sh restore <BACKUP_FILE.db>

  本地文件演练模式（无需 Docker Daemon，适合测试环境校验恢复流程）:
    bash deploy/backup-db.sh --local-db /opt/ops-inspect-test/data/ops_inspect_p5.db backup
    bash deploy/backup-db.sh --local-db /opt/ops-inspect-test/data/ops_inspect_p5.db restore <BACKUP_FILE.db>
EOF
}

python_bin() {
  if [[ -n "${PYTHON_BIN:-}" ]]; then
    echo "${PYTHON_BIN}"
  elif command -v python3 >/dev/null 2>&1; then
    echo "python3"
  else
    echo "python"
  fi
}

verify_sqlite_integrity() {
  local db_file="$1"
  local py
  py="$(python_bin)"
  "${py}" - "${db_file}" <<'PY'
import sqlite3, sys
p = sys.argv[1]
conn = sqlite3.connect(p)
res = conn.execute("PRAGMA integrity_check").fetchone()[0]
tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
conn.close()
if res != "ok":
    raise SystemExit(f"integrity_check failed: {res}")
required = {"targets", "schedule_config", "outbox_messages", "audit_logs"}
missing = required - tables
if missing:
    raise SystemExit(f"missing tables: {sorted(missing)}")
print(f"integrity_check=ok tables={len(tables)}")
PY
}

do_backup_local() {
  local src_db="$1"
  [[ -f "${src_db}" ]] || { log_error "源数据库不存在: ${src_db}"; exit 1; }
  mkdir -p "${BACKUP_DIR}"
  local ts out_file py
  ts="$(date '+%Y%m%d-%H%M%S')"
  out_file="${BACKUP_DIR}/ops_inspect-${ts}.db"
  py="$(python_bin)"

  log_info "执行 SQLite WAL 一致性在线热备: ${src_db} -> ${out_file}"
  "${py}" - "${src_db}" "${out_file}" <<'PY'
import sqlite3, sys
src_path, dst_path = sys.argv[1], sys.argv[2]
src = sqlite3.connect(src_path, timeout=15)
dst = sqlite3.connect(dst_path)
with dst:
    src.backup(dst)
dst.close()
src.close()
PY
  verify_sqlite_integrity "${out_file}"
  sha256sum "${out_file}" > "${out_file}.sha256"
  prune_old_backups
  log_info "本地在线热备成功: ${out_file}"
}

do_restore_local() {
  local target_db="$1"
  local backup_file="$2"
  [[ -f "${backup_file}" ]] || { log_error "备份文件不存在: ${backup_file}"; exit 1; }

  if [[ -f "${backup_file}.sha256" ]]; then
    log_info "校验备份文件 SHA-256..."
    sha256sum -c "${backup_file}.sha256"
  fi
  log_info "校验备份文件 SQLite 完整性..."
  verify_sqlite_integrity "${backup_file}"

  if [[ -f "${target_db}" ]]; then
    local pre_bak="${target_db}.pre-restore.$(date '+%Y%m%d-%H%M%S')"
    cp "${target_db}" "${pre_bak}"
    log_info "已留存恢复前现状副本: ${pre_bak}"
  fi

  rm -f "${target_db}-wal" "${target_db}-shm"
  cp "${backup_file}" "${target_db}"
  verify_sqlite_integrity "${target_db}"
  log_info "数据库恢复完成并已通过完整性复核: ${target_db}"
}

do_backup_docker() {
  mkdir -p "${BACKUP_DIR}"
  local ts tmp_in_container out_file
  ts="$(date '+%Y%m%d-%H%M%S')"
  tmp_in_container="/tmp/ops_inspect-${ts}.db"
  out_file="${BACKUP_DIR}/ops_inspect-${ts}.db"

  log_info "通过 Docker 容器在线热备 /data/ops_inspect.db ..."
  docker compose -f "${PROJECT_DIR}/docker-compose.yml" exec -T backend python -c \
    "import sqlite3; s=sqlite3.connect('/data/ops_inspect.db', timeout=15); d=sqlite3.connect('${tmp_in_container}'); s.backup(d); d.close(); s.close()"
  docker compose -f "${PROJECT_DIR}/docker-compose.yml" cp "backend:${tmp_in_container}" "${out_file}"
  docker compose -f "${PROJECT_DIR}/docker-compose.yml" exec -T backend rm -f "${tmp_in_container}"
  sha256sum "${out_file}" > "${out_file}.sha256"
  prune_old_backups
  log_info "容器数据库热备完成: ${out_file}"
}

do_restore_docker() {
  local backup_file="$1"
  [[ -f "${backup_file}" ]] || { log_error "备份文件不存在: ${backup_file}"; exit 1; }
  if [[ -f "${backup_file}.sha256" ]]; then
    sha256sum -c "${backup_file}.sha256"
  fi
  log_info "暂停 backend 容器以安全替换 /data/ops_inspect.db ..."
  docker compose -f "${PROJECT_DIR}/docker-compose.yml" stop backend
  docker compose -f "${PROJECT_DIR}/docker-compose.yml" cp "${backup_file}" "backend:/data/ops_inspect.db"
  docker compose -f "${PROJECT_DIR}/docker-compose.yml" run --rm --no-deps --entrypoint sh backend -c "rm -f /data/ops_inspect.db-wal /data/ops_inspect.db-shm"
  docker compose -f "${PROJECT_DIR}/docker-compose.yml" start backend
  log_info "容器数据库恢复并重启完成，请执行 bash deploy/build-and-deploy.sh status 确认健康。"
}

prune_old_backups() {
  local count
  count="$(ls -1t "${BACKUP_DIR}"/ops_inspect-*.db 2>/dev/null | wc -l | tr -d ' ')"
  if [[ "${count}" -gt "${KEEP_COPIES}" ]]; then
    ls -1t "${BACKUP_DIR}"/ops_inspect-*.db | tail -n +"$((KEEP_COPIES + 1))" | while read -r old; do
      rm -f "${old}" "${old}.sha256"
    done
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --local-db) LOCAL_DB="$2"; shift 2 ;;
    -h|--help)  usage; exit 0 ;;
    *)          break ;;
  esac
done

ACTION="${1:-}"
shift || true

case "${ACTION}" in
  backup)
    if [[ -n "${LOCAL_DB}" ]]; then do_backup_local "${LOCAL_DB}"; else do_backup_docker; fi
    ;;
  restore)
    if [[ -z "${1:-}" ]]; then log_error "restore 需要指定备份文件路径。"; exit 1; fi
    if [[ -n "${LOCAL_DB}" ]]; then do_restore_local "${LOCAL_DB}" "$1"; else do_restore_docker "$1"; fi
    ;;
  *)
    usage; exit 1 ;;
esac
