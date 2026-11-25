import React, { useState } from "react";

export default function LoginModal({ open, onClose, onLogin }) {
  const [username, setUsername] = useState("admin");
  const [secretInput, setSecretInput] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (!open) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await onLogin(username.trim(), secretInput);
      setSecretInput("");
      onClose();
    } catch (err) {
      setError(err.message || "登录失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-backdrop" role="presentation" onClick={onClose}>
      <div className="modal-panel" style={{ maxWidth: 420 }} role="dialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
        <div className="dlg-head">
          <h3>登录巡检平台</h3>
          <button className="btn btn-ghost btn-sm" type="button" onClick={onClose}>
            关闭
          </button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="dlg-body">
            <div className="field">
              <label htmlFor="login-user">账号</label>
              <input
                id="login-user"
                className="input mono"
                placeholder="请输入账号"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </div>
            <div className="field">
              <label htmlFor="login-secret">密码</label>
              <input
                id="login-secret"
                className="input mono"
                type="password"
                placeholder="请输入密码"
                value={secretInput}
                onChange={(e) => setSecretInput(e.target.value)}
                required
              />
            </div>
            <div className="err-msg">{error}</div>
          </div>
          <div className="dlg-foot">
            <button className="btn" type="button" onClick={onClose}>
              取消
            </button>
            <button className="btn btn-primary" type="submit" disabled={loading}>
              {loading ? "登录中..." : "登录"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
