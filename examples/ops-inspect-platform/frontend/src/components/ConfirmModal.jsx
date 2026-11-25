import React from "react";
import ReportView from "./ReportView.jsx";

export default function ConfirmModal({
  open,
  title,
  description,
  detail,
  isReportPreview = false,
  confirmText,
  onCancel,
  onConfirm,
}) {
  if (!open) return null;

  return (
    <div className="modal-backdrop" role="presentation" onClick={onCancel}>
      <div
        className={`modal-panel ${isReportPreview ? "modal-panel-wide" : ""}`}
        role="dialog"
        aria-modal="true"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="dlg-head">
          <h3>{title || "确认操作"}</h3>
          <button className="btn btn-ghost btn-sm" type="button" onClick={onCancel}>
            关闭
          </button>
        </div>
        <div className="dlg-body">
          <p style={{ fontSize: 14.5, color: "var(--ink-700)" }}>{description}</p>
          {detail && (isReportPreview ? <ReportView content={detail} compact /> : <pre className="md-box">{detail}</pre>)}
        </div>
        <div className="dlg-foot">
          <button className="btn" type="button" onClick={onCancel}>
            取消（不发出请求）
          </button>
          <button className="btn btn-primary" type="button" onClick={onConfirm}>
            {confirmText || "确认执行"}
          </button>
        </div>
      </div>
    </div>
  );
}
