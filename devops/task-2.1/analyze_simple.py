import os
import re
from collections import Counter
from ipaddress import ip_address

import requests

# 1. Настройки: файл лога, порог и включение Telegram.
LOG_FILE = "sample_access.log"
THRESHOLD = 50
SEND_TELEGRAM = False
TOKEN = os.getenv("TELEGRAM_TOKEN", "")
CHAT_ID = os.getenv("CHAT_ID", "")

if SEND_TELEGRAM and (not TOKEN or not CHAT_ID):
    raise SystemExit("Задайте TELEGRAM_TOKEN и CHAT_ID.")

# 2. Шаблон: IP в начале строки и статус 404 после запроса.
pattern = re.compile(
    r'^(\S+)\s+\S+\s+\S+\s+\[[^\]]+\]\s+"[^"]*"\s+404\s'
)
counts = Counter()

# 3. Читаем лог и считаем ошибки 404 для каждого IP.
try:
    with open(LOG_FILE, "r", encoding="utf-8", errors="replace") as log:
        for line in log:
            match = pattern.search(line)
            if not match:
                continue
            try:
                ip = str(ip_address(match.group(1)))
            except ValueError:
                continue
            counts[ip] += 1
except OSError as error:
    raise SystemExit(f"Не удалось прочитать лог: {error}")

# 4. Показываем результат подсчета.
print("Количество ошибок 404 по IP:")
for ip, count in counts.items():
    print(f"{ip}: {count}")

# 5. Выявляем превышение порога и формируем предупреждение.
for ip, count in counts.items():
    if count > THRESHOLD:
        message = f"Подозрительная активность: IP {ip}, ошибок 404 — {count}."
        print(message)

        # 6. При включенной настройке отправляем сообщение в Telegram.
        if SEND_TELEGRAM:
            try:
                response = requests.post(
                    f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                    json={"chat_id": CHAT_ID, "text": message},
                    timeout=10,
                )
                response.raise_for_status()
                if response.json().get("ok") is not True:
                    raise ValueError("Telegram не подтвердил отправку.")
                print("Сообщение отправлено в Telegram.")
            except (requests.RequestException, ValueError):
                print("Не удалось отправить сообщение в Telegram.")
