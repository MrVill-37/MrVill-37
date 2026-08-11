#!/usr/bin/env python3
"""Minimal local server for Airdrop Nexus UI.

Serves static files from the repository root.
"""

from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler


class NoCacheHandler(SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def main() -> int:
    host, port = "0.0.0.0", 8080
    server = ThreadingHTTPServer((host, port), NoCacheHandler)
    print(f"Airdrop Nexus UI running at http://{host}:{port}/ui/index.html")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
