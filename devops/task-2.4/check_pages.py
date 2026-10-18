#!/usr/bin/env python3
"""Проверяет, изменились ли страницы из link.txt с прошлого успешного обхода."""

import hashlib
import json
import sys
import time
from pathlib import Path

import requests


FOLDER = Path(__file__).resolve().parent
DELAY_SECONDS = 1
HEADERS = {"User-Agent": "PageChangeChecker/1.0"}


def load_links(path):
    lines = Path(path).read_text(encoding="utf-8-sig").splitlines()
    links = [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]
    return list(dict.fromkeys(links))  # Повторяющийся адрес проверяется один раз.


def load_hashes(path):
    if not Path(path).exists():
        return {}
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or any(
        not isinstance(url, str) or not isinstance(digest, str)
        or len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest)
        for url, digest in data.items()
    ):
        raise ValueError("hashes.json должен содержать словарь URL → SHA-256.")
    return data


def save_hashes(data, path):
    # Подмена готового файла защищает старое состояние от частичной записи.
    path = Path(path)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def check_pages(folder=FOLDER, delay=DELAY_SECONDS):
    folder = Path(folder)
    links = load_links(folder / "link.txt")
    hashes = load_hashes(folder / "hashes.json")
    lines = []
    errors = 0
    for index, url in enumerate(links):
        try:
            with requests.get(url, headers=HEADERS, timeout=10) as response:
                response.raise_for_status()
                if not 200 <= response.status_code < 300:
                    raise ValueError(f"Неуспешный конечный HTTP-статус: {response.status_code}")
                current = hashlib.sha256(response.content).hexdigest()
            if url not in hashes:
                status, message = "NEW", "первый успешный обход"
            elif hashes[url] == current:
                status, message = "OK", "без изменений"
            else:
                status, message = "CHANGED", "контент изменился"
            hashes[url] = current
        except (requests.RequestException, ValueError) as error:
            status = "ERROR"
            message = " ".join(str(error).split())
            errors += 1
            # При ошибке предыдущий успешный хеш остается в словаре.
        lines.append(f"[{status}] {url} — {message}")
        if index < len(links) - 1:
            time.sleep(delay)
    (folder / "report.txt").write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    save_hashes(hashes, folder / "hashes.json")
    return lines, errors


def main():
    try:
        lines, errors = check_pages()
    except (OSError, ValueError) as error:
        print(f"Ошибка чтения или сохранения файлов: {error}", file=sys.stderr)
        return 1
    print(f"Проверено страниц: {len(lines)}, ошибок: {errors}.")
    print("Отчет сохранен в report.txt, состояние — в hashes.json.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
