from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from virtual_lab.ui import api

STATIC = Path(__file__).resolve().parent / "static"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        print("[ui]", args[0] if args else fmt)

    def _json(self, code: int, payload: dict) -> None:
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def _bytes(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8") or "{}")

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path in {"/", "/index.html"}:
            html = (STATIC / "index.html").read_bytes()
            return self._bytes(200, html, "text/html; charset=utf-8")
        if path == "/styles.css":
            return self._bytes(200, (STATIC / "styles.css").read_bytes(), "text/css; charset=utf-8")
        if path == "/app.js":
            return self._bytes(200, (STATIC / "app.js").read_bytes(), "application/javascript; charset=utf-8")
        if path == "/api/snapshot":
            return self._json(200, api.snapshot())
        return self._json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        try:
            body = self._read_json()
            if path == "/api/run":
                return self._json(
                    200,
                    api.run_scenario(
                        body.get("scenario", "open_aisle"),
                        use_cbf=bool(body.get("use_cbf")),
                        speed=body.get("speed"),
                        friction=float(body.get("friction", 1.0)),
                        sensor_noise=float(body.get("sensor_noise", 0.0)),
                    ),
                )
            if path == "/api/search":
                return self._json(
                    200,
                    api.run_search(body.get("scenario", "open_aisle"), trials=int(body.get("trials", 8))),
                )
            if path == "/api/tune":
                return self._json(200, api.run_tune(body.get("scenario", "open_aisle")))
        except FileNotFoundError as exc:
            return self._json(404, {"error": str(exc)})
        except Exception as exc:  # noqa: BLE001
            return self._json(400, {"error": str(exc)})
        return self._json(404, {"error": "not found"})


def serve(host: str = "0.0.0.0", port: int = 8765) -> None:
    httpd = ThreadingHTTPServer((host, port), Handler)
    url = f"http://127.0.0.1:{port}/"
    print(f"VRTOP UI  ->  {url}")
    print("Click Run scenario to show the robot working.")
    httpd.serve_forever()
