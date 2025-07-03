import sqlite3
import os
from datetime import datetime, timedelta

class ExchangeRatesDB:
    def __init__(self, db_path="exchange_rates.db", days_to_keep=7):
        self.db_path = db_path
        self.days_to_keep = days_to_keep
        self._ensure_db()

    def _ensure_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS exchange_rates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                currency TEXT NOT NULL,
                buy REAL,
                sell REAL,
                date TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def add_rate(self, currency: str, buy: float, sell: float, date: str = None):
        if date is None:
            date = datetime.utcnow().strftime("%Y-%m-%d")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO exchange_rates (currency, buy, sell, date) VALUES (?, ?, ?, ?)",
            (currency, buy, sell, date)
        )
        conn.commit()
        conn.close()
        self._cleanup_old_data()

    def _cleanup_old_data(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT date FROM exchange_rates ORDER BY date DESC")
        dates = [row[0] for row in cursor.fetchall()]
        if len(dates) > self.days_to_keep:
            dates_to_delete = dates[self.days_to_keep:]
            cursor.execute(
                f"DELETE FROM exchange_rates WHERE date IN ({','.join('?' for _ in dates_to_delete)})",
                dates_to_delete
            )
            conn.commit()
        conn.close()

    def get_history(self, limit=30):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT date, 
                MAX(CASE WHEN currency='USD' THEN buy ELSE NULL END) AS usd,
                MAX(CASE WHEN currency='EUR' THEN buy ELSE NULL END) AS eur
            FROM exchange_rates
            GROUP BY date
            ORDER BY date DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [{"date": row[0], "usd": row[1], "eur": row[2]} for row in rows[::-1]]
