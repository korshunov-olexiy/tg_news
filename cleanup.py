import os
import sqlite3
from datetime import datetime, timedelta

class NewsCleaner:
    def __init__(self, db_path='news.db', media_root='media'):
        self.db_path = db_path
        self.media_root = media_root
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def _table_exists(self, table_name):
        cursor = self.conn.execute( "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,) )
        return cursor.fetchone() is not None

    def remove_old_news(self, days_to_keep):
        if not self._table_exists('news'):
            print("[INFO] Таблиця 'news' відсутня — очищення не проводиться.")
            return
        if days_to_keep == 0:  # якщо передали 0, то відбираємо всі записи для видалення
            cursor = self.conn.execute("SELECT id, channel, media_files FROM news")
        else:
            cutoff = datetime.now() - timedelta(days=days_to_keep)
            cutoff_ts = int(cutoff.timestamp())
            cursor = self.conn.execute( "SELECT id, channel, media_files FROM news WHERE strftime('%s', created_at) < ?", (cutoff_ts,) )
        to_delete = cursor.fetchall()
        for row in to_delete:
            if row["media_files"]:
                for file in row["media_files"].split(";"):
                    path = file.strip()
                    if path and os.path.exists(path):
                        try:
                            os.remove(path)
                        except Exception as e:
                            print(f"[WARN] Не вдалося видалити {path}: {e}")
        if days_to_keep == 0:
            self.conn.execute("DELETE FROM news")
        else:
            self.conn.execute( "DELETE FROM news WHERE strftime('%s', created_at) < ?", (cutoff_ts,) )
        self.conn.commit()
        print(f"[INFO] Видалено {len(to_delete)} новин.")

    def close(self):
        self.conn.close()
