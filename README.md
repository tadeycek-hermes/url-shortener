# 🔗 URL Shortener

A simple, self-hosted URL shortener built with **FastAPI** + **SQLite** and a vanilla JS frontend.

## Run locally

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the server
uvicorn main:app --reload

# 3. Open http://localhost:8000 in your browser
```

## Features

- Shorten any URL with an auto-generated 6-character code
- Optional custom short codes
- Click tracking
- Recent URLs list on the homepage
- REST API (`POST /api/shorten`, `GET /api/urls`, `GET /api/stats/{code}`)

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/shorten` | Create a short URL `{ "url": "...", "custom_code": "..." }` |
| GET | `/{short_code}` | Redirect to original URL |
| GET | `/api/stats/{short_code}` | Get clicks & metadata |
| GET | `/api/urls` | List all shortened URLs |
