"""ops-inspect-demo FastAPI 后端主入口（对齐 docs/vibe/03-openapi.yaml）。"""

from __future__ import annotations

import csv
import io
import json
import re
import sqlite3
import threading
import uuid
from contextlib import asynccontextmanager
from typing import Any, Literal

from fastapi import FastAPI, Header, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from pydantic import BaseModel, Field

from .auth import AuthUser, authenticate_user, create_token, verify_token
from .collector import inspect_all_targets, probe_target
from .config import Settings, load_settings
from .crypto import encrypt_secret
from .mailer import (
    MailerService,
    PushConflictError,
    SmtpDeliveryError,
    SmtpTimeoutError,
    build_markdown_report,
)
from .scheduler import InspectionScheduler
from .storage import Storage

MAX_IMPORT_BYTES = 2 * 1024 * 1024
MAX_IMPORT_ROWS = 2000
VALID_TYPES = {"物理机", "虚拟机", "容器节点"}
VALID_COLLECTORS = {"ssh", "local", "mock"}
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
HHMM_RE = re.compile(r"^([01][0-9]|2[0-3]):[0-5][0-9]$")

ACTION_CN = {
    "CREATE_TARGET": "登记目标服务器",
    "UPDATE_TARGET": "修改目标服务器",
    "DELETE_TARGET": "删除目标服务器",
    "IMPORT_PREVIEW": "校验导入文件",
    "IMPORT_TARGETS": "批量导入目标服务器",
    "INSPECT_ALL": "发起全量巡检",
    "INSPECT_ONE": "发起单台主机检测",
    "UPDATE_SCHEDULE": "修改定时推送配置",
    "UPDATE_SMTP": "保存发件邮箱账号",
    "ACTIVATE_SMTP_PROFILE": "切换发件邮箱账号",
    "DELETE_SMTP_PROFILE": "删除发件邮箱存档",
    "PUSH_REPORT_NOW": "手动推送巡检报告",
}


class LoginPayload(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=256)


class TargetPayload(BaseModel):
    host: str = Field(..., min_length=1, max_length=128)
    address: str = Field(..., min_length=1, max_length=128)
    type: Literal["物理机", "虚拟机", "容器节点"]
    vendor: str = Field(..., min_length=1, max_length=64)
    collector_type: Literal["ssh", "local", "mock"]
    ssh_port: int | None = Field(default=None, ge=1, le=65535)
    ssh_user: str = Field(default="", max_length=64)
    ssh_credential_ref: str = Field(default="", max_length=128)


class ImportPayload(BaseModel):
    format: Literal["csv", "json"]
    content: str
    policy: Literal["skip", "overwrite"] = "skip"


class SchedulePayload(BaseModel):
    enabled: bool
    push_time: str
    recipients: list[str]


class SmtpConfigPayload(BaseModel):
    enabled: bool
    host: str = Field(default="", max_length=255)
    port: int = Field(default=465, ge=1, le=65535)
    security: Literal["ssl", "starttls", "none"] = "ssl"
    username: str = Field(default="", max_length=128)
    auth_code: str = Field(default="", max_length=256)
    from_addr: str = Field(default="", max_length=128)
    timeout_seconds: int = Field(default=10, ge=3, le=30)


def _make_op_id() -> str:
    return f"op-{uuid.uuid4().hex[:8]}"


def _err_resp(status: int, detail: str, op_id: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"detail": detail, "op_id": op_id},
        headers={"X-Op-Id": op_id},
    )


def _csv_safe_cell(val: Any) -> str:
    text = "" if val is None else str(val)
    if text and text[0] in ("=", "+", "-", "@"):
        text = "'" + text
    return text


def _parse_and_validate_import(fmt: str, content: str, existing_hosts: set[str]) -> dict[str, Any]:
    raw_rows: list[dict[str, Any]] = []
    if fmt == "json":
        parsed = json.loads(content)
        if not isinstance(parsed, list):
            raise ValueError("JSON 根节点必须为数组")
        for idx, item in enumerate(parsed, start=1):
            if not isinstance(item, dict):
                raise ValueError(f"JSON 第 {idx} 项必须为对象")
            row = dict(item)
            row["_line"] = idx
            raw_rows.append(row)
    else:
        cleaned = content.lstrip("\ufeff").strip()
        if not cleaned:
            raise ValueError("CSV 内容为空")
        reader = csv.DictReader(io.StringIO(cleaned))
        if not reader.fieldnames:
            raise ValueError("CSV 缺少表头行")
        for idx, row in enumerate(reader, start=2):
            norm = {(k or "").strip(): (v or "").strip() for k, v in row.items()}
            norm["_line"] = idx
            raw_rows.append(norm)

    if len(raw_rows) > MAX_IMPORT_ROWS:
        raise ValueError(f"单次最多导入 {MAX_IMPORT_ROWS} 行目标记录")

    valid_rows: list[dict[str, Any]] = []
    errors: list[str] = []
    seen: set[str] = set()

    for idx, r in enumerate(raw_rows, start=1):
        ln = r.get("_line", idx)
        host = str(r.get("host") or "").strip()
        address = str(r.get("address") or "").strip()
        typ = str(r.get("type") or "物理机").strip()
        vendor = str(r.get("vendor") or "戴尔 Dell").strip()
        col = str(r.get("collector_type") or r.get("collectorType") or "ssh").strip().lower()
        port_raw = r.get("ssh_port") if r.get("ssh_port") not in (None, "") else r.get("sshPort")
        ssh_user = str(r.get("ssh_user") or r.get("sshUser") or ("ops-ro" if col == "ssh" else "")).strip()
        ssh_cred = str(r.get("ssh_credential_ref") or r.get("sshCredentialRef") or "").strip()

        if not host:
            errors.append(f"第 {ln} 行缺少 host")
            continue
        if not address:
            errors.append(f"第 {ln} 行 ({host}) 缺少 IP/address")
            continue
        if typ not in VALID_TYPES:
            errors.append(f"第 {ln} 行 type 非法（仅支持物理机/虚拟机/容器节点）")
            continue
        if col not in VALID_COLLECTORS:
            errors.append(f"第 {ln} 行 collectorType 非法（仅支持 ssh/local/mock）")
            continue

        ssh_port: int | None = None
        if col == "ssh":
            try:
                ssh_port = int(port_raw) if port_raw not in (None, "") else 22
            except (TypeError, ValueError):
                errors.append(f"第 {ln} 行 SSH 端口无效")
                continue
            if not (1 <= ssh_port <= 65535):
                errors.append(f"第 {ln} 行 SSH 端口超出范围 (1-65535)")
                continue

        if host in seen:
            errors.append(f"第 {ln} 行文件内主机名 {host} 重复")
            continue
        seen.add(host)

        valid_rows.append(
            {
                "host": host,
                "address": address,
                "type": typ,
                "vendor": vendor,
                "collector_type": col,
                "ssh_port": ssh_port,
                "ssh_user": ssh_user if col == "ssh" else "",
                "ssh_credential_ref": ssh_cred if col == "ssh" else "",
            }
        )

    dup_cnt = sum(1 for v in valid_rows if v["host"] in existing_hosts)
    return {"valid_rows": valid_rows, "errors": errors, "duplicate_count": dup_cnt}


def create_app(
    settings: Settings | None = None,
    storage: Storage | None = None,
    mailer: MailerService | None = None,
    seed_defaults: bool = True,
) -> FastAPI:
    cfg = settings or load_settings()
    store = storage or Storage(cfg.db_path, seed_defaults=seed_defaults)
    mail_svc = mailer or MailerService(cfg, store)
    scheduler = InspectionScheduler(cfg, store, mail_svc)
    inspect_lock = threading.Lock()

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        scheduler.start()
        try:
            yield
        finally:
            scheduler.stop()

    app = FastAPI(title="智能服务器巡检与定时邮件推送平台 API", version="1.0.0", lifespan=lifespan)
    app.state.settings = cfg
    app.state.storage = store
    app.state.mailer = mail_svc
    app.state.scheduler = scheduler
    app.state.inspect_lock = inspect_lock

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    def resolve_user(authorization: str | None) -> AuthUser | None:
        if not authorization or not authorization.lower().startswith("bearer "):
            return None
        token = authorization[7:].strip()
        return verify_token(token, cfg.auth_secret)

    def require_admin(authorization: str | None, action: str, op_id: str) -> tuple[AuthUser | None, JSONResponse | None]:
        user = resolve_user(authorization)
        label = ACTION_CN.get(action, action)
        if user is None:
            store.add_audit(
                op_id=op_id,
                actor="anonymous",
                role="anon",
                action=action,
                http_status=401,
                detail=f"未登录状态下尝试{label}，已拦截",
            )
            return None, _err_resp(401, f"尚未登录系统，请先使用管理员账号登录后再{label}。", op_id)
        if user.role != "admin":
            store.add_audit(
                op_id=op_id,
                actor=user.username,
                role=user.role,
                action=action,
                http_status=403,
                detail=f"只读成员 {user.username} 尝试{label}，已拦截",
            )
            return None, _err_resp(403, f"只读成员（viewer）无法{label}，请切换管理员账号后操作。", op_id)
        return user, None

    @app.get("/health")
    def health() -> dict[str, Any]:
        mode, source, _ = mail_svc.resolve_runtime_smtp()
        return {"status": "ok", "smtp_mode": mode, "smtp_source": source, "env": cfg.app_env}

    @app.post("/api/auth/login")
    def login(payload: LoginPayload) -> Response:
        op_id = _make_op_id()
        user = authenticate_user(payload.username, payload.password, cfg)
        if user is None:
            store.add_audit(
                op_id=op_id,
                actor=payload.username or "unknown",
                role="anon",
                action="AUTH_LOGIN",
                http_status=401,
                detail="登录凭据校验失败",
            )
            return _err_resp(401, "账号或口令不正确，请重新核对。", op_id)
        token = create_token(user, cfg.auth_secret)
        store.add_audit(
            op_id=op_id,
            actor=user.username,
            role=user.role,
            action="AUTH_LOGIN",
            http_status=200,
            detail=f"{user.username} ({user.role}) 登录成功",
        )
        mode, _, _ = mail_svc.resolve_runtime_smtp()
        return JSONResponse(
            content={
                "token": token,
                "username": user.username,
                "role": user.role,
                "smtp_mode": mode,
                "op_id": op_id,
            },
            headers={"X-Op-Id": op_id},
        )

    @app.get("/api/auth/me")
    def auth_me(authorization: str | None = Header(default=None)) -> Response:
        op_id = _make_op_id()
        user = resolve_user(authorization)
        if user is None:
            return _err_resp(401, "未登录或登录令牌已过期。", op_id)
        mode, _, _ = mail_svc.resolve_runtime_smtp()
        return JSONResponse(
            content={"username": user.username, "role": user.role, "smtp_mode": mode},
            headers={"X-Op-Id": op_id},
        )

    @app.get("/api/targets")
    def list_targets(
        q: str = Query(default=""),
        type: str = Query(default=""),
        vendor: str = Query(default=""),
        collector_type: str = Query(default=""),
        alert_only: bool = Query(default=False),
    ) -> dict[str, Any]:
        items = store.list_targets(
            q=q,
            target_type=type,
            vendor=vendor,
            collector_type=collector_type,
            alert_only=alert_only,
        )
        return {"items": items}

    @app.post("/api/targets", status_code=201)
    def create_target(payload: TargetPayload, authorization: str | None = Header(default=None)) -> Response:
        op_id = _make_op_id()
        user, err = require_admin(authorization, "CREATE_TARGET", op_id)
        if err:
            return err

        data = payload.model_dump()
        data["host"] = data["host"].strip()
        data["address"] = data["address"].strip()
        if data["collector_type"] == "ssh":
            data["ssh_port"] = data["ssh_port"] or 22
            data["ssh_user"] = data["ssh_user"].strip() or "ops-ro"
            data["ssh_credential_ref"] = data["ssh_credential_ref"].strip()
        else:
            data["ssh_port"] = None
            data["ssh_user"] = ""
            data["ssh_credential_ref"] = ""

        try:
            created = store.create_target(data)
        except sqlite3.IntegrityError:
            store.add_audit(
                op_id=op_id,
                actor=user.username,
                role=user.role,
                action="CREATE_TARGET",
                http_status=409,
                detail=f"主机名 {data['host']} 已存在",
            )
            return _err_resp(409, f"主机名 {data['host']} 已存在，请勿重复登记。", op_id)

        store.add_audit(
            op_id=op_id,
            actor=user.username,
            role=user.role,
            action="CREATE_TARGET",
            http_status=201,
            detail=f"登记目标 {created['host']}（{created['address']} / {created['collector_type']}）",
        )
        return JSONResponse(status_code=201, content={"item": created, "op_id": op_id}, headers={"X-Op-Id": op_id})

    @app.put("/api/targets/{target_id}")
    def update_target(target_id: int, payload: TargetPayload, authorization: str | None = Header(default=None)) -> Response:
        op_id = _make_op_id()
        user, err = require_admin(authorization, "UPDATE_TARGET", op_id)
        if err:
            return err

        data = payload.model_dump()
        data["host"] = data["host"].strip()
        data["address"] = data["address"].strip()
        if data["collector_type"] == "ssh":
            data["ssh_port"] = data["ssh_port"] or 22
            data["ssh_user"] = data["ssh_user"].strip() or "ops-ro"
            data["ssh_credential_ref"] = data["ssh_credential_ref"].strip()
        else:
            data["ssh_port"] = None
            data["ssh_user"] = ""
            data["ssh_credential_ref"] = ""

        try:
            updated = store.update_target(target_id, data)
        except sqlite3.IntegrityError:
            return _err_resp(409, f"主机名 {data['host']} 与其他记录重复。", op_id)

        if updated is None:
            return _err_resp(404, "目标服务器不存在。", op_id)

        store.add_audit(
            op_id=op_id,
            actor=user.username,
            role=user.role,
            action="UPDATE_TARGET",
            http_status=200,
            detail=f"更新目标 {updated['host']}（{updated['address']}）",
        )
        return JSONResponse(content={"item": updated, "op_id": op_id}, headers={"X-Op-Id": op_id})

    @app.delete("/api/targets/{target_id}")
    def delete_target(target_id: int, authorization: str | None = Header(default=None)) -> Response:
        op_id = _make_op_id()
        user, err = require_admin(authorization, "DELETE_TARGET", op_id)
        if err:
            return err

        deleted = store.delete_target(target_id)
        if deleted is None:
            return _err_resp(404, "目标服务器不存在。", op_id)

        store.add_audit(
            op_id=op_id,
            actor=user.username,
            role=user.role,
            action="DELETE_TARGET",
            http_status=200,
            detail=f"移除目标 {deleted['host']}（{deleted['address']}）",
        )
        return JSONResponse(content={"deleted": target_id, "op_id": op_id}, headers={"X-Op-Id": op_id})

    @app.post("/api/targets/import/preview")
    def import_preview(payload: ImportPayload, authorization: str | None = Header(default=None)) -> Response:
        op_id = _make_op_id()
        _, err = require_admin(authorization, "IMPORT_PREVIEW", op_id)
        if err:
            return err
        if len(payload.content.encode("utf-8")) > MAX_IMPORT_BYTES:
            return _err_resp(413, "导入文件内容超过 2MB 上限。", op_id)
        try:
            result = _parse_and_validate_import(payload.format, payload.content, store.get_existing_hosts())
        except Exception as exc:
            return _err_resp(400, f"导入文件解析失败：{exc}", op_id)
        return JSONResponse(content={**result, "op_id": op_id}, headers={"X-Op-Id": op_id})

    @app.post("/api/targets/import/commit")
    def import_commit(payload: ImportPayload, authorization: str | None = Header(default=None)) -> Response:
        op_id = _make_op_id()
        user, err = require_admin(authorization, "IMPORT_TARGETS", op_id)
        if err:
            return err
        if len(payload.content.encode("utf-8")) > MAX_IMPORT_BYTES:
            return _err_resp(413, "导入文件内容超过 2MB 上限。", op_id)
        try:
            parsed = _parse_and_validate_import(payload.format, payload.content, store.get_existing_hosts())
        except Exception as exc:
            return _err_resp(400, f"导入文件解析失败：{exc}", op_id)

        stats = store.commit_import(parsed["valid_rows"], policy=payload.policy)
        store.add_audit(
            op_id=op_id,
            actor=user.username,
            role=user.role,
            action="IMPORT_TARGETS",
            http_status=200,
            detail=f"批量导入完成：新增 {stats['added']} 台、覆盖 {stats['updated']} 台、跳过 {stats['skipped']} 台",
        )
        return JSONResponse(content={**stats, "op_id": op_id}, headers={"X-Op-Id": op_id})

    @app.get("/api/targets/export")
    def export_targets(
        format: Literal["csv", "json"] = Query(default="csv"),
        q: str = Query(default=""),
        type: str = Query(default=""),
        vendor: str = Query(default=""),
        collector_type: str = Query(default=""),
        alert_only: bool = Query(default=False),
    ) -> Response:
        items = store.list_targets(
            q=q,
            target_type=type,
            vendor=vendor,
            collector_type=collector_type,
            alert_only=alert_only,
        )
        if format == "json":
            return JSONResponse(content={"items": items})

        cols = [
            "host",
            "address",
            "type",
            "vendor",
            "collector_type",
            "ssh_port",
            "ssh_user",
            "ssh_credential_ref",
            "mem_total",
            "mem_free",
            "cores",
            "cpu",
            "probe_status",
            "last_checked_at",
        ]
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(cols)
        for item in items:
            writer.writerow([_csv_safe_cell(item.get(c)) for c in cols])
        content = "\ufeff" + buf.getvalue()
        return Response(
            content=content.encode("utf-8"),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="ops-inspect-export.csv"'},
        )

    @app.post("/api/inspect/run")
    def inspect_all(authorization: str | None = Header(default=None)) -> Response:
        op_id = _make_op_id()
        user, err = require_admin(authorization, "INSPECT_ALL", op_id)
        if err:
            return err

        if not inspect_lock.acquire(blocking=False):
            store.add_audit(
                op_id=op_id,
                actor=user.username,
                role=user.role,
                action="INSPECT_ALL",
                http_status=409,
                detail="已有全量巡检正在执行，重复触发已拦截",
            )
            return _err_resp(409, "已有全量巡检任务正在采集中，请稍候完成后再试。", op_id)

        try:
            targets = store.list_targets()
            results = inspect_all_targets(targets, cfg, max_workers=5)
            for res in results:
                store.update_probe_snapshot(
                    res.target_id,
                    mem_total=res.mem_total,
                    mem_free=res.mem_free,
                    cores=res.cores,
                    cpu=res.cpu,
                    probe_status=res.probe_status,
                    last_checked_at=res.last_checked_at,
                    probe_error=res.probe_error,
                )
            latest = store.list_targets()
            succeeded = sum(1 for r in results if r.ok)
            failed = len(results) - succeeded
            store.add_audit(
                op_id=op_id,
                actor=user.username,
                role=user.role,
                action="INSPECT_ALL",
                http_status=200,
                detail=f"全量巡检完成：共 {len(results)} 台，成功 {succeeded} 台，异常隔离 {failed} 台",
            )
            return JSONResponse(
                content={
                    "total": len(results),
                    "succeeded": succeeded,
                    "failed": failed,
                    "items": latest,
                    "op_id": op_id,
                },
                headers={"X-Op-Id": op_id},
            )
        finally:
            inspect_lock.release()

    @app.post("/api/inspect/{target_id}")
    def inspect_one(target_id: int, authorization: str | None = Header(default=None)) -> Response:
        op_id = _make_op_id()
        user, err = require_admin(authorization, "INSPECT_ONE", op_id)
        if err:
            return err

        target = store.get_target(target_id)
        if target is None:
            return _err_resp(404, "目标服务器不存在。", op_id)

        res = probe_target(target, cfg)
        updated = store.update_probe_snapshot(
            res.target_id,
            mem_total=res.mem_total,
            mem_free=res.mem_free,
            cores=res.cores,
            cpu=res.cpu,
            probe_status=res.probe_status,
            last_checked_at=res.last_checked_at,
            probe_error=res.probe_error,
        )

        if res.probe_status == "TIMEOUT":
            store.add_audit(
                op_id=op_id,
                actor=user.username,
                role=user.role,
                action="INSPECT_ONE",
                http_status=504,
                detail=f"单台采集 {target['host']}（{target['address']}）超时，已隔离未重试",
            )
            return _err_resp(
                504,
                f"{target['host']}（{target['address']}）等待超时无响应，已自动跳过且未重试，请检查网络或 SSH 服务状态。",
                op_id,
            )

        if not res.ok:
            store.add_audit(
                op_id=op_id,
                actor=user.username,
                role=user.role,
                action="INSPECT_ONE",
                http_status=502,
                detail=f"单台采集 {target['host']} 失败：{res.probe_error}",
            )
            return _err_resp(502, f"{target['host']} 采集失败：{res.probe_error}", op_id)

        store.add_audit(
            op_id=op_id,
            actor=user.username,
            role=user.role,
            action="INSPECT_ONE",
            http_status=200,
            detail=f"单台检测 {target['host']} 完成：CPU {res.cpu}%，可用内存 {res.mem_free}/{res.mem_total} GB",
        )
        return JSONResponse(content={"item": updated, "op_id": op_id}, headers={"X-Op-Id": op_id})

    @app.get("/api/schedule")
    def get_schedule() -> dict[str, Any]:
        s = store.get_schedule()
        smtp_view = mail_svc.get_public_smtp_view()
        return {
            "enabled": s["enabled"],
            "push_time": s["push_time"],
            "recipients": s["recipients"],
            "smtp_mode": smtp_view["mode"],
            "smtp": smtp_view,
        }

    @app.put("/api/schedule")
    def update_schedule(payload: SchedulePayload, authorization: str | None = Header(default=None)) -> Response:
        op_id = _make_op_id()
        user, err = require_admin(authorization, "UPDATE_SCHEDULE", op_id)
        if err:
            return err

        if not HHMM_RE.match(payload.push_time):
            return _err_resp(400, "推送时间格式必须为 HH:MM（如 09:00）。", op_id)
        cleaned_emails = [e.strip() for e in payload.recipients if e.strip()]
        if not cleaned_emails or any(not EMAIL_RE.match(e) for e in cleaned_emails):
            return _err_resp(400, "收件人列表包含无效邮箱地址或为空。", op_id)

        updated = store.update_schedule(
            enabled=payload.enabled,
            push_time=payload.push_time,
            recipients=cleaned_emails,
        )
        store.add_audit(
            op_id=op_id,
            actor=user.username,
            role=user.role,
            action="UPDATE_SCHEDULE",
            http_status=200,
            detail=f"{'启用' if updated['enabled'] else '停用'} 每日 {updated['push_time']} 定时推送（{len(cleaned_emails)} 位收件人）",
        )
        smtp_view = mail_svc.get_public_smtp_view()
        return JSONResponse(
            content={
                "enabled": updated["enabled"],
                "push_time": updated["push_time"],
                "recipients": updated["recipients"],
                "smtp_mode": smtp_view["mode"],
                "smtp": smtp_view,
                "op_id": op_id,
            },
            headers={"X-Op-Id": op_id},
        )

    @app.get("/api/smtp")
    def get_smtp_config() -> dict[str, Any]:
        return mail_svc.get_public_smtp_view()

    @app.put("/api/smtp")
    def update_smtp_config(payload: SmtpConfigPayload, authorization: str | None = Header(default=None)) -> Response:
        op_id = _make_op_id()
        user, err = require_admin(authorization, "UPDATE_SMTP", op_id)
        if err:
            return err

        host = payload.host.strip()
        username = payload.username.strip()
        from_addr = payload.from_addr.strip() or username
        raw_code = payload.auth_code.strip()

        if not payload.enabled:
            store.activate_smtp_profile(0)
            store.add_audit(
                op_id=op_id,
                actor=user.username,
                role=user.role,
                action="UPDATE_SMTP",
                http_status=200,
                detail="已切换为本地模拟收件箱模式（保留全部已保存发件账号）",
            )
            view = mail_svc.get_public_smtp_view()
            return JSONResponse(content={**view, "op_id": op_id}, headers={"X-Op-Id": op_id})

        if not host:
            return _err_resp(400, "启用真实发信时必须填写 SMTP 服务器地址（如 smtp.qq.com）。", op_id)
        if not username:
            return _err_resp(400, "启用真实发信时必须填写发件邮箱账号。", op_id)

        existing_profile = store.get_smtp_profile_by_username(username)
        has_existing_secret = bool(existing_profile and existing_profile.get("auth_code_enc"))
        if not raw_code and not has_existing_secret:
            return _err_resp(400, f"首次添加发件账号 {username} 时必须填写 SMTP 授权码。", op_id)

        enc_value = encrypt_secret(raw_code, cfg.effective_master_key) if raw_code else None
        store.upsert_smtp_profile(
            host=host,
            port=payload.port,
            security=payload.security,
            username=username,
            auth_code_enc=enc_value,
            from_addr=from_addr,
            timeout_seconds=payload.timeout_seconds,
            activate=True,
        )

        secret_note = "已更新加密授权码" if raw_code else "沿用已保存加密授权码"
        store.add_audit(
            op_id=op_id,
            actor=user.username,
            role=user.role,
            action="UPDATE_SMTP",
            http_status=200,
            detail=f"保存并启用发件账号 {username}（{host}:{payload.port} {payload.security.upper()}，{secret_note}）",
        )
        view = mail_svc.get_public_smtp_view()
        return JSONResponse(content={**view, "op_id": op_id}, headers={"X-Op-Id": op_id})

    @app.post("/api/smtp/profiles/{profile_id}/activate")
    def activate_smtp_profile(profile_id: int, authorization: str | None = Header(default=None)) -> Response:
        op_id = _make_op_id()
        user, err = require_admin(authorization, "ACTIVATE_SMTP_PROFILE", op_id)
        if err:
            return err

        res = store.activate_smtp_profile(profile_id)
        if res is None:
            return _err_resp(404, "指定的发件邮箱存档不存在。", op_id)

        detail = (
            "已切换为本地模拟收件箱（暂停外部 SMTP 发信）"
            if profile_id == 0
            else f"已切换当前发件账号为 {res['username']}（{res['host']}:{res['port']}）"
        )
        store.add_audit(
            op_id=op_id,
            actor=user.username,
            role=user.role,
            action="ACTIVATE_SMTP_PROFILE",
            http_status=200,
            detail=detail,
        )
        view = mail_svc.get_public_smtp_view()
        return JSONResponse(content={**view, "op_id": op_id}, headers={"X-Op-Id": op_id})

    @app.delete("/api/smtp/profiles/{profile_id}")
    def delete_smtp_profile(profile_id: int, authorization: str | None = Header(default=None)) -> Response:
        op_id = _make_op_id()
        user, err = require_admin(authorization, "DELETE_SMTP_PROFILE", op_id)
        if err:
            return err

        deleted = store.delete_smtp_profile(profile_id)
        if deleted is None:
            return _err_resp(404, "指定的发件邮箱存档不存在。", op_id)

        store.add_audit(
            op_id=op_id,
            actor=user.username,
            role=user.role,
            action="DELETE_SMTP_PROFILE",
            http_status=200,
            detail=f"删除已保存发件账号 {deleted['username']}（{deleted['host']}）",
        )
        view = mail_svc.get_public_smtp_view()
        return JSONResponse(content={**view, "op_id": op_id}, headers={"X-Op-Id": op_id})

    @app.get("/api/reports/markdown")
    def get_markdown_report() -> PlainTextResponse:
        targets = store.list_targets()
        return PlainTextResponse(content=build_markdown_report(targets), media_type="text/markdown; charset=utf-8")

    @app.post("/api/reports/push")
    def push_report_now(authorization: str | None = Header(default=None)) -> Response:
        op_id = _make_op_id()
        user, err = require_admin(authorization, "PUSH_REPORT_NOW", op_id)
        if err:
            return err

        sched = store.get_schedule()
        recipients = sched.get("recipients") or []
        if not recipients:
            return _err_resp(400, "尚未配置任何收件邮箱，请先在定时配置中保存收件人。", op_id)

        targets = store.list_targets()
        try:
            msg = mail_svc.push_report(targets=targets, recipients=recipients, op_id=op_id)
        except PushConflictError as exc:
            store.add_audit(
                op_id=op_id,
                actor=user.username,
                role=user.role,
                action="PUSH_REPORT_NOW",
                http_status=409,
                detail="并发推送被防重锁拦截",
            )
            return _err_resp(409, str(exc), op_id)
        except SmtpTimeoutError as exc:
            store.add_audit(
                op_id=op_id,
                actor=user.username,
                role=user.role,
                action="PUSH_REPORT_NOW",
                http_status=504,
                detail="SMTP 发送超时（结果未知，已禁止自动重试）",
            )
            return _err_resp(504, str(exc), op_id)
        except SmtpDeliveryError as exc:
            store.add_audit(
                op_id=op_id,
                actor=user.username,
                role=user.role,
                action="PUSH_REPORT_NOW",
                http_status=502,
                detail=f"SMTP 发送失败：{exc}",
            )
            return _err_resp(502, str(exc), op_id)

        delivery_mode = msg.get("delivery_mode") or mail_svc.get_public_smtp_view()["mode"]
        store.add_audit(
            op_id=op_id,
            actor=user.username,
            role=user.role,
            action="PUSH_REPORT_NOW",
            http_status=200,
            detail=f"手动推送成功（通道：{delivery_mode}，收件人：{len(recipients)} 位）",
        )
        return JSONResponse(
            content={"status": "sent", "delivery_mode": delivery_mode, "message": msg, "op_id": op_id},
            headers={"X-Op-Id": op_id},
        )

    @app.get("/api/outbox")
    def list_outbox() -> dict[str, Any]:
        return {"items": store.list_outbox()}

    @app.get("/api/audits")
    def list_audits() -> dict[str, Any]:
        return {"items": store.list_audits()}

    return app


app = create_app()
