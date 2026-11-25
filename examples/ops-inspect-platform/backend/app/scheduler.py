"""单实例进程内轻量定时调度器：到点先全量巡检，再推送报告，同分钟幂等防重发。"""

from __future__ import annotations

import threading
import uuid
from datetime import datetime
from typing import Callable

from .collector import inspect_all_targets
from .config import Settings
from .mailer import MailerService, PushConflictError, SmtpDeliveryError, SmtpTimeoutError
from .storage import Storage


class InspectionScheduler:
    def __init__(
        self,
        settings: Settings,
        storage: Storage,
        mailer: MailerService,
        poll_seconds: float = 20.0,
    ) -> None:
        self.settings = settings
        self.storage = storage
        self.mailer = mailer
        self.poll_seconds = poll_seconds
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self.settings.disable_scheduler:
            return
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, name="ops-inspect-scheduler", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

    def _loop(self) -> None:
        while not self._stop_event.wait(self.poll_seconds):
            try:
                self.tick_once()
            except Exception:
                # 守护循环内兜底捕获，防止调度线程意外退出
                pass

    def tick_once(self, now_fn: Callable[[], datetime] = datetime.now) -> bool:
        """检查当前分钟是否命中定时规则；命中则同分钟幂等执行全量巡检+邮件推送。"""
        cfg = self.storage.get_schedule()
        if not cfg.get("enabled"):
            return False

        now = now_fn()
        hhmm = now.strftime("%H:%M")
        if hhmm != cfg.get("push_time"):
            return False

        minute_key = now.strftime("%Y-%m-%d %H:%M")
        if not self.storage.mark_schedule_triggered(minute_key):
            return False

        op_id = f"op-{uuid.uuid4().hex[:8]}"
        targets = self.storage.list_targets()
        results = inspect_all_targets(targets, self.settings)
        for res in results:
            self.storage.update_probe_snapshot(
                res.target_id,
                mem_total=res.mem_total,
                mem_free=res.mem_free,
                cores=res.cores,
                cpu=res.cpu,
                probe_status=res.probe_status,
                last_checked_at=res.last_checked_at,
                probe_error=res.probe_error,
            )

        latest = self.storage.list_targets()
        ok_cnt = sum(1 for r in results if r.ok)
        fail_cnt = len(results) - ok_cnt
        recipients = cfg.get("recipients") or []
        if not recipients:
            return True

        try:
            self.mailer.push_report(targets=latest, recipients=recipients, op_id=op_id)
            self.storage.add_audit(
                op_id=op_id,
                actor="scheduler",
                role="system",
                action="SCHEDULED_INSPECT_AND_PUSH",
                http_status=200,
                detail=f"定时任务触发：巡检 {len(results)} 台（成功 {ok_cnt} / 异常 {fail_cnt}），已推送至 {len(recipients)} 位收件人",
            )
        except PushConflictError:
            self.storage.add_audit(
                op_id=op_id,
                actor="scheduler",
                role="system",
                action="SCHEDULED_INSPECT_AND_PUSH",
                http_status=409,
                detail="定时推送被并发防重锁拦截",
            )
        except SmtpTimeoutError:
            self.storage.add_audit(
                op_id=op_id,
                actor="scheduler",
                role="system",
                action="SCHEDULED_INSPECT_AND_PUSH",
                http_status=504,
                detail="定时推送 SMTP 超时（结果未知，未自动重试）",
            )
        except SmtpDeliveryError as exc:
            self.storage.add_audit(
                op_id=op_id,
                actor="scheduler",
                role="system",
                action="SCHEDULED_INSPECT_AND_PUSH",
                http_status=502,
                detail=f"定时推送失败：{exc}",
            )
        return True
