import requests
from bs4 import BeautifulSoup

# Страница с курсами и нужные валюты.
URL = "https://www.cbr.ru/currency_base/daily/"
CURRENCIES = ("USD", "EUR", "CNY", "JPY")

try:
    # Загружаем HTML и проверяем HTTP-ответ.
    response = requests.get(URL, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")

    # Находим таблицу и дату действия курсов.
    table = soup.find("table", class_="data")
    date_input = soup.find("input", attrs={"name": "UniDbQuery.To"})
    if table is None or date_input is None or not date_input.get("value"):
        raise ValueError("Таблица или дата курсов не найдены.")

    # Проверяем, что порядок столбцов не изменился.
    headers = [" ".join(cell.get_text().split()) for cell in table.find_all("th")]
    if headers != ["Цифр. код", "Букв. код", "Единиц", "Валюта", "Курс"]:
        raise ValueError("Структура таблицы изменилась.")

    # Извлекаем данные из строк таблицы.
    rates = {}
    for row in table.find_all("tr"):
        cols = row.find_all("td")
        if len(cols) != 5:
            continue
        code = cols[1].get_text(strip=True)
        if code in CURRENCIES:
            units = cols[2].get_text(strip=True)
            currency = cols[3].get_text(strip=True)
            rate = cols[4].get_text(strip=True)
            rates[code] = f"{code} — {currency}: {rate} RUB за {units} ед."

    if len(rates) != len(CURRENCIES):
        raise ValueError("Не все выбранные валюты найдены.")

    # Выводим дату и найденные курсы.
    print("Дата действия курсов:", date_input["value"])
    for code in CURRENCIES:
        print(rates[code])
except (requests.RequestException, ValueError) as error:
    raise SystemExit(f"Ошибка: {error}")
