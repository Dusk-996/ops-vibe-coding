import React, { useEffect, useRef, useState } from "react";

const HOURS = Array.from({ length: 24 }, (_, i) => String(i).padStart(2, "0"));
const MINUTES = Array.from({ length: 12 }, (_, i) => String(i * 5).padStart(2, "0"));
const PRESETS = [
  { time: "08:00", label: "08:00 早班" },
  { time: "09:00", label: "09:00 上班" },
  { time: "12:00", label: "12:00 午检" },
  { time: "18:00", label: "18:00 下班" },
  { time: "22:00", label: "22:00 晚检" },
];

export default function TimePicker({ value, onChange }) {
  const [open, setOpen] = useState(false);
  const wrapRef = useRef(null);
  const [pickedH = "09", pickedM = "00"] = (value || "09:00").split(":");

  useEffect(() => {
    const onDocClick = (e) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener("click", onDocClick);
    return () => document.removeEventListener("click", onDocClick);
  }, []);

  const selectHour = (h) => onChange(`${h}:${pickedM}`);
  const selectMin = (m) => {
    onChange(`${pickedH}:${m}`);
    setOpen(false);
  };
  const selectPreset = (t) => {
    onChange(t);
    setOpen(false);
  };

  return (
    <div className="tp-wrap" ref={wrapRef}>
      <button
        className="tp-trigger"
        type="button"
        aria-expanded={open}
        aria-haspopup="dialog"
        onClick={() => setOpen((v) => !v)}
      >
        <span className="tp-icon" aria-hidden="true">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="9" />
            <polyline points="12 7 12 12 15.5 14" />
          </svg>
        </span>
        <span className="tp-display">
          {pickedH} : {pickedM}
        </span>
        <span className="tp-caret" aria-hidden="true">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </span>
      </button>
      <span className="card-sub">每日自动执行 · 服务端本地时区</span>

      {open && (
        <div className="tp-popover" role="dialog" aria-label="选择每日推送时间">
          <div>
            <div className="tp-sec-title">
              <span>小时（00–23）</span>
              <span className="mono">{pickedH} 时</span>
            </div>
            <div className="tp-grid">
              {HOURS.map((h) => (
                <button
                  key={h}
                  type="button"
                  className={`tp-cell ${h === pickedH ? "active" : ""}`}
                  onClick={() => selectHour(h)}
                >
                  {h}
                </button>
              ))}
            </div>
          </div>

          <div>
            <div className="tp-sec-title">
              <span>分钟（每 5 分）</span>
              <span className="mono">{pickedM} 分</span>
            </div>
            <div className="tp-grid">
              {MINUTES.map((m) => (
                <button
                  key={m}
                  type="button"
                  className={`tp-cell ${m === pickedM ? "active" : ""}`}
                  onClick={() => selectMin(m)}
                >
                  {m}
                </button>
              ))}
            </div>
          </div>

          <div className="tp-presets">
            {PRESETS.map((p) => (
              <button
                key={p.time}
                type="button"
                className={`tp-preset ${p.time === value ? "active" : ""}`}
                onClick={() => selectPreset(p.time)}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
