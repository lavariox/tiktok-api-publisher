#!/usr/bin/env python3
"""Token storage + auto-refresh for the TikTok Content Posting API.

- Tokens are stored per TikTok account: scripts/tokens/<open_id>.json (mode 600).
- Access tokens last ~24h; refresh tokens ~365 days and rotate on each refresh.
- get_access_token() refreshes automatically when less than 1h of life remains.
"""
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
TOKENS_DIR = Path(__file__).resolve().parent / "tokens"
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


def load_dotenv():
    """Load KEY=VALUE pairs from the project .env (no external deps)."""
    if not ENV_FILE.exists():
        return
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _post_token(data: dict) -> dict:
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(
        TOKEN_URL, data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def token_path(open_id: str) -> Path:
    TOKENS_DIR.mkdir(parents=True, exist_ok=True)
    return TOKENS_DIR / f"{open_id}.json"


def list_accounts() -> list:
    if not TOKENS_DIR.exists():
        return []
    return sorted(p.stem for p in TOKENS_DIR.glob("*.json"))


def save_tokens(data: dict) -> Path:
    open_id = data.get("open_id")
    if not open_id:
        raise RuntimeError(f"Respuesta sin open_id: {data}")
    data = dict(data)
    data["saved_at"] = int(time.time())
    path = token_path(open_id)
    path.write_text(json.dumps(data, indent=2))
    os.chmod(path, 0o600)
    return path


def load_tokens(open_id: str) -> dict | None:
    path = token_path(open_id)
    if path.exists():
        return json.loads(path.read_text())
    return None


def refresh(client_key: str, client_secret: str, tokens: dict) -> dict:
    data = _post_token({
        "client_key": client_key,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
        "refresh_token": tokens["refresh_token"],
    })
    if "access_token" not in data:
        raise RuntimeError(f"Fallo el refresco de tokens: {data}")
    save_tokens(data)
    return data


def resolve_open_id(open_id: str | None = None) -> str:
    if open_id:
        return open_id
    accounts = list_accounts()
    if len(accounts) == 1:
        return accounts[0]
    if not accounts:
        raise RuntimeError("No hay cuentas autorizadas. Corre scripts/tiktok_oauth.py primero.")
    raise RuntimeError(
        f"Hay varias cuentas autorizadas {accounts}. Indica una con TIKTOK_OPEN_ID o el parametro open_id.")


def get_access_token(client_key: str, client_secret: str, open_id: str | None = None) -> str:
    open_id = resolve_open_id(open_id)
    tokens = load_tokens(open_id)
    if not tokens:
        raise RuntimeError(f"No hay tokens para {open_id}. Corre scripts/tiktok_oauth.py.")
    saved_at = tokens.get("saved_at", 0)
    expires_in = tokens.get("expires_in", 0)
    if time.time() > saved_at + expires_in - 3600:  # refresh 1h before expiry
        tokens = refresh(client_key, client_secret, tokens)
    return tokens["access_token"]
