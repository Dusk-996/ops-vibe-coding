import React, { useEffect, useRef, useState } from "react";

const DURATION_MS = 10000;

function ToastIcon({ type }) {
  if (type === "ok") {
    return (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
        <polyline points="20 6 9 17 4 12" />
      </svg>
    );
  }
  if (type === "warn") {
    return (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
        <line x1="12" y1="8" x2="12" y2="13" />
        <line x1="12" y1="17" x2="12.01" y2="17" />
      </svg>
    );
  }
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  );
}

export default function ToastCard({ toast, onClose }) {
  const [paused, setPaused] = useState(false);
  const remainingRef = useRef(DURATION_MS);
  const startedAtRef = useRef(Date.now());

  useEffect(() => {
    if (!toast) return;
    remainingRef.current = DURATION_MS;
    startedAtRef.current = Date.now();
    setPaused(false);
  }, [toast?.id]);

  useEffect(() => {
    if (!toast || paused) return undefined;
    startedAtRef.current = Date.now();
    const timer = setTimeout(() => {
      onClose();
    }, Math.max(0, remainingRef.current));

    return () => {
      clearTimeout(timer);
      const elapsed = Date.now() - startedAtRef.current;
      remainingRef.current = Math.max(0, remainingRef.current - elapsed);
    };
  }, [toast?.id, paused, onClose]);

  if (!toast) return null;

  const fallbackTitle =
    toast.type === "ok" ? "操作已完成" : toast.type === "warn" ? "状态提醒" : "操作未能执行";

  return (
    <div className="toast-container" role="status" aria-live="polite">
      <div
        className={`toast-card ${toast.type} ${paused ? "is-paused" : ""}`}
        key={toast.id}
        onMouseEnter={() => setPaused(true)}
        onMouseLeave={() => setPaused(false)}
      >
        <div className="toast-icon" aria-hidden="true">
          <ToastIcon type={toast.type} />
        </div>

        <div className="toast-content">
          <div className="toast-head">
            <span className="toast-title">{toast.title || fallbackTitle}</span>
            <span className="toast-timer">{paused ? "悬停已暂停" : "10s 自动关闭"}</span>
          </div>
          <div className="toast-msg">{toast.msg}</div>
          {toast.opId && <div className="toast-meta mono">追踪号 {toast.opId}</div>}
        </div>

        <button className="toast-close" type="button" aria-label="关闭通知" onClick={onClose}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>

        <div className="toast-progress" aria-hidden="true">
          <i />
        </div>
      </div>
    </div>
  );
}
