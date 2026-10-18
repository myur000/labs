"""Отдает учебные HTML-файлы из папки site на 127.0.0.1:8000."""

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


if __name__ == "__main__":
    handler = partial(SimpleHTTPRequestHandler, directory=str(Path(__file__).with_name("site")))
    with ThreadingHTTPServer(("127.0.0.1", 8000), handler) as server:
        print("Учебный сервер: http://127.0.0.1:8000 (Ctrl+C для остановки)", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
