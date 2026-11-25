/**
 * P4a 前端验收本地交互引擎：
 * 仅在开发态 (import.meta.env.DEV) 且后端 /health 尚未启动时提供完整交互验收能力；
 * 生产构建 (VITE_USE_MOCK=false) 绝不启用本模块。
 */
import { buildMarkdownReport, nowStr } from "../utils/format.js";

const makeOpId = () => "op-" + Math.random().toString(16).slice(2, 10);

const state = {
  role: "admin",
  nextId: 7,
  targets: [
    {
      id: 1,
      host: "ops-console-local",
      address: "127.0.0.1",
      type: "容器节点",
      vendor: "本地宿主机",
      collector_type: "local",
      ssh_port: null,
      ssh_user: "",
      ssh_credential_ref: "",
      mem_total: 32,
      mem_free: 14.6,
      cores: 16,
      cpu: 24,
      probe_status: "OK",
      last_checked_at: "2026-11-23 09:00:01",
      probe_error: "",
    },
    {
      id: 2,
      host: "prod-k8s-node-01",
      address: "10.10.2.11",
      type: "物理机",
      vendor: "戴尔 Dell",
      collector_type: "ssh",
      ssh_port: 22,
      ssh_user: "ops-ro",
      ssh_credential_ref: "prod-ro-key",
      mem_total: 256,
      mem_free: 38,
      cores: 64,
      cpu: 86,
      probe_status: "HIGH_LOAD",
      last_checked_at: "2026-11-23 09:00:02",
      probe_error: "",
    },
    {
      id: 3,
      host: "prod-db-master-01",
      address: "10.10.2.21",
      type: "物理机",
      vendor: "华为 TaiShan",
      collector_type: "ssh",
      ssh_port: 22,
      ssh_user: "ops-ro",
      ssh_credential_ref: "prod-ro-key",
      mem_total: 512,
      mem_free: 164,
      cores: 128,
      cpu: 64,
      probe_status: "WARN",
      last_checked_at: "2026-11-23 09:00:02",
      probe_error: "",
    },
    {
      id: 4,
      host: "prod-api-vm-03",
      address: "10.10.8.33",
      type: "虚拟机",
      vendor: "阿里云 ECS",
      collector_type: "ssh",
      ssh_port: 2222,
      ssh_user: "ops-ro",
      ssh_credential_ref: "cloud-ro-key",
      mem_total: 64,
      mem_free: 39,
      cores: 16,
      cpu: 28,
      probe_status: "OK",
      last_checked_at: "2026-11-23 09:00:02",
      probe_error: "",
    },
    {
      id: 5,
      host: "edge-gw-node-02",
      address: "10.10.9.52",
      type: "容器节点",
      vendor: "浪潮 Inspur",
      collector_type: "ssh",
      ssh_port: 22,
      ssh_user: "ops-ro",
      ssh_credential_ref: "edge-ro-key",
      mem_total: null,
      mem_free: null,
      cores: null,
      cpu: null,
      probe_status: "TIMEOUT",
      last_checked_at: "2026-11-23 09:00:08",
      probe_error: "SSH 连接超过 8s 超时（已隔离，未重试）",
    },
    {
      id: 6,
      host: "lab-mock-01",
      address: "192.168.50.10",
      type: "虚拟机",
      vendor: "戴尔 Dell",
      collector_type: "mock",
      ssh_port: null,
      ssh_user: "",
      ssh_credential_ref: "",
      mem_total: 128,
      mem_free: 84,
      cores: 32,
      cpu: 31,
      probe_status: "OK",
      last_checked_at: "2026-11-23 09:00:01",
      probe_error: "",
    },
  ],
  schedule: {
    enabled: true,
    push_time: "09:00",
    recipients: ["ops-oncall@corp.local", "sre-lead@corp.local"],
    smtp_mode: "mock",
  },
  smtp: {
    mode: "mock",
    source: "none",
    enabled: false,
    active_profile_id: null,
    host: "",
    port: 465,
    security: "ssl",
    username: "",
    from_addr: "",
    timeout_seconds: 10,
    has_auth_code: false,
    profiles: [],
  },
  outbox: [
    {
      id: 1,
      op_id: "op-init-0900",
      delivery_mode: "mock",
      status_code: 200,
      recipients: "ops-oncall@corp.local, sre-lead@corp.local",
      subject: "服务器每日巡检报告（2026-11-23 09:00）",
      body_md: [
        "# 服务器每日巡检报告（2026-11-23 09:00）",
        "",
        "## 一、巡检汇总",
        "- 纳管目标总数：6 台（已采集 5 台 / 采集失败 1 台）",
        "- 内存汇总（MemAvailable）：总计 992 GB ｜ 可用剩余 339.6 GB（34.2%）",
        "- 高负载告警：1 台（prod-k8s-node-01）",
        "- 采集异常主机：1 台（edge-gw-node-02[10.10.9.52]: SSH 连接超过 8s 超时）",
        "",
        "## 二、巡检明细",
        "| 主机名 | IP 地址 | 种类 | 厂商 | 采集方式 | 总内存(GB) | 可用内存(GB) | CPU | 状态 | 检测时间 |",
        "|---|---|---|---|---|---:|---:|---:|---|---|",
        "| ops-console-local | 127.0.0.1 | 容器节点 | 本地宿主机 | local | 32 | 14.6 | 24% | 正常 | 2026-11-23 09:00:01 |",
        "| prod-k8s-node-01 | 10.10.2.11 | 物理机 | 戴尔 Dell | ssh | 256 | 38 | 86% | 高负载 | 2026-11-23 09:00:02 |",
        "| prod-db-master-01 | 10.10.2.21 | 物理机 | 华为 TaiShan | ssh | 512 | 164 | 64% | 关注 | 2026-11-23 09:00:02 |",
        "| prod-api-vm-03 | 10.10.8.33 | 虚拟机 | 阿里云 ECS | ssh | 64 | 39 | 28% | 正常 | 2026-11-23 09:00:02 |",
        "| edge-gw-node-02 | 10.10.9.52 | 容器节点 | 浪潮 Inspur | ssh | - | - | - | 检测超时 | 2026-11-23 09:00:08 |",
        "| lab-mock-01 | 192.168.50.10 | 虚拟机 | 戴尔 Dell | mock | 128 | 84 | 31% | 正常 | 2026-11-23 09:00:01 |",
      ].join("\n"),
      error: "",
      created_at: "2026-11-23 09:00:09",
    },
  ],
  audits: [
    {
      id: 1,
      op_id: "op-init-0900",
      actor: "scheduler",
      role: "system",
      action: "SCHEDULED_INSPECT_AND_PUSH",
      http_status: 200,
      detail: "全量巡检 6 台（成功 5 / 超时 1），报告已发送",
      created_at: "2026-11-23 09:00:09",
    },
  ],
};

function makeApiError(status, detail, opId) {
  const err = new Error(detail);
  err.status = status;
  err.opId = opId;
  return err;
}

function recordAudit(actor, role, action, httpStatus, detail, opId) {
  state.audits.unshift({
    id: state.audits.length + 1,
    op_id: opId,
    actor,
    role,
    action,
    http_status: httpStatus,
    detail,
    created_at: nowStr(),
  });
}

const ACTION_CN = {
  CREATE_TARGET: "登记目标服务器",
  UPDATE_TARGET: "修改目标服务器",
  DELETE_TARGET: "删除目标服务器",
  IMPORT_PREVIEW: "校验导入文件",
  IMPORT_TARGETS: "批量导入服务器",
  INSPECT_ALL: "发起全量巡检",
  INSPECT_ONE: "发起单台主机检测",
  UPDATE_SCHEDULE: "修改定时推送配置",
  UPDATE_SMTP: "保存发件邮箱账号",
  ACTIVATE_SMTP_PROFILE: "切换发件邮箱账号",
  DELETE_SMTP_PROFILE: "删除发件邮箱存档",
  PUSH_REPORT_NOW: "立即推送巡检报告",
};

function requireAdmin(action) {
  const opId = makeOpId();
  const label = ACTION_CN[action] || "该操作";
  if (state.role === "anon") {
    recordAudit("anonymous", "anon", action, 401, `未登录状态下尝试${label}，已拦截`, opId);
    throw makeApiError(401, `尚未登录系统，请先切换为管理员身份后再${label}。`, opId);
  }
  if (state.role === "viewer") {
    recordAudit("viewer", "viewer", action, 403, `只读成员尝试${label}，已拦截`, opId);
    throw makeApiError(403, `只读成员（viewer）无法${label}，如需执行请切换为管理员身份。`, opId);
  }
  return opId;
}

function probeOneTarget(t) {
  const ts = nowStr();
  if (t.address.endsWith(".52") || t.host.toLowerCase().includes("timeout")) {
    t.probe_status = "TIMEOUT";
    t.probe_error = "SSH 连接超过 8s 超时（单台隔离，未重试）";
    t.last_checked_at = ts;
    return false;
  }
  const baseMem = t.mem_total || (t.collector_type === "local" ? 32 : 128);
  const cores = t.cores || (t.collector_type === "local" ? 16 : 32);
  const cpu = Math.min(96, Math.max(8, Math.round((t.cpu ?? 35) + (Math.random() * 14 - 7))));
  const free = Number(
    Math.max(4, Math.min(baseMem - 2, (t.mem_free ?? baseMem * 0.5) + (Math.random() * 8 - 4))).toFixed(1)
  );
  t.mem_total = baseMem;
  t.mem_free = free;
  t.cores = cores;
  t.cpu = cpu;
  t.last_checked_at = ts;
  t.probe_error = "";
  const ratio = free / baseMem;
  t.probe_status = cpu >= 80 || ratio < 0.15 ? "HIGH_LOAD" : cpu >= 60 || ratio < 0.25 ? "WARN" : "OK";
  return true;
}

function parseImportRows(format, content) {
  let raw = [];
  if (format === "json") {
    raw = JSON.parse(content);
    if (!Array.isArray(raw)) throw new Error("JSON 根节点必须为数组");
  } else {
    const lines = content
      .replace(/^\uFEFF/, "")
      .trim()
      .split(/\r?\n/)
      .filter((l) => l.trim());
    if (lines.length < 2) throw new Error("CSV 至少需表头与 1 行数据");
    const headers = lines[0].split(",").map((h) => h.trim().replace(/^"|"$/g, ""));
    raw = lines.slice(1).map((line, i) => {
      const cols = line.split(",").map((c) => c.trim().replace(/^"|"$/g, ""));
      const obj = { _line: i + 2 };
      headers.forEach((h, idx) => {
        obj[h] = cols[idx] ?? "";
      });
      return obj;
    });
  }

  const valid = [];
  const errors = [];
  const seen = new Set();
  raw.forEach((r, idx) => {
    const ln = r._line || idx + 1;
    const host = String(r.host || "").trim();
    const address = String(r.address || "").trim();
    const type = String(r.type || "物理机").trim();
    const vendor = String(r.vendor || "戴尔 Dell").trim();
    const collector_type = String(r.collector_type || r.collectorType || "ssh")
      .trim()
      .toLowerCase();
    const portRaw = r.ssh_port ?? r.sshPort;
    const ssh_port = collector_type === "ssh" ? Number(portRaw || 22) : null;
    const ssh_user = collector_type === "ssh" ? String(r.ssh_user || r.sshUser || "ops-ro").trim() : "";
    const ssh_credential_ref =
      collector_type === "ssh" ? String(r.ssh_credential_ref || r.sshCredentialRef || "").trim() : "";

    if (!host) return errors.push(`第 ${ln} 行缺少 host`);
    if (!address) return errors.push(`第 ${ln} 行 (${host}) 缺少 IP/address`);
    if (!["ssh", "local", "mock"].includes(collector_type)) {
      return errors.push(`第 ${ln} 行 collectorType 非法`);
    }
    if (collector_type === "ssh" && (!Number.isInteger(ssh_port) || ssh_port < 1 || ssh_port > 65535)) {
      return errors.push(`第 ${ln} 行 SSH 端口无效`);
    }
    if (seen.has(host)) return errors.push(`第 ${ln} 行文件内主机名 ${host} 重复`);
    seen.add(host);
    valid.push({ host, address, type, vendor, collector_type, ssh_port, ssh_user, ssh_credential_ref });
  });

  const existing = new Set(state.targets.map((t) => t.host));
  const duplicate_count = valid.filter((v) => existing.has(v.host)).length;
  return { valid_rows: valid, errors, duplicate_count };
}

export const localPreviewAdapter = {
  setPreviewRole(role) {
    state.role = role;
  },
  getPreviewRole() {
    return state.role;
  },
  async listTargets() {
    return { items: state.targets.map((t) => ({ ...t })) };
  },
  async createTarget(payload) {
    const opId = requireAdmin("CREATE_TARGET");
    if (state.targets.some((t) => t.host === payload.host)) {
      throw makeApiError(409, `主机名 ${payload.host} 已存在`, opId);
    }
    const created = {
      id: state.nextId++,
      ...payload,
      mem_total: null,
      mem_free: null,
      cores: null,
      cpu: null,
      probe_status: "PENDING",
      last_checked_at: "",
      probe_error: "",
    };
    state.targets.unshift(created);
    recordAudit("admin", "admin", "CREATE_TARGET", 201, `登记目标 ${created.host} (${created.address} / ${created.collector_type})`, opId);
    return { item: { ...created }, op_id: opId };
  },
  async updateTarget(id, payload) {
    const opId = requireAdmin("UPDATE_TARGET");
    const idx = state.targets.findIndex((t) => t.id === id);
    if (idx < 0) throw makeApiError(404, "目标不存在", opId);
    if (state.targets.some((t) => t.host === payload.host && t.id !== id)) {
      throw makeApiError(409, `主机名 ${payload.host} 已存在`, opId);
    }
    state.targets[idx] = { ...state.targets[idx], ...payload };
    recordAudit("admin", "admin", "UPDATE_TARGET", 200, `更新目标 ${payload.host} (${payload.address})`, opId);
    return { item: { ...state.targets[idx] }, op_id: opId };
  },
  async deleteTarget(id) {
    const opId = requireAdmin("DELETE_TARGET");
    const target = state.targets.find((t) => t.id === id);
    if (!target) throw makeApiError(404, "目标不存在", opId);
    state.targets = state.targets.filter((t) => t.id !== id);
    recordAudit("admin", "admin", "DELETE_TARGET", 200, `删除目标 ${target.host}`, opId);
    return { deleted: id, op_id: opId };
  },
  async previewImport({ format, content }) {
    const opId = requireAdmin("IMPORT_PREVIEW");
    try {
      const parsed = parseImportRows(format, content);
      return { ...parsed, op_id: opId };
    } catch (err) {
      throw makeApiError(400, err.message, opId);
    }
  },
  async commitImport({ format, content, policy }) {
    const opId = requireAdmin("IMPORT_TARGETS");
    const { valid_rows } = parseImportRows(format, content);
    let added = 0;
    let updated = 0;
    let skipped = 0;
    valid_rows.forEach((r) => {
      const idx = state.targets.findIndex((t) => t.host === r.host);
      if (idx >= 0) {
        if (policy === "overwrite") {
          state.targets[idx] = { ...state.targets[idx], ...r };
          updated += 1;
        } else {
          skipped += 1;
        }
      } else {
        state.targets.unshift({
          id: state.nextId++,
          ...r,
          mem_total: null,
          mem_free: null,
          cores: null,
          cpu: null,
          probe_status: "PENDING",
          last_checked_at: "",
          probe_error: "",
        });
        added += 1;
      }
    });
    recordAudit("admin", "admin", "IMPORT_TARGETS", 200, `导入目标：新增 ${added}、覆盖 ${updated}、跳过 ${skipped}`, opId);
    return { added, updated, skipped, op_id: opId };
  },
  async inspectAll() {
    const opId = requireAdmin("INSPECT_ALL");
    let succeeded = 0;
    let failed = 0;
    state.targets.forEach((t) => {
      if (probeOneTarget(t)) succeeded += 1;
      else failed += 1;
    });
    recordAudit("admin", "admin", "INSPECT_ALL", 200, `全量巡检完成：成功 ${succeeded} 台，异常隔离 ${failed} 台`, opId);
    return { total: state.targets.length, succeeded, failed, items: state.targets.map((t) => ({ ...t })), op_id: opId };
  },
  async inspectOne(id) {
    const opId = requireAdmin("INSPECT_ONE");
    const target = state.targets.find((t) => t.id === id);
    if (!target) throw makeApiError(404, "目标不存在", opId);
    const ok = probeOneTarget(target);
    recordAudit(
      "admin",
      "admin",
      "INSPECT_ONE",
      ok ? 200 : 504,
      `单台巡检 ${target.host} (${target.address}): ${ok ? "成功" : target.probe_error}`,
      opId
    );
    if (!ok) {
      throw makeApiError(
        504,
        `${target.host}（${target.address}）等待 8 秒无响应，已自动跳过且未重试，请检查网络或 SSH 服务状态。`,
        opId
      );
    }
    return { item: { ...target }, op_id: opId };
  },
  async getSchedule() {
    return { ...state.schedule, recipients: [...state.schedule.recipients] };
  },
  async updateSchedule(payload) {
    const opId = requireAdmin("UPDATE_SCHEDULE");
    state.schedule = { ...state.schedule, ...payload };
    recordAudit("admin", "admin", "UPDATE_SCHEDULE", 200, `${payload.enabled ? "启用" : "停用"} 每日 ${payload.push_time} 推送`, opId);
    return { ...state.schedule, op_id: opId };
  },
  async getSmtpConfig() {
    return { ...state.smtp, profiles: state.smtp.profiles.map((p) => ({ ...p })) };
  },
  async updateSmtpConfig(payload) {
    const opId = requireAdmin("UPDATE_SMTP");
    if (!payload.enabled) {
      return this.activateSmtpProfile(0);
    }
    const existingIdx = state.smtp.profiles.findIndex((p) => p.username === payload.username);
    state.smtp.profiles.forEach((p) => {
      p.is_active = false;
    });
    let activeId;
    if (existingIdx >= 0) {
      const old = state.smtp.profiles[existingIdx];
      state.smtp.profiles[existingIdx] = {
        ...old,
        host: payload.host,
        port: payload.port,
        security: payload.security,
        from_addr: payload.from_addr || payload.username,
        has_auth_code: Boolean(payload.auth_code) || old.has_auth_code,
        is_active: true,
        updated_at: nowStr(),
      };
      activeId = old.id;
    } else {
      activeId = state.smtp.profiles.length + 1;
      state.smtp.profiles.unshift({
        id: activeId,
        host: payload.host,
        port: payload.port,
        security: payload.security,
        username: payload.username,
        from_addr: payload.from_addr || payload.username,
        timeout_seconds: payload.timeout_seconds || 10,
        has_auth_code: Boolean(payload.auth_code),
        is_active: true,
        updated_at: nowStr(),
      });
    }
    state.smtp = {
      ...state.smtp,
      mode: "smtp",
      source: "database",
      enabled: true,
      active_profile_id: activeId,
      host: payload.host,
      port: payload.port,
      security: payload.security,
      username: payload.username,
      from_addr: payload.from_addr || payload.username,
      has_auth_code: true,
    };
    state.schedule.smtp_mode = "smtp";
    recordAudit("admin", "admin", "UPDATE_SMTP", 200, `保存并启用发件账号 ${payload.username}`, opId);
    return { ...state.smtp, profiles: state.smtp.profiles.map((p) => ({ ...p })), op_id: opId };
  },
  async activateSmtpProfile(profileId) {
    const opId = requireAdmin("ACTIVATE_SMTP_PROFILE");
    if (profileId === 0) {
      state.smtp.profiles.forEach((p) => {
        p.is_active = false;
      });
      state.smtp = { ...state.smtp, mode: "mock", enabled: false, active_profile_id: null };
      state.schedule.smtp_mode = "mock";
      recordAudit("admin", "admin", "ACTIVATE_SMTP_PROFILE", 200, "已切回本地模拟收件箱", opId);
      return { ...state.smtp, profiles: state.smtp.profiles.map((p) => ({ ...p })), op_id: opId };
    }
    const target = state.smtp.profiles.find((p) => p.id === profileId);
    if (!target) throw makeApiError(404, "发件邮箱存档不存在", opId);
    state.smtp.profiles.forEach((p) => {
      p.is_active = p.id === profileId;
    });
    state.smtp = {
      ...state.smtp,
      mode: "smtp",
      source: "database",
      enabled: true,
      active_profile_id: target.id,
      host: target.host,
      port: target.port,
      security: target.security,
      username: target.username,
      from_addr: target.from_addr,
      has_auth_code: target.has_auth_code,
    };
    state.schedule.smtp_mode = "smtp";
    recordAudit("admin", "admin", "ACTIVATE_SMTP_PROFILE", 200, `切换发件账号为 ${target.username}`, opId);
    return { ...state.smtp, profiles: state.smtp.profiles.map((p) => ({ ...p })), op_id: opId };
  },
  async deleteSmtpProfile(profileId) {
    const opId = requireAdmin("DELETE_SMTP_PROFILE");
    const target = state.smtp.profiles.find((p) => p.id === profileId);
    if (!target) throw makeApiError(404, "发件邮箱存档不存在", opId);
    state.smtp.profiles = state.smtp.profiles.filter((p) => p.id !== profileId);
    if (state.smtp.active_profile_id === profileId) {
      state.smtp = { ...state.smtp, mode: "mock", enabled: false, active_profile_id: null };
      state.schedule.smtp_mode = "mock";
    }
    recordAudit("admin", "admin", "DELETE_SMTP_PROFILE", 200, `删除发件账号 ${target.username}`, opId);
    return { ...state.smtp, profiles: state.smtp.profiles.map((p) => ({ ...p })), op_id: opId };
  },
  async getMarkdownReport() {
    return buildMarkdownReport(state.targets);
  },
  async pushReportNow({ simMode = "ok" } = {}) {
    const opId = requireAdmin("PUSH_REPORT_NOW");
    if (simMode === "conflict") {
      recordAudit("admin", "admin", "PUSH_REPORT_NOW", 409, "并发推送防重锁拦截", opId);
      throw makeApiError(409, "已有推送进行中，本次请求已被防重锁拦截。", opId);
    }
    if (simMode === "timeout") {
      recordAudit("admin", "admin", "PUSH_REPORT_NOW", 504, "SMTP 超时，结果未知，禁止自动重试", opId);
      throw makeApiError(504, "SMTP 超时，结果未知，已禁止自动重试。", opId);
    }
    const md = buildMarkdownReport(state.targets);
    state.outbox.unshift({
      id: state.outbox.length + 1,
      op_id: opId,
      delivery_mode: "mock",
      status_code: 200,
      recipients: state.schedule.recipients.join(", "),
      subject: `服务器每日巡检报告（${nowStr()}）`,
      body_md: md,
      error: "",
      created_at: nowStr(),
    });
    recordAudit("admin", "admin", "PUSH_REPORT_NOW", 200, `手动推送成功（${state.schedule.recipients.length} 个收件人）`, opId);
    return { status: "sent", op_id: opId };
  },
  async listOutbox() {
    return { items: state.outbox.map((m) => ({ ...m })) };
  },
  async listAudits() {
    return { items: state.audits.map((a) => ({ ...a })) };
  },
};
