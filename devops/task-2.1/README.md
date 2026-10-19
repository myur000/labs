# Задание 2.1. Единый отчет: анализ логов Nginx и уведомления в Telegram

**Состав отчета:** ответы на все три вопроса задания, полный код измененного скрипта, генератора учебного лога и тестов, команды запуска и фактический результат. Для изучения работы не требуется открывать отдельные файлы с кодом.

**Цель работы:** изучить Python-скрипт, который находит IP-адреса с большим количеством ответов HTTP 404, определить необходимое окружение и реализовать работающую часть его функционала.

**Практический результат:** реализован и запущен анализатор учебного access.log в формате Nginx. Он обнаружил IP с 51 ответом 404 при пороге «больше 50». Результат воспроизводится без работающего веб-сервера и без Telegram-бота.

## 1. Какие библиотеки используются в исходном скрипте?

В исходном скрипте используются два модуля стандартной библиотеки Python и одна сторонняя библиотека.

| Библиотека / модуль | Назначение | Использование в скрипте |
| --- | --- | --- |
| `re` | Работа с регулярными выражениями: поиск, проверка и извлечение фрагментов текста по шаблону. | `re.findall(pattern, log_content)` находит все совпадения. Поскольку в шаблоне одна захватывающая группа, результатом становится список извлеченных IP-адресов из записей с кодом 404. |
| `collections` → `Counter` | Подсчет количества повторений элементов. `Counter` — класс счетчика, похожего на словарь. | `Counter(ips)` сопоставляет каждому IP число найденных записей. Метод `.items()` позволяет перебрать пары `(ip, count)`. |
| `requests` | Отправка HTTP-запросов и получение ответов сервера. Устанавливается отдельно. | `requests.post(url, json=...)` отправляет POST-запрос с JSON, содержащим `chat_id` и `text`, для обращения к Telegram Bot API. |

Функции `open()` и метод файла `.read()` также участвуют в работе: файл открывается для чтения, затем его содержимое загружается в строку. `open()` — встроенная функция Python, отдельную библиотеку для нее импортировать не нужно. Конструкция `with` закрывает файл при выходе из блока, в том числе при исключении.

### Как работает исходный алгоритм

1. Читает файл `/var/log/nginx/access.log` целиком.
2. Находит IP-адреса в строках с кодом ответа 404.
3. Подсчитывает число таких ответов для каждого IP.
4. При `count > 50` формирует предупреждение и пытается отправить его в Telegram.

Условие строгое: **50 ответов не вызывают предупреждение, 51 ответ вызывает**. Подсчитываются ответы во всем прочитанном файле; временной интервал исходный скрипт не задает.

### Что необходимо исправить

- Адрес Telegram API указан неверно. Правильный шаблон: `https://api.telegram.org/bot<TOKEN>/sendMessage`. В Python-коде должна находиться обычная строка URL, без Markdown-разметки ссылки.
- В исходнике отсутствуют тайм-аут и обработка ошибок HTTP или сети. Скрипт не проверяет, подтвердил ли Telegram отправку.
- Токен и ID чата представлены заглушками. Реальные значения требуется настроить; токен не следует помещать в публичный репозиторий.
- Чтение всего файла через `.read()` расходует память пропорционально размеру лога.
- Исходный шаблон ищет только IPv4 и не проверяет допустимость его октетов: например, `999.1.1.1` соответствует форме шаблона, но не является корректным IPv4-адресом. Также поиск не привязан к полю IP в начале записи.

## 2. Какое окружение нужно обеспечить?

### Для исходного скрипта и полного варианта с Telegram

| Компонент | Что необходимо |
| --- | --- |
| Python | Установленный Python 3; для нового окружения рекомендуется Python 3.11 или новее. |
| Зависимости | Библиотека `requests`; `re` и `collections` уже входят в Python. |
| Лог | Существующий текстовый файл access.log в ожидаемом формате. В исходнике путь фиксирован; в доработке задается через `--log`. |
| Права | Пользователь, запускающий скрипт, должен иметь право читать лог и проходить в его каталог. Запуск от root сам по себе не требуется. |
| Данные для обнаружения | Для предупреждения с исходным порогом нужны как минимум 51 запись с кодом 404 от одного IP. |
| Telegram | Созданный через `@BotFather` бот, его токен и ID целевого чата. Для личного чата пользователь предварительно начинает диалог с ботом; для группы бот должен быть добавлен и иметь возможность отправлять сообщения. |
| Сеть | Для отправки нужны DNS, доступ по HTTPS к `api.telegram.org` и корректная проверка TLS-сертификатов. |

Linux удобен для работы непосредственно на сервере Nginx, однако анализ скачанного лога можно выполнять и на macOS или Windows. Сам Nginx нужен для получения настоящего лога, но не для анализа уже существующего файла. Путь `/var/log/nginx/access.log` зависит от настройки сервера и не является универсальным.

Для режима отправки создать рядом со скриптом файл `requirements.txt` со следующим содержимым:

```text
requests>=2.32.4,<3
```

Подготовка окружения для отправки уведомлений, команды для Linux/macOS из каталога этой работы:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

В PowerShell на Windows окружение активируется командой `.venv\Scripts\Activate.ps1`; вместо `python3` обычно используется `python`.

### Для выполненной практической части

Достаточно Python 3 и учебного файла `sample_access.log`. В локальном режиме `requests` не импортируется: установка пакетов, доступ к сети, Telegram-бот и работающий Nginx не нужны. Фактический запуск выполнен на macOS с Python **3.9.6**.

## 3. Модификация скрипта и практическая проверка

Полный код приведен непосредственно в этом отчете. Сохранить следующий блок как `analyze_logs.py`.

### Полный код analyze_logs.py

```python
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
```

Выполнена часть задания по **анализу лога и выявлению подозрительных IP**. Для проверки создан искусственный лог в формате Nginx combined. Это учебные данные, а не лог действующего сервера Beget. Функция отправки в Telegram добавлена, но реальная доставка сообщения не проверялась: токен и ID чата не предоставлялись.

### Изменения в программе

1. Добавлены аргументы `--log`, `--status` и `--threshold`: можно выбрать файл, код ответа и порог без редактирования исходника.
2. По умолчанию выполняется локальный анализ с выводом предупреждений в терминал. Отправка включается явно через `--send`.
3. Файл читается построчно. В памяти хранятся счетчики по IP, а не весь текст лога.
4. Шаблон извлекает IP из начала строки и трехзначный HTTP-статус после запроса в кавычках. Число `404` внутри URL или User-Agent не принимается за код ответа.
5. Добавлена проверка IP через `ipaddress.ip_address()`; поддерживаются IPv4 и IPv6. Некорректные строки пропускаются и учитываются в отдельном счетчике.
6. Исправлен адрес Telegram API. Токен и ID чата читаются из переменных окружения. Добавлены тайм-ауты соединения и чтения, проверка HTTP-ответа и поля `ok` в JSON.
7. При недоступном файле или ошибке отправки выводится понятное сообщение, программа завершается с ненулевым кодом. Текст сетевого исключения с URL и токеном не выводится.

Дополнительно используются стандартные модули `argparse` для аргументов командной строки, `os` для переменных окружения, `sys` для потока ошибок и кода завершения, `ipaddress` для проверки и нормализации IP. Генератор примера использует `pathlib`, а проверки — `unittest` и `tempfile`. Их установка через pip не требуется.

### Учебный лог

Чтобы получить учебный `sample_access.log`, сохранить следующий блок как `generate_sample.py`. Генератор создает все необходимые строки локально и не обращается к реальным серверам.

### Полный код generate_sample.py

```python
"""Создает воспроизводимый учебный лог. Реальные серверы не используются."""

from pathlib import Path


def log_line(ip, path, status):
    return (
        f'{ip} - - [19/Oct/2026:00:00:00 +0700] '
        f'"GET {path} HTTP/1.1" {status} 123 "-" "StudyClient/1.0"\n'
    )


def main():
    lines = [log_line("192.0.2.10", f"/missing-{i}", 404) for i in range(51)]
    lines += [log_line("198.51.100.20", f"/not-found-{i}", 404) for i in range(50)]
    lines += [log_line("203.0.113.30", "/index.html", 200) for _ in range(3)]
    lines += [log_line("2001:db8::1", "/private", 403)]
    lines += ["Некорректная строка лога\n", log_line("999.1.1.1", "/missing", 404)]
    path = Path(__file__).with_name("sample_access.log")
    path.write_text("".join(lines), encoding="utf-8")
    print(f"Создан {path.name}: {len(lines)} строк.")


if __name__ == "__main__":
    main()
```

| IP / тип записи | Код | Число записей | Назначение |
| --- | --- | ---: | --- |
| `192.0.2.10` | 404 | 51 | Должен вызвать предупреждение. |
| `198.51.100.20` | 404 | 50 | Проверка границы: предупреждения быть не должно. |
| `203.0.113.30` | 200 | 3 | Успешные запросы не входят в счетчик 404. |
| `2001:db8::1` | 403 | 1 | Проверка IPv6 и выбора другого HTTP-статуса. |
| Некорректная строка и запись с `999.1.1.1` | — | 2 | Должны быть пропущены. |
| **Всего** | | **107** | |

Пример корректной записи:

```text
192.0.2.10 - - [19/Oct/2026:00:00:00 +0700] "GET /missing-0 HTTP/1.1" 404 123 "-" "StudyClient/1.0"
```

### Запуск и фактический результат

Для повторения практической части сохранить `analyze_logs.py` и `generate_sample.py` в одной папке. Из этой папки выполнить:

```bash
python3 generate_sample.py
python3 analyze_logs.py --log sample_access.log
```

Полученный вывод:

```text
Прочитано строк: 107
Пропущено некорректных строк: 2
Ответов с кодом 404: 101
Уникальных IP с кодом 404: 2
Обнаружена подозрительная активность! IP 192.0.2.10: ответов с кодом 404 — 51 (порог: > 50).
Режим локального анализа: отправка в Telegram отключена.
```

Программа завершилась с кодом `0`. Найден ровно один подозрительный IP. Адрес `198.51.100.20` с 50 ответами 404 не вызвал предупреждения, поэтому условие исходного задания сохранено.

Дополнительный запуск для другого статуса и IPv6:

```bash
python3 analyze_logs.py --log sample_access.log --status 403 --threshold 0
```

Результат: найден один ответ 403 от `2001:db8::1`, сформировано предупреждение при пороге `> 0`.

### Автоматические проверки

```bash
python3 -m unittest -v
```

Сохранить следующий блок как `test_analyze_logs.py` в той же папке. Проверки используют созданный выше учебный лог.

### Полный код test_analyze_logs.py

```python
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
```

Пройдены **7 тестов**: подсчет учебного лога; граница 50/51; IPv6 и статус 403; отсутствие ложного подсчета `404` из URL или User-Agent; некорректные строки и IP; пустой лог; отсутствующий файл.

```text
Ran 7 tests
OK
```

Результаты запуска и проверок приведены выше. Код из блоков этого Markdown-файла дополнительно извлечен в отдельную папку и проверен на Python 3.12.14: все 7 тестов прошли.

### Как включить Telegram

После установки `requests` задать реальные значения локально, не публикуя токен:

```bash
export TELEGRAM_TOKEN='ВСТАВЬТЕ_ТОКЕН_БОТА'
export CHAT_ID='ВСТАВЬТЕ_ID_ЧАТА'
python3 analyze_logs.py --log sample_access.log --send
```

Скрипт отправляет отдельное предупреждение на каждый IP, превысивший порог. В представленном учебном логе такой IP один. Эти команды описывают способ запуска; факт доставки сообщения в рамках работы не заявляется.

### Использование с настоящим логом

```bash
python3 analyze_logs.py --log /var/log/nginx/access.log
```

Для лога с хостинга нужно указать путь к скачанному файлу. Парсер рассчитан на структуру common/combined: IP, два служебных поля, время в квадратных скобках, запрос в кавычках, статус и размер ответа. Если порядок полей отличается, регулярное выражение необходимо адаптировать по реальной строке лога.

### Ограничения решения

Большое число 404 — повод проверить активность, но не доказательство атаки: причиной могут быть битые ссылки или особенности приложения. Подсчет ведется по всему файлу, без временного окна. При повторном запуске те же записи снова учитываются; позиция чтения и история предупреждений не сохраняются. Для постоянного мониторинга потребуются обработка только новых записей, учет ротации логов и защита от повторных уведомлений. За обратным прокси также необходимо убедиться, что первое поле содержит реальный адрес клиента.

## Итог

Изучены библиотеки исходного скрипта и требования к окружению. Исправлены ошибки и реализован работающий анализатор. Практически подтверждены чтение лога, отбор HTTP-статуса, подсчет запросов по IP и обнаружение превышения порога. Это выполняет требование задания о реализации хотя бы части функционала.

## Источники

- [Python: регулярные выражения и re.findall](https://docs.python.org/3/library/re.html#re.findall).
- [Python: collections.Counter](https://docs.python.org/3/library/collections.html#collections.Counter).
- [Requests: POST, JSON, обработка ошибок и тайм-ауты](https://requests.readthedocs.io/en/latest/user/quickstart/).
- [Telegram Bot API: формат запросов](https://core.telegram.org/bots/api#making-requests) и [sendMessage](https://core.telegram.org/bots/api#sendmessage).
- [Nginx: access_log и формат combined](https://nginx.org/en/docs/http/ngx_http_log_module.html#log_format).
- [Python: виртуальные окружения venv](https://docs.python.org/3/library/venv.html).
