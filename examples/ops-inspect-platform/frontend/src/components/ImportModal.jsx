import React, { useEffect, useState } from "react";
import { buildImportTemplateCsv, downloadBlob } from "../utils/format.js";
import CustomSelect from "./CustomSelect.jsx";

const IMPORT_POLICY_OPTIONS = [
  { value: "skip", label: "跳过已存在主机名", desc: "保留现有记录，仅导入新主机（推荐）" },
  { value: "overwrite", label: "覆盖更新连接信息", desc: "按导入文件更新 IP、端口与采集配置" },
];

export default function ImportModal({ open, onClose, onPreview, onCommit, onToast }) {
  const [policy, setPolicy] = useState("skip");
  const [filePayload, setFilePayload] = useState(null);
  const [previewResult, setPreviewResult] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!open) return;
    setPolicy("skip");
    setFilePayload(null);
    setPreviewResult(null);
    setError("");
  }, [open]);

  if (!open) return null;

  const handleDownloadTemplate = () => {
    downloadBlob("servers-ip-import-template.csv", buildImportTemplateCsv(), "text/csv;charset=utf-8");
    onToast({
      type: "ok",
      title: "导入模板已下载",
      msg: "标准 IP 导入 CSV 模板已保存到本地，填好主机列表后可直接在此上传预览。",
    });
  };

  const handleFileChange = async (e) => {
    const file = e.target.files?.[0];
    setError("");
    setPreviewResult(null);
    setFilePayload(null);
    if (!file) return;

    try {
      const text = await file.text();
      const format = file.name.toLowerCase().endsWith(".json") ? "json" : "csv";
      setBusy(true);
      const res = await onPreview({ format, content: text });
      setFilePayload({ format, content: text });
      setPreviewResult(res);
      if (res.errors?.length) {
        setError(`校验发现 ${res.errors.length} 处错误（${res.errors.slice(0, 2).join("；")}）`);
      }
    } catch (err) {
      setError(`解析失败：${err.message}`);
    } finally {
      setBusy(false);
    }
  };

  const handleCommit = async () => {
    if (!filePayload) return;
    setBusy(true);
    try {
      await onCommit({ ...filePayload, policy });
    } catch (err) {
      setError(err.message || "提交导入失败");
    } finally {
      setBusy(false);
    }
  };

  const validRows = previewResult?.valid_rows || [];

  return (
    <div className="modal-backdrop" role="presentation" onClick={onClose}>
      <div className="modal-panel" role="dialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
        <div className="dlg-head">
          <h3>批量导入目标服务器（含 IP 与采集方式）</h3>
          <button className="btn btn-ghost btn-sm" type="button" onClick={onClose}>
            关闭
          </button>
        </div>

        <div className="dlg-body">
          <div className="drop-zone">
            <div style={{ fontSize: 14, color: "var(--ink-700)" }}>
              上传 <strong>.csv</strong> 或 <strong>.json</strong>（字段：
              <code>host, address, type, vendor, collectorType, sshPort, sshUser, sshCredentialRef</code>）
            </div>
            <input type="file" accept=".csv,.json,text/csv,application/json" onChange={handleFileChange} />
            <button className="btn btn-sm" type="button" onClick={handleDownloadTemplate}>
              下载标准 IP 导入 CSV 模板
            </button>
          </div>

          <div className="field">
            <label htmlFor="import-policy">主机名重复处理策略</label>
            <CustomSelect
              id="import-policy"
              fullWidth
              value={policy}
              onChange={setPolicy}
              options={IMPORT_POLICY_OPTIONS}
            />
          </div>

          {previewResult && validRows.length > 0 && (
            <>
              <div style={{ fontSize: 14, color: "var(--ink-700)" }}>
                预检通过 <strong>{validRows.length}</strong> 台目标（重名{" "}
                <strong>{previewResult.duplicate_count}</strong> 台），导入后状态为
                <strong>待检测</strong>，可点“立即全量巡检”采集指标。
              </div>
              <div className="preview-box">
                <table>
                  <thead>
                    <tr>
                      <th>主机名</th>
                      <th>IP / 地址</th>
                      <th>种类 / 厂商</th>
                      <th>采集</th>
                      <th>SSH 参数</th>
                    </tr>
                  </thead>
                  <tbody>
                    {validRows.slice(0, 8).map((r) => (
                      <tr key={r.host}>
                        <td className="mono">{r.host}</td>
                        <td className="mono">{r.address}</td>
                        <td>
                          {r.type} / {r.vendor}
                        </td>
                        <td className="mono">{r.collector_type}</td>
                        <td className="mono">
                          {r.collector_type === "ssh"
                            ? `${r.ssh_user}@:${r.ssh_port} [${r.ssh_credential_ref || "-"}]`
                            : "-"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}

          <div className="err-msg">{error}</div>
        </div>

        <div className="dlg-foot">
          <button className="btn" type="button" onClick={onClose}>
            取消
          </button>
          <button
            className="btn btn-primary"
            type="button"
            disabled={busy || validRows.length === 0}
            onClick={handleCommit}
          >
            {busy ? "处理中..." : "确认导入（初始状态：待检测）"}
          </button>
        </div>
      </div>
    </div>
  );
}
