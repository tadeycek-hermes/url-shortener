# 🚀 One-Time Setup Guide (2 minutes)

This app auto-deploys to Vercel + Supabase via GitHub Actions. You only need to do this once.

---

## Step 1: Create Supabase Database (30 sec)

1. Go to [supabase.com](https://supabase.com) → **Sign Up** (use GitHub, fastest)
2. Click **New Project** → name it `url-shortener`
3. Wait ~1 min for provisioning
4. Go to **SQL Editor** (left sidebar) → click **New Query**
5. Paste and run:

```sql
CREATE TABLE IF NOT EXISTS urls (
    id SERIAL PRIMARY KEY,
    short_code VARCHAR(32) UNIQUE NOT NULL,
    original_url TEXT NOT NULL,
    clicks INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

6. Go to **Project Settings** → **Database** → copy the **Transaction pooler** connection string (starts with `postgresql://...`)

---

## Step 2: Create Vercel Account (30 sec)

1. Go to [vercel.com/signup](https://vercel.com/signup) → **Continue with GitHub**
2. Done — no extra verification needed since GitHub already verified your email

---

## Step 3: Get Tokens (30 sec)

### Vercel Token
1. Go to [vercel.com/account/tokens](https://vercel.com/account/tokens)
2. Click **Create Token** → name it `url-shortener-deploy`
3. Copy the token

### Supabase Connection String
You already copied this in Step 1. It looks like:
```
postgresql://postgres.xxxxx:password@aws-0-eu-central-1.pooler.supabase.com:6543/postgres
```

---

## Step 4: Add GitHub Secrets (30 sec)

1. Go to your GitHub repo: `https://github.com/tadeycek-hermes/url-shortener`
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** and add these two:

| Name | Value |
|------|-------|
| `VERCEL_TOKEN` | Your Vercel token from Step 3 |
| `DATABASE_URL` | Your Supabase connection string from Step 3 |

---

## Step 5: Deploy 🎉

Push any change to the repo (or just click **Actions** → **Deploy to Vercel** → **Run workflow**).

Your app will be live at `https://url-shortener-XXXX.vercel.app`

---

## Local Development

```bash
cd ~/HERMES/apps/url-shortener
pip install -r requirements.txt
uvicorn main:app --reload
```

Open http://localhost:8000
