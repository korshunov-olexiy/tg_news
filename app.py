import json
import os
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from telethon import TelegramClient
from telethon.errors import MessageIdInvalidError
from telethon.tl.types import MessageMediaDocument, MessageMediaPhoto

from modules.currency import CurrencyRates
from modules.debuger import Debugger
from modules.exchange import ExchangeRatesDB
from modules.formatter import NewsProcessor

DB_PATH = "news.db"
MEDIA_FOLDER = "media"
SESSION_FILE = "tg.session"

os.makedirs(MEDIA_FOLDER, exist_ok=True)

with open("config.json", "r") as f:
    config = json.load(f)

API_ID = config["api_id"]
API_HASH = config["api_hash"]
CHANNELS = config["channels"]
DAYS_TO_KEEP = config.get("days_to_keep", 30)
NEWS_UPDATE_INTERVAL_MINUTES = config.get("news_update_in_minutes", 60)
MAX_FILE_SIZE_MB = config.get("MAX_FILE_SIZE_MB", 25)

Debugger.set_enabled(config.get("debug", False))

client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
processor = NewsProcessor()
currency = CurrencyRates()
exchange_db = ExchangeRatesDB()

templates = Jinja2Templates(directory="templates")
ITEMS_PER_PAGE = 50

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media", StaticFiles(directory=MEDIA_FOLDER), name="media")

def format_datetime(value):
    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime("%d.%m.%Y %H:%M")
    except Exception:
        return value

templates.env.filters["format_datetime"] = format_datetime

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY,
            message_id INTEGER,
            channel TEXT,
            text TEXT,
            media_files TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def cleanup_old_news():
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(days=DAYS_TO_KEEP - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, media_files FROM news WHERE created_at < ?", (cutoff.isoformat(),))
    rows = cursor.fetchall()
    for news_id, media_files in rows:
        if media_files:
            for path in media_files.split(";"):
                if os.path.exists(path):
                    os.remove(path)
        cursor.execute("DELETE FROM news WHERE id = ?", (news_id,))
    conn.commit()
    conn.close()

def get_file_extension(message):
    ext = ".bin"
    if isinstance(message.media, MessageMediaPhoto):
        ext = ".jpg"
    elif isinstance(message.media, MessageMediaDocument) and message.file and message.file.ext:
        ext = message.file.ext.lower()
        if not ext.startswith("."):
            ext = "." + ext
    return ext

def news_exists(channel, message_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM news WHERE channel = ? AND message_id = ?", (channel, message_id))
    result = cursor.fetchone() is not None
    conn.close()
    return result

def save_news(channel, message_id, text, media_files, created_at):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO news (message_id, channel, text, media_files, created_at) VALUES (?, ?, ?, ?, ?)",
                   (message_id, channel, text, media_files, created_at.isoformat()))
    conn.commit()
    conn.close()

def get_news(channel=None, date_from=None, date_to=None, query_text=None, offset=0, limit=50):
    if not os.path.exists(DB_PATH):
        return [], 0
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    where_clauses = []
    params = []
    if channel:
        where_clauses.append("channel = ?")
        params.append(channel)
    if date_from:
        where_clauses.append("created_at >= ?")
        params.append(date_from)
    if date_to:
        where_clauses.append("created_at <= ?")
        params.append(date_to)
    if query_text:
        where_clauses.append("text LIKE ?")
        params.append(f"%{query_text}%")
    where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    count_query = f"SELECT COUNT(*) FROM news {where_clause}"
    cursor.execute(count_query, tuple(params))
    total = cursor.fetchone()[0]
    query = f"""
        SELECT text, media_files, created_at FROM news
        {where_clause}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])
    cursor.execute(query, tuple(params))
    news = cursor.fetchall()
    result = []
    for n in news:
        text = processor.process(n[0])
        media_files = [m for m in (n[1] or "").split(";") if m.startswith("media/") and os.path.exists(m) or not m.startswith("media/")]
        result.append((text, ";".join(media_files), n[2]))
    conn.close()
    return result, total

async def fetch_news():
    max_file_size = MAX_FILE_SIZE_MB * 1024 * 1024
    now = datetime.now(timezone.utc)
    date_limit = (now - timedelta(days=DAYS_TO_KEEP - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
    for channel in CHANNELS.keys():
        media_dir = os.path.join(MEDIA_FOLDER, channel)
        os.makedirs(media_dir, exist_ok=True)
        async for message in client.iter_messages(f"@{channel}", offset_date=date_limit, reverse=True):
            if news_exists(channel, message.id):
                continue
            media_files = []
            if message.media:
                try:
                    filename = f"{message.id}" + get_file_extension(message)
                    media_path = os.path.join(media_dir, filename)
                    if isinstance(message.media, MessageMediaPhoto) or (isinstance(message.media, MessageMediaDocument) and message.file and message.file.size <= max_file_size):
                        await client.download_media(message, file=media_path)
                        media_files.append(media_path)
                    else:
                        media_files.append(f"https://t.me/{channel}/{message.id}")
                except Exception as e:
                    print(f"[ERR] Завантаження медіа: {e}")
            save_news(channel, message.id, message.text or "", ";".join(media_files), message.date)

async def fetch_exchange_rates():
    try:
        rates = currency.fetch()
        for code in ("usd", "eur"):
            data = rates.get(code)
            if data:
                exchange_db.add_rate(code.upper(), data['buy'], data['sell'])
    except Exception as e:
        print(f"[ERR] Оновлення курсів валют: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    await client.start()
    init_db()

    from asyncio import create_task, sleep

    async def background_tasks():
        last_cleanup_time = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        while True:
            try:
                if datetime.now(timezone.utc) > last_cleanup_time:
                    cleanup_old_news()
                    await fetch_exchange_rates()
                    last_cleanup_time = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
                await fetch_news()
                await fetch_exchange_rates()
            except Exception as e:
                print(f"[ERR] Background: {e}")
            await sleep(NEWS_UPDATE_INTERVAL_MINUTES * 60)

    create_task(background_tasks())
    yield
    await client.disconnect()

app.router.lifespan_context = lifespan

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, channel: str = Query(None), date_from: str = Query(None), date_to: str = Query(None), search: str = Query(None), page: int = Query(1)):
    current_channel = channel or (list(CHANNELS.keys())[0] if CHANNELS else None)
    offset = (page - 1) * ITEMS_PER_PAGE
    news, total = get_news(current_channel, date_from, date_to, search, offset, ITEMS_PER_PAGE)
    total_pages = (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    return templates.TemplateResponse("index.html", {
        "request": request,
        "channel_map": CHANNELS,
        "channel_list": list(CHANNELS.items()),
        "channels": list(CHANNELS.keys()),
        "selected_channel": current_channel,
        "news": news,
        "page": page,
        "total_pages": total_pages,
        "search": search or "",
        "date_from": date_from or "",
        "date_to": date_to or "",
    })

@app.get("/api/rates")
async def get_rates():
    try:
        return currency.fetch()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/exchange-history")
def exchange_history(limit: int = 30):
    return exchange_db.get_history(limit=limit)

class DownloadMediaRequest(BaseModel):
    channel: str
    message_id: int

class DeleteMediaRequest(BaseModel):
    filename: str

@app.post("/api/download-media")
async def download_media_api(data: DownloadMediaRequest):
    try:
        message = await client.get_messages(data.channel, ids=data.message_id)
        if not message or not message.media:
            raise HTTPException(status_code=404, detail="Медіа не знайдено")
        ext = get_file_extension(message)
        media_dir = os.path.join(MEDIA_FOLDER, data.channel)
        os.makedirs(media_dir, exist_ok=True)
        filename = f"{data.message_id}{ext}"
        path = os.path.join(media_dir, filename)
        if not os.path.exists(path):
            await client.download_media(message, file=path)
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT media_files FROM news WHERE channel = ? AND message_id = ?", (data.channel, data.message_id))
            row = cursor.fetchone()
            if row:
                current_media_files = row[0] or ""
                files = [f for f in current_media_files.split(";") if f]
                if path not in files:
                    files.append(path)
                    cursor.execute("UPDATE news SET media_files = ? WHERE channel = ? AND message_id = ?", (";".join(files), data.channel, data.message_id))
                    conn.commit()
            conn.close()
        return {"filename": path}
    except MessageIdInvalidError:
        raise HTTPException(status_code=404, detail="Невірний ID повідомлення")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/delete-media")
def delete_media_api(data: DeleteMediaRequest):
    try:
        if os.path.exists(data.filename):
            os.remove(data.filename)
            return {"deleted": True}
        else:
            raise HTTPException(status_code=404, detail="Файл не знайдено")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
