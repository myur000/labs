#!/usr/bin/env python3
"""Анализ access.log в формате Nginx combined/common."""

import argparse
import os
import re
import sys
from collections import Counter
from ipaddress import ip_address


# IP расположен в начале строки, код ответа — сразу после запроса в кавычках.
LOG_PATTERN = re.compile(
    r'^\s*(?P<ip>\S+)\s+\S+\s+\S+\s+\[[^\]]+\]\s+'
    r'"[^"\r\n]*"\s+(?P<status>[1-5][0-9]{2})\s+(?:[0-9]+|-)(?:\s|$)'
)


def analyze_log(path, status=404):
    """Возвращает счетчик выбранного статуса, число строк и число пропусков."""
    counts = Counter()
    total = skipped = 0
    with open(path, "r", encoding="utf-8", errors="replace") as log_file:
        for line in log_file:
            total += 1
            match = LOG_PATTERN.match(line)
            if not match:
                skipped += 1
                continue
            try:
                ip = str(ip_address(match.group("ip")))
            except ValueError:
                skipped += 1
                continue
            if int(match.group("status")) == status:
                counts[ip] += 1
    return counts, total, skipped


def suspicious_ips(counts, threshold):
    """Условие исходного задания: строго больше порога."""
    return [(ip, count) for ip, count in counts.most_common() if count > threshold]


def send_telegram(message):
    token = os.environ.get("TELEGRAM_TOKEN", "").strip()
    chat_id = os.environ.get("CHAT_ID", "").strip()
    if not token or not chat_id:
        raise RuntimeError("Для отправки задайте TELEGRAM_TOKEN и CHAT_ID.")
    # Для локального анализа сторонние библиотеки не нужны.
    try:
        import requests
    except ImportError:
        raise RuntimeError("Установите requests: python3 -m pip install -r requirements.txt") from None

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message},
            timeout=(5, 15),
        )
        response.raise_for_status()
        if response.json().get("ok") is not True:
            raise RuntimeError("Telegram API не подтвердил отправку сообщения.")
    except requests.RequestException:
        # URL запроса содержит токен, поэтому текст сетевого исключения не печатаем.
        raise RuntimeError("Не удалось отправить сообщение: ошибка сети или HTTP.") from None
    except ValueError:
        raise RuntimeError("Telegram API вернул некорректный JSON.") from None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", default="/var/log/nginx/access.log", help="Путь к логу")
    parser.add_argument("--status", type=int, default=404, help="HTTP-статус (по умолчанию 404)")
    parser.add_argument("--threshold", type=int, default=50, help="Порог (по умолчанию 50)")
    parser.add_argument("--send", action="store_true", help="Отправить предупреждения в Telegram")
    args = parser.parse_args()
    if not 100 <= args.status <= 599:
        parser.error("--status должен быть от 100 до 599")
    if args.threshold < 0:
        parser.error("--threshold не может быть отрицательным")

    try:
        counts, total, skipped = analyze_log(args.log, args.status)
    except OSError as error:
        print(f"Не удалось прочитать лог: {error}", file=sys.stderr)
        return 1

    print(f"Прочитано строк: {total}")
    print(f"Пропущено некорректных строк: {skipped}")
    print(f"Ответов с кодом {args.status}: {sum(counts.values())}")
    print(f"Уникальных IP с кодом {args.status}: {len(counts)}")
    alerts = suspicious_ips(counts, args.threshold)
    if not alerts:
        print(f"IP с числом ответов {args.status} больше {args.threshold} не обнаружены.")
    for ip, count in alerts:
        message = (
            f"Обнаружена подозрительная активность! IP {ip}: "
            f"ответов с кодом {args.status} — {count} (порог: > {args.threshold})."
        )
        print(message)
        if args.send:
            try:
                send_telegram(message)
                print("Сообщение отправлено в Telegram.")
            except RuntimeError as error:
                print(error, file=sys.stderr)
                return 1
    if not args.send:
        print("Режим локального анализа: отправка в Telegram отключена.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
