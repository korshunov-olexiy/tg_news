import requests
from bs4 import BeautifulSoup


class CurrencyRates:
    URL = "https://rates.com.ua/sumy"
    HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"}

    def __init__(self):
        self.rates = {}

    def fetch(self):
        response = requests.get(self.URL, headers=self.HEADERS, verify=False, timeout=10)
        if response.status_code != 200:
            raise Exception(f"HTTP error {response.status_code}")
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.select_one("table.summary-rates.full-rates tbody")
        if not table:
            raise Exception("Не знайдено таблицю курсів")
        def safe_float(text):
            text = text.strip()
            if text == '—':
                return None
            return float(text.replace(",", "."))
        result = {}
        for row in table.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) != 5:
                continue
            currency = cols[1].get_text(strip=True)
            buy = safe_float(cols[3].get_text())
            sell = safe_float(cols[4].get_text())
            if currency == "USD":
                result["usd"] = {"buy": buy, "sell": sell}
            elif currency == "EUR":
                result["eur"] = {"buy": buy, "sell": sell}
        if not result:
            raise Exception("Не знайдено курсів USD/EUR")
        self.rates = result
        return result

    def get_rates(self):
        if not self.rates:
            return self.fetch()
        return self.rates
