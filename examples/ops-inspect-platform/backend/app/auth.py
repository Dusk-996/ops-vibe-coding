"""HMAC-SHA256 轻量 Bearer Token 认证与双角色校验（纯 Python 标准库）。"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass

from .config import Settings

TOKEN_TTL_SECONDS = 24 * 3600


@dataclass(frozen=True)
class AuthUser:
    username: str
    role: str  # "admin" | "viewer"


def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64_decode(text: str) -> bytes:
    padding = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + padding)


def _sign(payload_b64: str, secret: str) -> str:
    mac = hmac.new(secret.encode("utf-8"), payload_b64.encode("ascii"), hashlib.sha256).digest()
    return _b64_encode(mac)


def authenticate_user(username: str, credential: str, settings: Settings) -> AuthUser | None:
    """使用恒定时间比对校验 admin / viewer 登录凭据。"""
    uname = (username or "").strip()
    cred = credential or ""
    if uname == settings.admin_username and settings.admin_cred and hmac.compare_digest(cred, settings.admin_cred):
        return AuthUser(username=uname, role="admin")
    if uname == settings.viewer_username and settings.viewer_cred and hmac.compare_digest(cred, settings.viewer_cred):
        return AuthUser(username=uname, role="viewer")
    return None


def create_token(user: AuthUser, secret: str, ttl_seconds: int = TOKEN_TTL_SECONDS) -> str:
    payload = {
        "sub": user.username,
        "role": user.role,
        "exp": int(time.time()) + ttl_seconds,
    }
    payload_b64 = _b64_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    sig = _sign(payload_b64, secret)
    return f"{payload_b64}.{sig}"


def verify_token(token: str, secret: str) -> AuthUser | None:
    if not token or "." not in token or not secret:
        return None
    parts = token.split(".", 1)
    if len(parts) != 2:
        return None
    payload_b64, sig = parts
    expected = _sign(payload_b64, secret)
    if not hmac.compare_digest(sig, expected):
        return None
    try:
        data = json.loads(_b64_decode(payload_b64).decode("utf-8"))
    except Exception:
        return None
    if int(data.get("exp", 0)) < int(time.time()):
        return None
    role = str(data.get("role", ""))
    sub = str(data.get("sub", ""))
    if role not in ("admin", "viewer") or not sub:
        return None
    return AuthUser(username=sub, role=role)
