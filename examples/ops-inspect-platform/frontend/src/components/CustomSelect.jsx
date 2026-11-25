import React, { useEffect, useRef, useState } from "react";

/**
 * 生产级自定义下拉选择器：替代系统原生 <select>，提供统一的圆角浮层、柔和悬停与右侧勾选态。
 * options: Array<{ value: string, label: string, desc?: string, dot?: "ok"|"warn"|"crit"|"blue"|"muted" }>
 */
export default function CustomSelect({
  id,
  value,
  options,
  onChange,
  placeholder = "请选择",
  size = "md",
  fullWidth = false,
  align = "left",
  minWidth,
}) {
  const [open, setOpen] = useState(false);
  const wrapRef = useRef(null);

  const selected = options.find((opt) => opt.value === value) || options[0];

  useEffect(() => {
    if (!open) return undefined;
    const onDocMouseDown = (e) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    const onKeyDown = (e) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onDocMouseDown);
    window.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onDocMouseDown);
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  const handleSelect = (val) => {
    onChange(val);
    setOpen(false);
  };

  return (
    <div
      className={`cselect ${fullWidth ? "cselect-full" : ""} ${open ? "is-open" : ""}`}
      ref={wrapRef}
      style={minWidth ? { minWidth } : undefined}
    >
      <button
        id={id}
        type="button"
        className={`cselect-trigger cselect-${size}`}
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        <span className="cselect-val">
          {selected?.dot && <i className={`cselect-dot dot-${selected.dot}`} aria-hidden="true" />}
          <span className="cselect-label">{selected ? selected.label : placeholder}</span>
        </span>
        <span className="cselect-chevron" aria-hidden="true">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </span>
      </button>

      {open && (
        <div
          className={`cselect-menu ${align === "right" ? "cselect-menu-right" : ""}`}
          role="listbox"
        >
          {options.map((opt) => {
            const isSelected = opt.value === value;
            return (
              <button
                key={opt.value}
                type="button"
                role="option"
                aria-selected={isSelected}
                className={`cselect-option ${isSelected ? "is-selected" : ""}`}
                onClick={() => handleSelect(opt.value)}
              >
                <span className="cselect-opt-main">
                  <span className="cselect-opt-line">
                    {opt.dot && <i className={`cselect-dot dot-${opt.dot}`} aria-hidden="true" />}
                    <span className="cselect-opt-label">{opt.label}</span>
                  </span>
                  {opt.desc && <span className="cselect-opt-desc">{opt.desc}</span>}
                </span>
                {isSelected && (
                  <span className="cselect-check" aria-hidden="true">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                  </span>
                )}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
