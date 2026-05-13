from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel
from pymongo import MongoClient
from bson import ObjectId
import string
import random
import os
import datetime
from mangum import Mangum

MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
client = MongoClient(MONGODB_URI)
db = client.hermes_url_shortener
collection = db.urls

def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choices(chars, k=length))
        if not collection.find_one({"short_code": code}):
            return code

app = FastAPI(title="URL Shortener")

class ShortenRequest(BaseModel):
    url: str
    custom_code: str | None = None

class ShortenResponse(BaseModel):
    short_code: str
    short_url: str
    original_url: str

index_html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>URL Shortener</title>
<style>
:root{--bg:#0f172a;--card:#1e293b;--text:#f8fafc;--muted:#94a3b8;--accent:#38bdf8;--accent2:#818cf8;--error:#f87171;--success:#34d399}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Segoe UI',system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--text);min-height:100vh;padding:2rem 1rem}
.container{width:100%;max-width:720px;margin:0 auto}
h1{font-size:2rem;margin-bottom:1.5rem;text-align:center;background:linear-gradient(90deg,var(--accent),var(--accent2));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
h2{font-size:1.25rem;margin:2rem 0 1rem;color:var(--muted)}
.card{background:var(--card);border:1px solid #334155;border-radius:12px;padding:1.25rem;margin-bottom:1rem}
.input-card{display:flex;flex-direction:column;gap:0.75rem}
input{background:#0b1220;border:1px solid #334155;border-radius:8px;padding:0.75rem 1rem;color:var(--text);font-size:1rem;outline:none;transition:border-color .2s}
input:focus{border-color:var(--accent)}
button{background:linear-gradient(90deg,var(--accent),var(--accent2));border:none;border-radius:8px;padding:0.75rem 1rem;color:#0f172a;font-weight:700;font-size:1rem;cursor:pointer;transition:opacity .2s,transform .1s}
button:hover{opacity:.9}button:active{transform:scale(0.98)}
.result-card p{margin-bottom:0.5rem}
.short-url-row{display:flex;gap:0.5rem;align-items:center}
.short-url-row a{color:var(--accent);text-decoration:none;font-weight:600;font-size:1.1rem;word-break:break-all;flex:1}
.short-url-row a:hover{text-decoration:underline}
.meta{font-size:.85rem;color:var(--muted);margin-top:0.5rem}
.error-card{background:rgba(248,113,113,.1);border-color:var(--error);color:var(--error)}
.hidden{display:none!important}
.url-list{display:flex;flex-direction:column;gap:0.75rem}
.url-item{background:var(--card);border:1px solid #334155;border-radius:10px;padding:1rem;display:flex;flex-direction:column;gap:0.4rem}
.url-item .top{display:flex;justify-content:space-between;align-items:center;gap:0.5rem}
.url-item a.short{color:var(--accent);font-weight:600;text-decoration:none}
.url-item a.short:hover{text-decoration:underline}
.url-item .original{color:var(--muted);font-size:.85rem;word-break:break-all}
.url-item .stats{font-size:.8rem;color:#64748b}
.empty{text-align:center;color:var(--muted);padding:2rem}
</style>
</head>
<body>
<div class="container">
<h1>🔗 URL Shortener</h1>
<div class="card input-card">
<input type="text" id="urlInput" placeholder="Paste a long URL here..." />
<input type="text" id="customCodeInput" placeholder="Custom short code (optional)" />
<button id="shortenBtn">Shorten</button>
</div>
<div id="result" class="card result-card hidden">
<p>Your short URL:</p>
<div class="short-url-row">
<a id="shortUrl" href="#" target="_blank"></a>
<button id="copyBtn">Copy</button>
</div>
<p class="meta" id="metaText"></p>
</div>
<div id="error" class="card error-card hidden"></div>
<h2>Recent URLs</h2>
<div id="urlList" class="url-list"></div>
</div>
<script>
const API="";
const urlInput=document.getElementById("urlInput"),customInput=document.getElementById("customCodeInput"),shortenBtn=document.getElementById("shortenBtn"),resultCard=document.getElementById("result"),shortUrlA=document.getElementById("shortUrl"),copyBtn=document.getElementById("copyBtn"),metaText=document.getElementById("metaText"),errorCard=document.getElementById("error"),urlList=document.getElementById("urlList");
async function shorten(){const url=urlInput.value.trim(),custom=customInput.value.trim()||undefined;if(!url){showError("Please enter a URL");return}shortenBtn.disabled=true;shortenBtn.textContent="Shortening...";hideError();resultCard.classList.add("hidden");try{const res=await fetch("/api/shorten",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({url,custom_code:custom})});const data=await res.json();if(!res.ok){showError(data.detail||"Something went wrong");return}shortUrlA.href=data.short_url;shortUrlA.textContent=data.short_url;metaText.textContent="Redirects to: "+data.original_url;resultCard.classList.remove("hidden");urlInput.value="";customInput.value="";loadUrls()}catch(e){showError("Network error. Is the backend running?")}finally{shortenBtn.disabled=false;shortenBtn.textContent="Shorten"}}
function showError(msg){errorCard.textContent=msg;errorCard.classList.remove("hidden")}
function hideError(){errorCard.classList.add("hidden")}
copyBtn.addEventListener("click",async()=>{try{await navigator.clipboard.writeText(shortUrlA.href);copyBtn.textContent="Copied!";setTimeout(()=>copyBtn.textContent="Copy",1500)}catch{copyBtn.textContent="Failed"}});
shortenBtn.addEventListener("click",shorten);
urlInput.addEventListener("keydown",e=>{if(e.key==="Enter")shorten()});
async function loadUrls(){try{const res=await fetch("/api/urls");const data=await res.json();urlList.innerHTML="";if(data.length===0){urlList.innerHTML=`<div class="empty">No URLs yet. Create one above!</div>`;return}for(const item of data){const div=document.createElement("div");div.className="url-item";div.innerHTML=`<div class="top"><a class="short" href="/${item.short_code}" target="_blank">${location.origin}/${item.short_code}</a><span class="stats">${item.clicks} clicks</span></div><div class="original">${item.original_url}</div><div class="stats">${item.created_at}</div>`;urlList.appendChild(div)}}catch(e){urlList.innerHTML=`<div class="empty">Could not load recent URLs.</div>`}}
loadUrls();
</script>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
def read_index():
    return index_html

@app.post("/api/shorten")
def shorten_url(req: ShortenRequest):
    original = req.url.strip()
    if not original.startswith(("http://", "https://")):
        original = "https://" + original

    if req.custom_code:
        code = req.custom_code.strip()
        if not code or len(code) > 32:
            raise HTTPException(status_code=400, detail="Custom code must be 1-32 characters")
        if collection.find_one({"short_code": code}):
            raise HTTPException(status_code=409, detail="Custom code already in use")
    else:
        code = generate_short_code()

    collection.insert_one({
        "short_code": code,
        "original_url": original,
        "clicks": 0,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat() + "Z",
    })

    base = os.environ.get("BASE_URL", "https://url-shortener-flax-theta.vercel.app")
    return {
        "short_code": code,
        "short_url": f"{base}/{code}",
        "original_url": original
    }

@app.get("/{short_code}")
def redirect(short_code: str):
    doc = collection.find_one({"short_code": short_code})
    if not doc:
        raise HTTPException(status_code=404, detail="Short URL not found")
    collection.update_one({"short_code": short_code}, {"$inc": {"clicks": 1}})
    return RedirectResponse(url=doc["original_url"])

@app.get("/api/stats/{short_code}")
def get_stats(short_code: str):
    doc = collection.find_one({"short_code": short_code})
    if not doc:
        raise HTTPException(status_code=404, detail="Short URL not found")
    return {
        "short_code": doc["short_code"],
        "original_url": doc["original_url"],
        "clicks": doc.get("clicks", 0),
        "created_at": doc.get("created_at", "")
    }

@app.get("/api/urls")
def list_urls():
    urls = list(collection.find().sort("created_at", -1).limit(50))
    return [{"short_code": u["short_code"], "original_url": u["original_url"], "clicks": u.get("clicks", 0), "created_at": u.get("created_at", "")} for u in urls]

# Vercel serverless handler
from mangum import Mangum
handler = Mangum(app, lifespan="off")
