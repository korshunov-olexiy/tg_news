import json
import os
import re

from markdown_it import MarkdownIt


class NewsProcessor:
    def __init__(self):
        # ключові слова, по яким видаляється весь рядок з новини
        self.banned_words = ["підписатись", "відправити новину", "war zone", "подписаться", "https://t.me/sluhaiukr"]
        self.md = MarkdownIt("commonmark")
        self.empty_p_pattern = re.compile(r"<p>\s*</p>", re.IGNORECASE)
        # Додатково прибираємо markdown-символи, якщо залишилися
        self.basic_md_cleanup = re.compile(r"[*_`~]+", re.MULTILINE)

    def clean_markdown(self, text: str) -> str:
        if not text:
            return ""
        # Видалити все, що містить ключові слова (жорстко)
        lines = text.splitlines()
        cleaned_lines = []
        for line in lines:
            if any(kw.lower() in line.lower() for kw in self.banned_words):
                continue  # ігнорувати ці рядки повністю
            cleaned_lines.append(line)
        return "\n".join(cleaned_lines).strip()

    def process(self, text: str) -> str:
        if not text:
            return ""
        cleaned_md = self.clean_markdown(text)
        html = self.md.render(cleaned_md)
        return html
