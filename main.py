from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse
from pydantic import BaseModel
import string
import random
import os
import pathlib
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

MONGODB_URI = os.environ.get("MONGODB_URI")

def get_db():
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    return client["url-shortener"]

def init_db():
    if not MONGODB_URI:
        return
    db = get_db()
    urls = db["urls"]
    urls.create_index("short_code", unique=True)
    urls.create_index("original_url")

def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits
    db = get_db()
    urls = db["urls"]
    while True:
        code = "".join(random.choices(chars, k=length))
        if not urls.find_one({"short_code": code}):
            return code

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

    db = get_db()
    urls = db["urls"]

    if req.custom_code:
        code = req.custom_code.strip()
        if not code or len(code) > 32:
            raise HTTPException(status_code=400, detail="Custom code must be 1-32 characters")
        if urls.find_one({"short_code": code}):
            raise HTTPException(status_code=409, detail="Custom code already in use")
    else:
        code = generate_short_code()

    import datetime
    urls.insert_one({
        "short_code": code,
        "original_url": original,
        "clicks": 0,
        "created_at": datetime.datetime.utcnow().isoformat()
    })

    base = os.environ.get("BASE_URL", "https://" + os.environ.get("VERCEL_URL", "localhost:8000"))
    return ShortenResponse(
        short_code=code,
        short_url=f"{base}/{code}",
        original_url=original
    )

@app.get("/{short_code}")
def redirect(short_code: str):
    db = get_db()
    urls = db["urls"]
    doc = urls.find_one({"short_code": short_code})
    if not doc:
        raise HTTPException(status_code=404, detail="Short URL not found")
    urls.update_one({"short_code": short_code}, {"$inc": {"clicks": 1}})
    return RedirectResponse(url=doc["original_url"])

@app.get("/api/stats/{short_code}", response_model=URLStats)
def get_stats(short_code: str):
    db = get_db()
    urls = db["urls"]
    doc = urls.find_one({"short_code": short_code})
    if not doc:
        raise HTTPException(status_code=404, detail="Short URL not found")
    return URLStats(
        short_code=doc["short_code"],
        original_url=doc["original_url"],
        clicks=doc.get("clicks", 0),
        created_at=doc.get("created_at", "")
    )

@app.get("/api/urls")
def list_urls():
    db = get_db()
    urls = db["urls"]
    docs = urls.find().sort("created_at", -1)
    result = []
    for doc in docs:
        result.append({
            "short_code": doc["short_code"],
            "original_url": doc["original_url"],
            "clicks": doc.get("clicks", 0),
            "created_at": doc.get("created_at", "")
        })
    return result

# Vercel serverless handler
from mangum import Mangum
handler = Mangum(app)
