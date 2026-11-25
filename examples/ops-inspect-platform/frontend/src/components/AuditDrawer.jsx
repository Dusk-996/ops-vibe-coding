import React, { useEffect } from "react";

const ACTION_LABELS = {
  SCHEDULED_INSPECT_AND_PUSH: "定时巡检与报告推送",
  CREATE_TARGET: "登记目标服务器",
  UPDATE_TARGET: "修改目标服务器",
  DELETE_TARGET: "移除目标服务器",
  IMPORT_PREVIEW: "导入文件校验",
  IMPORT_TARGETS: "批量导入目标服务器",
  INSPECT_ALL: "全量巡检采集",
  INSPECT_ONE: "单台主机指标检测",
  UPDATE_SCHEDULE: "调整定时推送规则",
  UPDATE_SMTP: "保存发件邮箱账号",
  ACTIVATE_SMTP_PROFILE: "切换发件邮箱账号",
  DELETE_SMTP_PROFILE: "删除发件邮箱存档",
  AUTH_LOGIN: "用户登录认证",
  PUSH_REPORT_NOW: "手动推送巡检报告",
};

const ROLE_LABELS = {
  admin: "管理员（admin）",
  viewer: "只读成员（viewer）",
  anon: "未登录访客",
  system: "系统调度器",
};

function resultMeta(code) {
  if (code >= 200 && code < 300) {
    return { cls: "ok", label: "执行成功", desc: "请求已正常完成并持久化落库。" };
  }
  if (code === 401) {
    return { cls: "crit", label: "未认证拦截", desc: "未携带有效登录凭证，写操作已被安全门禁拦截。" };
  }
  if (code === 403) {
    return { cls: "crit", label: "权限不足拦截", desc: "当前角色仅具备只读权限，越权操作已阻断并留痕。" };
  }
  if (code === 409) {
    return { cls: "warn", label: "并发防重拦截", desc: "同类任务正在执行或存在资源冲突，本次重复请求已拦截。" };
  }
  if (code === 504) {
    return { cls: "crit", label: "上游响应超时", desc: "目标主机或邮件服务超时未返回，系统已按红线禁止自动重试。" };
  }
  return { cls: "crit", label: `异常退出 (${code})`, desc: "操作未成功完成，请结合事件摘要排查。" };
}

export default function AuditDrawer({ audit, onClose, onCopyOpId }) {
  useEffect(() => {
    if (!audit) return undefined;
    const onKeyDown = (e) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [audit, onClose]);

  if (!audit) return null;

  const res = resultMeta(audit.http_status);
  const actionTitle = ACTION_LABELS[audit.action] || audit.action;
  const roleLabel = ROLE_LABELS[audit.role] || audit.role || "-";

  const handleCopy = async () => {
    if (!audit.op_id) return;
    try {
      await navigator.clipboard.writeText(audit.op_id);
      if (onCopyOpId) onCopyOpId(audit.op_id);
    } catch {
      if (onCopyOpId) onCopyOpId(audit.op_id);
    }
  };

  return (
    <div className="drawer-backdrop" role="presentation" onClick={onClose}>
      <aside
        className="drawer-panel drawer-panel-sm"
        role="dialog"
        aria-modal="true"
        aria-label="审计事件详情"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="drawer-head">
          <div className="drawer-head-title">
            <span className={`badge badge-${res.cls}`}>{res.label}</span>
            <h3>{actionTitle}</h3>
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
              <span className="mail-meta-label">发生时间</span>
              <span className="mono">{audit.created_at}</span>
            </div>
            <div className="mail-meta-row">
              <span className="mail-meta-label">操作人</span>
              <span className="mono" style={{ fontWeight: 600, color: "var(--ink-900)" }}>
                {audit.actor}
              </span>
              <span className="mail-chip">{roleLabel}</span>
            </div>
            <div className="mail-meta-row">
              <span className="mail-meta-label">执行结果</span>
              <span className={`badge badge-${res.cls}`}>{res.label}</span>
              <span className="mono" style={{ color: "var(--ink-500)", fontSize: 12.5 }}>
                状态码 {audit.http_status}
              </span>
            </div>
            <div className="mail-meta-row">
              <span className="mail-meta-label">事件代码</span>
              <span className="mail-chip">{audit.action}</span>
            </div>
            {audit.op_id && (
              <div className="mail-meta-row">
                <span className="mail-meta-label">流水追踪号</span>
                <span className="mono" style={{ color: "var(--ink-700)" }}>
                  {audit.op_id}
                </span>
              </div>
            )}
          </div>

          <div className="audit-detail-section">
            <div className="rv-heading">事件摘要</div>
            <div className="audit-detail-box">{audit.detail}</div>
          </div>

          <div className="audit-detail-section">
            <div className="rv-heading">状态释义</div>
            <div className="audit-detail-box" style={{ color: "var(--ink-500)" }}>
              {res.desc}
            </div>
          </div>
        </div>

        <div className="drawer-foot">
          {audit.op_id && (
            <button className="btn" type="button" onClick={handleCopy}>
              复制追踪号
            </button>
          )}
          <button className="btn btn-primary" type="button" onClick={onClose}>
            关闭
          </button>
        </div>
      </aside>
    </div>
  );
}
