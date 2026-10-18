"""Проверки анализа без подключения к Nginx или Telegram."""

import tempfile
import unittest
from collections import Counter
from pathlib import Path

from analyze_logs import analyze_log, suspicious_ips
from generate_sample import log_line


class LogAnalysisTests(unittest.TestCase):
    def analyze(self, content, status=404):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "access.log"
            path.write_text(content, encoding="utf-8")
            return analyze_log(path, status)

    def test_sample(self):
        counts, total, skipped = analyze_log(Path(__file__).with_name("sample_access.log"))
        self.assertEqual((total, skipped), (107, 2))
        self.assertEqual(counts, Counter({"192.0.2.10": 51, "198.51.100.20": 50}))
        self.assertEqual(suspicious_ips(counts, 50), [("192.0.2.10", 51)])

    def test_threshold_is_strict(self):
        self.assertEqual(suspicious_ips(Counter({"192.0.2.1": 50}), 50), [])
        self.assertEqual(suspicious_ips(Counter({"192.0.2.1": 51}), 50), [("192.0.2.1", 51)])

    def test_ipv6_and_another_status(self):
        counts, total, skipped = self.analyze(log_line("2001:db8::1", "/private", 403), 403)
        self.assertEqual((counts, total, skipped), (Counter({"2001:db8::1": 1}), 1, 0))

    def test_does_not_count_404_in_url_or_user_agent(self):
        line = log_line("192.0.2.1", "/404", 200).replace("StudyClient/1.0", "404")
        self.assertEqual(self.analyze(line), (Counter(), 1, 0))

    def test_invalid_lines_and_ip_are_skipped(self):
        content = "broken\n" + log_line("999.1.1.1", "/", 404)
        self.assertEqual(self.analyze(content), (Counter(), 2, 2))

    def test_empty_log(self):
        self.assertEqual(self.analyze(""), (Counter(), 0, 0))

    def test_missing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                analyze_log(Path(directory) / "missing.log")


if __name__ == "__main__":
    unittest.main()
