import hashlib
import json
import time
from pathlib import Path

import requests

# Файлы со ссылками, состоянием и результатом.
LINKS_FILE = Path("link.txt")
HASHES_FILE = Path("hashes.json")
REPORT_FILE = Path("report.txt")
DELAY_SECONDS = 1

try:
    # Читаем адреса, пропускаем пустые строки и комментарии.
    lines = LINKS_FILE.read_text(encoding="utf-8-sig").splitlines()
    urls = [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]
    urls = list(dict.fromkeys(urls))

    # При первом запуске сохраненных хешей еще нет.
    hashes = json.loads(HASHES_FILE.read_text(encoding="utf-8")) if HASHES_FILE.exists() else {}
    if not isinstance(hashes, dict) or any(not isinstance(value, str) or len(value) != 64 for value in hashes.values()):
        raise ValueError("Неверный формат hashes.json.")
except (OSError, ValueError) as error:
    raise SystemExit(f"Ошибка чтения файлов: {error}")

report_lines = []
for index, url in enumerate(urls):
    try:
        # Загружаем страницу и вычисляем SHA-256 ее содержимого.
        with requests.get(url, timeout=10) as response:
            response.raise_for_status()
            if not 200 <= response.status_code < 300:
                raise ValueError("Неуспешный HTTP-ответ.")
            current_hash = hashlib.sha256(response.content).hexdigest()

        # Сравниваем новую версию с последней успешной.
        if url not in hashes:
            status, message = "NEW", "первый успешный обход"
        elif hashes[url] == current_hash:
            status, message = "OK", "без изменений"
        else:
            status, message = "CHANGED", "контент изменился"
        hashes[url] = current_hash
    except (requests.RequestException, ValueError):
        # При ошибке прежний хеш не меняется.
        status, message = "ERROR", "ошибка загрузки"

    report_lines.append(f"[{status}] {url} — {message}")
    if index < len(urls) - 1:
        time.sleep(DELAY_SECONDS)

try:
    # Записываем отчет и сохраняем обновленные хеши.
    REPORT_FILE.write_text("\n".join(report_lines) + ("\n" if report_lines else ""), encoding="utf-8")
    temporary = HASHES_FILE.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(hashes, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(HASHES_FILE)
except OSError as error:
    raise SystemExit(f"Ошибка сохранения файлов: {error}")

print("Отчет сохранен в report.txt, состояние — в hashes.json.")
