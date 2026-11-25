"""巡检报告生成、标准 SMTP（兼容 465 SSL / 587 STARTTLS）与本地模拟收件箱双模式。"""

from __future__ import annotations

import html
import smtplib
import socket
import ssl
import threading
from dataclasses import replace
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate, make_msgid
from typing import Any, Callable

from .config import Settings
from .crypto import decrypt_secret
from .storage import Storage, now_str


class PushConflictError(RuntimeError):
    """已有推送任务进行中（HTTP 409）。"""


class SmtpTimeoutError(RuntimeError):
    """SMTP 响应超时，结果未知且严禁自动重试（HTTP 504）。"""


class SmtpDeliveryError(RuntimeError):
    """SMTP 投递失败（HTTP 502）。"""


STATUS_TEXT = {
    "OK": "正常",
    "WARN": "关注",
    "HIGH_LOAD": "高负载",
    "TIMEOUT": "检测超时",
    "UNREACHABLE": "不可达",
    "PENDING": "待检测",
}


def _classify_targets(targets: list[dict[str, Any]]) -> dict[str, Any]:
    probed = [t for t in targets if t.get("mem_total") is not None]
    normal = [t for t in targets if t.get("probe_status") == "OK"]
    abnormal = [t for t in targets if t.get("probe_status") != "OK"]
    high = [t for t in targets if t.get("probe_status") == "HIGH_LOAD"]
    warn = [t for t in targets if t.get("probe_status") == "WARN"]
    failed = [t for t in targets if t.get("probe_status") in ("TIMEOUT", "UNREACHABLE")]
    pending = [t for t in targets if t.get("probe_status") not in ("OK", "WARN", "HIGH_LOAD", "TIMEOUT", "UNREACHABLE")]

    total_mem = round(sum(float(t["mem_total"]) for t in probed), 1)
    free_mem = round(sum(float(t["mem_free"] or 0) for t in probed), 1)
    free_pct = f"{(free_mem / total_mem * 100):.1f}%" if total_mem > 0 else "0.0%"
    avg_cpu = f"{(sum(float(t['cpu'] or 0) for t in probed) / len(probed)):.1f}%" if probed else "-"

    return {
        "total": len(targets),
        "probed": probed,
        "normal": normal,
        "abnormal": abnormal,
        "high": high,
        "warn": warn,
        "failed": failed,
        "pending": pending,
        "total_mem": total_mem,
        "free_mem": free_mem,
        "free_pct": free_pct,
        "avg_cpu": avg_cpu,
    }


def _abnormal_reason(t: dict[str, Any]) -> str:
    st = str(t.get("probe_status") or "PENDING")
    if t.get("probe_error"):
        return str(t["probe_error"])
    if st == "HIGH_LOAD":
        return f"高负载（CPU {t.get('cpu')}%，剩余内存 {t.get('mem_free')}/{t.get('mem_total')} GB）"
    if st == "WARN":
        return f"接近水位（CPU {t.get('cpu')}%，剩余内存 {t.get('mem_free')}/{t.get('mem_total')} GB）"
    if st == "PENDING":
        return "尚未执行采集检测"
    return "状态异常"


def build_markdown_report(targets: list[dict[str, Any]], timestamp: str | None = None) -> str:
    """总—分生产结构：先汇总总体概况，仅详细展示异常/待关注主机，正常主机省略明细不刷屏。"""
    ts = timestamp or now_str()
    stat = _classify_targets(targets)

    issue_breakdown = []
    if stat["high"]:
        issue_breakdown.append(f"高负载 {len(stat['high'])} 台")
    if stat["warn"]:
        issue_breakdown.append(f"需关注 {len(stat['warn'])} 台")
    if stat["failed"]:
        issue_breakdown.append(f"采集失败/超时 {len(stat['failed'])} 台")
    if stat["pending"]:
        issue_breakdown.append(f"待检测 {len(stat['pending'])} 台")
    issue_summary = "、".join(issue_breakdown) if issue_breakdown else "无异常节点"

    lines = [
        f"# 服务器巡检报告（{ts}）",
        "",
        "## 一、巡检总览",
        f"- 纳管服务器总数：{stat['total']} 台（正常 {len(stat['normal'])} 台 ｜ 异常/需关注 {len(stat['abnormal'])} 台）",
        f"- 异常分布：{issue_summary}",
        f"- 已采节点资源汇总：总内存 {stat['total_mem']} GB ｜ 可用剩余 {stat['free_mem']} GB（{stat['free_pct']}）｜ 平均 CPU {stat['avg_cpu']}",
        "",
    ]

    if stat["abnormal"]:
        lines.extend(
            [
                f"## 二、异常及需关注主机明细（共 {len(stat['abnormal'])} 台）",
                "| 主机名 | IP 地址 | 类型 / 厂商 | 总内存(GB) | 可用内存(GB) | CPU | 状态 | 异常说明 |",
                "|---|---|---|---:|---:|---:|---|---|",
            ]
        )
        for t in stat["abnormal"]:
            st = STATUS_TEXT.get(str(t.get("probe_status", "PENDING")), "待检测")
            mt = t["mem_total"] if t.get("mem_total") is not None else "-"
            mf = t["mem_free"] if t.get("mem_free") is not None else "-"
            cpu_str = f"{t['cpu']}%" if t.get("cpu") is not None else "-"
            reason = _abnormal_reason(t).replace("|", "/")
            lines.append(
                f"| {t['host']} | {t['address']} | {t['type']} / {t['vendor']} | {mt} | {mf} | {cpu_str} | {st} | {reason} |"
            )
    else:
        lines.extend(
            [
                "## 二、异常主机明细",
                f"当前全部 {stat['total']} 台纳管服务器均运行正常，无高负载或采集异常节点。",
            ]
        )

    if stat["normal"]:
        lines.extend(
            [
                "",
                "## 三、正常运行主机说明",
                f"共 {len(stat['normal'])} 台服务器运行平稳（状态：正常），已省略逐台明细；如需全量清单请在巡检平台查看或导出。",
            ]
        )

    return "\n".join(lines)


def build_html_email(targets: list[dict[str, Any]], timestamp: str) -> str:
    """生成生产级总—分 HTML 邮件正文：先总览 KPI，仅详展异常主机表，正常主机简述不刷屏。"""
    stat = _classify_targets(targets)

    issue_parts = []
    if stat["high"]:
        issue_parts.append(f"高负载 {len(stat['high'])} 台")
    if stat["warn"]:
        issue_parts.append(f"关注 {len(stat['warn'])} 台")
    if stat["failed"]:
        issue_parts.append(f"采集异常 {len(stat['failed'])} 台")
    if stat["pending"]:
        issue_parts.append(f"待检测 {len(stat['pending'])} 台")
    issue_text = " · ".join(issue_parts) if issue_parts else "全部运行平稳"

    if stat["abnormal"]:
        rows_html = []
        for t in stat["abnormal"]:
            st_key = str(t.get("probe_status", "PENDING"))
            st_text = STATUS_TEXT.get(st_key, "待检测")
            color = "#b45309" if st_key == "WARN" else "#64748b" if st_key == "PENDING" else "#b91c1c"
            mt = f"{t['mem_total']} G" if t.get("mem_total") is not None else "-"
            mf = f"{t['mem_free']} G" if t.get("mem_free") is not None else "-"
            cpu = f"{t['cpu']}%" if t.get("cpu") is not None else "-"
            reason = _abnormal_reason(t)
            rows_html.append(
                "<tr>"
                f"<td style='padding:9px 10px;border-bottom:1px solid #e2e8f0;font-family:monospace;font-weight:600'>{html.escape(str(t['host']))}</td>"
                f"<td style='padding:9px 10px;border-bottom:1px solid #e2e8f0;font-family:monospace'>{html.escape(str(t['address']))}</td>"
                f"<td style='padding:9px 10px;border-bottom:1px solid #e2e8f0'>{html.escape(mt)} / {html.escape(mf)}</td>"
                f"<td style='padding:9px 10px;border-bottom:1px solid #e2e8f0'>{html.escape(cpu)}</td>"
                f"<td style='padding:9px 10px;border-bottom:1px solid #e2e8f0;color:{color};font-weight:700'>{html.escape(st_text)}</td>"
                f"<td style='padding:9px 10px;border-bottom:1px solid #e2e8f0;color:#334155'>{html.escape(reason)}</td>"
                "</tr>"
            )
        abnormal_section = (
            f"<h3 style='margin:18px 0 10px;font-size:15px;color:#0f172a'>异常及需关注主机明细（{len(stat['abnormal'])} 台）</h3>"
            "<table style='width:100%;border-collapse:collapse;font-size:13px;border:1px solid #e2e8f0'>"
            "<thead><tr style='background:#f8fafc;text-align:left;color:#475569'>"
            "<th style='padding:9px 10px;border-bottom:1px solid #e2e8f0'>主机名</th>"
            "<th style='padding:9px 10px;border-bottom:1px solid #e2e8f0'>IP 地址</th>"
            "<th style='padding:9px 10px;border-bottom:1px solid #e2e8f0'>总内存 / 可用</th>"
            "<th style='padding:9px 10px;border-bottom:1px solid #e2e8f0'>CPU</th>"
            "<th style='padding:9px 10px;border-bottom:1px solid #e2e8f0'>状态</th>"
            "<th style='padding:9px 10px;border-bottom:1px solid #e2e8f0'>异常说明</th>"
            "</tr></thead>"
            f"<tbody>{''.join(rows_html)}</tbody>"
            "</table>"
        )
    else:
        abnormal_section = (
            "<div style='margin-top:16px;padding:12px 16px;background:#ecfdf5;border:1px solid #a7f3d0;border-radius:8px;color:#047857;font-size:14px;font-weight:600'>"
            f"当前全部 {stat['total']} 台纳管服务器均运行正常，无高负载或采集异常节点。"
            "</div>"
        )

    normal_footer = (
        f"<p style='margin:16px 0 0;font-size:13px;color:#64748b'>说明：其余 <strong>{len(stat['normal'])}</strong> 台正常运行主机已省略明细，如需查看全量资产请登录智能服务器巡检平台。</p>"
        if stat["normal"]
        else ""
    )

    return (
        "<div style='font-family:Microsoft YaHei,Segoe UI,sans-serif;color:#0f172a;max-width:820px;line-height:1.6'>"
        f"<h2 style='margin:0 0 14px;font-size:18px;border-bottom:1px solid #e2e8f0;padding-bottom:10px'>服务器巡检报告（{html.escape(timestamp)}）</h2>"
        "<table style='width:100%;border-collapse:separate;border-spacing:10px 0;margin:0 -10px 14px'>"
        "<tr>"
        f"<td style='background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:12px 14px'><div style='font-size:12px;color:#64748b'>纳管总数</div><div style='font-size:22px;font-weight:700;font-family:monospace'>{stat['total']} 台</div></td>"
        f"<td style='background:#ecfdf5;border:1px solid #a7f3d0;border-radius:8px;padding:12px 14px'><div style='font-size:12px;color:#047857'>正常运行</div><div style='font-size:22px;font-weight:700;font-family:monospace;color:#047857'>{len(stat['normal'])} 台</div></td>"
        f"<td style='background:{'#fef2f2' if stat['abnormal'] else '#f8fafc'};border:1px solid {'#fecaca' if stat['abnormal'] else '#e2e8f0'};border-radius:8px;padding:12px 14px'><div style='font-size:12px;color:{'#b91c1c' if stat['abnormal'] else '#64748b'}'>异常 / 需关注</div><div style='font-size:22px;font-weight:700;font-family:monospace;color:{'#b91c1c' if stat['abnormal'] else '#0f172a'}'>{len(stat['abnormal'])} 台</div></td>"
        "</tr>"
        "</table>"
        "<div style='background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:11px 15px;font-size:13.5px;color:#334155'>"
        f"<div><strong>异常分布：</strong>{html.escape(issue_text)}</div>"
        f"<div><strong>已采节点资源：</strong>总内存 {stat['total_mem']} GB ｜ 可用剩余 {stat['free_mem']} GB（{stat['free_pct']}）｜ 平均 CPU {stat['avg_cpu']}</div>"
        "</div>"
        f"{abnormal_section}"
        f"{normal_footer}"
        "</div>"
    )


def _is_timeout_exception(exc: BaseException) -> bool:
    cur: BaseException | None = exc
    while cur is not None:
        if isinstance(cur, (TimeoutError, socket.timeout)):
            return True
        if "timed out" in str(cur).lower():
            return True
        cur = cur.__cause__ or cur.__context__
    return False


def default_smtp_send(
    settings: Settings,
    recipients: list[str],
    subject: str,
    body_md: str,
    body_html: str,
) -> None:
    """真实 SMTP 发送（单次尝试，超时不自动重试；兼容 QQ 邮箱 465 SSL 与 587 STARTTLS）。"""
    from_addr = (settings.smtp_from or settings.smtp_user).strip()
    msg = MIMEMultipart("alternative")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = formataddr((str(Header("智能服务器巡检平台", "utf-8")), from_addr))
    msg["To"] = ", ".join(recipients)
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid()
    msg.attach(MIMEText(body_md, "plain", "utf-8"))
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    timeout = max(10, settings.smtp_timeout_seconds)
    if settings.smtp_use_ssl:
        server: smtplib.SMTP = smtplib.SMTP_SSL(
            settings.smtp_host,
            settings.smtp_port,
            timeout=timeout,
            context=ssl.create_default_context(),
        )
    else:
        server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=timeout)

    try:
        server.ehlo()
        if not settings.smtp_use_ssl and settings.smtp_use_tls:
            server.starttls(context=ssl.create_default_context())
            server.ehlo()
        if settings.smtp_user and settings.smtp_pass:
            server.login(settings.smtp_user, settings.smtp_pass)
        server.sendmail(from_addr, recipients, msg.as_string())
    finally:
        # QQ 邮箱等服务商在 sendmail 成功后偶发 QUIT 不回 221 断连，收紧关闭超时避免卡顿或误报失败
        try:
            if getattr(server, "sock", None) is not None:
                server.sock.settimeout(2)
            server.quit()
        except Exception:
            try:
                server.close()
            except Exception:
                pass


class MailerService:
    def __init__(
        self,
        settings: Settings,
        storage: Storage,
        smtp_sender: Callable[[Settings, list[str], str, str, str], None] | None = None,
    ) -> None:
        self.settings = settings
        self.storage = storage
        self.smtp_sender = smtp_sender or default_smtp_send
        self._push_lock = threading.Lock()

    def resolve_runtime_smtp(self) -> tuple[str, str, Settings]:
        """动态解析当前生效的发信配置（优先已激活发件箱存档 -> 其次单行配置 -> 环境变量兜底）。"""
        active_profile = self.storage.get_active_smtp_profile()
        if active_profile is not None and active_profile["host"].strip():
            sec = str(active_profile.get("security") or "ssl").lower()
            secret_plain = decrypt_secret(active_profile.get("auth_code_enc") or "", self.settings.effective_master_key)
            runtime = replace(
                self.settings,
                smtp_host=active_profile["host"].strip(),
                smtp_port=int(active_profile["port"]),
                smtp_user=active_profile["username"].strip(),
                smtp_pass=secret_plain,
                smtp_from=(active_profile["from_addr"] or active_profile["username"] or self.settings.smtp_from).strip(),
                smtp_use_ssl=(sec == "ssl"),
                smtp_use_tls=(sec == "starttls"),
                smtp_timeout_seconds=max(1, int(active_profile.get("timeout_seconds") or 10)),
            )
            return "smtp", "database", runtime

        db_cfg = self.storage.get_smtp_config()
        if db_cfg is not None:
            if db_cfg["enabled"] and db_cfg["host"].strip():
                sec = str(db_cfg.get("security") or "ssl").lower()
                secret_plain = decrypt_secret(db_cfg.get("auth_code_enc") or "", self.settings.effective_master_key)
                runtime = replace(
                    self.settings,
                    smtp_host=db_cfg["host"].strip(),
                    smtp_port=int(db_cfg["port"]),
                    smtp_user=db_cfg["username"].strip(),
                    smtp_pass=secret_plain,
                    smtp_from=(db_cfg["from_addr"] or db_cfg["username"] or self.settings.smtp_from).strip(),
                    smtp_use_ssl=(sec == "ssl"),
                    smtp_use_tls=(sec == "starttls"),
                    smtp_timeout_seconds=max(1, int(db_cfg.get("timeout_seconds") or 10)),
                )
                return "smtp", "database", runtime
            return "mock", "database", self.settings

        if self.settings.smtp_host.strip():
            return "smtp", "env", self.settings
        return "mock", "none", self.settings

    @staticmethod
    def _sanitize_profile(p: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": p["id"],
            "host": p["host"],
            "port": p["port"],
            "security": p["security"],
            "username": p["username"],
            "from_addr": p["from_addr"],
            "timeout_seconds": p["timeout_seconds"],
            "is_active": p["is_active"],
            "has_auth_code": bool(p.get("auth_code_enc")),
            "updated_at": p.get("updated_at", ""),
        }

    def get_public_smtp_view(self) -> dict[str, Any]:
        """返回脱敏后的 SMTP 状态视图与已保存账号列表（永不回显授权码明文或密文）。"""
        mode, source, _ = self.resolve_runtime_smtp()
        profiles = [self._sanitize_profile(p) for p in self.storage.list_smtp_profiles()]
        active = next((p for p in profiles if p["is_active"]), None)

        if active is not None:
            return {
                "mode": mode,
                "source": source,
                "enabled": True,
                "active_profile_id": active["id"],
                "host": active["host"],
                "port": active["port"],
                "security": active["security"],
                "username": active["username"],
                "from_addr": active["from_addr"],
                "timeout_seconds": active["timeout_seconds"],
                "has_auth_code": active["has_auth_code"],
                "updated_at": active["updated_at"],
                "profiles": profiles,
            }

        db_cfg = self.storage.get_smtp_config()
        if db_cfg is not None:
            return {
                "mode": mode,
                "source": source,
                "enabled": db_cfg["enabled"],
                "active_profile_id": None,
                "host": db_cfg["host"],
                "port": db_cfg["port"],
                "security": db_cfg["security"],
                "username": db_cfg["username"],
                "from_addr": db_cfg["from_addr"],
                "timeout_seconds": db_cfg["timeout_seconds"],
                "has_auth_code": bool(db_cfg.get("auth_code_enc")),
                "updated_at": db_cfg.get("updated_at", ""),
                "profiles": profiles,
            }

        if self.settings.smtp_host.strip():
            sec = "ssl" if self.settings.smtp_use_ssl else ("starttls" if self.settings.smtp_use_tls else "none")
            return {
                "mode": mode,
                "source": source,
                "enabled": True,
                "active_profile_id": None,
                "host": self.settings.smtp_host,
                "port": self.settings.smtp_port,
                "security": sec,
                "username": self.settings.smtp_user,
                "from_addr": self.settings.smtp_from,
                "timeout_seconds": self.settings.smtp_timeout_seconds,
                "has_auth_code": bool(self.settings.smtp_pass),
                "updated_at": "",
                "profiles": profiles,
            }
        return {
            "mode": "mock",
            "source": "none",
            "enabled": False,
            "active_profile_id": None,
            "host": "",
            "port": 465,
            "security": "ssl",
            "username": "",
            "from_addr": "",
            "timeout_seconds": 10,
            "has_auth_code": False,
            "updated_at": "",
            "profiles": profiles,
        }

    def push_report(
        self,
        *,
        targets: list[dict[str, Any]],
        recipients: list[str],
        op_id: str,
    ) -> dict[str, Any]:
        """执行一次报告推送：并发立即 409；SMTP 超时立即 504 且严禁自动重试。"""
        if not self._push_lock.acquire(blocking=False):
            raise PushConflictError("已有推送任务正在执行，本次请求已被防重锁拦截。")

        try:
            mode, _source, runtime_cfg = self.resolve_runtime_smtp()
            ts = now_str()
            subject = f"服务器每日巡检报告（{ts}）"
            body_md = build_markdown_report(targets, timestamp=ts)
            body_html = build_html_email(targets, timestamp=ts)
            rec_str = ", ".join(recipients)

            if mode == "mock":
                return self.storage.add_outbox(
                    op_id=op_id,
                    delivery_mode="mock",
                    status_code=200,
                    recipients=rec_str,
                    subject=subject,
                    body_md=body_md,
                )

            try:
                # 仅调用 1 次，严格禁止任何自动重试循环
                self.smtp_sender(runtime_cfg, recipients, subject, body_md, body_html)
            except Exception as exc:
                if _is_timeout_exception(exc):
                    self.storage.add_outbox(
                        op_id=op_id,
                        delivery_mode="smtp",
                        status_code=504,
                        recipients=rec_str,
                        subject=subject,
                        body_md=body_md,
                        error="SMTP 响应超时（结果未知，已禁止自动重试）",
                    )
                    raise SmtpTimeoutError("邮件服务器响应超时，投递结果未知，系统已禁止自动重试。") from exc
                self.storage.add_outbox(
                    op_id=op_id,
                    delivery_mode="smtp",
                    status_code=502,
                    recipients=rec_str,
                    subject=subject,
                    body_md=body_md,
                    error=f"SMTP 发送失败：{exc.__class__.__name__}",
                )
                raise SmtpDeliveryError(f"邮件发送失败：{exc}") from exc

            return self.storage.add_outbox(
                op_id=op_id,
                delivery_mode="smtp",
                status_code=200,
                recipients=rec_str,
                subject=subject,
                body_md=body_md,
            )
        finally:
            self._push_lock.release()
