"""ops-inspect-demo 后端核心采集引擎与 mutating 全量安全测试套件。"""

from __future__ import annotations

import io
import logging
import smtplib
import socket
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.collector import SSH_READONLY_CMD, collect_local, collect_ssh
from app.config import Settings, load_settings
from app.mailer import MailerService
from app.main import create_app
from app.storage import Storage


def _build_test_settings(tmp_path: Path, **overrides) -> Settings:
    base = Settings(
        app_env="development",
        auth_secret="test_secret_key_for_pytest_01",
        admin_username="admin",
        admin_cred="admin_test_pass_2026",
        viewer_username="viewer",
        viewer_cred="viewer_test_pass_2026",
        cors_origins=["http://127.0.0.1:5173"],
        db_path=tmp_path / "test_ops_inspect.db",
        ssh_keys_dir=tmp_path / "ssh_keys",
        disable_scheduler=True,
    )
    for k, v in overrides.items():
        setattr(base, k, v)
    return base


def _login_headers(client: TestClient, username: str, password: str) -> dict[str, str]:
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    token = res.json()["token"]
    return {"Authorization": f"Bearer {token}"}


# ==================== 1. 核心主动采集引擎实测 ====================


def test_local_collect_real_system_metrics():
    """真实调用本机 local 采集驱动，验证返回物理内存、可用内存、CPU 核数与使用率。"""
    result = collect_local({"id": 1, "host": "local-real-node", "address": "127.0.0.1"}, sample_interval=0.1)
    assert result.ok is True
    assert result.mem_total is not None and result.mem_total > 0
    assert result.mem_free is not None and 0 <= result.mem_free <= result.mem_total
    assert result.cores is not None and result.cores >= 1
    assert result.cpu is not None and 0.0 <= result.cpu <= 100.0
    assert result.probe_status in ("OK", "WARN", "HIGH_LOAD")


def test_ssh_collect_readonly_whitelist_and_timeout_no_retry(tmp_path: Path):
    """验证 SSH 驱动只执行写死的只读命令并准确解析指标；遇到超时直接标 TIMEOUT 且仅调用 1 次不重试。"""
    settings = _build_test_settings(tmp_path)
    executed_cmds: list[str] = []

    class FakeSshClientOk:
        def connect(self, **_kwargs):
            return None

        def exec_command(self, cmd: str, timeout: float = 8.0):
            executed_cmds.append(cmd)
            sample = (
                "MemTotal: 134217728 kB\n"
                "MemAvailable: 67108864 kB\n"
                "---CORES---\n"
                "32\n"
                "---STAT1---\n"
                "cpu  1000 0 500 8500 0 0 0 0 0 0\n"
                "---STAT2---\n"
                "cpu  1400 0 600 9000 0 0 0 0 0 0\n"
            )
            return None, io.BytesIO(sample.encode("utf-8")), io.BytesIO(b"")

        def close(self):
            return None

    target = {
        "id": 10,
        "host": "prod-linux-01",
        "address": "10.10.2.10",
        "ssh_port": 22,
        "ssh_user": "ops-ro",
        "ssh_credential_ref": "prod-ro-key",
    }
    res_ok = collect_ssh(target, settings, ssh_client_factory=FakeSshClientOk)
    assert executed_cmds == [SSH_READONLY_CMD]
    assert res_ok.ok is True
    assert res_ok.mem_total == 128.0
    assert res_ok.mem_free == 64.0
    assert res_ok.cores == 32
    assert res_ok.cpu == 50.0
    assert res_ok.probe_status == "OK"

    # SSH 连接超时场景：必须返回 TIMEOUT 且仅尝试 1 次（绝不自动重试）
    connect_calls = {"count": 0}

    class FakeSshClientTimeout:
        def connect(self, **_kwargs):
            connect_calls["count"] += 1
            raise socket.timeout("SSH connect timed out")

        def close(self):
            return None

    res_to = collect_ssh(target, settings, ssh_client_factory=FakeSshClientTimeout)
    assert res_to.probe_status == "TIMEOUT"
    assert connect_calls["count"] == 1


def test_inspect_all_concurrent_timeout_isolation(tmp_path: Path):
    """全量巡检混合真实 local 本机、正常 mock 与超时节点，验证单台故障隔离不拖垮整批。"""
    settings = _build_test_settings(tmp_path)
    app = create_app(settings=settings, seed_defaults=True)
    client = TestClient(app)
    admin_headers = _login_headers(client, "admin", settings.admin_cred)

    res = client.post("/api/inspect/run", headers=admin_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 5
    assert body["succeeded"] == 4
    assert body["failed"] == 1

    by_host = {item["host"]: item for item in body["items"]}
    # 真实本机节点拿到非空真实内存/CPU
    assert by_host["ops-console-local"]["mem_total"] > 0
    assert by_host["ops-console-local"]["cores"] >= 1
    assert by_host["ops-console-local"]["probe_status"] in ("OK", "WARN", "HIGH_LOAD")
    # 异常节点被精准隔离为 TIMEOUT
    assert by_host["edge-gw-node-02"]["probe_status"] == "TIMEOUT"
    assert by_host["edge-gw-node-02"]["mem_total"] is None


# ==================== 2. 目标导入、导出与 CSV 防公式注入 ====================


def test_import_preview_commit_and_csv_formula_escape(tmp_path: Path):
    settings = _build_test_settings(tmp_path)
    app = create_app(settings=settings, seed_defaults=False)
    client = TestClient(app)
    admin_headers = _login_headers(client, "admin", settings.admin_cred)

    csv_content = "\n".join(
        [
            "host,address,type,vendor,collectorType,sshPort,sshUser,sshCredentialRef",
            "=EVIL_HOST,10.10.3.18,物理机,华为 TaiShan,ssh,22,ops-ro,prod-ro-key",
            "prod-web-08,10.10.4.25,虚拟机,阿里云 ECS,mock,,,",
        ]
    )

    prev = client.post(
        "/api/targets/import/preview",
        headers=admin_headers,
        json={"format": "csv", "content": csv_content, "policy": "skip"},
    )
    assert prev.status_code == 200
    assert len(prev.json()["valid_rows"]) == 2
    assert prev.json()["duplicate_count"] == 0

    commit1 = client.post(
        "/api/targets/import/commit",
        headers=admin_headers,
        json={"format": "csv", "content": csv_content, "policy": "skip"},
    )
    assert commit1.status_code == 200
    assert commit1.json()["added"] == 2

    # 再次按 skip 导入应全部跳过
    commit2 = client.post(
        "/api/targets/import/commit",
        headers=admin_headers,
        json={"format": "csv", "content": csv_content, "policy": "skip"},
    )
    assert commit2.json()["skipped"] == 2

    # 新导入目标初始状态为 PENDING
    items = client.get("/api/targets", headers=admin_headers).json()["items"]
    assert all(i["probe_status"] == "PENDING" for i in items)

    # 导出 CSV 含 UTF-8 BOM 且对 = 开头字段防公式注入转义
    exp = client.get("/api/targets/export?format=csv", headers=admin_headers)
    assert exp.status_code == 200
    raw_bytes = exp.content
    assert raw_bytes.startswith(b"\xef\xbb\xbf")
    assert "'=EVIL_HOST" in raw_bytes.decode("utf-8-sig")


# ==================== 3. mutating 强制 4 类负面安全用例 + 读接口鉴权 ====================


def test_security_401_anonymous_reads_blocked(tmp_path: Path):
    """401 未认证读接口测试：除 /health 外，全部 7 个只读接口匿名访问必须返回 401 且带 X-Op-Id；viewer 可正常读取。"""
    settings = _build_test_settings(tmp_path)
    app = create_app(settings=settings, seed_defaults=True)
    client = TestClient(app)

    assert client.get("/health").status_code == 200

    read_paths = [
        "/api/targets",
        "/api/targets/export?format=csv",
        "/api/schedule",
        "/api/smtp",
        "/api/reports/markdown",
        "/api/outbox",
        "/api/audits",
    ]
    for path in read_paths:
        resp = client.get(path)
        assert resp.status_code == 401, f"{path} 应拦截匿名访问"
        assert resp.headers.get("X-Op-Id")

    viewer_headers = _login_headers(client, "viewer", settings.viewer_cred)
    for path in read_paths:
        resp = client.get(path, headers=viewer_headers)
        assert resp.status_code == 200, f"viewer 应可读取 {path}"


def test_security_401_unauthorized_write_blocked(tmp_path: Path):
    """401 未认证负面测试：未携带 Token 调用所有写接口必须被拒绝且写入审计。"""
    settings = _build_test_settings(tmp_path)
    app = create_app(settings=settings, seed_defaults=True)
    client = TestClient(app)
    admin_headers = _login_headers(client, "admin", settings.admin_cred)

    assert client.post("/api/inspect/run").status_code == 401
    assert client.post("/api/reports/push").status_code == 401
    assert (
        client.put(
            "/api/schedule",
            json={"enabled": True, "push_time": "10:00", "recipients": ["ops@corp.local"]},
        ).status_code
        == 401
    )

    audits = client.get("/api/audits", headers=admin_headers).json()["items"]
    assert any(a["http_status"] == 401 and a["action"] == "INSPECT_ALL" for a in audits)


def test_security_403_viewer_forbidden_write_blocked(tmp_path: Path):
    """403 越权负面测试：viewer 只读角色可查看/导出，但任何写操作必须返回 403 并记审计。"""
    settings = _build_test_settings(tmp_path)
    app = create_app(settings=settings, seed_defaults=True)
    client = TestClient(app)
    viewer_headers = _login_headers(client, "viewer", settings.viewer_cred)

    assert client.get("/api/targets", headers=viewer_headers).status_code == 200
    assert client.get("/api/targets/export?format=json", headers=viewer_headers).status_code == 200

    assert client.post("/api/inspect/run", headers=viewer_headers).status_code == 403
    assert client.post("/api/reports/push", headers=viewer_headers).status_code == 403
    assert (
        client.post(
            "/api/targets",
            headers=viewer_headers,
            json={
                "host": "forbidden-host",
                "address": "10.0.0.9",
                "type": "物理机",
                "vendor": "戴尔 Dell",
                "collector_type": "mock",
            },
        ).status_code
        == 403
    )

    audits = client.get("/api/audits", headers=viewer_headers).json()["items"]
    assert any(a["http_status"] == 403 and a["actor"] == "viewer" for a in audits)


def test_security_409_concurrent_push_conflict(tmp_path: Path):
    """409 冲突防重负面测试：已有推送任务持有锁时，并发重复提交必须返回 409 Conflict。"""
    settings = _build_test_settings(tmp_path)
    app = create_app(settings=settings, seed_defaults=True)
    client = TestClient(app)
    admin_headers = _login_headers(client, "admin", settings.admin_cred)

    mailer: MailerService = app.state.mailer
    assert mailer._push_lock.acquire(blocking=False) is True
    try:
        res = client.post("/api/reports/push", headers=admin_headers)
        assert res.status_code == 409
    finally:
        mailer._push_lock.release()

    audits = client.get("/api/audits", headers=admin_headers).json()["items"]
    assert any(a["http_status"] == 409 and a["action"] == "PUSH_REPORT_NOW" for a in audits)


def test_security_504_smtp_timeout_no_retry(tmp_path: Path):
    """504 超时不重试负面测试：SMTP 发送超时必须立即返 504 且底层发送函数仅调用 1 次（禁止自动重试）。"""
    call_count = 0

    def timeout_smtp_sender(_settings, _recipients, _subject, _body_md, _body_html):
        nonlocal call_count
        call_count += 1
        raise socket.timeout("SMTP server timed out")

    settings = _build_test_settings(tmp_path, smtp_host="smtp.example.local", smtp_port=465, smtp_use_ssl=True)
    storage = Storage(settings.db_path, seed_defaults=True)
    mailer = MailerService(settings, storage, smtp_sender=timeout_smtp_sender)
    app = create_app(settings=settings, storage=storage, mailer=mailer)
    client = TestClient(app)
    admin_headers = _login_headers(client, "admin", settings.admin_cred)

    res = client.post("/api/reports/push", headers=admin_headers)
    assert res.status_code == 504
    assert call_count == 1  # 关键安全红线：超时不重试

    audits = client.get("/api/audits", headers=admin_headers).json()["items"]
    assert any(a["http_status"] == 504 and a["action"] == "PUSH_REPORT_NOW" for a in audits)


# ==================== 4. 生产 Fail-Fast 与定时幂等 ====================


def test_production_fail_fast_rejects_weak_secrets(monkeypatch, tmp_path: Path):
    """生产模式下缺失或使用占位符密钥/密码必须 Fail-Fast 拒启。"""
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("AUTH_SECRET", "changeme_weak")
    monkeypatch.setenv("ADMIN_PASSWORD", "123456")
    monkeypatch.setenv("VIEWER_PASSWORD", "123456")
    monkeypatch.setenv("DB_PATH", str(tmp_path / "prod.db"))

    with pytest.raises(RuntimeError, match="Fail-Fast"):
        load_settings(env_file=tmp_path / "nonexistent.env")


def test_scheduler_tick_idempotent_same_minute(tmp_path: Path):
    """定时任务到点先巡检再推送，同分钟内重复 tick 严格幂等防重发。"""
    settings = _build_test_settings(tmp_path)
    app = create_app(settings=settings, seed_defaults=True)
    sched = app.state.scheduler
    store: Storage = app.state.storage

    fixed_time = datetime(2026, 11, 25, 9, 0, 12)
    assert sched.tick_once(now_fn=lambda: fixed_time) is True
    assert sched.tick_once(now_fn=lambda: fixed_time) is False  # 同分钟幂等防重发
    assert len(store.list_outbox()) == 1


def test_smtp_web_config_encrypted_storage_and_hot_reload(tmp_path: Path):
    """模式 2 验证：网页热配 SMTP 仅 admin 可写、授权码 Fernet 加密存库永不回显、留空不覆盖、免重启热生效。"""
    sent_records: list[dict] = []

    def fake_smtp_sender(runtime_cfg, recipients, subject, _body_md, _body_html):
        sent_records.append(
            {
                "host": runtime_cfg.smtp_host,
                "port": runtime_cfg.smtp_port,
                "ssl": runtime_cfg.smtp_use_ssl,
                "user": runtime_cfg.smtp_user,
                "secret": runtime_cfg.smtp_pass,
                "recipients": recipients,
                "subject": subject,
            }
        )

    settings = _build_test_settings(tmp_path)  # 初始无 SMTP_HOST -> mock 模式
    storage = Storage(settings.db_path, seed_defaults=True)
    mailer = MailerService(settings, storage, smtp_sender=fake_smtp_sender)
    app = create_app(settings=settings, storage=storage, mailer=mailer)
    client = TestClient(app)

    admin_headers = _login_headers(client, "admin", settings.admin_cred)
    viewer_headers = _login_headers(client, "viewer", settings.viewer_cred)

    payload = {
        "enabled": True,
        "host": "smtp.qq.com",
        "port": 465,
        "security": "ssl",
        "username": "sender@qq.com",
        "auth_code": "qq_secret_auth_code_16",
        "from_addr": "sender@qq.com",
        "timeout_seconds": 10,
    }
    # 401 / 403 权限门禁校验
    assert client.put("/api/smtp", json=payload).status_code == 401
    assert client.put("/api/smtp", headers=viewer_headers, json=payload).status_code == 403

    # admin 保存热生效
    save_res = client.put("/api/smtp", headers=admin_headers, json=payload)
    assert save_res.status_code == 200
    body = save_res.json()
    assert body["mode"] == "smtp"
    assert body["has_auth_code"] is True
    assert "qq_secret_auth_code_16" not in save_res.text  # 绝不回显明文

    # 校验数据库存的是密文（绝不含明文）
    raw_db_cfg = storage.get_smtp_config()
    assert raw_db_cfg is not None
    assert raw_db_cfg["auth_code_enc"].startswith("v1:")
    assert "qq_secret_auth_code_16" not in raw_db_cfg["auth_code_enc"]

    # 留空 auth_code 再次修改端口，原加密授权码必须完整保留
    res2 = client.put(
        "/api/smtp",
        headers=admin_headers,
        json={**payload, "port": 465, "auth_code": ""},
    )
    assert res2.status_code == 200
    assert res2.json()["has_auth_code"] is True

    # 无需重启直接发起推送，应热生效走真实 SMTP 通道并解密出原授权码
    push_res = client.post("/api/reports/push", headers=admin_headers)
    assert push_res.status_code == 200
    assert push_res.json()["delivery_mode"] == "smtp"
    assert len(sent_records) == 1
    assert sent_records[0]["host"] == "smtp.qq.com"
    assert sent_records[0]["ssl"] is True
    assert sent_records[0]["secret"] == "qq_secret_auth_code_16"


def test_smtp_multi_profiles_save_switch_and_delete(tmp_path: Path):
    """验证多发件人账号加密存档、下拉一键热切换免重输授权码、切回模拟模式及安全删除。"""
    used_senders: list[tuple[str, str]] = []

    def fake_smtp_sender(runtime_cfg, _recipients, _subject, _body_md, _body_html):
        used_senders.append((runtime_cfg.smtp_user, runtime_cfg.smtp_pass))

    settings = _build_test_settings(tmp_path)
    storage = Storage(settings.db_path, seed_defaults=True)
    mailer = MailerService(settings, storage, smtp_sender=fake_smtp_sender)
    app = create_app(settings=settings, storage=storage, mailer=mailer)
    client = TestClient(app)

    admin_headers = _login_headers(client, "admin", settings.admin_cred)
    viewer_headers = _login_headers(client, "viewer", settings.viewer_cred)

    # 保存第 1 个发件人账号（QQ 邮箱）
    r1 = client.put(
        "/api/smtp",
        headers=admin_headers,
        json={
            "enabled": True,
            "host": "smtp.qq.com",
            "port": 465,
            "security": "ssl",
            "username": "ops1@qq.com",
            "auth_code": "qq_code_one_1234",
            "from_addr": "ops1@qq.com",
        },
    )
    assert r1.status_code == 200
    p1_id = r1.json()["active_profile_id"]

    # 保存第 2 个发件人账号（163 邮箱）
    r2 = client.put(
        "/api/smtp",
        headers=admin_headers,
        json={
            "enabled": True,
            "host": "smtp.163.com",
            "port": 465,
            "security": "ssl",
            "username": "ops2@163.com",
            "auth_code": "netease_code_two",
            "from_addr": "ops2@163.com",
        },
    )
    assert r2.status_code == 200
    assert len(r2.json()["profiles"]) == 2
    p2_id = r2.json()["active_profile_id"]
    assert p2_id != p1_id

    # 权限边界：未登录 401、viewer 403 不可切换或删除
    assert client.post(f"/api/smtp/profiles/{p1_id}/activate").status_code == 401
    assert client.post(f"/api/smtp/profiles/{p1_id}/activate", headers=viewer_headers).status_code == 403
    assert client.delete(f"/api/smtp/profiles/{p2_id}", headers=viewer_headers).status_code == 403

    # 一键切回第 1 个发件人（无需再填授权码），发信应自动使用第 1 个账号的原解密授权码
    sw = client.post(f"/api/smtp/profiles/{p1_id}/activate", headers=admin_headers)
    assert sw.status_code == 200
    assert sw.json()["username"] == "ops1@qq.com"
    assert client.post("/api/reports/push", headers=admin_headers).status_code == 200
    assert used_senders == [("ops1@qq.com", "qq_code_one_1234")]

    # 一键切回模拟收件箱（id=0），但已保存的 2 个发件箱依然保留在列表里
    mock_sw = client.post("/api/smtp/profiles/0/activate", headers=admin_headers)
    assert mock_sw.status_code == 200
    assert mock_sw.json()["mode"] == "mock"
    assert len(mock_sw.json()["profiles"]) == 2

    # 删除第 2 个发件箱存档
    del_res = client.delete(f"/api/smtp/profiles/{p2_id}", headers=admin_headers)
    assert del_res.status_code == 200
    assert len(del_res.json()["profiles"]) == 1


def test_report_summary_shows_only_abnormal_details():
    """验证巡检报告与 HTML 邮件采用总—分结构：详细展示异常主机，正常主机省略明细。"""
    from app.mailer import build_html_email, build_markdown_report

    sample_targets = [
        {"host": "ok-node-01", "address": "10.0.0.1", "type": "物理机", "vendor": "戴尔 Dell", "collector_type": "ssh", "mem_total": 64.0, "mem_free": 40.0, "cores": 16, "cpu": 20.0, "probe_status": "OK", "last_checked_at": "2026-11-25 22:00:00", "probe_error": ""},
        {"host": "bad-node-02", "address": "10.0.0.2", "type": "物理机", "vendor": "戴尔 Dell", "collector_type": "ssh", "mem_total": 64.0, "mem_free": 5.0, "cores": 16, "cpu": 92.0, "probe_status": "HIGH_LOAD", "last_checked_at": "2026-11-25 22:00:00", "probe_error": ""},
    ]
    md = build_markdown_report(sample_targets, timestamp="2026-11-25 22:00:00")
    html_body = build_html_email(sample_targets, timestamp="2026-11-25 22:00:00")

    assert "纳管服务器总数：2 台（正常 1 台 ｜ 异常/需关注 1 台）" in md
    assert "bad-node-02" in md
    assert "ok-node-01" not in md  # 正常主机不详展
    assert "bad-node-02" in html_body
    assert "ok-node-01" not in html_body


# ==================== 5. Ops Readiness 加固回归用例 ====================


def test_production_fail_fast_rejects_weak_master_key(monkeypatch, tmp_path: Path):
    """MINOR-01：独立配置 CREDENTIAL_MASTER_KEY 若弱于安全基线，生产模式必须 Fail-Fast 拒启。"""
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("AUTH_SECRET", "Strong_Auth_Secret_2026_9999")
    monkeypatch.setenv("CREDENTIAL_MASTER_KEY", "changeme")
    monkeypatch.setenv("ADMIN_PASSWORD", "Strong_Admin_Pass_2026!")
    monkeypatch.setenv("VIEWER_PASSWORD", "Strong_Viewer_Pass_2026!")
    monkeypatch.setenv("DB_PATH", str(tmp_path / "prod_mk.db"))

    with pytest.raises(RuntimeError, match="CREDENTIAL_MASTER_KEY"):
        load_settings(env_file=tmp_path / "nonexistent.env")


def test_ssh_strict_host_key_and_output_limit(tmp_path: Path):
    """MAJOR-02：严格模式缺少 known_hosts 必须拒连，不静默降级 AutoAddPolicy；超过 64KB 输出必须阻断。"""
    keys_dir = tmp_path / "ssh_keys"
    keys_dir.mkdir(parents=True, exist_ok=True)
    (keys_dir / "ro_key").write_text("DUMMY_KEY_CONTENT", encoding="utf-8")

    settings = _build_test_settings(tmp_path, ssh_keys_dir=keys_dir, ssh_strict_host_key=True)
    target = {
        "id": 99,
        "host": "prod-ssh-strict",
        "address": "10.10.9.9",
        "ssh_port": 22,
        "ssh_user": "ops-ro",
        "ssh_credential_ref": "ro_key",
    }
    res_no_kh = collect_ssh(target, settings)
    assert res_no_kh.probe_status == "UNREACHABLE"
    assert "known_hosts" in res_no_kh.probe_error

    # 验证超过 64KB 输出被安全截断拒收
    class OversizedSshClient:
        def connect(self, **_kwargs):
            return None

        def exec_command(self, _cmd: str, timeout: float = 8.0):
            return None, io.BytesIO(b"A" * 70000), io.BytesIO(b"")

        def close(self):
            return None

    res_big = collect_ssh(target, settings, ssh_client_factory=OversizedSshClient)
    assert res_big.probe_status == "UNREACHABLE"
    assert "ValueError" in res_big.probe_error


def test_scheduler_loop_error_logged_and_audited(tmp_path: Path, caplog):
    """MAJOR-03：后台调度轮询抛出非预期异常时，不得静默吞错，必须记标准日志与 500 审计。"""
    settings = _build_test_settings(tmp_path)
    app = create_app(settings=settings, seed_defaults=True)
    sched = app.state.scheduler
    store: Storage = app.state.storage

    def broken_tick():
        raise RuntimeError("simulated sqlite disk full")

    sched.tick_once = broken_tick  # type: ignore[method-assign]
    with caplog.at_level(logging.ERROR, logger="ops_inspect.scheduler"):
        sched._run_loop_iteration()

    assert any("后台定时调度轮询发生未预期异常" in rec.getMessage() for rec in caplog.records)
    audits = store.list_audits()
    assert any(a["action"] == "SCHEDULER_LOOP_ERROR" and a["http_status"] == 500 for a in audits)


def test_scheduler_shares_inspect_lock_with_manual_inspect(tmp_path: Path):
    """MINOR-02：手动全量巡检持有 inspect_lock 时，定时巡检必须跳过并记录 409 审计，绝不并发撞车。"""
    settings = _build_test_settings(tmp_path)
    app = create_app(settings=settings, seed_defaults=True)
    sched = app.state.scheduler
    store: Storage = app.state.storage
    lock = app.state.inspect_lock

    fixed_time = datetime(2026, 11, 25, 9, 0, 15)
    assert lock.acquire(blocking=False) is True
    try:
        assert sched.tick_once(now_fn=lambda: fixed_time) is False
    finally:
        lock.release()

    audits = store.list_audits()
    assert any(a["action"] == "SCHEDULED_INSPECT_AND_PUSH" and a["http_status"] == 409 for a in audits)
    assert len(store.list_outbox()) == 0


def test_smtp_error_sanitized_to_client(tmp_path: Path):
    """MINOR-03：SMTP 投递失败时向前端返回脱敏运维人话，不得透传底层敏感异常细节。"""

    def auth_fail_sender(_settings, _recipients, _subject, _body_md, _body_html):
        raise smtplib.SMTPAuthenticationError(535, b"INTERNAL_RELAY_SECRET_TOKEN_LEAK")

    settings = _build_test_settings(tmp_path, smtp_host="smtp.example.local", smtp_port=465, smtp_use_ssl=True)
    storage = Storage(settings.db_path, seed_defaults=True)
    mailer = MailerService(settings, storage, smtp_sender=auth_fail_sender)
    app = create_app(settings=settings, storage=storage, mailer=mailer)
    client = TestClient(app)
    admin_headers = _login_headers(client, "admin", settings.admin_cred)

    res = client.post("/api/reports/push", headers=admin_headers)
    assert res.status_code == 502
    assert "INTERNAL_RELAY_SECRET_TOKEN_LEAK" not in res.text
    assert "认证失败" in res.json()["detail"]


def test_storage_retention_pruning(tmp_path: Path):
    """MINOR-04：发件历史与审计表写入时自动按上限裁剪，防止 SQLite 无限膨胀。"""
    store = Storage(tmp_path / "prune.db", seed_defaults=False, max_outbox_rows=3, max_audit_rows=5)
    for i in range(6):
        store.add_outbox(
            op_id=f"op-m{i}",
            delivery_mode="mock",
            status_code=200,
            recipients="ops@corp.local",
            subject=f"subj-{i}",
            body_md="body",
        )
    for i in range(9):
        store.add_audit(
            op_id=f"op-a{i}",
            actor="admin",
            role="admin",
            action="TEST_PRUNE",
            http_status=200,
            detail=f"detail-{i}",
        )

    outbox_rows = store.list_outbox(limit=50)
    audit_rows = store.list_audits(limit=50)
    assert len(outbox_rows) == 3
    assert [r["subject"] for r in outbox_rows] == ["subj-5", "subj-4", "subj-3"]
    assert len(audit_rows) == 5
    assert [r["detail"] for r in audit_rows] == ["detail-8", "detail-7", "detail-6", "detail-5", "detail-4"]




