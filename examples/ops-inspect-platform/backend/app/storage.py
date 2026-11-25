"""SQLite 持久化存储层：目标资产、巡检快照、定时配置、收件箱与全量审计。"""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class Storage:
    def __init__(self, db_path: Path, seed_defaults: bool = True) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init_schema()
        if seed_defaults:
            self._seed_if_empty()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=15, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_schema(self) -> None:
        with self._lock, self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS targets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    host TEXT UNIQUE NOT NULL,
                    address TEXT NOT NULL,
                    type TEXT NOT NULL,
                    vendor TEXT NOT NULL,
                    collector_type TEXT NOT NULL,
                    ssh_port INTEGER NULL,
                    ssh_user TEXT NOT NULL DEFAULT '',
                    ssh_credential_ref TEXT NOT NULL DEFAULT '',
                    mem_total REAL NULL,
                    mem_free REAL NULL,
                    cores INTEGER NULL,
                    cpu REAL NULL,
                    probe_status TEXT NOT NULL DEFAULT 'PENDING',
                    last_checked_at TEXT NOT NULL DEFAULT '',
                    probe_error TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS schedule_config (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    enabled INTEGER NOT NULL DEFAULT 1,
                    push_time TEXT NOT NULL DEFAULT '09:00',
                    recipients_json TEXT NOT NULL DEFAULT '["ops-oncall@corp.local"]',
                    last_triggered_minute TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS outbox_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    op_id TEXT NOT NULL,
                    delivery_mode TEXT NOT NULL,
                    status_code INTEGER NOT NULL,
                    recipients TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    body_md TEXT NOT NULL,
                    error TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    op_id TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    role TEXT NOT NULL,
                    action TEXT NOT NULL,
                    http_status INTEGER NOT NULL,
                    detail TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS smtp_config (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    enabled INTEGER NOT NULL DEFAULT 0,
                    host TEXT NOT NULL DEFAULT '',
                    port INTEGER NOT NULL DEFAULT 465,
                    security TEXT NOT NULL DEFAULT 'ssl',
                    username TEXT NOT NULL DEFAULT '',
                    auth_code_enc TEXT NOT NULL DEFAULT '',
                    from_addr TEXT NOT NULL DEFAULT '',
                    timeout_seconds INTEGER NOT NULL DEFAULT 10,
                    updated_at TEXT NOT NULL DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS smtp_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    host TEXT NOT NULL,
                    port INTEGER NOT NULL DEFAULT 465,
                    security TEXT NOT NULL DEFAULT 'ssl',
                    username TEXT UNIQUE NOT NULL,
                    auth_code_enc TEXT NOT NULL DEFAULT '',
                    from_addr TEXT NOT NULL DEFAULT '',
                    timeout_seconds INTEGER NOT NULL DEFAULT 10,
                    is_active INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL DEFAULT ''
                );
                """
            )
            # 平滑迁移：若旧单行 smtp_config 已有发件邮箱记录而新表为空，自动迁入不丢失授权码
            prof_cnt = conn.execute("SELECT COUNT(*) AS cnt FROM smtp_profiles").fetchone()["cnt"]
            if prof_cnt == 0:
                old = conn.execute("SELECT * FROM smtp_config WHERE id = 1").fetchone()
                if old and old["host"].strip() and old["username"].strip():
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO smtp_profiles (
                            host, port, security, username, auth_code_enc, from_addr, timeout_seconds, is_active, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            old["host"].strip(),
                            int(old["port"]),
                            old["security"],
                            old["username"].strip(),
                            old["auth_code_enc"],
                            old["from_addr"] or old["username"].strip(),
                            int(old["timeout_seconds"]),
                            1 if old["enabled"] else 0,
                            old["updated_at"] or now_str(),
                        ),
                    )

    def _seed_if_empty(self) -> None:
        ts = now_str()
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS cnt FROM schedule_config").fetchone()
            if row["cnt"] == 0:
                conn.execute(
                    """
                    INSERT INTO schedule_config (id, enabled, push_time, recipients_json, last_triggered_minute, updated_at)
                    VALUES (1, 1, '09:00', ?, '', ?)
                    """,
                    (json.dumps(["ops-oncall@corp.local", "sre-lead@corp.local"], ensure_ascii=False), ts),
                )

            t_cnt = conn.execute("SELECT COUNT(*) AS cnt FROM targets").fetchone()["cnt"]
            if t_cnt == 0:
                # 开箱预置 1 台真实本机采集目标 + 若干演示节点，点击“检测”立即可采本机真实内存/CPU
                seeds = [
                    ("ops-console-local", "127.0.0.1", "容器节点", "本地宿主机", "local", None, "", ""),
                    ("prod-k8s-node-01", "10.10.2.11", "物理机", "戴尔 Dell", "mock", None, "", ""),
                    ("prod-db-master-01", "10.10.2.21", "物理机", "华为 TaiShan", "mock", None, "", ""),
                    ("prod-api-vm-03", "10.10.8.33", "虚拟机", "阿里云 ECS", "mock", None, "", ""),
                    ("edge-gw-node-02", "10.10.9.52", "容器节点", "浪潮 Inspur", "mock", None, "", ""),
                ]
                for host, addr, typ, vendor, col, port, user, cred in seeds:
                    conn.execute(
                        """
                        INSERT INTO targets (
                            host, address, type, vendor, collector_type,
                            ssh_port, ssh_user, ssh_credential_ref,
                            probe_status, last_checked_at, probe_error, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', '', '', ?, ?)
                        """,
                        (host, addr, typ, vendor, col, port, user, cred, ts, ts),
                    )

    @staticmethod
    def _row_to_target(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "host": row["host"],
            "address": row["address"],
            "type": row["type"],
            "vendor": row["vendor"],
            "collector_type": row["collector_type"],
            "ssh_port": row["ssh_port"],
            "ssh_user": row["ssh_user"],
            "ssh_credential_ref": row["ssh_credential_ref"],
            "mem_total": row["mem_total"],
            "mem_free": row["mem_free"],
            "cores": row["cores"],
            "cpu": row["cpu"],
            "probe_status": row["probe_status"],
            "last_checked_at": row["last_checked_at"],
            "probe_error": row["probe_error"],
        }

    def list_targets(
        self,
        q: str = "",
        target_type: str = "",
        vendor: str = "",
        collector_type: str = "",
        alert_only: bool = False,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if q.strip():
            like = f"%{q.strip()}%"
            clauses.append("(host LIKE ? OR address LIKE ?)")
            params.extend([like, like])
        if target_type.strip():
            clauses.append("type = ?")
            params.append(target_type.strip())
        if vendor.strip():
            clauses.append("vendor = ?")
            params.append(vendor.strip())
        if collector_type.strip():
            clauses.append("collector_type = ?")
            params.append(collector_type.strip())
        if alert_only:
            clauses.append("probe_status IN ('HIGH_LOAD', 'TIMEOUT', 'UNREACHABLE')")

        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        with self._lock, self._connect() as conn:
            rows = conn.execute(f"SELECT * FROM targets{where} ORDER BY id DESC", params).fetchall()
            return [self._row_to_target(r) for r in rows]

    def get_target(self, target_id: int) -> dict[str, Any] | None:
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT * FROM targets WHERE id = ?", (target_id,)).fetchone()
            return self._row_to_target(row) if row else None

    def get_existing_hosts(self) -> set[str]:
        with self._lock, self._connect() as conn:
            rows = conn.execute("SELECT host FROM targets").fetchall()
            return {r["host"] for r in rows}

    def create_target(self, data: dict[str, Any]) -> dict[str, Any]:
        ts = now_str()
        with self._lock, self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO targets (
                    host, address, type, vendor, collector_type,
                    ssh_port, ssh_user, ssh_credential_ref,
                    probe_status, last_checked_at, probe_error, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', '', '', ?, ?)
                """,
                (
                    data["host"],
                    data["address"],
                    data["type"],
                    data["vendor"],
                    data["collector_type"],
                    data.get("ssh_port"),
                    data.get("ssh_user", ""),
                    data.get("ssh_credential_ref", ""),
                    ts,
                    ts,
                ),
            )
            row = conn.execute("SELECT * FROM targets WHERE id = ?", (cur.lastrowid,)).fetchone()
            return self._row_to_target(row)

    def update_target(self, target_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
        ts = now_str()
        with self._lock, self._connect() as conn:
            existing = conn.execute("SELECT id FROM targets WHERE id = ?", (target_id,)).fetchone()
            if not existing:
                return None
            conn.execute(
                """
                UPDATE targets
                SET host = ?, address = ?, type = ?, vendor = ?, collector_type = ?,
                    ssh_port = ?, ssh_user = ?, ssh_credential_ref = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    data["host"],
                    data["address"],
                    data["type"],
                    data["vendor"],
                    data["collector_type"],
                    data.get("ssh_port"),
                    data.get("ssh_user", ""),
                    data.get("ssh_credential_ref", ""),
                    ts,
                    target_id,
                ),
            )
            row = conn.execute("SELECT * FROM targets WHERE id = ?", (target_id,)).fetchone()
            return self._row_to_target(row)

    def delete_target(self, target_id: int) -> dict[str, Any] | None:
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT * FROM targets WHERE id = ?", (target_id,)).fetchone()
            if not row:
                return None
            conn.execute("DELETE FROM targets WHERE id = ?", (target_id,))
            return self._row_to_target(row)

    def commit_import(self, rows: list[dict[str, Any]], policy: str) -> dict[str, int]:
        ts = now_str()
        added = 0
        updated = 0
        skipped = 0
        with self._lock, self._connect() as conn:
            for item in rows:
                ex = conn.execute("SELECT id FROM targets WHERE host = ?", (item["host"],)).fetchone()
                if ex:
                    if policy == "overwrite":
                        conn.execute(
                            """
                            UPDATE targets
                            SET address = ?, type = ?, vendor = ?, collector_type = ?,
                                ssh_port = ?, ssh_user = ?, ssh_credential_ref = ?, updated_at = ?
                            WHERE id = ?
                            """,
                            (
                                item["address"],
                                item["type"],
                                item["vendor"],
                                item["collector_type"],
                                item.get("ssh_port"),
                                item.get("ssh_user", ""),
                                item.get("ssh_credential_ref", ""),
                                ts,
                                ex["id"],
                            ),
                        )
                        updated += 1
                    else:
                        skipped += 1
                else:
                    conn.execute(
                        """
                        INSERT INTO targets (
                            host, address, type, vendor, collector_type,
                            ssh_port, ssh_user, ssh_credential_ref,
                            probe_status, last_checked_at, probe_error, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', '', '', ?, ?)
                        """,
                        (
                            item["host"],
                            item["address"],
                            item["type"],
                            item["vendor"],
                            item["collector_type"],
                            item.get("ssh_port"),
                            item.get("ssh_user", ""),
                            item.get("ssh_credential_ref", ""),
                            ts,
                            ts,
                        ),
                    )
                    added += 1
        return {"added": added, "updated": updated, "skipped": skipped}

    def update_probe_snapshot(
        self,
        target_id: int,
        *,
        mem_total: float | None,
        mem_free: float | None,
        cores: int | None,
        cpu: float | None,
        probe_status: str,
        last_checked_at: str,
        probe_error: str,
    ) -> dict[str, Any] | None:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                UPDATE targets
                SET mem_total = ?, mem_free = ?, cores = ?, cpu = ?,
                    probe_status = ?, last_checked_at = ?, probe_error = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    mem_total,
                    mem_free,
                    cores,
                    cpu,
                    probe_status,
                    last_checked_at,
                    probe_error,
                    last_checked_at,
                    target_id,
                ),
            )
            row = conn.execute("SELECT * FROM targets WHERE id = ?", (target_id,)).fetchone()
            return self._row_to_target(row) if row else None

    def get_schedule(self) -> dict[str, Any]:
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT * FROM schedule_config WHERE id = 1").fetchone()
            if not row:
                return {
                    "enabled": True,
                    "push_time": "09:00",
                    "recipients": ["ops-oncall@corp.local"],
                    "last_triggered_minute": "",
                }
            return {
                "enabled": bool(row["enabled"]),
                "push_time": row["push_time"],
                "recipients": json.loads(row["recipients_json"]),
                "last_triggered_minute": row["last_triggered_minute"],
            }

    def update_schedule(self, *, enabled: bool, push_time: str, recipients: list[str]) -> dict[str, Any]:
        ts = now_str()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                UPDATE schedule_config
                SET enabled = ?, push_time = ?, recipients_json = ?, updated_at = ?
                WHERE id = 1
                """,
                (1 if enabled else 0, push_time, json.dumps(recipients, ensure_ascii=False), ts),
            )
        return self.get_schedule()

    def mark_schedule_triggered(self, minute_key: str) -> bool:
        """同分钟幂等原子标记：若本分钟尚未触发则写入并返回 True，否则返回 False。"""
        with self._lock, self._connect() as conn:
            cur = conn.execute(
                """
                UPDATE schedule_config
                SET last_triggered_minute = ?, updated_at = ?
                WHERE id = 1 AND last_triggered_minute != ?
                """,
                (minute_key, now_str(), minute_key),
            )
            return cur.rowcount > 0

    def add_outbox(
        self,
        *,
        op_id: str,
        delivery_mode: str,
        status_code: int,
        recipients: str,
        subject: str,
        body_md: str,
        error: str = "",
    ) -> dict[str, Any]:
        ts = now_str()
        with self._lock, self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO outbox_messages (op_id, delivery_mode, status_code, recipients, subject, body_md, error, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (op_id, delivery_mode, status_code, recipients, subject, body_md, error, ts),
            )
            row = conn.execute("SELECT * FROM outbox_messages WHERE id = ?", (cur.lastrowid,)).fetchone()
            return dict(row)

    def list_outbox(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._lock, self._connect() as conn:
            rows = conn.execute("SELECT * FROM outbox_messages ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    def add_audit(
        self,
        *,
        op_id: str,
        actor: str,
        role: str,
        action: str,
        http_status: int,
        detail: str,
    ) -> dict[str, Any]:
        ts = now_str()
        with self._lock, self._connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO audit_logs (op_id, actor, role, action, http_status, detail, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (op_id, actor, role, action, http_status, detail, ts),
            )
            row = conn.execute("SELECT * FROM audit_logs WHERE id = ?", (cur.lastrowid,)).fetchone()
            return dict(row)

    def list_audits(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._lock, self._connect() as conn:
            rows = conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    def get_smtp_config(self) -> dict[str, Any] | None:
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT * FROM smtp_config WHERE id = 1").fetchone()
            if not row:
                return None
            return {
                "enabled": bool(row["enabled"]),
                "host": row["host"],
                "port": int(row["port"]),
                "security": row["security"],
                "username": row["username"],
                "auth_code_enc": row["auth_code_enc"],
                "from_addr": row["from_addr"],
                "timeout_seconds": int(row["timeout_seconds"]),
                "updated_at": row["updated_at"],
            }

    def save_smtp_config(
        self,
        *,
        enabled: bool,
        host: str,
        port: int,
        security: str,
        username: str,
        auth_code_enc: str | None,
        from_addr: str,
        timeout_seconds: int = 10,
    ) -> dict[str, Any]:
        ts = now_str()
        with self._lock, self._connect() as conn:
            existing = conn.execute("SELECT auth_code_enc FROM smtp_config WHERE id = 1").fetchone()
            final_enc = auth_code_enc if auth_code_enc is not None else (existing["auth_code_enc"] if existing else "")
            if existing:
                conn.execute(
                    """
                    UPDATE smtp_config
                    SET enabled = ?, host = ?, port = ?, security = ?, username = ?,
                        auth_code_enc = ?, from_addr = ?, timeout_seconds = ?, updated_at = ?
                    WHERE id = 1
                    """,
                    (1 if enabled else 0, host, port, security, username, final_enc, from_addr, timeout_seconds, ts),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO smtp_config (
                        id, enabled, host, port, security, username, auth_code_enc, from_addr, timeout_seconds, updated_at
                    ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (1 if enabled else 0, host, port, security, username, final_enc, from_addr, timeout_seconds, ts),
                )
        return self.get_smtp_config() or {}

    @staticmethod
    def _row_to_smtp_profile(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": int(row["id"]),
            "host": row["host"],
            "port": int(row["port"]),
            "security": row["security"],
            "username": row["username"],
            "auth_code_enc": row["auth_code_enc"],
            "from_addr": row["from_addr"],
            "timeout_seconds": int(row["timeout_seconds"]),
            "is_active": bool(row["is_active"]),
            "updated_at": row["updated_at"],
        }

    def list_smtp_profiles(self) -> list[dict[str, Any]]:
        with self._lock, self._connect() as conn:
            rows = conn.execute("SELECT * FROM smtp_profiles ORDER BY is_active DESC, id DESC").fetchall()
            return [self._row_to_smtp_profile(r) for r in rows]

    def get_active_smtp_profile(self) -> dict[str, Any] | None:
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT * FROM smtp_profiles WHERE is_active = 1 LIMIT 1").fetchone()
            return self._row_to_smtp_profile(row) if row else None

    def get_smtp_profile_by_username(self, username: str) -> dict[str, Any] | None:
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT * FROM smtp_profiles WHERE username = ?", (username.strip(),)).fetchone()
            return self._row_to_smtp_profile(row) if row else None

    def upsert_smtp_profile(
        self,
        *,
        host: str,
        port: int,
        security: str,
        username: str,
        auth_code_enc: str | None,
        from_addr: str,
        timeout_seconds: int = 10,
        activate: bool = True,
    ) -> dict[str, Any]:
        ts = now_str()
        clean_user = username.strip()
        clean_host = host.strip()
        clean_from = from_addr.strip() or clean_user
        with self._lock, self._connect() as conn:
            existing = conn.execute(
                "SELECT id, auth_code_enc FROM smtp_profiles WHERE username = ?",
                (clean_user,),
            ).fetchone()
            final_enc = auth_code_enc if auth_code_enc is not None else (existing["auth_code_enc"] if existing else "")

            if activate:
                conn.execute("UPDATE smtp_profiles SET is_active = 0")

            if existing:
                conn.execute(
                    """
                    UPDATE smtp_profiles
                    SET host = ?, port = ?, security = ?, auth_code_enc = ?, from_addr = ?,
                        timeout_seconds = ?, is_active = CASE WHEN ? = 1 THEN 1 ELSE is_active END, updated_at = ?
                    WHERE id = ?
                    """,
                    (clean_host, port, security, final_enc, clean_from, timeout_seconds, 1 if activate else 0, ts, existing["id"]),
                )
                profile_id = int(existing["id"])
            else:
                cur = conn.execute(
                    """
                    INSERT INTO smtp_profiles (
                        host, port, security, username, auth_code_enc, from_addr, timeout_seconds, is_active, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (clean_host, port, security, clean_user, final_enc, clean_from, timeout_seconds, 1 if activate else 0, ts),
                )
                profile_id = int(cur.lastrowid)

            # 同步维护单行 smtp_config，保证老逻辑与测试兼容
            if activate:
                self._sync_legacy_smtp_row(
                    conn,
                    enabled=True,
                    host=clean_host,
                    port=port,
                    security=security,
                    username=clean_user,
                    auth_code_enc=final_enc,
                    from_addr=clean_from,
                    timeout_seconds=timeout_seconds,
                    ts=ts,
                )

            row = conn.execute("SELECT * FROM smtp_profiles WHERE id = ?", (profile_id,)).fetchone()
            return self._row_to_smtp_profile(row)

    def activate_smtp_profile(self, profile_id: int) -> dict[str, Any] | None:
        """激活指定发件箱；传入 0 表示切回本地模拟收件箱（保留所有已存账号）。"""
        ts = now_str()
        with self._lock, self._connect() as conn:
            if profile_id == 0:
                conn.execute("UPDATE smtp_profiles SET is_active = 0")
                existing_legacy = conn.execute("SELECT * FROM smtp_config WHERE id = 1").fetchone()
                if existing_legacy:
                    conn.execute("UPDATE smtp_config SET enabled = 0, updated_at = ? WHERE id = 1", (ts,))
                else:
                    conn.execute(
                        """
                        INSERT INTO smtp_config (id, enabled, host, port, security, username, auth_code_enc, from_addr, timeout_seconds, updated_at)
                        VALUES (1, 0, '', 465, 'ssl', '', '', '', 10, ?)
                        """,
                        (ts,),
                    )
                return {"id": 0, "mode": "mock"}

            row = conn.execute("SELECT * FROM smtp_profiles WHERE id = ?", (profile_id,)).fetchone()
            if not row:
                return None
            conn.execute("UPDATE smtp_profiles SET is_active = 0")
            conn.execute("UPDATE smtp_profiles SET is_active = 1, updated_at = ? WHERE id = ?", (ts, profile_id))
            self._sync_legacy_smtp_row(
                conn,
                enabled=True,
                host=row["host"],
                port=int(row["port"]),
                security=row["security"],
                username=row["username"],
                auth_code_enc=row["auth_code_enc"],
                from_addr=row["from_addr"],
                timeout_seconds=int(row["timeout_seconds"]),
                ts=ts,
            )
            updated = conn.execute("SELECT * FROM smtp_profiles WHERE id = ?", (profile_id,)).fetchone()
            return self._row_to_smtp_profile(updated)

    def delete_smtp_profile(self, profile_id: int) -> dict[str, Any] | None:
        ts = now_str()
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT * FROM smtp_profiles WHERE id = ?", (profile_id,)).fetchone()
            if not row:
                return None
            was_active = bool(row["is_active"])
            conn.execute("DELETE FROM smtp_profiles WHERE id = ?", (profile_id,))
            if was_active:
                conn.execute("UPDATE smtp_config SET enabled = 0, updated_at = ? WHERE id = 1", (ts,))
            return self._row_to_smtp_profile(row)

    @staticmethod
    def _sync_legacy_smtp_row(
        conn: sqlite3.Connection,
        *,
        enabled: bool,
        host: str,
        port: int,
        security: str,
        username: str,
        auth_code_enc: str,
        from_addr: str,
        timeout_seconds: int,
        ts: str,
    ) -> None:
        ex = conn.execute("SELECT id FROM smtp_config WHERE id = 1").fetchone()
        if ex:
            conn.execute(
                """
                UPDATE smtp_config
                SET enabled = ?, host = ?, port = ?, security = ?, username = ?,
                    auth_code_enc = ?, from_addr = ?, timeout_seconds = ?, updated_at = ?
                WHERE id = 1
                """,
                (1 if enabled else 0, host, port, security, username, auth_code_enc, from_addr, timeout_seconds, ts),
            )
        else:
            conn.execute(
                """
                INSERT INTO smtp_config (
                    id, enabled, host, port, security, username, auth_code_enc, from_addr, timeout_seconds, updated_at
                ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (1 if enabled else 0, host, port, security, username, auth_code_enc, from_addr, timeout_seconds, ts),
            )
