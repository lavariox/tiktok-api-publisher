#!/usr/bin/env python3
"""One-time OAuth authorization for the TikTok app (Conecta AI / TikTok API Publisher).

Steps:
  1. Copy .env.example to .env and fill TIKTOK_CLIENT_KEY / TIKTOK_CLIENT_SECRET.
  2. Run: python3 scripts/tiktok_oauth.py
  3. Approve TikTok's consent screen in the browser.
  4. Tokens are saved to scripts/tokens/<open_id>.json (auto-refreshed from then on).

The redirect URI must match EXACTLY the one registered in the app's Login Kit:
    http://localhost:8723/callback

Repeat once per TikTok account (H&S, EEX, each client).
"""
import http.server
import json
import os
import sys
import threading
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tiktok_tokens import TOKEN_URL, load_dotenv, save_tokens  # noqa: E402

AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
SCOPES = "user.info.basic,video.upload,video.publish"


def exchange_code(client_key, client_secret, code, redirect_uri):
    body = urllib.parse.urlencode({
        "client_key": client_key,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }).encode()
    req = urllib.request.Request(
        TOKEN_URL, data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def main():
    load_dotenv()
    client_key = os.environ.get("TIKTOK_CLIENT_KEY")
    client_secret = os.environ.get("TIKTOK_CLIENT_SECRET")
    redirect_uri = os.environ.get("TIKTOK_REDIRECT_URI", "http://localhost:8723/callback")
    if not client_key or not client_secret:
        raise SystemExit("Faltan TIKTOK_CLIENT_KEY / TIKTOK_CLIENT_SECRET. Copia .env.example a .env y completalo.")

    state = os.urandom(8).hex()
    params = {
        "client_key": client_key,
        "scope": SCOPES,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "state": state,
    }
    url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    code_holder = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if q.get("state", [""])[0] != state:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"state mismatch")
                return
            code_holder["code"] = q.get("code", [""])[0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write("Autorizado. Puedes cerrar esta ventana y volver a la terminal.".encode())
        def log_message(self, *args):
            pass

    parsed = urllib.parse.urlparse(redirect_uri)
    port = parsed.port or 8723
    server = http.server.HTTPServer(("127.0.0.1", port), Handler)

    print("Abriendo el navegador para autorizar en TikTok...")
    print("Si no se abre solo, pega este enlace:\n")
    print(url + "\n")
    webbrowser.open(url)
    server.handle_request()  # single callback request, then exit

    code = code_holder.get("code")
    if not code:
        raise SystemExit("No se recibio el codigo de autorizacion.")
    data = exchange_code(client_key, client_secret, code, redirect_uri)
    if "access_token" not in data:
        raise SystemExit(f"Fallo el intercambio de tokens: {data}")
    path = save_tokens(data)
    print(f"OK. Tokens guardados en {path} para open_id={data.get('open_id')}.")
    print("El refresco es automatico desde ahora.")


if __name__ == "__main__":
    main()
