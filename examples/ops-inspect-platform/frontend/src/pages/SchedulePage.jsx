import React, { useEffect, useState } from "react";
import AuditDrawer from "../components/AuditDrawer.jsx";
import CustomSelect from "../components/CustomSelect.jsx";
import MailDrawer from "../components/MailDrawer.jsx";
import TimePicker from "../components/TimePicker.jsx";

const ACTION_LABELS = {
  SCHEDULED_INSPECT_AND_PUSH: "定时巡检与推送",
  CREATE_TARGET: "登记目标主机",
  UPDATE_TARGET: "更新目标主机",
  DELETE_TARGET: "移除目标主机",
  IMPORT_PREVIEW: "导入文件校验",
  IMPORT_TARGETS: "批量导入主机",
  INSPECT_ALL: "全量巡检采集",
  INSPECT_ONE: "单台指标检测",
  UPDATE_SCHEDULE: "调整定时规则",
  UPDATE_SMTP: "保存发件邮箱账号",
  ACTIVATE_SMTP_PROFILE: "切换发件邮箱账号",
  DELETE_SMTP_PROFILE: "删除发件邮箱存档",
  AUTH_LOGIN: "用户登录认证",
  PUSH_REPORT_NOW: "手动推送报告",
};

const PUSH_SIM_OPTIONS = [
  { value: "ok", label: "正常送达", desc: "写入下方本地模拟收件箱", dot: "ok" },
  { value: "conflict", label: "模拟并发拦截（409）", desc: "演练重复提交防重锁保护", dot: "warn" },
  { value: "timeout", label: "模拟发信超时（504）", desc: "演练超时不自动重试安全红线", dot: "crit" },
];

function auditStatusBadge(code) {
  if (code >= 200 && code < 300) return { cls: "ok", text: "成功" };
  if (code === 409) return { cls: "warn", text: "防重拦截" };
  if (code === 401) return { cls: "crit", text: "未登录拦截" };
  if (code === 403) return { cls: "crit", text: "越权拦截" };
  if (code === 504) return { cls: "crit", text: "响应超时" };
  return { cls: "crit", text: `异常 (${code})` };
}

function summarizeMailBody(bodyMd) {
  const text = String(bodyMd || "");
  const newMatch = text.match(/纳管服务器总数：(\d+)\s*台（正常\s*(\d+)\s*台\s*｜\s*异常\/需关注\s*(\d+)\s*台）/);
  if (newMatch) {
    const total = Number(newMatch[1]);
    const ok = Number(newMatch[2]);
    const abnormal = Number(newMatch[3]);
    if (abnormal === 0) return { text: `全部 ${total} 台正常`, hasIssue: false };
    return { text: `共 ${total} 台 · 正常 ${ok} · 异常 ${abnormal}`, hasIssue: true };
  }

  const oldMatch = text.match(/纳管目标总数：(\d+)\s*台（已采集\s*(\d+)\s*台\s*\/\s*采集失败\s*(\d+)\s*台）/);
  const highMatch = text.match(/高负载告警：(\d+)\s*台/);
  if (!oldMatch) return { text: "巡检报告快照", hasIssue: false };
  const total = Number(oldMatch[1]);
  const probed = Number(oldMatch[2]);
  const failed = Number(oldMatch[3]);
  const high = highMatch ? Number(highMatch[1]) : 0;

  if (failed === 0 && high === 0) {
    return { text: `全部 ${total} 台正常`, hasIssue: false };
  }
  const parts = [`已采 ${probed}/${total} 台`];
  if (high > 0) parts.push(`高负载 ${high}`);
  if (failed > 0) parts.push(`异常 ${failed}`);
  return { text: parts.join(" · "), hasIssue: true };
}

export default function SchedulePage({
  schedule,
  smtpConfig,
  outbox,
  audits,
  previewMode,
  onSaveSchedule,
  onSelectSmtpProfile,
  onOpenSmtpConfig,
  onRequestPush,
  onDownloadMarkdown,
  onToast,
}) {
  const [enabled, setEnabled] = useState(true);
  const [pushTime, setPushTime] = useState("09:00");
  const [emailsInput, setEmailsInput] = useState("");
  const [simMode, setSimMode] = useState("ok");
  const [activeTab, setActiveTab] = useState("outbox");
  const [saving, setSaving] = useState(false);
  const [selectedMail, setSelectedMail] = useState(null);
  const [selectedAudit, setSelectedAudit] = useState(null);

  useEffect(() => {
    setEnabled(Boolean(schedule.enabled));
    setPushTime(schedule.push_time || "09:00");
    setEmailsInput((schedule.recipients || []).join(", "));
  }, [schedule]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const recipients = emailsInput
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    const bad = recipients.find((m) => !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(m));
    if (!recipients.length || bad) {
      onToast({
        type: "err",
        title: "收件邮箱格式有误",
        msg: bad ? `「${bad}」不是有效的邮箱地址，请检查后再保存。` : "请至少填写一个收件邮箱地址。",
      });
      return;
    }
    setSaving(true);
    try {
      await onSaveSchedule({ enabled, push_time: pushTime, recipients });
    } finally {
      setSaving(false);
    }
  };

  const savedProfiles = smtpConfig?.profiles || [];
  const activeProfileId = smtpConfig?.active_profile_id ? String(smtpConfig.active_profile_id) : "0";
  const senderOptions = [
    ...savedProfiles.map((p) => ({
      value: String(p.id),
      label: p.username,
      desc: `${p.host}:${p.port} · ${String(p.security || "ssl").toUpperCase()} · 授权码已加密存档`,
      dot: "ok",
    })),
    ...(smtpConfig?.source === "env" && savedProfiles.length === 0
      ? [
          {
            value: "env",
            label: smtpConfig.username || smtpConfig.host,
            desc: `${smtpConfig.host}:${smtpConfig.port} · 环境变量注入`,
            dot: "blue",
          },
        ]
      : []),
    {
      value: "0",
      label: "本地模拟收件箱",
      desc: "不发送外部真实邮件，报告仅写入下方记录",
      dot: "muted",
    },
  ];
  const selectedSenderValue =
    smtpConfig?.source === "env" && savedProfiles.length === 0 && smtpConfig?.mode === "smtp"
      ? "env"
      : activeProfileId;

  return (
    <main className="page">
      <div className="page-head">
        <div>
          <h1>每日定时推送与邮箱配置</h1>
        </div>
        <span className={`badge ${schedule.enabled ? "badge-ok" : "badge-muted"}`}>
          {schedule.enabled ? `每日 ${schedule.push_time} 已启用` : `已停用（原计划 ${schedule.push_time}）`}
        </span>
      </div>

      <div className="sched-top-grid">
        <section className="card card-overflow-visible">
          <div className="card-head">
            <h2>定时任务规则</h2>
            <span className="card-sub">持久化保存 · 服务重启自动重载 · 同分钟幂等防重发</span>
          </div>
          <form className="form-stack" onSubmit={handleSubmit}>
            <div className="field">
              <label className="check-inline">
                <input type="checkbox" checked={enabled} onChange={(e) => setEnabled(e.target.checked)} />
                <strong>启用每日自动巡检并推送邮件</strong>
              </label>
            </div>

            <div className="field">
              <label>每日推送时间节点</label>
              <TimePicker value={pushTime} onChange={setPushTime} />
            </div>

            <div className="field">
              <label>发件人邮箱账号（已保存直接选，免重输授权码）</label>
              <div className="smtp-selector-row">
                <div style={{ flex: 1, minWidth: 220 }}>
                  <CustomSelect
                    fullWidth
                    value={selectedSenderValue}
                    onChange={(val) => {
                      if (val === "env") return;
                      onSelectSmtpProfile(Number(val));
                    }}
                    options={senderOptions}
                  />
                </div>
                <button className="btn" type="button" onClick={onOpenSmtpConfig}>
                  + 添加 / 管理发件箱
                </button>
              </div>
              <span className="help">
                首次配置发件邮箱后自动加密存档；日常只需在此下拉框点选发件人账号即可秒切生效，全程不再接触授权码。
              </span>
            </div>

            <div className="field">
              <label htmlFor="sched-emails">指定收件人邮箱列表</label>
              <input
                id="sched-emails"
                className="input mono"
                type="text"
                value={emailsInput}
                onChange={(e) => setEmailsInput(e.target.value)}
                required
              />
              <span className="help">支持多个收件邮箱，英文逗号分隔</span>
            </div>

            <div className="form-actions">
              <span className="card-sub">
                当前生效：{schedule.enabled ? `每日 ${schedule.push_time}` : "已停用"} →{" "}
                {(schedule.recipients || []).length} 个收件人
              </span>
              <button className="btn btn-primary" type="submit" disabled={saving}>
                {saving ? "保存中..." : "保存定时配置"}
              </button>
            </div>
          </form>
        </section>

        <section className="card card-overflow-visible">
          <div className="card-head">
            <h2>手动立即推送（测试与演练）</h2>
            <span className="card-sub">含并发防重与超时不重试保护</span>
          </div>
          <div className="push-panel">
            <div className="info-box">
              <strong>安全红线：</strong>推送前强制确认收件人与本次巡检摘要；并发重复点击自动拦截（409）；SMTP 超时记录审计并<strong>绝不自动重试</strong>（504）。
            </div>

            {previewMode && (
              <div className="field">
                <label htmlFor="smtp-sim">发信演练场景</label>
                <CustomSelect
                  id="smtp-sim"
                  fullWidth
                  value={simMode}
                  onChange={setSimMode}
                  options={PUSH_SIM_OPTIONS}
                />
              </div>
            )}

            <button
              className="btn btn-primary"
              type="button"
              style={{ width: "100%" }}
              onClick={() => onRequestPush(simMode)}
            >
              立即推送最新巡检报告
            </button>
          </div>
        </section>
      </div>

      <section className="card">
        <div className="card-head" style={{ paddingBottom: 0, borderBottom: "none" }}>
          <div className="tabs" role="tablist">
            <button
              className={`tab ${activeTab === "outbox" ? "active" : ""}`}
              type="button"
              onClick={() => setActiveTab("outbox")}
            >
              发送记录 / 模拟收件箱 ({outbox.length})
            </button>
            <button
              className={`tab ${activeTab === "audit" ? "active" : ""}`}
              type="button"
              onClick={() => setActiveTab("audit")}
            >
              全量操作审计 ({audits.length})
            </button>
          </div>
          <div className="head-actions" style={{ paddingBottom: 8 }}>
            <button className="btn btn-sm" type="button" onClick={onDownloadMarkdown}>
              导出最新巡检报告
            </button>
          </div>
        </div>

        <div style={{ borderTop: "1px solid var(--line)" }}>
          {activeTab === "outbox" ? (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>发送时间</th>
                    <th>投递状态</th>
                    <th>邮件主题</th>
                    <th>收件人</th>
                    <th>巡检概览</th>
                    <th style={{ textAlign: "right" }}>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {outbox.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="empty-state">
                        暂无邮件发送记录，点击上方「立即推送最新巡检报告」即可演练。
                      </td>
                    </tr>
                  ) : (
                    outbox.map((m) => {
                      const key = m.id || m.op_id;
                      const isSuccess = m.status_code === 200;
                      const modeLabel =
                        m.delivery_mode === "smtp"
                          ? isSuccess
                            ? "SMTP 已发送"
                            : `发送失败 (${m.status_code})`
                          : isSuccess
                            ? "模拟送达"
                            : `模拟异常 (${m.status_code})`;
                      const recipientList = String(m.recipients || "")
                        .split(",")
                        .map((r) => r.trim())
                        .filter(Boolean);
                      const summary = summarizeMailBody(m.body_md);

                      return (
                        <tr className="row-clickable" key={key} onClick={() => setSelectedMail(m)}>
                          <td className="mono" style={{ fontSize: 13, color: "var(--ink-500)" }}>
                            {m.created_at}
                          </td>
                          <td>
                            <span className={`badge ${isSuccess ? "badge-ok" : "badge-crit"}`}>{modeLabel}</span>
                          </td>
                          <td style={{ fontWeight: 600, color: "var(--ink-900)" }}>
                            {m.subject || "服务器每日巡检报告"}
                          </td>
                          <td>
                            <div className="mail-recipients">
                              {recipientList.slice(0, 2).map((addr) => (
                                <span className="mail-chip" key={addr}>
                                  {addr}
                                </span>
                              ))}
                              {recipientList.length > 2 && (
                                <span className="card-sub">+{recipientList.length - 2}</span>
                              )}
                            </div>
                          </td>
                          <td>
                            <span className={`badge ${summary.hasIssue ? "badge-warn" : "badge-ok"}`}>
                              {summary.text}
                            </span>
                          </td>
                          <td style={{ textAlign: "right" }}>
                            <button
                              className="btn btn-ghost btn-sm"
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedMail(m);
                              }}
                            >
                              查看邮件
                            </button>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>发生时间</th>
                    <th>执行状态</th>
                    <th>操作类型</th>
                    <th>操作人</th>
                    <th>事件摘要</th>
                    <th style={{ textAlign: "right" }}>操作</th>
                  </tr>
                </thead>
                <tbody>
                  {audits.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="empty-state">
                        暂无审计记录
                      </td>
                    </tr>
                  ) : (
                    audits.map((a) => {
                      const st = auditStatusBadge(a.http_status);
                      return (
                        <tr
                          className="row-clickable"
                          key={a.id || `${a.op_id}-${a.created_at}`}
                          onClick={() => setSelectedAudit(a)}
                        >
                          <td className="mono" style={{ fontSize: 13, color: "var(--ink-500)" }}>
                            {a.created_at}
                          </td>
                          <td>
                            <span className={`badge badge-${st.cls}`}>{st.text}</span>
                          </td>
                          <td style={{ fontWeight: 600, color: "var(--ink-900)" }}>
                            {ACTION_LABELS[a.action] || a.action}
                          </td>
                          <td>
                            <span className="mail-chip">{a.actor}</span>
                          </td>
                          <td
                            style={{
                              maxWidth: 360,
                              overflow: "hidden",
                              textOverflow: "ellipsis",
                              color: "var(--ink-700)",
                            }}
                            title={a.detail}
                          >
                            {a.detail}
                          </td>
                          <td style={{ textAlign: "right" }}>
                            <button
                              className="btn btn-ghost btn-sm"
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedAudit(a);
                              }}
                            >
                              查看详情
                            </button>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </section>

      <MailDrawer
        mail={selectedMail}
        onClose={() => setSelectedMail(null)}
        onExportDone={() =>
          onToast({
            type: "ok",
            title: "报告已导出",
            msg: "已将该封历史巡检报告保存至本地下载目录。",
          })
        }
      />

      <AuditDrawer
        audit={selectedAudit}
        onClose={() => setSelectedAudit(null)}
        onCopyOpId={(opId) =>
          onToast({
            type: "ok",
            title: "追踪号已复制",
            msg: `已复制流水追踪号 ${opId}，可用于关联排查后端日志。`,
          })
        }
      />
    </main>
  );
}
