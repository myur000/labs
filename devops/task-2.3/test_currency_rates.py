"""Проверки HTML-парсера на искусственном фрагменте, без доступа к сети."""

import unittest
from decimal import Decimal

import requests
from unittest.mock import patch

from currency_rates import format_report, main, parse_rates


# Искусственные значения: это тестовые данные, не текущие курсы.
HTML = '''
<html><input name="UniDbQuery.To" value="17.10.2026">
<table class="data"><tbody>
<tr><th>Цифр. код</th><th>Букв. код</th><th>Единиц</th><th>Валюта</th><th>Курс</th></tr>
<tr><td>840</td><td>USD</td><td>1</td><td>Доллар США</td><td>90,1234</td></tr>
<tr><td>392</td><td>JPY</td><td>100</td><td>Иен</td><td>60,0000</td></tr>
<tr><td>156</td><td>CNY</td><td>1</td><td><span>Юань</span></td><td>12,3456</td></tr>
</tbody></table></html>
'''


class CurrencyParserTests(unittest.TestCase):
    def test_currency_comes_from_fourth_cell_and_rate_from_fifth(self):
        date, rates = parse_rates(HTML)
        self.assertEqual(date, "17.10.2026")
        self.assertEqual(rates["USD"], {"currency": "Доллар США", "units": 1, "rate": Decimal("90.1234")})
        self.assertEqual(rates["CNY"]["currency"], "Юань")

    def test_nominal_and_conversion_to_one_unit(self):
        date, rates = parse_rates(HTML)
        report = format_report(date, rates, currencies=("JPY",))
        self.assertIn("60,0000 RUB за 100 ед.", report)
        self.assertIn("За 1 JPY: 0,600000 RUB", report)

    def test_nonbreaking_spaces_in_numbers(self):
        html = HTML.replace("90,1234", "1&nbsp;090,1234")
        self.assertEqual(parse_rates(html)[1]["USD"]["rate"], Decimal("1090.1234"))

    def test_missing_table(self):
        with self.assertRaisesRegex(ValueError, "Таблица"):
            parse_rates("<html>Страница недоступна</html>")

    def test_changed_columns(self):
        with self.assertRaisesRegex(ValueError, "Столбцы"):
            parse_rates(HTML.replace("Букв. код", "Другой столбец"))

    def test_invalid_date(self):
        with self.assertRaisesRegex(ValueError, "дата"):
            parse_rates(HTML.replace("17.10.2026", "32.13.2026"))

    def test_invalid_number_and_nominal(self):
        for html in [HTML.replace("90,1234", "нет данных"), HTML.replace("90,1234", "NaN"), HTML.replace("<td>100</td>", "<td>0</td>")]:
            with self.subTest(html=html):
                with self.assertRaises(ValueError):
                    parse_rates(html)

    def test_currency_missing_from_table(self):
        date, rates = parse_rates(HTML)
        with self.assertRaisesRegex(ValueError, "EUR"):
            format_report(date, rates, currencies=("EUR",))

    def test_network_failure_does_not_write_report(self):
        with patch("currency_rates.requests.get", side_effect=requests.Timeout("timeout")), patch("currency_rates.OUTPUT_FILE") as output, patch("sys.stderr"):
            self.assertEqual(main(), 1)
            output.write_text.assert_not_called()


if __name__ == "__main__":
    unittest.main()
