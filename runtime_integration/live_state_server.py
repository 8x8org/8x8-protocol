#!/usr/bin/env python3
"""Read-only local HTTP server for 8x8 live state.

Binds to loopback by default, serves only explicitly configured JSON files, adds
no mutation endpoints, and sends restrictive response headers. It is not a
remote-control API and should remain behind local or authenticated transport.
"""
from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


class StateHandler(BaseHTTPRequestHandler):
    routes: dict[str, Path] = {}

    def _headers(self, status: int, content_type: str = "application/json; charset=utf-8") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/healthz":
            payload = {"status": "ok", "mode": "READ_ONLY", "product_version": "0.0.1"}
        elif path in self.routes:
            target = self.routes[path]
            try:
                with target.open(encoding="utf-8") as handle:
                    payload = json.load(handle)
            except (OSError, json.JSONDecodeError):
                self._headers(503)
                self.wfile.write(b'{"error":"state_unavailable"}')
                return
        else:
            self._headers(404)
            self.wfile.write(b'{"error":"not_found"}')
            return
        body = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()
        self._headers(200)
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        self._headers(405)
        self.wfile.write(b'{"error":"read_only"}')

    do_PUT = do_POST
    do_PATCH = do_POST
    do_DELETE = do_POST

    def log_message(self, format: str, *args: object) -> None:
        return


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8877)
    parser.add_argument("--context", required=True)
    parser.add_argument("--live-state", required=True)
    parser.add_argument("--events")
    args = parser.parse_args()
    routes = {
        "/v0.0.1/context": Path(args.context).resolve(),
        "/v0.0.1/live-state": Path(args.live_state).resolve(),
    }
    if args.events:
        routes["/v0.0.1/events"] = Path(args.events).resolve()
    StateHandler.routes = routes
    server = ThreadingHTTPServer((args.bind, args.port), StateHandler)
    print(json.dumps({"bind": args.bind, "port": args.port, "mode": "READ_ONLY", "routes": sorted(routes)}))
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
