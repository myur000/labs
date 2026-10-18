"""Проверки реальных HTTP-запросов к локальному серверу и формата отчета."""

import socket
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

from check_links import check_file, check_url
from demo_server import DemoHandler


class LinkCheckerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), DemoHandler)
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"
        cls.worker = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.worker.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.worker.join()

    def test_200(self):
        self.assertEqual(check_url(self.base + "/ok"), "Ok")

    def test_redirect(self):
        self.assertEqual(check_url(self.base + "/redirect"), "Ok")

    def test_404(self):
        self.assertEqual(check_url(self.base + "/missing"), "Error")

    def test_500(self):
        self.assertEqual(check_url(self.base + "/server-error"), "Error")

    def test_malformed_addresses(self):
        for url in ["неверный-адрес", "ftp://example.com", "https://", "http://example.com:bad", "http://example.com:0", "http://bad host/"]:
            with self.subTest(url=url):
                self.assertEqual(check_url(url), "Error")

    def test_timeout(self):
        with patch("check_links.urlopen", side_effect=socket.timeout("timed out")):
            self.assertEqual(check_url(self.base + "/ok", timeout=0.1), "Error")

    def test_dns_error(self):
        with patch("check_links.urlopen", side_effect=URLError("DNS failure")):
            self.assertEqual(check_url("https://example.com/"), "Error")

    def test_report_format_order_duplicates_and_blank_lines(self):
        urls = [self.base + "/ok", self.base + "/missing", self.base + "/ok"]
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "link.txt"
            output = Path(directory) / "report.txt"
            source.write_text("\ufeff  " + urls[0] + "  \n\n" + "\n".join(urls[1:]) + "\n", encoding="utf-8")
            output.write_text("старый отчет\n", encoding="utf-8")
            self.assertEqual(check_file(source, output), 3)
            expected = f"{urls[0]} -> Ok\n{urls[1]} -> Error\n{urls[2]} -> Ok\n"
            self.assertEqual(output.read_text(encoding="utf-8"), expected)

    def test_missing_input(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                check_file(Path(directory) / "absent.txt", Path(directory) / "report.txt")

    def test_input_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "link.txt"
            path.write_text("https://example.com/\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                check_file(path, path)
            self.assertEqual(path.read_text(encoding="utf-8"), "https://example.com/\n")

    def test_empty_file(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / "link.txt", Path(directory) / "report.txt"
            source.write_text("\n\n", encoding="utf-8")
            self.assertEqual(check_file(source, output), 0)
            self.assertEqual(output.read_text(encoding="utf-8"), "")

    def test_invalid_timeout_rejected(self):
        script = Path(__file__).with_name("check_links.py")
        for value in ["0", "-1", "nan", "inf"]:
            with self.subTest(timeout=value):
                result = subprocess.run([sys.executable, str(script), "--timeout", value], capture_output=True)
                self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
