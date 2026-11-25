import React, { useEffect, useState } from "react";
import { COLLECTOR_OPTIONS, SERVER_TYPES, SERVER_VENDORS } from "../utils/format.js";
import CustomSelect from "./CustomSelect.jsx";

export default function ServerModal({ open, initialItem, onClose, onSave }) {
  const [host, setHost] = useState("");
  const [address, setAddress] = useState("");
  const [type, setType] = useState("物理机");
  const [vendor, setVendor] = useState("戴尔 Dell");
  const [collectorType, setCollectorType] = useState("ssh");
  const [sshPort, setSshPort] = useState(22);
  const [sshUser, setSshUser] = useState("ops-ro");
  const [sshCredentialRef, setSshCredentialRef] = useState("prod-ro-key");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!open) return;
    setError("");
    setHost(initialItem?.host || "");
    setAddress(initialItem?.address || "");
    setType(initialItem?.type || "物理机");
    setVendor(initialItem?.vendor || "戴尔 Dell");
    setCollectorType(initialItem?.collector_type || "ssh");
    setSshPort(initialItem?.ssh_port ?? 22);
    setSshUser(initialItem?.ssh_user || "ops-ro");
    setSshCredentialRef(initialItem?.ssh_credential_ref || "prod-ro-key");
  }, [open, initialItem]);

  if (!open) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    const cleanHost = host.trim();
    const cleanAddr = address.trim();
    if (!cleanHost || !cleanAddr) {
      setError("主机名与服务器 IP/地址不能为空");
      return;
    }
    const payload = {
      host: cleanHost,
      address: cleanAddr,
      type,
      vendor,
      collector_type: collectorType,
      ssh_port: collectorType === "ssh" ? Number(sshPort) : null,
      ssh_user: collectorType === "ssh" ? sshUser.trim() : "",
      ssh_credential_ref: collectorType === "ssh" ? sshCredentialRef.trim() : "",
    };
    setSubmitting(true);
    try {
      await onSave(payload, initialItem?.id ?? null);
    } catch (err) {
      setError(err.message || "保存失败");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-backdrop" role="presentation" onClick={onClose}>
      <div className="modal-panel" role="dialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
        <div className="dlg-head">
          <h3>{initialItem ? `编辑目标：${initialItem.host}` : "登记目标服务器"}</h3>
          <button className="btn btn-ghost btn-sm" type="button" onClick={onClose}>
            关闭
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="dlg-body">
            <div className="form-two">
              <div className="field">
                <label htmlFor="f-host">主机名（唯一）</label>
                <input
                  id="f-host"
                  className="input mono"
                  value={host}
                  onChange={(e) => setHost(e.target.value)}
                  placeholder="prod-k8s-node-05"
                  required
                />
              </div>
              <div className="field">
                <label htmlFor="f-address">服务器 IP / 地址</label>
                <input
                  id="f-address"
                  className="input mono"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  placeholder="10.10.2.15"
                  required
                />
              </div>
            </div>

            <div className="form-two">
              <div className="field">
                <label htmlFor="f-type">服务器类型</label>
                <CustomSelect
                  id="f-type"
                  fullWidth
                  value={type}
                  onChange={setType}
                  options={SERVER_TYPES.map((t) => ({ value: t, label: t }))}
                />
              </div>
              <div className="field">
                <label htmlFor="f-vendor">厂商</label>
                <CustomSelect
                  id="f-vendor"
                  fullWidth
                  value={vendor}
                  onChange={setVendor}
                  options={SERVER_VENDORS.map((v) => ({ value: v, label: v }))}
                />
              </div>
            </div>

            <div className="field">
              <label htmlFor="f-collector">采集方式</label>
              <CustomSelect
                id="f-collector"
                fullWidth
                value={collectorType}
                onChange={setCollectorType}
                options={COLLECTOR_OPTIONS}
              />
              <span className="help">内存与 CPU 指标将在登记后由采集引擎主动检测，此处无需手填。</span>
            </div>

            {collectorType === "ssh" && (
              <div className="ssh-panel">
                <div className="form-two">
                  <div className="field">
                    <label htmlFor="f-ssh-port">SSH 端口</label>
                    <input
                      id="f-ssh-port"
                      className="input mono"
                      type="number"
                      min={1}
                      max={65535}
                      value={sshPort}
                      onChange={(e) => setSshPort(e.target.value)}
                    />
                  </div>
                  <div className="field">
                    <label htmlFor="f-ssh-user">SSH 只读账号</label>
                    <input
                      id="f-ssh-user"
                      className="input mono"
                      value={sshUser}
                      onChange={(e) => setSshUser(e.target.value)}
                      placeholder="ops-ro"
                    />
                  </div>
                </div>
                <div className="field">
                  <label htmlFor="f-ssh-cred">SSH 凭据引用别名（绝不填明文密码或私钥）</label>
                  <input
                    id="f-ssh-cred"
                    className="input mono"
                    value={sshCredentialRef}
                    onChange={(e) => setSshCredentialRef(e.target.value)}
                    placeholder="prod-ro-key"
                  />
                  <span className="help">后端按别名从只读密钥目录或环境变量映射私钥文件。</span>
                </div>
              </div>
            )}

            <div className="err-msg">{error}</div>
          </div>

          <div className="dlg-foot">
            <button className="btn" type="button" onClick={onClose}>
              取消
            </button>
            <button className="btn btn-primary" type="submit" disabled={submitting}>
              {submitting ? "保存中..." : "保存目标"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
