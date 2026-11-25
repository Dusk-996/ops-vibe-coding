import { localPreviewAdapter } from "./localPreviewAdapter.js";

const TOKEN_STORAGE_KEY = "ops_inspect_token";
const USER_STORAGE_KEY = "ops_inspect_user";

let backendAvailable = true;

export function isPreviewFallbackMode() {
  return import.meta.env.DEV && !backendAvailable;
}

export async function detectBackendAvailability() {
  if (!import.meta.env.DEV) {
    backendAvailable = true;
    return true;
  }
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 1500);
  try {
    const res = await fetch("/health", { signal: ctrl.signal });
    backendAvailable = res.ok;
  } catch {
    backendAvailable = false;
  } finally {
    clearTimeout(timer);
  }
  return backendAvailable;
}

export function getSavedSession() {
  try {
    const token = localStorage.getItem(TOKEN_STORAGE_KEY) || "";
    const rawUser = localStorage.getItem(USER_STORAGE_KEY);
    const user = rawUser ? JSON.parse(rawUser) : null;
    return { token, user };
  } catch {
    return { token: "", user: null };
  }
}

export function saveSession(token, user) {
  localStorage.setItem(TOKEN_STORAGE_KEY, token);
  localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
}

export function clearSession() {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
  localStorage.removeItem(USER_STORAGE_KEY);
}

async function httpRequest(path, { method = "GET", body, expectText = false } = {}) {
  const { token } = getSavedSession();
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  if (body !== undefined) headers["Content-Type"] = "application/json";

  const res = await fetch(path, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  const opId = res.headers.get("X-Op-Id") || "";
  if (!res.ok) {
    let detail = `请求失败 (HTTP ${res.status})`;
    let errOpId = opId;
    try {
      const data = await res.json();
      if (data?.detail) detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
      if (data?.op_id) errOpId = data.op_id;
    } catch {
      // 忽略非 JSON 错误体
    }
    const err = new Error(detail);
    err.status = res.status;
    err.opId = errOpId;
    throw err;
  }

  return expectText ? res.text() : res.json();
}

export const apiClient = {
  setPreviewRole(role) {
    localPreviewAdapter.setPreviewRole(role);
  },
  getPreviewRole() {
    return localPreviewAdapter.getPreviewRole();
  },
  async login(username, password) {
    const data = await httpRequest("/api/auth/login", {
      method: "POST",
      body: { username, password },
    });
    saveSession(data.token, {
      username: data.username,
      role: data.role,
      smtp_mode: data.smtp_mode,
    });
    return data;
  },
  async listTargets() {
    if (isPreviewFallbackMode()) return localPreviewAdapter.listTargets();
    return httpRequest("/api/targets");
  },
  async createTarget(payload) {
    if (isPreviewFallbackMode()) return localPreviewAdapter.createTarget(payload);
    return httpRequest("/api/targets", { method: "POST", body: payload });
  },
  async updateTarget(id, payload) {
    if (isPreviewFallbackMode()) return localPreviewAdapter.updateTarget(id, payload);
    return httpRequest(`/api/targets/${id}`, { method: "PUT", body: payload });
  },
  async deleteTarget(id) {
    if (isPreviewFallbackMode()) return localPreviewAdapter.deleteTarget(id);
    return httpRequest(`/api/targets/${id}`, { method: "DELETE" });
  },
  async previewImport(payload) {
    if (isPreviewFallbackMode()) return localPreviewAdapter.previewImport(payload);
    return httpRequest("/api/targets/import/preview", { method: "POST", body: payload });
  },
  async commitImport(payload) {
    if (isPreviewFallbackMode()) return localPreviewAdapter.commitImport(payload);
    return httpRequest("/api/targets/import/commit", { method: "POST", body: payload });
  },
  async inspectAll() {
    if (isPreviewFallbackMode()) return localPreviewAdapter.inspectAll();
    return httpRequest("/api/inspect/run", { method: "POST" });
  },
  async inspectOne(id) {
    if (isPreviewFallbackMode()) return localPreviewAdapter.inspectOne(id);
    return httpRequest(`/api/inspect/${id}`, { method: "POST" });
  },
  async getSchedule() {
    if (isPreviewFallbackMode()) return localPreviewAdapter.getSchedule();
    return httpRequest("/api/schedule");
  },
  async updateSchedule(payload) {
    if (isPreviewFallbackMode()) return localPreviewAdapter.updateSchedule(payload);
    return httpRequest("/api/schedule", { method: "PUT", body: payload });
  },
  async getSmtpConfig() {
    if (isPreviewFallbackMode()) return localPreviewAdapter.getSmtpConfig();
    return httpRequest("/api/smtp");
  },
  async updateSmtpConfig(payload) {
    if (isPreviewFallbackMode()) return localPreviewAdapter.updateSmtpConfig(payload);
    return httpRequest("/api/smtp", { method: "PUT", body: payload });
  },
  async activateSmtpProfile(profileId) {
    if (isPreviewFallbackMode()) return localPreviewAdapter.activateSmtpProfile(profileId);
    return httpRequest(`/api/smtp/profiles/${profileId}/activate`, { method: "POST" });
  },
  async deleteSmtpProfile(profileId) {
    if (isPreviewFallbackMode()) return localPreviewAdapter.deleteSmtpProfile(profileId);
    return httpRequest(`/api/smtp/profiles/${profileId}`, { method: "DELETE" });
  },
  async getMarkdownReport() {
    if (isPreviewFallbackMode()) return localPreviewAdapter.getMarkdownReport();
    return httpRequest("/api/reports/markdown", { expectText: true });
  },
  async pushReportNow(opts = {}) {
    if (isPreviewFallbackMode()) return localPreviewAdapter.pushReportNow(opts);
    return httpRequest("/api/reports/push", { method: "POST" });
  },
  async listOutbox() {
    if (isPreviewFallbackMode()) return localPreviewAdapter.listOutbox();
    return httpRequest("/api/outbox");
  },
  async listAudits() {
    if (isPreviewFallbackMode()) return localPreviewAdapter.listAudits();
    return httpRequest("/api/audits");
  },
};
