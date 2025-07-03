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
        cursor = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        return cursor.fetchone() is not None

    def remove_old_news(self, days_to_keep):
        if not self._table_exists('news'):
            print("[INFO] Таблиця 'news' відсутня — очищення не проводиться.")
            return

        cutoff = datetime.now() - timedelta(days=days_to_keep)
        cutoff_ts = int(cutoff.timestamp())

        cursor = self.conn.execute(
            "SELECT id, channel, media_files FROM news WHERE strftime('%s', created_at) < ?",
            (cutoff_ts,)
        )
        to_delete = cursor.fetchall()

        for row in to_delete:
            channel_dir = os.path.join(self.media_root, row["channel"])
            if row["media_files"]:
                for file in row["media_files"].split(";"):
                    path = file.strip()
                    if path and os.path.exists(path):
                        try:
                            os.remove(path)
                        except Exception as e:
                            print(f"[WARN] Не вдалося видалити {path}: {e}")

        self.conn.execute(
            "DELETE FROM news WHERE strftime('%s', created_at) < ?",
            (cutoff_ts,)
        )
        self.conn.commit()
        print(f"[INFO] Видалено {len(to_delete)} новин старше {days_to_keep} днів.")

    def close(self):
        self.conn.close()
