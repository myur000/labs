#!/usr/bin/env python3
"""Читает link.txt и сохраняет доступность сайтов в report.txt."""

import argparse
import math
import sys
from http.client import HTTPException
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


def check_url(url, timeout=10):
    """Ok — конечный HTTP-ответ 2xx; иначе Error."""
    try:
        parsed = urlsplit(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            return "Error"
        # Явно проверяем некорректный порт и пробелы в адресе.
        if parsed.port is not None and not 1 <= parsed.port <= 65535:
            return "Error"
        if any(char.isspace() for char in url):
            return "Error"
        request = Request(url, headers={"User-Agent": "DevOpsLinkChecker/1.0"})
        with urlopen(request, timeout=timeout) as response:
            return "Ok" if 200 <= response.status < 300 else "Error"
    except HTTPError as error:
        error.close()
        return "Error"
    except (URLError, OSError, ValueError, HTTPException, UnicodeError):
        return "Error"


def check_file(input_path, output_path, timeout=10):
    if Path(input_path).resolve() == Path(output_path).resolve():
        raise ValueError("Входной файл и отчет должны иметь разные имена.")
    with open(input_path, "r", encoding="utf-8-sig") as source:
        urls = [line.strip() for line in source if line.strip()]
    with open(output_path, "w", encoding="utf-8") as report:
        for url in urls:
            report.write(f"{url} -> {check_url(url, timeout)}\n")
    return len(urls)


def main():
    folder = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=folder / "link.txt")
    parser.add_argument("--output", type=Path, default=folder / "report.txt")
    parser.add_argument("--timeout", type=float, default=10, help="Тайм-аут сетевых операций, секунды")
    args = parser.parse_args()
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--timeout должен быть положительным конечным числом")
    try:
        count = check_file(args.input, args.output, args.timeout)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"Ошибка работы с файлами: {error}", file=sys.stderr)
        return 1
    print(f"Проверено адресов: {count}. Результат записан в {args.output.name}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
