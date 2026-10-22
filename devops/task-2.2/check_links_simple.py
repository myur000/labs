import requests

# Имена входного файла и отчета.
LINKS_FILE = "link.txt"
REPORT_FILE = "report.txt"

try:
    # Читаем адреса и пропускаем пустые строки.
    with open(LINKS_FILE, "r", encoding="utf-8-sig") as source:
        urls = [line.strip() for line in source if line.strip()]

    # Создаем отчет. При повторном запуске он перезаписывается.
    with open(REPORT_FILE, "w", encoding="utf-8") as report:
        for url in urls:
            try:
                # Загружаем страницу с ограничением ожидания.
                with requests.get(url, timeout=10) as response:
                    status = "Ok" if 200 <= response.status_code < 300 else "Error"
            except (requests.RequestException, ValueError):
                # Ошибка одного адреса не останавливает остальные проверки.
                status = "Error"

            # Записываем результат в формате из задания.
            report.write(f"{url} -> {status}\n")
except OSError as error:
    raise SystemExit(f"Ошибка работы с файлами: {error}")

print("Проверка завершена. Результат сохранен в report.txt.")
