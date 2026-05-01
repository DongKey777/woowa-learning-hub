#!/usr/bin/env python3
"""Long-lived local RAG runtime server.

The daemon keeps encoder/reranker module caches warm across `bin/rag-ask`
calls. It binds only to localhost and speaks a tiny JSON-over-HTTP protocol.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from socketserver import TCPServer
from typing import Any

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

import cli as workbench_cli  # type: ignore  # noqa: E402

_REQUEST_LOCK = threading.Lock()


def namespace_from_payload(payload: dict[str, Any]) -> argparse.Namespace:
    return argparse.Namespace(
        prompt=str(payload.get("prompt") or ""),
        repo=payload.get("repo"),
        module=payload.get("module"),
        rag_backend=payload.get("rag_backend"),
        via_daemon=False,
    )


def handle_rag_ask_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if not str(payload.get("prompt") or "").strip():
        raise ValueError("prompt is required")
    with _REQUEST_LOCK:
        return workbench_cli.build_rag_ask_output(namespace_from_payload(payload))


class RagDaemonHandler(BaseHTTPRequestHandler):
    server_version = "WoowaRagDaemon/1.0"

    def log_message(self, format: str, *args: Any) -> None:
        sys.stderr.write("[rag-daemon] " + (format % args) + "\n")

    def _write_json(self, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or "0")
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        payload = json.loads(raw or "{}")
        if not isinstance(payload, dict):
            raise ValueError("request body must be a JSON object")
        return payload

    def do_GET(self) -> None:
        if self.path != "/health":
            self._write_json(404, {"error": "not_found"})
            return
        self._write_json(
            200,
            {
                "ok": True,
                "pid": os.getpid(),
                "uptime_s": round(time.time() - self.server.started_at, 3),  # type: ignore[attr-defined]
            },
        )

    def do_POST(self) -> None:
        if self.path == "/rag-ask":
            try:
                payload = handle_rag_ask_payload(self._read_json())
            except Exception as exc:  # noqa: BLE001 - client needs JSON
                self._write_json(500, {"error": f"{type(exc).__name__}: {exc}"})
                return
            self._write_json(200, payload)
            return
        if self.path == "/shutdown":
            self._write_json(200, {"ok": True, "pid": os.getpid()})
            threading.Thread(target=self.server.shutdown, daemon=True).start()
            return
        self._write_json(404, {"error": "not_found"})


class LocalThreadingHTTPServer(ThreadingHTTPServer):
    """ThreadingHTTPServer without slow reverse DNS during local bind."""

    def server_bind(self) -> None:
        TCPServer.server_bind(self)
        host, port = self.server_address[:2]
        self.server_name = str(host)
        self.server_port = int(port)


def write_state(
    path: Path,
    *,
    host: str,
    port: int,
    started_at: float,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "pid": os.getpid(),
        "host": host,
        "port": port,
        "started_at": started_at,
        "root": str(Path(__file__).resolve().parents[2]),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def serve(args: argparse.Namespace) -> int:
    started_at = time.time()
    server = LocalThreadingHTTPServer((args.host, args.port), RagDaemonHandler)
    server.started_at = started_at  # type: ignore[attr-defined]
    host, port = server.server_address[:2]
    state_path = Path(args.state_path)
    write_state(state_path, host=str(host), port=int(port), started_at=started_at)
    try:
        server.serve_forever()
    finally:
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except Exception:
            state = {}
        if state.get("pid") == os.getpid():
            state_path.unlink(missing_ok=True)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    serve_parser = subparsers.add_parser("serve")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=0)
    serve_parser.add_argument("--state-path", required=True)
    serve_parser.set_defaults(func=serve)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
