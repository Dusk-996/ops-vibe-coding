import React from "react";

/**
 * 将巡检报告内容解析为干净的可视化邮件排版视图（纯 React 节点，无 dangerouslySetInnerHTML，不向用户暴露 Markdown 原始符号）。
 */
function parseReportBlocks(rawText) {
  const lines = String(rawText || "").replace(/\r\n/g, "\n").split("\n");
  const blocks = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i].trim();
    if (!line) {
      i += 1;
      continue;
    }

    if (line.startsWith("# ")) {
      blocks.push({ type: "title", text: line.slice(2).trim() });
      i += 1;
      continue;
    }

    if (line.startsWith("## ")) {
      blocks.push({ type: "heading", text: line.slice(3).trim() });
      i += 1;
      continue;
    }

    if (line.startsWith("- ")) {
      const items = [];
      while (i < lines.length && lines[i].trim().startsWith("- ")) {
        items.push(lines[i].trim().slice(2).trim());
        i += 1;
      }
      blocks.push({ type: "list", items });
      continue;
    }

    if (line.startsWith("|") && line.endsWith("|")) {
      const tableLines = [];
      while (i < lines.length && lines[i].trim().startsWith("|") && lines[i].trim().endsWith("|")) {
        tableLines.push(lines[i].trim());
        i += 1;
      }
      if (tableLines.length >= 2) {
        const splitRow = (r) =>
          r
            .slice(1, -1)
            .split("|")
            .map((cell) => cell.trim());
        const headers = splitRow(tableLines[0]);
        const bodyRows = tableLines
          .slice(1)
          .filter((r) => !/^\|[\s:|-]+\|$/.test(r))
          .map(splitRow);
        blocks.push({ type: "table", headers, rows: bodyRows });
        continue;
      }
    }

    blocks.push({ type: "paragraph", text: line });
    i += 1;
  }

  return blocks;
}

function renderStatusPill(val) {
  if (val === "正常") return <span className="badge badge-ok">{val}</span>;
  if (val === "关注") return <span className="badge badge-warn">{val}</span>;
  if (val === "高负载" || val === "检测超时" || val === "不可达") {
    return <span className="badge badge-crit">{val}</span>;
  }
  if (val === "待检测") return <span className="badge badge-muted">{val}</span>;
  return val;
}

export default function ReportView({ content, compact = false }) {
  const blocks = parseReportBlocks(content);

  return (
    <div className={`report-view ${compact ? "report-view-compact" : ""}`}>
      {blocks.map((b, idx) => {
        if (b.type === "title") {
          return (
            <div className="rv-title" key={idx}>
              {b.text}
            </div>
          );
        }
        if (b.type === "heading") {
          return (
            <div className="rv-heading" key={idx}>
              {b.text}
            </div>
          );
        }
        if (b.type === "list") {
          return (
            <div className="rv-summary-grid" key={idx}>
              {b.items.map((item, j) => {
                const sepIdx = item.indexOf("：");
                if (sepIdx > 0 && sepIdx < 18) {
                  const label = item.slice(0, sepIdx);
                  const val = item.slice(sepIdx + 1);
                  return (
                    <div className="rv-kv" key={j}>
                      <span className="rv-kv-label">{label}</span>
                      <span className="rv-kv-val">{val}</span>
                    </div>
                  );
                }
                return (
                  <div className="rv-kv" key={j}>
                    <span className="rv-kv-val">{item}</span>
                  </div>
                );
              })}
            </div>
          );
        }
        if (b.type === "table") {
          const statusColIdx = b.headers.findIndex((h) => h.includes("状态"));
          return (
            <div className="rv-table-wrap" key={idx}>
              <table className="rv-table">
                <thead>
                  <tr>
                    {b.headers.map((h, hi) => (
                      <th key={hi}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {b.rows.map((row, ri) => (
                    <tr key={ri}>
                      {row.map((cell, ci) => (
                        <td key={ci} className={ci === 0 || ci === 1 ? "mono" : ""}>
                          {ci === statusColIdx ? renderStatusPill(cell) : cell}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
        }
        return (
          <p className="rv-para" key={idx}>
            {b.text}
          </p>
        );
      })}
    </div>
  );
}
