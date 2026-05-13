from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
import string
import random
import os
import pathlib

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def init_db():
    conn = psycopg2.connect(DATABASE_URL)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            id SERIAL PRIMARY KEY,
            short_code VARCHAR(32) UNIQUE NOT NULL,
            original_url TEXT NOT NULL,
            clicks INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choices(chars, k=length))
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT 1 FROM urls WHERE short_code = %s", (code,))
        if not c.fetchone():
            conn.close()
            return code
        conn.close()

app = FastAPI(title="URL Shortener")

BASE_DIR = pathlib.Path(__file__).parent.resolve()
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

class ShortenRequest(BaseModel):
    url: str
    custom_code: str | None = None

class ShortenResponse(BaseModel):
    short_code: str
    short_url: str
    original_url: str

class URLStats(BaseModel):
    short_code: str
    original_url: str
    clicks: int
    created_at: str

@app.on_event("startup")
def startup():
    init_db()

@app.get("/")
def read_index():
    return FileResponse(BASE_DIR / "static" / "index.html")

@app.post("/api/shorten", response_model=ShortenResponse)
def shorten_url(req: ShortenRequest):
    original = req.url.strip()
    if not original.startswith(("http://", "https://")):
        original = "https://" + original

    if req.custom_code:
        code = req.custom_code.strip()
        if not code or len(code) > 32:
            raise HTTPException(status_code=400, detail="Custom code must be 1-32 characters")
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT 1 FROM urls WHERE short_code = %s", (code,))
        if c.fetchone():
            conn.close()
            raise HTTPException(status_code=409, detail="Custom code already in use")
    else:
        code = generate_short_code()

    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO urls (short_code, original_url) VALUES (%s, %s)", (code, original))
    conn.commit()
    conn.close()

    base = os.environ.get("BASE_URL", "https://url-shortener-nine-nu.vercel.app")
    return ShortenResponse(
        short_code=code,
        short_url=f"{base}/{code}",
        original_url=original
    )

@app.get("/{short_code}")
def redirect(short_code: str):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT original_url FROM urls WHERE short_code = %s", (short_code,))
    row = c.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Short URL not found")
    original = row["original_url"]
    c.execute("UPDATE urls SET clicks = clicks + 1 WHERE short_code = %s", (short_code,))
    conn.commit()
    conn.close()
    return RedirectResponse(url=original)

@app.get("/api/stats/{short_code}", response_model=URLStats)
def get_stats(short_code: str):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT short_code, original_url, clicks, created_at FROM urls WHERE short_code = %s", (short_code,))
    row = c.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Short URL not found")
    return URLStats(
        short_code=row["short_code"],
        original_url=row["original_url"],
        clicks=row["clicks"],
        created_at=str(row["created_at"])
    )

@app.get("/api/urls")
def list_urls():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT short_code, original_url, clicks, created_at FROM urls ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# Vercel serverless handler
from mangum import Mangum
handler = Mangum(app)
