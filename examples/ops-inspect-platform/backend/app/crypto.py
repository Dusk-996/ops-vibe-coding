"""敏感凭据对称认证加密工具（基于 cryptography.fernet.Fernet）。"""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

ENC_PREFIX = "v1:"


def _derive_fernet_key(master_secret: str) -> bytes:
    digest = hashlib.sha256(master_secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt_secret(plaintext: str, master_secret: str) -> str:
    if not plaintext:
        return ""
    f = Fernet(_derive_fernet_key(master_secret))
    token = f.encrypt(plaintext.encode("utf-8")).decode("ascii")
    return f"{ENC_PREFIX}{token}"


def decrypt_secret(ciphertext: str, master_secret: str) -> str:
    if not ciphertext:
        return ""
    raw = ciphertext[len(ENC_PREFIX) :] if ciphertext.startswith(ENC_PREFIX) else ciphertext
    f = Fernet(_derive_fernet_key(master_secret))
    try:
        return f.decrypt(raw.encode("ascii")).decode("utf-8")
    except InvalidToken as exc:
        raise RuntimeError("SMTP 授权码解密失败，请检查主加密密钥配置或重新保存发件箱授权码。") from exc
