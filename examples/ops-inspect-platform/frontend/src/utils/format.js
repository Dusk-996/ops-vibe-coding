export const SERVER_TYPES = ["物理机", "虚拟机", "容器节点"];

export const SERVER_VENDORS = [
  "戴尔 Dell",
  "华为 TaiShan",
  "阿里云 ECS",
  "浪潮 Inspur",
  "本地宿主机",
];

export const COLLECTOR_OPTIONS = [
  { value: "ssh", label: "SSH 远程采集", desc: "无 Agent 远程 Linux 只读采集（/proc 指标）", dot: "ok" },
  { value: "local", label: "本机采集", desc: "直采当前运行宿主机真实系统指标", dot: "blue" },
  { value: "mock", label: "模拟探针", desc: "离线联调与演练用虚拟采集器", dot: "muted" },
];

export function statusMeta(probeStatus) {
  switch (probeStatus) {
    case "OK":
      return { cls: "ok", text: "正常", color: "#059669" };
    case "WARN":
      return { cls: "warn", text: "关注", color: "#d97706" };
    case "HIGH_LOAD":
      return { cls: "crit", text: "高负载", color: "#dc2626" };
    case "TIMEOUT":
      return { cls: "crit", text: "检测超时", color: "#dc2626" };
    case "UNREACHABLE":
      return { cls: "crit", text: "不可达", color: "#dc2626" };
    default:
      return { cls: "muted", text: "待检测", color: "#64748b" };
  }
}

export function collectorMeta(collectorType) {
  if (collectorType === "local") return { cls: "blue", text: "本机采集" };
  if (collectorType === "ssh") return { cls: "ok", text: "SSH 采集" };
  return { cls: "muted", text: "模拟探针" };
}

export function isAlertRow(item) {
  return ["HIGH_LOAD", "TIMEOUT", "UNREACHABLE"].includes(item.probe_status);
}

export function nowStr() {
  const d = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

export function downloadBlob(filename, content, mime) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export function csvCell(val) {
  let s = String(val ?? "");
  if (/^[=+\-@]/.test(s)) s = "'" + s;
  if (/[",\n\r]/.test(s)) s = '"' + s.replace(/"/g, '""') + '"';
  return s;
}

export function buildExportCsv(rows) {
  const cols = [
    "host",
    "address",
    "type",
    "vendor",
    "collector_type",
    "ssh_port",
    "ssh_user",
    "ssh_credential_ref",
    "mem_total",
    "mem_free",
    "cores",
    "cpu",
    "probe_status",
    "last_checked_at",
  ];
  const lines = [
    cols.join(","),
    ...rows.map((r) => cols.map((k) => csvCell(r[k])).join(",")),
  ];
  return "\uFEFF" + lines.join("\r\n");
}

export function buildImportTemplateCsv() {
  const sample = [
    "host,address,type,vendor,collectorType,sshPort,sshUser,sshCredentialRef",
    "prod-cache-01,10.10.3.18,物理机,华为 TaiShan,ssh,22,ops-ro,prod-ro-key",
    "prod-web-08,10.10.4.25,虚拟机,阿里云 ECS,ssh,2222,ops-ro,cloud-ro-key",
    "local-host-01,127.0.0.1,容器节点,本地宿主机,local,,,",
  ].join("\r\n");
  return "\uFEFF" + sample;
}

export function buildMarkdownReport(items) {
  const probed = items.filter((s) => s.mem_total != null);
  const normal = items.filter((s) => s.probe_status === "OK");
  const abnormal = items.filter((s) => s.probe_status !== "OK");
  const totalMem = Number(probed.reduce((a, s) => a + s.mem_total, 0).toFixed(1));
  const freeMem = Number(probed.reduce((a, s) => a + s.mem_free, 0).toFixed(1));
  const pct = totalMem ? ((freeMem / totalMem) * 100).toFixed(1) : "0.0";
  const avgCpu = probed.length
    ? (probed.reduce((a, s) => a + (s.cpu ?? 0), 0) / probed.length).toFixed(1) + "%"
    : "-";
  const high = items.filter((s) => s.probe_status === "HIGH_LOAD");
  const warn = items.filter((s) => s.probe_status === "WARN");
  const failed = items.filter((s) => ["TIMEOUT", "UNREACHABLE"].includes(s.probe_status));
  const pending = items.filter((s) => !["OK", "WARN", "HIGH_LOAD", "TIMEOUT", "UNREACHABLE"].includes(s.probe_status));

  const issueParts = [];
  if (high.length) issueParts.push(`高负载 ${high.length} 台`);
  if (warn.length) issueParts.push(`需关注 ${warn.length} 台`);
  if (failed.length) issueParts.push(`采集失败/超时 ${failed.length} 台`);
  if (pending.length) issueParts.push(`待检测 ${pending.length} 台`);

  const lines = [
    `# 服务器巡检报告（${nowStr()}）`,
    "",
    "## 一、巡检总览",
    `- 纳管服务器总数：${items.length} 台（正常 ${normal.length} 台 ｜ 异常/需关注 ${abnormal.length} 台）`,
    `- 异常分布：${issueParts.length ? issueParts.join("、") : "无异常节点"}`,
    `- 已采节点资源汇总：总内存 ${totalMem} GB ｜ 可用剩余 ${freeMem} GB（${pct}%）｜ 平均 CPU ${avgCpu}`,
    "",
  ];

  if (abnormal.length) {
    lines.push(
      `## 二、异常及需关注主机明细（共 ${abnormal.length} 台）`,
      "| 主机名 | IP 地址 | 类型 / 厂商 | 总内存(GB) | 可用内存(GB) | CPU | 状态 | 异常说明 |",
      "|---|---|---|---:|---:|---:|---|---|",
      ...abnormal.map((s) => {
        const reason =
          s.probe_error ||
          (s.probe_status === "HIGH_LOAD"
            ? `高负载（CPU ${s.cpu}%）`
            : s.probe_status === "WARN"
              ? `接近水位（CPU ${s.cpu}%）`
              : "尚未执行采集检测");
        return `| ${s.host} | ${s.address} | ${s.type} / ${s.vendor} | ${s.mem_total ?? "-"} | ${s.mem_free ?? "-"} | ${s.cpu != null ? s.cpu + "%" : "-"} | ${statusMeta(s.probe_status).text} | ${reason} |`;
      })
    );
  } else {
    lines.push("## 二、异常主机明细", `当前全部 ${items.length} 台纳管服务器均运行正常，无高负载或采集异常节点。`);
  }

  if (normal.length) {
    lines.push(
      "",
      "## 三、正常运行主机说明",
      `共 ${normal.length} 台服务器运行平稳（状态：正常），已省略逐台明细；如需全量清单请在巡检平台查看或导出。`
    );
  }
  return lines.join("\n");
}

export function computeKpi(items) {
  const byType = {};
  const byVendor = {};
  let totalMem = 0;
  let freeMem = 0;
  let totalCores = 0;
  let sumCpu = 0;
  let probedCount = 0;
  let highCount = 0;
  let failCount = 0;

  items.forEach((s) => {
    byType[s.type] = (byType[s.type] || 0) + 1;
    byVendor[s.vendor] = (byVendor[s.vendor] || 0) + 1;
    if (s.mem_total != null) {
      totalMem += s.mem_total;
      freeMem += s.mem_free ?? 0;
      totalCores += s.cores ?? 0;
      sumCpu += s.cpu ?? 0;
      probedCount += 1;
    }
    if (s.probe_status === "HIGH_LOAD") highCount += 1;
    if (s.probe_status === "TIMEOUT" || s.probe_status === "UNREACHABLE") failCount += 1;
  });

  return {
    total: items.length,
    byType,
    byVendor,
    totalMem: Number(totalMem.toFixed(1)),
    freeMem: Number(freeMem.toFixed(1)),
    freePct: totalMem ? Number(((freeMem / totalMem) * 100).toFixed(1)) : 0,
    totalCores,
    avgCpu: probedCount ? Number((sumCpu / probedCount).toFixed(1)) : null,
    probedCount,
    highCount,
    failCount,
  };
}
