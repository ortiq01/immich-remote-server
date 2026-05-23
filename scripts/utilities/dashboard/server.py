#!/usr/bin/env python3
"""
Immich Photo Dashboard - stdlib-only HTTP server with Immich API proxy.
Run:  python3 server.py
Then open:  http://<host-ip>:8088
"""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib import error, request as urllib_request

ENV_FILE = Path(__file__).parent.parent.parent.parent / ".env.immich-api"
PORT = int(os.environ.get("DASHBOARD_PORT", "8088"))
BIND = os.environ.get("DASHBOARD_BIND", "0.0.0.0")


def load_env() -> dict:
    env = {}
    if not ENV_FILE.exists():
        return env
    for raw in ENV_FILE.read_text().splitlines():
        s = raw.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        env[k.strip()] = v.strip()
    return env


CFG = load_env()
IMMICH_URL = CFG.get("IMMICH_URL", "http://localhost:2283").rstrip("/")
IMMICH_KEY = CFG.get("IMMICH_API_KEY", "")
PERSONAL_ALBUM_NAME = CFG.get("DASHBOARD_PERSONAL_ALBUM_NAME", "Personal Foto's")
SMART_FILTER_SHARED_ONLY = (CFG.get("DASHBOARD_SMART_FILTER_SHARED_ONLY", "true").strip().lower() in {"1", "true", "yes", "y"})
DASHBOARD_HTML = Path(__file__).parent / "index.html"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[{self.address_string()}] {fmt % args}")

    def send_json(self, code: int, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_bytes(self, code: int, content_type: str, body: bytes):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # ---- proxy to Immich ----

    def proxy(self, method: str, immich_path: str, body: bytes | None = None, extra_headers: dict | None = None):
        url = IMMICH_URL + immich_path
        headers = {
            "x-api-key": IMMICH_KEY,
            "accept": "application/json",
        }
        if body:
            headers["content-type"] = "application/json"
        if extra_headers:
            headers.update(extra_headers)
        req = urllib_request.Request(url, data=body, method=method, headers=headers)
        try:
            with urllib_request.urlopen(req, timeout=90) as resp:
                ct = resp.headers.get("content-type", "application/octet-stream")
                data = resp.read()
                return resp.status, ct, data
        except error.HTTPError as e:
            return e.code, "application/json", e.read()
        except (error.URLError, TimeoutError) as e:
            payload = json.dumps({
                "error": "immich_unreachable",
                "message": str(e),
                "path": immich_path,
            }).encode()
            return 502, "application/json", payload
        except Exception as e:
            payload = json.dumps({
                "error": "proxy_failure",
                "message": str(e),
                "path": immich_path,
            }).encode()
            return 500, "application/json", payload

    # ---- routing ----

    def do_GET(self):
        if self.path in ("/", ""):
            self._serve_html()
        elif self.path.startswith("/proxy/"):
            self._handle_proxy("GET")
        elif self.path == "/config":
            self.send_json(
                200,
                {
                    "personal_album_name": PERSONAL_ALBUM_NAME,
                    "smart_filter_shared_only": SMART_FILTER_SHARED_ONLY,
                },
            )
        elif self.path == "/status":
            self.send_json(200, {"immich_url": IMMICH_URL, "key_set": bool(IMMICH_KEY)})
        else:
            self.send_json(404, {"error": "not found"})

    def do_POST(self):
        if self.path.startswith("/proxy/"):
            self._handle_proxy("POST")
        else:
            self.send_json(404, {"error": "not found"})

    def do_PUT(self):
        if self.path.startswith("/proxy/"):
            self._handle_proxy("PUT")
        else:
            self.send_json(404, {"error": "not found"})

    def do_DELETE(self):
        if self.path.startswith("/proxy/"):
            self._handle_proxy("DELETE")
        else:
            self.send_json(404, {"error": "not found"})

    def _serve_html(self):
        if not DASHBOARD_HTML.exists():
            self.send_json(500, {"error": "index.html missing"})
            return
        body = DASHBOARD_HTML.read_bytes()
        self.send_bytes(200, "text/html; charset=utf-8", body)

    def _handle_proxy(self, method: str):
        # strip /proxy prefix, keep /api/... and query string
        immich_path = self.path[len("/proxy"):]
        length = int(self.headers.get("content-length", 0))
        body = self.rfile.read(length) if length else None
        code, ct, data = self.proxy(method, immich_path, body)
        self.send_bytes(code, ct, data)


if __name__ == "__main__":
    if not IMMICH_KEY:
        print(f"[WARN] IMMICH_API_KEY not set in {ENV_FILE}")
    server = HTTPServer((BIND, PORT), Handler)
    print(f"[OK] Dashboard running at http://{BIND}:{PORT}")
    print(f"[OK] Proxying Immich at {IMMICH_URL}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[INFO] Stopped.")
        sys.exit(0)
