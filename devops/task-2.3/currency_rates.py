#!/usr/bin/env python3
"""Получает официальные курсы валют с HTML-страницы Банка России."""

import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

import requests
from bs4 import BeautifulSoup


URL = "https://www.cbr.ru/currency_base/daily/"
CURRENCIES = ("USD", "EUR", "CNY", "JPY")
OUTPUT_FILE = Path(__file__).with_name("rates.txt")
HEADERS = ["Цифр. код", "Букв. код", "Единиц", "Валюта", "Курс"]


def parse_rates(html):
    """Извлекает дату действия и курсы из HTML; не выполняет сетевых запросов."""
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_="data")
    if table is None:
        raise ValueError("Таблица курсов не найдена: проверьте структуру сайта.")
    headers = [" ".join(cell.get_text().split()) for cell in table.find_all("th")]
    if headers != HEADERS:
        raise ValueError("Столбцы таблицы изменились: нужно обновить парсер.")

    date_input = soup.find("input", attrs={"name": "UniDbQuery.To"})
    date_text = date_input.get("value", "") if date_input else ""
    try:
        datetime.strptime(date_text, "%d.%m.%Y")
    except ValueError:
        raise ValueError("Не найдена корректная дата действия курсов.") from None

    rates = {}
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if not cells:  # Строка заголовка содержит th, поэтому пропускается.
            continue
        if len(cells) != 5:
            raise ValueError("Неожиданное число столбцов в строке курса.")
        code = cells[1].get_text(strip=True)
        currency = cells[3].get_text(" ", strip=True)
        try:
            units = int("".join(cells[2].get_text().split()))
            rate = Decimal("".join(cells[4].get_text().split()).replace(",", "."))
        except (ValueError, InvalidOperation):
            raise ValueError(f"Некорректное числовое значение для {code}.") from None
        if units <= 0 or not rate.is_finite() or rate <= 0:
            raise ValueError(f"Некорректный номинал или курс для {code}.")
        rates[code] = {"currency": currency, "units": units, "rate": rate}
    if not rates:
        raise ValueError("Таблица курсов пуста.")
    return date_text, rates


def format_report(date_text, rates, currencies=CURRENCIES):
    lines = [f"Источник: {URL}", f"Дата действия курсов: {date_text}"]
    for code in currencies:
        if code not in rates:
            raise ValueError(f"Валюта {code} не найдена в таблице.")
        item = rates[code]
        rate = f"{item['rate']:.4f}".replace(".", ",")
        lines.append(f"{code} — {item['currency']}: {rate} RUB за {item['units']} ед.")
        if item["units"] != 1:
            per_unit = f"{item['rate'] / item['units']:.6f}".replace(".", ",")
            lines.append(f"  За 1 {code}: {per_unit} RUB (до 6 знаков после запятой).")
    return "\n".join(lines) + "\n"


def main():
    try:
        response = requests.get(URL, timeout=10)
        response.raise_for_status()
        # Передаем исходные байты: BeautifulSoup определит кодировку HTML.
        date_text, rates = parse_rates(response.content)
        report = format_report(date_text, rates)
        OUTPUT_FILE.write_text(report, encoding="utf-8")
    except requests.RequestException as error:
        print(f"Ошибка загрузки страницы: {error}", file=sys.stderr)
        return 1
    except (ValueError, OSError) as error:
        print(f"Ошибка обработки: {error}", file=sys.stderr)
        return 1
    print(report, end="")
    print(f"Результат сохранен в {OUTPUT_FILE.name}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
