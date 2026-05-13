# 🔗 URL Shortener

A simple, serverless URL shortener built with **FastAPI** + **PostgreSQL (Supabase)** + **Vercel**.

## Deploy

See [`SETUP.md`](./SETUP.md) for a **2-minute one-time setup** that auto-deploys via GitHub Actions.

## Local Development

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Open http://localhost:8000

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/shorten` | Create short URL `{ "url": "...", "custom_code": "..." }` |
| GET | `/{short_code}` | Redirect to original URL |
| GET | `/api/stats/{short_code}` | Get clicks & metadata |
| GET | `/api/urls` | List all shortened URLs |
