"""应用配置加载与生产安全 Fail-Fast 校验（纯 Python 标准库）。"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

PLACEHOLDER_HINTS = ("changeme", "example", "placeholder", "your_", "dummy")


def load_dotenv_file(env_path: Path) -> None:
    """轻量加载 .env 文件到 os.environ（不覆盖进程已显式设置的环境变量）。"""
    if not env_path.is_file():
        return
    for raw in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


def _is_weak_secret(value: str) -> bool:
    low = (value or "").strip().lower()
    if len(low) < 12:
        return True
    return any(hint in low for hint in PLACEHOLDER_HINTS)


@dataclass
class Settings:
    app_env: str = "development"
    auth_secret: str = ""
    credential_master_key: str = ""
    admin_username: str = "admin"
    admin_cred: str = ""
    viewer_username: str = "viewer"
    viewer_cred: str = ""
    cors_origins: list[str] = field(default_factory=list)
    db_path: Path = Path("ops_inspect.db")
    ssh_keys_dir: Path = Path("ssh_keys")
    ssh_key_map: dict[str, str] = field(default_factory=dict)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    smtp_from: str = "ops-inspect@corp.local"
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    smtp_timeout_seconds: int = 10
    disable_scheduler: bool = False
    ssh_strict_host_key: bool = True
    max_outbox_rows: int = 500
    max_audit_rows: int = 2000

    @property
    def effective_master_key(self) -> str:
        return self.credential_master_key.strip() or self.auth_secret

    @property
    def smtp_mode(self) -> str:
        return "smtp" if self.smtp_host.strip() else "mock"

    def validate_production_security(self) -> None:
        """生产模式下若缺失强密钥/强口令或放开通配 CORS，立即 Fail-Fast 拒启。"""
        if self.app_env.lower() != "production":
            return

        problems: list[str] = []
        if _is_weak_secret(self.auth_secret):
            problems.append("AUTH_SECRET 缺失、不足 12 位或仍为占位符")
        if self.credential_master_key.strip() and _is_weak_secret(self.credential_master_key):
            problems.append("CREDENTIAL_MASTER_KEY 不足 12 位或仍为占位符")
        if _is_weak_secret(self.admin_cred):
            problems.append("ADMIN_PASSWORD 缺失、不足 12 位或仍为占位符")
        if _is_weak_secret(self.viewer_cred):
            problems.append("VIEWER_PASSWORD 缺失、不足 12 位或仍为占位符")
        if any(origin.strip() == "*" for origin in self.cors_origins):
            problems.append("CORS_ORIGINS 禁止使用通配符 *")

        if problems:
            raise RuntimeError("生产安全校验失败（Fail-Fast 拒启）：" + "；".join(problems))


def load_settings(env_file: Path | None = None) -> Settings:
    """从环境变量（可选 .env）构造并校验配置。"""
    if env_file is not None:
        load_dotenv_file(env_file)
    else:
        project_root = Path(__file__).resolve().parents[2]
        load_dotenv_file(project_root / ".env")

    app_env = os.environ.get("APP_ENV", "development").strip().lower() or "development"
    is_dev = app_env != "production"

    # 开发态允许使用显式占位值便于开箱运行；生产态不提供任何回退默认凭据
    auth_secret = os.environ.get("AUTH_SECRET", "changeme_dev_auth_secret_key" if is_dev else "")
    admin_cred = os.environ.get("ADMIN_PASSWORD", "changeme_admin_2026" if is_dev else "")
    viewer_cred = os.environ.get("VIEWER_PASSWORD", "changeme_viewer_2026" if is_dev else "")

    cors_raw = os.environ.get(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8080",
    )
    cors_origins = [o.strip() for o in cors_raw.split(",") if o.strip()]

    default_db = Path(__file__).resolve().parents[2] / "ops_inspect.db"
    db_path = Path(os.environ.get("DB_PATH", str(default_db)))
    ssh_keys_dir = Path(os.environ.get("SSH_KEYS_DIR", str(Path(__file__).resolve().parents[2] / "ssh_keys")))

    ssh_key_map: dict[str, str] = {}
    map_raw = os.environ.get("SSH_KEY_MAP_JSON", "").strip()
    if map_raw:
        try:
            parsed = json.loads(map_raw)
            if isinstance(parsed, dict):
                ssh_key_map = {str(k): str(v) for k, v in parsed.items()}
        except json.JSONDecodeError:
            ssh_key_map = {}

    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_ssl_env = os.environ.get("SMTP_USE_SSL", "").strip().lower()
    smtp_use_ssl = smtp_ssl_env in ("1", "true", "yes") or (smtp_ssl_env == "" and smtp_port == 465)

    strict_hk_env = os.environ.get("SSH_STRICT_HOST_KEY", "").strip().lower()
    if strict_hk_env in ("1", "true", "yes"):
        ssh_strict_host_key = True
    elif strict_hk_env in ("0", "false", "no"):
        ssh_strict_host_key = False
    else:
        # 生产环境默认强制校验 known_hosts，防止静默降级 AutoAddPolicy
        ssh_strict_host_key = not is_dev

    settings = Settings(
        app_env=app_env,
        auth_secret=auth_secret,
        credential_master_key=os.environ.get("CREDENTIAL_MASTER_KEY", "").strip(),
        admin_username=os.environ.get("ADMIN_USERNAME", "admin").strip() or "admin",
        admin_cred=admin_cred,
        viewer_username=os.environ.get("VIEWER_USERNAME", "viewer").strip() or "viewer",
        viewer_cred=viewer_cred,
        cors_origins=cors_origins,
        db_path=db_path,
        ssh_keys_dir=ssh_keys_dir,
        ssh_key_map=ssh_key_map,
        smtp_host=os.environ.get("SMTP_HOST", "").strip(),
        smtp_port=smtp_port,
        smtp_user=os.environ.get("SMTP_USER", "").strip(),
        smtp_pass=os.environ.get("SMTP_PASS", "").strip(),
        smtp_from=os.environ.get("SMTP_FROM", "").strip() or os.environ.get("SMTP_USER", "ops-inspect@corp.local"),
        smtp_use_tls=os.environ.get("SMTP_USE_TLS", "true").strip().lower() in ("1", "true", "yes"),
        smtp_use_ssl=smtp_use_ssl,
        smtp_timeout_seconds=max(1, int(os.environ.get("SMTP_TIMEOUT_SECONDS", "10"))),
        disable_scheduler=os.environ.get("DISABLE_SCHEDULER", "0").strip().lower() in ("1", "true", "yes"),
        ssh_strict_host_key=ssh_strict_host_key,
        max_outbox_rows=max(50, int(os.environ.get("MAX_OUTBOX_ROWS", "500"))),
        max_audit_rows=max(100, int(os.environ.get("MAX_AUDIT_ROWS", "2000"))),
    )
    settings.validate_production_security()
    return settings
