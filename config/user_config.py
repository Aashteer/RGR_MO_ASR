"""Сохранение пользовательских настроек (HF токен)."""

from __future__ import annotations

from pathlib import Path

from config.settings import PROJECT_ROOT

TOKEN_FILE = PROJECT_ROOT / "config" / ".hf_token"


def load_hf_token() -> str:
    if TOKEN_FILE.exists():
        token = TOKEN_FILE.read_text(encoding="utf-8").strip()
        if token:
            return token
    import os
    return os.getenv("HF_TOKEN", "").strip()


def save_hf_token(token: str) -> None:
    token = token.strip()
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    if token:
        TOKEN_FILE.write_text(token, encoding="utf-8")
    elif TOKEN_FILE.exists():
        TOKEN_FILE.unlink(missing_ok=True)
