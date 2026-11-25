import React, { useEffect, useMemo, useRef, useState } from "react";
import CustomSelect from "../components/CustomSelect.jsx";
import {
  SERVER_TYPES,
  SERVER_VENDORS,
  buildExportCsv,
  collectorMeta,
  computeKpi,
  downloadBlob,
  isAlertRow,
  statusMeta,
} from "../utils/format.js";

const COLLECTOR_FILTER_OPTIONS = [
  { value: "", label: "全部采集方式" },
  { value: "ssh", label: "SSH 远程采集", dot: "ok" },
  { value: "local", label: "本机采集", dot: "blue" },
  { value: "mock", label: "模拟探针", dot: "muted" },
];

export default function ServersPage({
  targets,
  inspectingAll,
  probingId,
  onOpenAdd,
  onOpenEdit,
  onOpenImport,
  onDeleteRequest,
  onInspectAll,
  onInspectOne,
  onToast,
}) {
  const [query, setQuery] = useState("");
  const [filterType, setFilterType] = useState("");
  const [filterVendor, setFilterVendor] = useState("");
  const [filterCollector, setFilterCollector] = useState("");
  const [alertOnly, setAlertOnly] = useState(false);
  const [exportMenuOpen, setExportMenuOpen] = useState(false);
  const exportWrapRef = useRef(null);

  useEffect(() => {
    if (!exportMenuOpen) return undefined;
    const onDocDown = (e) => {
      if (exportWrapRef.current && !exportWrapRef.current.contains(e.target)) {
        setExportMenuOpen(false);
      }
    };
    const onKey = (e) => {
      if (e.key === "Escape") setExportMenuOpen(false);
    };
    document.addEventListener("mousedown", onDocDown);
    window.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDocDown);
      window.removeEventListener("keydown", onKey);
    };
  }, [exportMenuOpen]);

  const vendorOptions = useMemo(() => {
    const set = new Set(SERVER_VENDORS);
    targets.forEach((t) => {
      if (t.vendor) set.add(t.vendor);
    });
    return Array.from(set);
  }, [targets]);

  const kpi = useMemo(() => computeKpi(targets), [targets]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return targets.filter((s) => {
      if (q && !s.host.toLowerCase().includes(q) && !s.address.toLowerCase().includes(q)) return false;
      if (filterType && s.type !== filterType) return false;
      if (filterVendor && s.vendor !== filterVendor) return false;
      if (filterCollector && s.collector_type !== filterCollector) return false;
      if (alertOnly && !isAlertRow(s)) return false;
      return true;
    });
  }, [targets, query, filterType, filterVendor, filterCollector, alertOnly]);

  const handleExportCsv = () => {
    setExportMenuOpen(false);
    const today = new Date().toISOString().slice(0, 10);
    downloadBlob(`ops-inspect-export-${today}.csv`, buildExportCsv(filtered), "text/csv;charset=utf-8");
    onToast({
      type: "ok",
      title: "表格数据已导出",
      msg: `已导出当前列表中的 ${filtered.length} 台服务器配置与最新巡检指标（CSV）。`,
    });
  };

  const handleExportJson = () => {
    setExportMenuOpen(false);
    const today = new Date().toISOString().slice(0, 10);
    const rows = filtered.map(({ id, ...rest }) => rest);
    downloadBlob(`ops-inspect-export-${today}.json`, JSON.stringify(rows, null, 2), "application/json;charset=utf-8");
    onToast({
      type: "ok",
      title: "JSON 数据已导出",
      msg: `已导出当前列表中的 ${filtered.length} 台服务器数据（JSON）。`,
    });
  };

  const typeSummary =
    Object.entries(kpi.byType)
      .map(([k, v]) => `${k} ${v}`)
      .join(" · ") || "暂无";
  const vendorSummary =
    Object.entries(kpi.byVendor)
      .map(([k, v]) => `${k.split(" ")[0]} ${v}`)
      .join(" · ") || "暂无";

  return (
    <main className="page">
      <div className="page-head">
        <div>
          <h1>服务器资产与实时巡检检测</h1>
        </div>
      </div>

      <section className="kpi-grid" aria-label="巡检汇总统计">
        <div className="kpi">
          <div className="kpi-label">已纳管目标</div>
          <div className="kpi-value">{kpi.total}</div>
          <div className="kpi-detail" title={typeSummary}>
            {typeSummary}
          </div>
        </div>
        <div className="kpi">
          <div className="kpi-label">厂商覆盖</div>
          <div className="kpi-value">{Object.keys(kpi.byVendor).length} 家</div>
          <div className="kpi-detail" title={vendorSummary}>
            {vendorSummary}
          </div>
        </div>
        <div className="kpi">
          <div className="kpi-label">已测可用总内存</div>
          <div className="kpi-value" style={{ color: "var(--ok)" }}>
            {kpi.freeMem.toFixed(1)} G
          </div>
          <div className="kpi-detail">
            总计 {kpi.totalMem} G（可用 {kpi.freePct.toFixed(1)}%）
          </div>
        </div>
        <div className="kpi">
          <div className="kpi-label">平均 CPU（已采）</div>
          <div className="kpi-value">{kpi.avgCpu != null ? `${kpi.avgCpu}%` : "-"}</div>
          <div className="kpi-detail">
            已采 {kpi.probedCount} 台 · 共 {kpi.totalCores} vCPU
          </div>
        </div>
        <div className="kpi">
          <div className="kpi-label">告警 / 检测失败</div>
          <div className="kpi-value" style={{ color: "var(--crit)" }}>
            {kpi.highCount + kpi.failCount}
          </div>
          <div className="kpi-detail">
            高负载 {kpi.highCount} 台 · 采集失败 {kpi.failCount} 台
          </div>
        </div>
      </section>

      <section className="card card-overflow-visible" aria-label="主机资产列表">
        <div className="card-head">
          <div style={{ display: "flex", alignItems: "baseline", gap: 12, flexWrap: "wrap" }}>
            <h2>主机资产列表</h2>
            <span className="card-sub mono">
              显示 {filtered.length} / 共 {targets.length} 台
            </span>
          </div>
          <div className="head-actions">
            <button className="btn btn-blue btn-sm" type="button" disabled={inspectingAll} onClick={onInspectAll}>
              {inspectingAll ? "巡检采集中..." : "立即全量巡检"}
            </button>
          </div>
        </div>

        <div className="toolbar">
          <div className="filter-group">
            <input
              className="input"
              type="search"
              placeholder="搜索主机名或 IP..."
              style={{ width: 196 }}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <CustomSelect
              value={filterType}
              onChange={setFilterType}
              minWidth={124}
              options={[
                { value: "", label: "全部类型" },
                ...SERVER_TYPES.map((t) => ({ value: t, label: t })),
              ]}
            />
            <CustomSelect
              value={filterVendor}
              onChange={setFilterVendor}
              minWidth={142}
              options={[
                { value: "", label: "全部厂商" },
                ...vendorOptions.map((v) => ({ value: v, label: v })),
              ]}
            />
            <CustomSelect
              value={filterCollector}
              onChange={setFilterCollector}
              minWidth={148}
              options={COLLECTOR_FILTER_OPTIONS}
            />
            <label className="check-inline">
              <input type="checkbox" checked={alertOnly} onChange={(e) => setAlertOnly(e.target.checked)} />
              仅看异常
            </label>
          </div>

          <div className="head-actions">
            <button className="btn btn-sm" type="button" onClick={onOpenImport}>
              批量导入
            </button>

            <div className={`cselect ${exportMenuOpen ? "is-open" : ""}`} ref={exportWrapRef}>
              <button
                className="btn btn-sm"
                type="button"
                aria-haspopup="menu"
                aria-expanded={exportMenuOpen}
                onClick={() => setExportMenuOpen((v) => !v)}
              >
                <span>导出</span>
                <span className="cselect-chevron" aria-hidden="true">
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.3">
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                </span>
              </button>
              {exportMenuOpen && (
                <div className="cselect-menu cselect-menu-right" role="menu" style={{ minWidth: 186 }}>
                  <button className="cselect-option" type="button" role="menuitem" onClick={handleExportCsv}>
                    <span className="cselect-opt-main">
                      <span className="cselect-opt-label">导出 CSV 表格</span>
                      <span className="cselect-opt-desc">支持 Excel 直接打开</span>
                    </span>
                  </button>
                  <button className="cselect-option" type="button" role="menuitem" onClick={handleExportJson}>
                    <span className="cselect-opt-main">
                      <span className="cselect-opt-label">导出 JSON 数据</span>
                      <span className="cselect-opt-desc">便于脚本或接口对接</span>
                    </span>
                  </button>
                </div>
              )}
            </div>

            <button className="btn btn-primary btn-sm" type="button" onClick={onOpenAdd}>
              + 添加服务器
            </button>
          </div>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>主机名 / IP 地址</th>
                <th>种类 · 厂商</th>
                <th>采集方式</th>
                <th>总内存 / 可用剩余</th>
                <th>CPU（检测值）</th>
                <th>巡检状态</th>
                <th>最后检测时间</th>
                <th style={{ textAlign: "right" }}>操作</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={8} className="empty-state">
                    无匹配目标服务器，可清空筛选或点击上方「+ 添加服务器」或「批量导入」。
                  </td>
                </tr>
              ) : (
                filtered.map((s) => {
                  const st = statusMeta(s.probe_status);
                  const col = collectorMeta(s.collector_type);
                  return (
                    <tr key={s.id}>
                      <td>
                        <span className="cell-host">{s.host}</span>
                        <span className="cell-sub">
                          {s.address}
                          {s.collector_type === "ssh" ? `:${s.ssh_port ?? 22} (${s.ssh_user || "ops-ro"})` : ""}
                        </span>
                      </td>
                      <td>
                        {s.type}
                        <span className="cell-sub">{s.vendor}</span>
                      </td>
                      <td>
                        <span className={`badge badge-${col.cls} mono`}>{col.text}</span>
                      </td>
                      <td>
                        {s.mem_total != null ? (
                          <span className="mono">
                            {s.mem_total} G / 剩 <strong>{s.mem_free} G</strong>
                          </span>
                        ) : (
                          <span className="card-sub">{s.probe_error || "待检测"}</span>
                        )}
                      </td>
                      <td>
                        {s.cpu != null ? (
                          <span className="meter-wrap mono">
                            <span className="meter">
                              <i style={{ width: `${Math.min(100, Math.max(0, s.cpu))}%`, background: st.color }} />
                            </span>
                            {s.cpu}% ({s.cores}C)
                          </span>
                        ) : (
                          <span className="card-sub">-</span>
                        )}
                      </td>
                      <td>
                        <span className={`badge badge-${st.cls}`} title={s.probe_error || ""}>
                          {st.text}
                        </span>
                      </td>
                      <td className="mono" style={{ fontSize: 12.5, color: "var(--ink-500)" }}>
                        {s.last_checked_at || "尚未检测"}
                      </td>
                      <td style={{ textAlign: "right" }}>
                        <button
                          className="btn btn-ghost btn-sm"
                          type="button"
                          disabled={probingId === s.id}
                          onClick={() => onInspectOne(s)}
                        >
                          {probingId === s.id ? "检测中..." : "检测"}
                        </button>
                        <button className="btn btn-ghost btn-sm" type="button" onClick={() => onOpenEdit(s)}>
                          编辑
                        </button>
                        <button className="btn btn-danger-text btn-sm" type="button" onClick={() => onDeleteRequest(s)}>
                          删除
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
