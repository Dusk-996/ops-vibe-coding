import React, { useEffect } from "react";
import { downloadBlob } from "../utils/format.js";
import ReportView from "./ReportView.jsx";

export default function MailDrawer({ mail, onClose, onExportDone }) {
  useEffect(() => {
    if (!mail) return undefined;
    const onKeyDown = (e) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [mail, onClose]);

  if (!mail) return null;

  const isSuccess = mail.status_code === 200;
  const isSmtp = mail.delivery_mode === "smtp";
  const statusLabel = isSmtp
    ? isSuccess
      ? "SMTP 已发送"
      : `发送异常 (${mail.status_code})`
    : isSuccess
      ? "模拟投递成功"
      : `模拟异常 (${mail.status_code})`;

  const recipients = String(mail.recipients || "")
    .split(",")
    .map((r) => r.trim())
    .filter(Boolean);

  const handleDownload = () => {
    const stamp = String(mail.created_at || "report").replace(/[: ]/g, "-");
    downloadBlob(`ops-inspection-${stamp}.md`, mail.body_md || "", "text/markdown;charset=utf-8");
    if (onExportDone) onExportDone();
  };

  return (
    <div className="drawer-backdrop" role="presentation" onClick={onClose}>
      <aside
        className="drawer-panel"
        role="dialog"
        aria-modal="true"
        aria-label="邮件报告详情"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="drawer-head">
          <div className="drawer-head-title">
            <span className={`badge ${isSuccess ? "badge-ok" : "badge-crit"}`}>{statusLabel}</span>
            <h3>{mail.subject || "服务器每日巡检报告"}</h3>
          </div>
          <button className="toast-close" type="button" aria-label="关闭抽屉" onClick={onClose}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <div className="drawer-body">
          <div className="mail-meta-card">
            <div className="mail-meta-row">
              <span className="mail-meta-label">投递通道</span>
              <span>{isSmtp ? "生产 SMTP 邮件服务器" : "本地模拟收件箱（演练模式，未外发真实邮件）"}</span>
            </div>
            <div className="mail-meta-row">
              <span className="mail-meta-label">发送时间</span>
              <span className="mono">{mail.created_at}</span>
            </div>
            <div className="mail-meta-row">
              <span className="mail-meta-label">收件人</span>
              <div className="mail-recipients">
                {recipients.map((addr) => (
                  <span className="mail-chip" key={addr}>
                    {addr}
                  </span>
                ))}
              </div>
            </div>
            {mail.op_id && (
              <div className="mail-meta-row">
                <span className="mail-meta-label">流水追踪号</span>
                <span className="mono" style={{ color: "var(--ink-500)" }}>
                  {mail.op_id}
                </span>
              </div>
            )}
          </div>

          <ReportView content={mail.body_md} />
        </div>

        <div className="drawer-foot">
          <button className="btn" type="button" onClick={handleDownload}>
            导出本封巡检报告
          </button>
          <button className="btn btn-primary" type="button" onClick={onClose}>
            关闭
          </button>
        </div>
      </aside>
    </div>
  );
}
