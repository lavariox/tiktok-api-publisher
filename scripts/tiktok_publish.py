#!/usr/bin/env python3
"""Publish a video to TikTok via Content Posting API (Direct Post, FILE_UPLOAD).

Usage:
    python3 scripts/tiktok_publish.py <video.mp4> "caption with #hashtags"

Env (.env): TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET,
            TIKTOK_PRIVACY=SELF_ONLY (until the app audit passes, then PUBLIC_TO_EVERYONE),
            TIKTOK_OPEN_ID (optional; auto-detected when a single account is authorized).

Flow: init -> chunked PUT upload -> status polling until PUBLISH_COMPLETE.
"""
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tiktok_tokens import get_access_token, load_dotenv  # noqa: E402

INIT_URL = "https://open.tiktokapis.com/v2/post/publish/video/init/"
STATUS_URL = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"
CHUNK_SIZE = 10 * 1024 * 1024  # 10 MB


def api_post(url, access_token, payload):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {access_token}",
                 "Content-Type": "application/json; charset=UTF-8"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def main():
    load_dotenv()
    if len(sys.argv) < 3:
        raise SystemExit('Uso: python3 scripts/tiktok_publish.py <video.mp4> "caption con #hashtags"')
    video = Path(sys.argv[1])
    caption = sys.argv[2]
    if not video.exists():
        raise SystemExit(f"No existe el archivo: {video}")

    client_key = os.environ.get("TIKTOK_CLIENT_KEY")
    client_secret = os.environ.get("TIKTOK_CLIENT_SECRET")
    if not client_key or not client_secret:
        raise SystemExit("Faltan TIKTOK_CLIENT_KEY / TIKTOK_CLIENT_SECRET en .env.")
    privacy = os.environ.get("TIKTOK_PRIVACY", "SELF_ONLY").upper()
    if privacy not in ("SELF_ONLY", "PUBLIC_TO_EVERYONE"):
        raise SystemExit("TIKTOK_PRIVACY debe ser SELF_ONLY o PUBLIC_TO_EVERYONE.")
    open_id = os.environ.get("TIKTOK_OPEN_ID") or None

    access_token = get_access_token(client_key, client_secret, open_id)
    size = video.stat().st_size
    total_chunks = (size + CHUNK_SIZE - 1) // CHUNK_SIZE

    init = api_post(INIT_URL, access_token, {
        "post_info": {
            "title": caption,
            "privacy_level": privacy,
            "disable_duet": False,
            "disable_comment": False,
            "disable_stitch": False,
        },
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": size,
            "chunk_size": CHUNK_SIZE,
            "total_chunk_count": total_chunks,
        },
        "post_mode": "DIRECT_POST",
        "media_type": "VIDEO",
    })
    if init.get("error", {}).get("code") != "ok":
        raise SystemExit(f"INIT fallo: {init}")
    upload_url = init["data"]["upload_url"]
    publish_id = init["data"]["publish_id"]
    print(f"Subiendo {size} bytes en {total_chunks} parte(s)... publish_id={publish_id}")

    with open(video, "rb") as f:
        for i in range(total_chunks):
            chunk = f.read(CHUNK_SIZE)
            start = i * CHUNK_SIZE
            end = start + len(chunk) - 1
            req = urllib.request.Request(
                upload_url, data=chunk, method="PUT",
                headers={"Content-Type": "video/mp4",
                         "Content-Length": str(len(chunk)),
                         "Content-Range": f"bytes {start}-{end}/{size}"})
            with urllib.request.urlopen(req, timeout=180) as resp:
                resp.read()
            print(f"  parte {i + 1}/{total_chunks} ok")

    print("Video subido. TikTok lo esta procesando...")
    for _ in range(20):
        time.sleep(15)
        st = api_post(STATUS_URL, access_token, {"publish_id": publish_id})
        status = st.get("data", {}).get("status")
        print(f"  estado: {status}")
        if status == "PUBLISH_COMPLETE":
            print("Publicado.")
            return
        if status == "FAILED":
            raise SystemExit(f"Fallo la publicacion: {st}")
    print("Sigue en proceso; verifica el estado en TikTok.")


if __name__ == "__main__":
    main()
