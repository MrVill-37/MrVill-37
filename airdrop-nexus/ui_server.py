#!/usr/bin/env python3
"""Minimal local server for the Airdrop Nexus UI."""

from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path


class NoCacheHandler(SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def main() -> int:
    host, port = "127.0.0.1", 8080
    project_dir = Path(__file__).resolve().parent
    handler = lambda *args, **kwargs: NoCacheHandler(*args, directory=str(project_dir / "ui"), **kwargs)
    server = ThreadingHTTPServer((host, port), handler)
    print(f"Airdrop Nexus UI running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
