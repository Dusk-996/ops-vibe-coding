import React, { useEffect, useState } from "react";
import CustomSelect from "./CustomSelect.jsx";

const SMTP_PRESETS = [
  { id: "qq", label: "QQ 邮箱", host: "smtp.qq.com", port: 465, security: "ssl" },
  { id: "163", label: "网易 163", host: "smtp.163.com", port: 465, security: "ssl" },
  { id: "exmail", label: "企业微信邮箱", host: "smtp.exmail.qq.com", port: 465, security: "ssl" },
  { id: "custom", label: "自定义 SMTP", host: "", port: 587, security: "starttls" },
];

const SECURITY_OPTIONS = [
  { value: "ssl", label: "SSL / TLS 加密（推荐 465 端口）", desc: "适用于 QQ 邮箱、163、企业微信邮箱", dot: "ok" },
  { value: "starttls", label: "STARTTLS 加密（587 端口）", desc: "适用于标准企业邮箱与云邮件服务", dot: "blue" },
  { value: "none", label: "不加密（仅限内网中继）", desc: "仅在可信内网 SMTP 中继服务器使用", dot: "warn" },
];

export default function SmtpConfigModal({ open, smtpConfig, onClose, onSave, onDeleteProfile }) {
  const profiles = smtpConfig?.profiles || [];

  const [editingUser, setEditingUser] = useState("");
  const [host, setHost] = useState("smtp.qq.com");
  const [port, setPort] = useState(465);
  const [security, setSecurity] = useState("ssl");
  const [username, setUsername] = useState("");
  const [authCode, setAuthCode] = useState("");
  const [fromAddr, setFromAddr] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const matchedProfile = profiles.find((p) => p.username === username.trim());
  const hasSavedAuthCode = Boolean(matchedProfile?.has_auth_code);

  const resetForNew = () => {
    setEditingUser("");
    setHost("smtp.qq.com");
    setPort(465);
    setSecurity("ssl");
    setUsername("");
    setFromAddr("");
    setAuthCode("");
    setError("");
  };

  const loadProfileForEdit = (p) => {
    setEditingUser(p.username);
    setHost(p.host);
    setPort(p.port);
    setSecurity(p.security || "ssl");
    setUsername(p.username);
    setFromAddr(p.from_addr || p.username);
    setAuthCode("");
    setError("");
  };

  useEffect(() => {
    if (!open) return;
    resetForNew();
  }, [open]);

  if (!open) return null;

  const applyPreset = (preset) => {
    if (preset.host) setHost(preset.host);
    setPort(preset.port);
    setSecurity(preset.security);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    const cleanHost = host.trim();
    const cleanUser = username.trim();
    if (!cleanHost) return setError("请填写 SMTP 服务器地址（例如 smtp.qq.com）。");
    if (!cleanUser) return setError("请填写发件人邮箱账号。");
    if (!authCode.trim() && !hasSavedAuthCode) {
      return setError("首次保存该发件账号时必须填写 SMTP 授权码（保存后下次直接下拉选用，无需再填）。");
    }

    setSaving(true);
    try {
      await onSave({
        enabled: true,
        host: cleanHost,
        port: Number(port) || 465,
        security,
        username: cleanUser,
        auth_code: authCode.trim(),
        from_addr: fromAddr.trim() || cleanUser,
        timeout_seconds: smtpConfig?.timeout_seconds || 10,
      });
    } catch (err) {
      setError(err.message || "保存失败");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-backdrop" role="presentation" onClick={onClose}>
      <div className="modal-panel modal-panel-wide" role="dialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
        <div className="dlg-head">
          <h3>新增 / 管理发件人邮箱账号</h3>
          <button className="btn btn-ghost btn-sm" type="button" onClick={onClose}>
            关闭
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="dlg-body">
            {profiles.length > 0 && (
              <div className="field">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <label>已加密保存的发件邮箱（{profiles.length} 个）</label>
                  {editingUser && (
                    <button className="btn btn-ghost btn-sm" type="button" onClick={resetForNew}>
                      + 切换为添加新账号
                    </button>
                  )}
                </div>
                <div className="saved-profile-list">
                  {profiles.map((p) => (
                    <div className={`saved-profile-item ${editingUser === p.username ? "is-editing" : ""}`} key={p.id}>
                      <div className="saved-profile-info">
                        <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                          <strong className="mono">{p.username}</strong>
                          {p.is_active && <span className="badge badge-ok">当前启用</span>}
                          <span className="badge badge-muted">授权码已加密</span>
                        </div>
                        <span className="card-sub mono">
                          {p.host}:{p.port} · {String(p.security || "ssl").toUpperCase()}
                        </span>
                      </div>
                      <div style={{ display: "flex", gap: 6 }}>
                        <button className="btn btn-ghost btn-sm" type="button" onClick={() => loadProfileForEdit(p)}>
                          编辑 / 换码
                        </button>
                        <button
                          className="btn btn-danger-text btn-sm"
                          type="button"
                          onClick={() => onDeleteProfile(p)}
                        >
                          删除
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="field">
              <label>{editingUser ? `更新发件账号：${editingUser}` : "新增发件账号（常用邮箱一键填充）"}</label>
              <div className="tp-presets" style={{ borderTop: "none", paddingTop: 0 }}>
                {SMTP_PRESETS.map((p) => (
                  <button
                    key={p.id}
                    type="button"
                    className={`tp-preset ${p.host && host === p.host ? "active" : ""}`}
                    onClick={() => applyPreset(p)}
                  >
                    {p.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="form-two">
              <div className="field">
                <label htmlFor="smtp-host">SMTP 服务器地址</label>
                <input
                  id="smtp-host"
                  className="input mono"
                  value={host}
                  onChange={(e) => setHost(e.target.value)}
                  placeholder="smtp.qq.com"
                />
              </div>
              <div className="field">
                <label htmlFor="smtp-port">端口</label>
                <input
                  id="smtp-port"
                  className="input mono"
                  type="number"
                  min={1}
                  max={65535}
                  value={port}
                  onChange={(e) => setPort(e.target.value)}
                />
              </div>
            </div>

            <div className="field">
              <label htmlFor="smtp-sec">加密协议</label>
              <CustomSelect
                id="smtp-sec"
                fullWidth
                value={security}
                onChange={setSecurity}
                options={SECURITY_OPTIONS}
              />
            </div>

            <div className="form-two">
              <div className="field">
                <label htmlFor="smtp-user">发件人邮箱账号</label>
                <input
                  id="smtp-user"
                  className="input mono"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="your_name@qq.com"
                />
              </div>
              <div className="field">
                <label htmlFor="smtp-from">发件人显示地址（选填）</label>
                <input
                  id="smtp-from"
                  className="input mono"
                  value={fromAddr}
                  onChange={(e) => setFromAddr(e.target.value)}
                  placeholder="留空默认与发件账号一致"
                />
              </div>
            </div>

            <div className="field">
              <label htmlFor="smtp-auth-code">
                SMTP 授权码 / 专用密码
                {hasSavedAuthCode && (
                  <span className="badge badge-ok" style={{ marginLeft: 8 }}>
                    该账号已加密存档
                  </span>
                )}
              </label>
              <input
                id="smtp-auth-code"
                className="input mono"
                type="password"
                autoComplete="new-password"
                value={authCode}
                onChange={(e) => setAuthCode(e.target.value)}
                placeholder={
                  hasSavedAuthCode
                    ? "已加密存库，留空保存将继续使用原授权码"
                    : "首次添加请输入 16 位 SMTP 授权码（下次直接下拉选用）"
                }
              />
              <span className="help">
                安全保护：保存一次后自动加密存档，后续直接在页面下拉框选择发件人账号即可切换，全程不再暴露授权码。
              </span>
            </div>

            <div className="err-msg">{error}</div>
          </div>

          <div className="dlg-foot">
            <button className="btn" type="button" onClick={onClose}>
              取消
            </button>
            <button className="btn btn-primary" type="submit" disabled={saving}>
              {saving ? "保存中..." : "保存存档并设为当前发件箱"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
