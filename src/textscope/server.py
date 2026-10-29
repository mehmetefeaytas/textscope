from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

from .clean import clean_text
from .metrics import report as metrics_report
from .protected import verify_protected
from .rewrite import rewrite_text


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        data = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8", errors="replace")
        try:
            payload = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self._send(400, {"error": "invalid json"})
            return
        text = payload.get("text", "")
        path = urlparse(self.path).path
        if path == "/clean":
            out = clean_text(text)
            ok, errs = verify_protected(text, out)
            self._send(200, {"text": out, "protected_ok": ok, "protected_errors": errs})
        elif path == "/rewrite":
            strict = bool(payload.get("strict", False))
            lang = payload.get("lang", "auto")
            profile = payload.get("profile", "balanced")
            seed = int(payload.get("seed", 0))
            out = rewrite_text(text, strict=strict, lang=lang, profile=profile, seed=seed)
            ok, errs = verify_protected(text, out)
            self._send(200, {"text": out, "protected_ok": ok, "protected_errors": errs,
                             "word_count_original": len(text.split()),
                             "word_count_result": len(out.split())})
        elif path == "/check":
            self._send(200, {"metrics": metrics_report(text)})
        else:
            self._send(404, {"error": "not found"})

    def log_message(self, *args):
        return


def serve(host: str = "127.0.0.1", port: int = 8765) -> None:
    httpd = HTTPServer((host, port), Handler)
    print(f"textscope server listening on http://{host}:{port}")
    httpd.serve_forever()
