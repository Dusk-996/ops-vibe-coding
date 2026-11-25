"""单实例进程内轻量定时调度器：到点先全量巡检，再推送报告，同分钟幂等防重发。"""

from __future__ import annotations

import logging
import threading
import uuid
from datetime import datetime
from typing import Callable

from .collector import inspect_all_targets
from .config import Settings
from .mailer import MailerService, PushConflictError, SmtpDeliveryError, SmtpTimeoutError
from .storage import Storage

logger = logging.getLogger("ops_inspect.scheduler")


class InspectionScheduler:
    def __init__(
        self,
        settings: Settings,
        storage: Storage,
        mailer: MailerService,
        poll_seconds: float = 20.0,
        inspect_lock: threading.Lock | None = None,
    ) -> None:
        self.settings = settings
        self.storage = storage
        self.mailer = mailer
        self.poll_seconds = poll_seconds
        self._inspect_lock = inspect_lock or threading.Lock()
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
        logger.info("定时巡检调度器已启动（轮询间隔 %.1fs）", self.poll_seconds)

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("定时巡检调度器已停止")

    def _run_loop_iteration(self) -> None:
        """执行单次调度轮询并在异常时落日志与审计，避免守护线程静默吞错或退出。"""
        try:
            self.tick_once()
        except Exception as exc:
            op_id = f"op-{uuid.uuid4().hex[:8]}"
            logger.exception("后台定时调度轮询发生未预期异常 op_id=%s", op_id)
            try:
                self.storage.add_audit(
                    op_id=op_id,
                    actor="scheduler",
                    role="system",
                    action="SCHEDULER_LOOP_ERROR",
                    http_status=500,
                    detail=f"定时调度后台异常（{exc.__class__.__name__}），请凭操作编号查看服务端日志",
                )
            except Exception:
                logger.exception("写入定时调度异常审计失败 op_id=%s", op_id)

    def _loop(self) -> None:
        while not self._stop_event.wait(self.poll_seconds):
            self._run_loop_iteration()

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
        if not self._inspect_lock.acquire(blocking=False):
            logger.warning("定时全量巡检与手动巡检并发冲突，已跳过本轮 op_id=%s minute=%s", op_id, minute_key)
            self.storage.add_audit(
                op_id=op_id,
                actor="scheduler",
                role="system",
                action="SCHEDULED_INSPECT_AND_PUSH",
                http_status=409,
                detail="定时巡检与手动全量巡检撞车，已被并发防重锁跳过",
            )
            return False

        try:
            logger.info("定时巡检命中触发 op_id=%s minute=%s", op_id, minute_key)
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
        finally:
            self._inspect_lock.release()

        latest = self.storage.list_targets()
        ok_cnt = sum(1 for r in results if r.ok)
        fail_cnt = len(results) - ok_cnt
        recipients = cfg.get("recipients") or []
        if not recipients:
            logger.info("定时巡检完成但未配置收件人，跳过发信 op_id=%s ok=%d fail=%d", op_id, ok_cnt, fail_cnt)
            return True

        try:
            self.mailer.push_report(targets=latest, recipients=recipients, op_id=op_id)
            logger.info("定时巡检与推送完成 op_id=%s ok=%d fail=%d recipients=%d", op_id, ok_cnt, fail_cnt, len(recipients))
            self.storage.add_audit(
                op_id=op_id,
                actor="scheduler",
                role="system",
                action="SCHEDULED_INSPECT_AND_PUSH",
                http_status=200,
                detail=f"定时任务触发：巡检 {len(results)} 台（成功 {ok_cnt} / 异常 {fail_cnt}），已推送至 {len(recipients)} 位收件人",
            )
        except PushConflictError:
            logger.warning("定时推送被并发防重锁拦截 op_id=%s", op_id)
            self.storage.add_audit(
                op_id=op_id,
                actor="scheduler",
                role="system",
                action="SCHEDULED_INSPECT_AND_PUSH",
                http_status=409,
                detail="定时推送被并发防重锁拦截",
            )
        except SmtpTimeoutError:
            logger.error("定时推送 SMTP 超时（未自动重试） op_id=%s", op_id)
            self.storage.add_audit(
                op_id=op_id,
                actor="scheduler",
                role="system",
                action="SCHEDULED_INSPECT_AND_PUSH",
                http_status=504,
                detail="定时推送 SMTP 超时（结果未知，未自动重试）",
            )
        except SmtpDeliveryError as exc:
            logger.error("定时推送失败 op_id=%s reason=%s", op_id, exc)
            self.storage.add_audit(
                op_id=op_id,
                actor="scheduler",
                role="system",
                action="SCHEDULED_INSPECT_AND_PUSH",
                http_status=502,
                detail=f"定时推送失败：{exc}",
            )
        return True
