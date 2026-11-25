import React, { useCallback, useEffect, useState } from "react";
import {
  apiClient,
  clearSession,
  detectBackendAvailability,
  getSavedSession,
  isPreviewFallbackMode,
} from "./api/client.js";
import ConfirmModal from "./components/ConfirmModal.jsx";
import CustomSelect from "./components/CustomSelect.jsx";
import ImportModal from "./components/ImportModal.jsx";
import LoginModal from "./components/LoginModal.jsx";
import ServerModal from "./components/ServerModal.jsx";
import SmtpConfigModal from "./components/SmtpConfigModal.jsx";
import ToastCard from "./components/ToastCard.jsx";
import SchedulePage from "./pages/SchedulePage.jsx";
import ServersPage from "./pages/ServersPage.jsx";
import { downloadBlob } from "./utils/format.js";

function readHashRoute() {
  return window.location.hash.replace(/^#\/?/, "") === "schedule" ? "schedule" : "servers";
}

function errorTitleByStatus(status) {
  if (status === 401) return "需要管理员登录";
  if (status === 403) return "当前账号无操作权限";
  if (status === 409) return "任务正在执行中";
  if (status === 504) return "目标响应超时";
  return "操作未能完成";
}

export default function App() {
  const [route, setRoute] = useState(readHashRoute);
  const [previewMode, setPreviewMode] = useState(false);
  const [previewRole, setPreviewRole] = useState("admin");
  const [sessionUser, setSessionUser] = useState(() => getSavedSession().user);

  const [targets, setTargets] = useState([]);
  const [schedule, setSchedule] = useState({
    enabled: true,
    push_time: "09:00",
    recipients: ["ops-oncall@corp.local", "sre-lead@corp.local"],
    smtp_mode: "mock",
  });
  const [smtpConfig, setSmtpConfig] = useState({
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
  });
  const [outbox, setOutbox] = useState([]);
  const [audits, setAudits] = useState([]);

  const [toast, setToast] = useState(null);
  const [inspectingAll, setInspectingAll] = useState(false);
  const [probingId, setProbingId] = useState(null);

  const [serverModal, setServerModal] = useState({ open: false, item: null });
  const [importOpen, setImportOpen] = useState(false);
  const [smtpOpen, setSmtpOpen] = useState(false);
  const [loginOpen, setLoginOpen] = useState(false);
  const [confirmState, setConfirmState] = useState({
    open: false,
    title: "",
    description: "",
    detail: "",
    isReportPreview: false,
    onConfirm: null,
  });

  const showToast = useCallback((arg1, arg2) => {
    if (typeof arg1 === "object" && arg1 !== null) {
      setToast({ id: Date.now() + Math.random(), ...arg1 });
      return;
    }
    setToast({ id: Date.now() + Math.random(), type: arg1, msg: arg2 });
  }, []);

  const clearToast = useCallback(() => setToast(null), []);

  const refreshAll = useCallback(async () => {
    const [tRes, sRes, smtpRes, oRes, aRes] = await Promise.all([
      apiClient.listTargets(),
      apiClient.getSchedule(),
      apiClient.getSmtpConfig(),
      apiClient.listOutbox(),
      apiClient.listAudits(),
    ]);
    setTargets(tRes.items || []);
    setSchedule(sRes);
    setSmtpConfig(smtpRes);
    setOutbox(oRes.items || []);
    setAudits(aRes.items || []);
  }, []);

  const initConnection = useCallback(async () => {
    await detectBackendAvailability();
    setPreviewMode(isPreviewFallbackMode());
    try {
      await refreshAll();
    } catch (err) {
      showToast({
        type: "err",
        title: "页面数据加载失败",
        msg: err.message || "无法获取服务器列表与配置，请稍后重试。",
      });
    }
  }, [refreshAll, showToast]);

  useEffect(() => {
    initConnection();
  }, [initConnection]);

  useEffect(() => {
    const onHash = () => setRoute(readHashRoute());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const switchRoute = (nextRoute) => {
    window.location.hash = `#/${nextRoute}`;
    setRoute(nextRoute);
  };

  const handleApiError = useCallback(
    async (err, customTitle) => {
      showToast({
        type: err.status === 409 ? "warn" : "err",
        title: customTitle || errorTitleByStatus(err.status),
        msg: err.message,
        opId: err.opId || "",
      });
      try {
        await refreshAll();
      } catch {
        // 忽略二次刷新异常
      }
    },
    [refreshAll, showToast]
  );

  const handlePreviewRoleChange = (role) => {
    setPreviewRole(role);
    apiClient.setPreviewRole(role);
    const labelMap = {
      admin: "已切换为管理员（admin），当前拥有全部巡检、导入与推送权限。",
      viewer: "已切换为只读成员（viewer），仅可查看与导出，写操作将被拦截。",
      anon: "已切换为未登录状态，发起写操作时将模拟未认证拦截。",
    };
    showToast({ type: role === "admin" ? "ok" : "warn", title: "验收身份已切换", msg: labelMap[role] });
  };

  const handleLogin = async (username, secret) => {
    const data = await apiClient.login(username, secret);
    setSessionUser({ username: data.username, role: data.role, smtp_mode: data.smtp_mode });
    showToast({
      type: "ok",
      title: "登录成功",
      msg: `欢迎回来，${data.username}（当前权限：${data.role === "admin" ? "管理员" : "只读成员"}）。`,
    });
    await refreshAll();
  };

  const handleLogout = () => {
    clearSession();
    setSessionUser(null);
    showToast({
      type: "warn",
      title: "已退出登录",
      msg: "当前处于未登录状态，发起巡检、变更配置或推送邮件前需重新登录。",
    });
  };

  const handleSaveTarget = async (payload, editId) => {
    try {
      if (editId != null) {
        const res = await apiClient.updateTarget(editId, payload);
        showToast({
          type: "ok",
          title: "目标主机已更新",
          msg: `已更新 ${payload.host}（${payload.address}）的连接配置，下次巡检将按新配置采集。`,
          opId: res.op_id,
        });
      } else {
        const res = await apiClient.createTarget(payload);
        showToast({
          type: "ok",
          title: "新主机已纳管",
          msg: `${payload.host}（${payload.address}）已加入巡检列表，当前为待检测状态，点击「检测」即可采集实时指标。`,
          opId: res.op_id,
        });
      }
      setServerModal({ open: false, item: null });
      await refreshAll();
    } catch (err) {
      await handleApiError(err);
      throw err;
    }
  };

  const handleDeleteRequest = (target) => {
    setConfirmState({
      open: true,
      title: "确认移除目标服务器",
      description: "移除后该主机将不再参与日常巡检与报告汇总（取消不会发出任何请求）：",
      detail: `${target.host} (${target.address}) ｜ ${target.type} / ${target.vendor} ｜ ${target.collector_type}`,
      isReportPreview: false,
      onConfirm: async () => {
        setConfirmState((s) => ({ ...s, open: false }));
        try {
          const res = await apiClient.deleteTarget(target.id);
          showToast({
            type: "ok",
            title: "目标主机已移除",
            msg: `已将 ${target.host} 从巡检列表中删除，本次变更已记入审计。`,
            opId: res.op_id,
          });
          await refreshAll();
        } catch (err) {
          await handleApiError(err);
        }
      },
    });
  };

  const handleInspectAll = async () => {
    setInspectingAll(true);
    try {
      const res = await apiClient.inspectAll();
      const latestItems = res.items || [];
      const failedHosts = latestItems
        .filter((s) => s.probe_status === "TIMEOUT" || s.probe_status === "UNREACHABLE")
        .map((s) => s.host);
      const highHosts = latestItems.filter((s) => s.probe_status === "HIGH_LOAD").map((s) => s.host);

      if (failedHosts.length === 0 && highHosts.length === 0) {
        showToast({
          type: "ok",
          title: "全量巡检完成",
          msg: `全部 ${res.total} 台主机采集完毕，当前均运行平稳。`,
          opId: res.op_id,
        });
      } else {
        const details = [];
        if (failedHosts.length > 0) {
          details.push(`${failedHosts.length} 台连接异常（${failedHosts.slice(0, 2).join("、")}${failedHosts.length > 2 ? " 等" : ""}，已自动隔离）`);
        }
        if (highHosts.length > 0) {
          details.push(`${highHosts.length} 台负载偏高（${highHosts.slice(0, 2).join("、")}${highHosts.length > 2 ? " 等" : ""}）`);
        }
        showToast({
          type: "warn",
          title: "全量巡检完成（发现需关注主机）",
          msg: `共检测 ${res.total} 台主机，${res.succeeded} 台获取成功；其中 ${details.join("，")}。`,
          opId: res.op_id,
        });
      }
      await refreshAll();
    } catch (err) {
      await handleApiError(err);
    } finally {
      setInspectingAll(false);
    }
  };

  const handleInspectOne = async (target) => {
    setProbingId(target.id);
    try {
      const res = await apiClient.inspectOne(target.id);
      const item = res.item;
      if (item.probe_status === "HIGH_LOAD") {
        showToast({
          type: "warn",
          title: "检测到主机负载偏高",
          msg: `${item.host} 当前 CPU ${item.cpu}%、可用内存 ${item.mem_free} / ${item.mem_total} GB，建议及时排查高占用进程。`,
          opId: res.op_id,
        });
      } else if (item.probe_status === "WARN") {
        showToast({
          type: "warn",
          title: "主机负载需留意",
          msg: `${item.host} 指标已刷新：CPU ${item.cpu}%、可用内存 ${item.mem_free} / ${item.mem_total} GB，接近告警水位。`,
          opId: res.op_id,
        });
      } else {
        showToast({
          type: "ok",
          title: "实时状态已更新",
          msg: `${item.host} 运行正常，当前 CPU ${item.cpu}%，可用内存 ${item.mem_free} / ${item.mem_total} GB。`,
          opId: res.op_id,
        });
      }
      await refreshAll();
    } catch (err) {
      await handleApiError(err, err.status === 504 ? "主机连接超时" : undefined);
    } finally {
      setProbingId(null);
    }
  };

  const handleImportPreview = async (payload) => {
    try {
      return await apiClient.previewImport(payload);
    } catch (err) {
      await handleApiError(err);
      throw err;
    }
  };

  const handleImportCommit = async (payload) => {
    try {
      const res = await apiClient.commitImport(payload);
      setImportOpen(false);
      const summaryParts = [];
      if (res.added) summaryParts.push(`新增 ${res.added} 台`);
      if (res.updated) summaryParts.push(`覆盖更新 ${res.updated} 台`);
      if (res.skipped) summaryParts.push(`跳过重名 ${res.skipped} 台`);
      showToast({
        type: "ok",
        title: "批量导入完成",
        msg: `已完成目标导入（${summaryParts.join("，") || "无变更"}）。新纳管主机当前为待检测状态，点击「立即全量巡检」即可采集实时指标。`,
        opId: res.op_id,
      });
      await refreshAll();
    } catch (err) {
      await handleApiError(err);
      throw err;
    }
  };

  const handleSaveSchedule = async (payload) => {
    try {
      const res = await apiClient.updateSchedule(payload);
      showToast({
        type: "ok",
        title: payload.enabled ? "定时推送规则已生效" : "每日自动推送已暂停",
        msg: payload.enabled
          ? `系统将在每天 ${payload.push_time} 自动执行全量巡检，并将报告发送给 ${payload.recipients.length} 位收件人。`
          : "已暂停每日自动巡检任务，你仍可随时手动发起巡检或立即推送。",
        opId: res.op_id,
      });
      await refreshAll();
    } catch (err) {
      await handleApiError(err);
    }
  };

  const handleSaveSmtpConfig = async (payload) => {
    try {
      const res = await apiClient.updateSmtpConfig(payload);
      setSmtpOpen(false);
      showToast({
        type: "ok",
        title: "发件人邮箱已加密存档并启用",
        msg: `已保存 ${payload.username}（${payload.host}:${payload.port}）并设为当前发件通道，下次直接在下拉框选择即可使用。`,
        opId: res.op_id,
      });
      await refreshAll();
    } catch (err) {
      await handleApiError(err);
      throw err;
    }
  };

  const handleSelectSmtpProfile = async (profileId) => {
    try {
      const res = await apiClient.activateSmtpProfile(profileId);
      if (profileId === 0) {
        showToast({
          type: "ok",
          title: "已切换为本地模拟收件箱",
          msg: "已暂停外部发信，已保存的发件邮箱账号仍安全保留在下拉列表中。",
          opId: res.op_id,
        });
      } else {
        showToast({
          type: "ok",
          title: "发件人邮箱已切换",
          msg: `当前发件通道已切换为 ${res.username}（${res.host}:${res.port}），免重启立即生效。`,
          opId: res.op_id,
        });
      }
      await refreshAll();
    } catch (err) {
      await handleApiError(err);
    }
  };

  const handleDeleteSmtpProfile = async (profile) => {
    try {
      const res = await apiClient.deleteSmtpProfile(profile.id);
      showToast({
        type: "ok",
        title: "已删除发件邮箱存档",
        msg: `已移除 ${profile.username}（${profile.host}）及其加密授权码。`,
        opId: res.op_id,
      });
      await refreshAll();
    } catch (err) {
      await handleApiError(err);
    }
  };

  const handleDownloadMarkdown = async () => {
    try {
      const md = await apiClient.getMarkdownReport();
      const today = new Date().toISOString().slice(0, 10);
      downloadBlob(`ops-inspection-${today}.md`, md, "text/markdown;charset=utf-8");
      showToast({
        type: "ok",
        title: "巡检报告已导出",
        msg: "最新巡检汇总报告已下载至本地。",
      });
    } catch (err) {
      await handleApiError(err);
    }
  };

  const handleRequestPush = async (simMode) => {
    try {
      const md = await apiClient.getMarkdownReport();
      const count = (schedule.recipients || []).length;
      setConfirmState({
        open: true,
        title: "确认立即推送最新巡检报告",
        description: `即将发送给 ${count} 位收件人：${(schedule.recipients || []).join("、")}`,
        detail: md,
        isReportPreview: true,
        onConfirm: async () => {
          setConfirmState((s) => ({ ...s, open: false }));
          try {
            const res = await apiClient.pushReportNow({ simMode });
            const isRealSmtp = (res.delivery_mode || smtpConfig.mode || schedule.smtp_mode) === "smtp" && !previewMode;
            showToast({
              type: "ok",
              title: isRealSmtp ? "巡检报告已发送" : "报告已投递至模拟收件箱",
              msg: isRealSmtp
                ? `已通过发件邮箱（${smtpConfig.host || "SMTP"}）发送至 ${count} 位收件人邮箱，请查收邮件。`
                : "最新巡检报告已写入下方发送记录（当前为本地模拟模式，未连接外部邮箱服务器）。",
              opId: res.op_id,
            });
            await refreshAll();
          } catch (err) {
            await handleApiError(err, err.status === 504 ? "邮件服务响应超时" : undefined);
          }
        },
      });
    } catch (err) {
      await handleApiError(err);
    }
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar-inner">
          <div className="topbar-left">
            <a
              className="brand"
              href="#/servers"
              onClick={(e) => {
                e.preventDefault();
                switchRoute("servers");
              }}
            >
              <div className="brand-mark" aria-hidden="true">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="2" y="3" width="20" height="7" rx="1" />
                  <rect x="2" y="14" width="20" height="7" rx="1" />
                  <line x1="6" y1="6.5" x2="6.01" y2="6.5" />
                  <line x1="6" y1="17.5" x2="6.01" y2="17.5" />
                </svg>
              </div>
              <span className="brand-title">智能服务器巡检系统</span>
            </a>

            <nav className="nav-links" aria-label="主页面切换">
              <button
                className={`nav-link ${route === "servers" ? "active" : ""}`}
                type="button"
                onClick={() => switchRoute("servers")}
              >
                服务器巡检
              </button>
              <button
                className={`nav-link ${route === "schedule" ? "active" : ""}`}
                type="button"
                onClick={() => switchRoute("schedule")}
              >
                定时推送
              </button>
            </nav>
          </div>

          {previewMode ? (
            <div className="role-control" title="P4a 前端验收模式：切换身份验证权限边界">
              <label htmlFor="role-select">验收身份</label>
              <CustomSelect
                id="role-select"
                size="sm"
                align="right"
                minWidth={172}
                value={previewRole}
                onChange={handlePreviewRoleChange}
                options={[
                  { value: "admin", label: "管理员 · admin", desc: "可登记、导入、巡检与推送", dot: "ok" },
                  { value: "viewer", label: "只读成员 · viewer", desc: "仅查看与导出，写操作拦截", dot: "warn" },
                  { value: "anon", label: "未登录访客", desc: "发起写操作将要求登录", dot: "crit" },
                ]}
              />
            </div>
          ) : (
            <div className="role-control">
              {sessionUser ? (
                <>
                  <span title={`当前权限：${sessionUser.role === "admin" ? "管理员" : "只读成员"}`}>
                    已登录：<strong className="mono">{sessionUser.username}</strong>
                  </span>
                  <button className="btn btn-sm" type="button" onClick={handleLogout}>
                    退出
                  </button>
                </>
              ) : (
                <>
                  <span>未登录</span>
                  <button className="btn btn-primary btn-sm" type="button" onClick={() => setLoginOpen(true)}>
                    登录
                  </button>
                </>
              )}
            </div>
          )}
        </div>
      </header>

      {previewMode && (
        <div className="mode-banner">
          <div className="mode-banner-inner">
            <span>
              <strong>P4a 前端实机验收模式：</strong>当前仅启动了 React 前端（后端将在你确认前端通过后的 P4b 实现），所有页面交互、IP 导入预览、时间选择器与异常拦截均可直接点验。
            </span>
            <button className="btn btn-sm" type="button" onClick={initConnection}>
              重新检测后端连接
            </button>
          </div>
        </div>
      )}

      <ToastCard toast={toast} onClose={clearToast} />

      {route === "servers" ? (
        <ServersPage
          targets={targets}
          inspectingAll={inspectingAll}
          probingId={probingId}
          onOpenAdd={() => setServerModal({ open: true, item: null })}
          onOpenEdit={(item) => setServerModal({ open: true, item })}
          onOpenImport={() => setImportOpen(true)}
          onDeleteRequest={handleDeleteRequest}
          onInspectAll={handleInspectAll}
          onInspectOne={handleInspectOne}
          onToast={showToast}
        />
      ) : (
        <SchedulePage
          schedule={schedule}
          smtpConfig={smtpConfig}
          outbox={outbox}
          audits={audits}
          previewMode={previewMode}
          onSaveSchedule={handleSaveSchedule}
          onSelectSmtpProfile={handleSelectSmtpProfile}
          onOpenSmtpConfig={() => setSmtpOpen(true)}
          onRequestPush={handleRequestPush}
          onDownloadMarkdown={handleDownloadMarkdown}
          onToast={showToast}
        />
      )}

      <ServerModal
        open={serverModal.open}
        initialItem={serverModal.item}
        onClose={() => setServerModal({ open: false, item: null })}
        onSave={handleSaveTarget}
      />

      <ImportModal
        open={importOpen}
        onClose={() => setImportOpen(false)}
        onPreview={handleImportPreview}
        onCommit={handleImportCommit}
        onToast={showToast}
      />

      <ConfirmModal
        open={confirmState.open}
        title={confirmState.title}
        description={confirmState.description}
        detail={confirmState.detail}
        isReportPreview={confirmState.isReportPreview}
        onCancel={() => setConfirmState((s) => ({ ...s, open: false }))}
        onConfirm={() => confirmState.onConfirm && confirmState.onConfirm()}
      />

      <SmtpConfigModal
        open={smtpOpen}
        smtpConfig={smtpConfig}
        onClose={() => setSmtpOpen(false)}
        onSave={handleSaveSmtpConfig}
        onDeleteProfile={handleDeleteSmtpProfile}
      />

      <LoginModal open={loginOpen} onClose={() => setLoginOpen(false)} onLogin={handleLogin} />
    </div>
  );
}
