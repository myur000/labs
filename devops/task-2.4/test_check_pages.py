"""Проверяет сохранение состояния и обработку ошибок без сетевых запросов."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import requests

from check_pages import check_pages, load_links


URL = "https://example.com/"


def response(content=b"version 1", status=200):
    item = MagicMock()
    item.__enter__.return_value = item
    item.content = content
    item.status_code = status
    return item


class PageChangeTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.folder = Path(self.directory.name)
        (self.folder / "link.txt").write_text(URL + "\n", encoding="utf-8")

    def test_first_unchanged_changed_and_updated_baseline(self):
        for body, expected in [(b"v1", "NEW"), (b"v1", "OK"), (b"v2", "CHANGED"), (b"v2", "OK")]:
            with patch("check_pages.requests.get", return_value=response(body)):
                lines, errors = check_pages(self.folder, delay=0)
            self.assertEqual(errors, 0)
            self.assertTrue(lines[0].startswith(f"[{expected}]"))
        state = json.loads((self.folder / "hashes.json").read_text(encoding="utf-8"))
        self.assertEqual(state[URL], hashlib.sha256(b"v2").hexdigest())

    def test_failure_preserves_previous_hash(self):
        with patch("check_pages.requests.get", return_value=response()):
            check_pages(self.folder, delay=0)
        before = (self.folder / "hashes.json").read_bytes()
        with patch("check_pages.requests.get", side_effect=requests.Timeout("тайм-аут")):
            lines, errors = check_pages(self.folder, delay=0)
        self.assertEqual(errors, 1)
        self.assertTrue(lines[0].startswith("[ERROR]"))
        self.assertEqual((self.folder / "hashes.json").read_bytes(), before)

    def test_failed_first_request_does_not_create_baseline(self):
        with patch("check_pages.requests.get", side_effect=requests.ConnectionError("нет связи")):
            check_pages(self.folder, delay=0)
        self.assertEqual(json.loads((self.folder / "hashes.json").read_text()), {})

    def test_error_does_not_stop_other_urls(self):
        (self.folder / "link.txt").write_text(URL + "\nhttps://example.org/\n", encoding="utf-8")
        with patch("check_pages.requests.get", side_effect=[requests.ConnectionError("нет связи"), response()]), patch("check_pages.time.sleep") as sleep:
            lines, errors = check_pages(self.folder, delay=1)
        self.assertEqual(errors, 1)
        self.assertTrue(lines[0].startswith("[ERROR]"))
        self.assertTrue(lines[1].startswith("[NEW]"))
        sleep.assert_called_once_with(1)

    def test_http_error_is_not_hashed(self):
        item = response(b"error page", status=404)
        item.raise_for_status.side_effect = requests.HTTPError("HTTP 404")
        with patch("check_pages.requests.get", return_value=item):
            lines, errors = check_pages(self.folder, delay=0)
        self.assertEqual(errors, 1)
        self.assertIn("[ERROR]", lines[0])
        self.assertEqual(json.loads((self.folder / "hashes.json").read_text()), {})

    def test_comments_bom_blank_lines_and_duplicates(self):
        path = self.folder / "link.txt"
        path.write_text("\ufeff  # комментарий\n\n " + URL + " \n" + URL + "\n", encoding="utf-8")
        self.assertEqual(load_links(path), [URL])

    def test_corrupt_state_is_not_overwritten(self):
        for bad in ["{broken", "[]", '{"url": "invalid hash"}']:
            with self.subTest(bad=bad):
                path = self.folder / "hashes.json"
                path.write_text(bad, encoding="utf-8")
                with patch("check_pages.requests.get") as get:
                    with self.assertRaises(ValueError):
                        check_pages(self.folder, delay=0)
                    get.assert_not_called()
                self.assertEqual(path.read_text(encoding="utf-8"), bad)

    def test_empty_list(self):
        (self.folder / "link.txt").write_text("\n# пустой список\n", encoding="utf-8")
        with patch("check_pages.requests.get") as get:
            self.assertEqual(check_pages(self.folder, delay=0), ([], 0))
            get.assert_not_called()
        self.assertEqual((self.folder / "report.txt").read_text(), "")

    def test_report_is_replaced_and_hashes_are_persistent(self):
        (self.folder / "report.txt").write_text("старый отчет", encoding="utf-8")
        with patch("check_pages.requests.get", return_value=response()):
            lines, _ = check_pages(self.folder, delay=0)
        self.assertEqual((self.folder / "report.txt").read_text(encoding="utf-8"), lines[0] + "\n")
        self.assertTrue((self.folder / "hashes.json").is_file())
        self.assertFalse((self.folder / "hashes.json.tmp").exists())


if __name__ == "__main__":
    unittest.main()
