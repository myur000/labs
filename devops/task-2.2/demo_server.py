"""Локальный сервер для воспроизводимой проверки задания 2.2."""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class DemoHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        status = {"/ok": 200, "/redirect": 302, "/server-error": 500}.get(self.path, 404)
        self.send_response(status)
        if status == 302:
            self.send_header("Location", "/ok")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    with ThreadingHTTPServer(("127.0.0.1", args.port), DemoHandler) as server:
        print(f"Учебный сервер: http://127.0.0.1:{server.server_port} (Ctrl+C для остановки)", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
