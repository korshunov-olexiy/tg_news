import requests
from bs4 import BeautifulSoup


class CurrencyRates:
    URL = "https://minfin.com.ua/ua/currency/sumy/"
    HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"}

    def __init__(self):
        self.rates = {}

    def fetch(self):
        currency_names = ['USD', 'EUR']
        response = requests.get(self.URL, headers=self.HEADERS, timeout=10)
        if response.status_code != 200:
            raise Exception(f"HTTP error {response.status_code}")
        
        soup = BeautifulSoup(response.text, "html.parser")
        # отримуємо таблицю по 'css selector'
        table = soup.select_one(".bvp3d3-11 > table:nth-child(1)")
        if not table:
            raise Exception("Не знайдено таблицю курсів валют")

        def safe_float(text):
            text = text.strip().replace(",", ".")
            try:
                return float(text)
            except ValueError:
                return None
        result = {}
        rows = table.select("tbody tr")
        for row in rows:
            cols = row.find_all("td")
            if len(cols) != 3:
                continue
            name_tag = cols[0].find("a")
            if not name_tag or name_tag.text.strip() not in currency_names:
                continue
            currency = name_tag.text.strip()
            buy_block = cols[1].find("div", recursive=True)
            sell_block = cols[2].find("div", recursive=True)
            buy = safe_float(buy_block.contents[0]) if buy_block and buy_block.contents else None
            sell = safe_float(sell_block.contents[0]) if sell_block and sell_block.contents else None
            print(currency, buy, sell)
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
