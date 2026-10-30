---
title: PulseMM News Hub
emoji: 📰
colorFrom: red
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
---

# Personal News Aggregator, Weather Dashboard & Myanmar Market Tracker

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/lhk-dev/pulsemm)

A zero-cost (`$0`), local personal news skimmer across **180 verified RSS feeds** (10 categories × 18 prestigious sources), coupled with a live **Yangon Open-Meteo Weather Widget** and **Yangon Street Market Currency (USD, EUR, SGD, THB → MMK) & Gold (16 Pae / 15 Pae per Tical)** exchange rate tracker with live calibration.

---

## Project Structure

```text
personal-news-hub/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI routes, background refresh & 7-day auto-purge
│   ├── database.py      # SQLite schema, SHA-256 deduplication, 7-day cutoff & bookmarks
│   ├── fetcher.py       # Async 180-feed fetcher, strict noise filter, Weather & Market clients
│   └── feeds_config.py  # 10 categories × 18 RSS/Atom feeds (180 prestigious sources total)
├── static/
│   ├── index.html       # Minimalist UI, collapsible market drawer, slim sticky tabs
│   └── app.js           # Vanilla JS controller with '★ Saved' & keyboard navigation
├── tests/
│   └── test_app.py      # Unit & API test suite (sanitizer, deduplication, 7-day retention)
├── requirements.txt
└── README.md
```

---

## Quick Start (Single-Command Server)

Run the following commands in your terminal from the project directory (`/Users/m2pro/.gemini/antigravity/scratch/personal-news-hub`):

```bash
# 1. Create and activate a Python 3.11+ virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
.venv/bin/pip install -r requirements.txt

# 3. Start the FastAPI server (listening on all interfaces)
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8765
```

- On your Mac: **http://127.0.0.1:8765**

---

## Sharing With Friends Outside Your Wi-Fi (100% Free / $0)

If your friends are on cellular data or different Wi-Fi networks, they cannot reach your Mac's private local IP. You can give them a secure, free public HTTPS link in 10 seconds:

### Method 1: Cloudflare Quick Tunnel (Recommended, $0, No Account Needed)
Install and run Cloudflare's free tunnel:
```bash
brew install cloudflared
cloudflared tunnel --url http://localhost:8765
```
Cloudflare will print a secure public URL (e.g. `https://random-words.trycloudflare.com`). Share this link with your friends—it opens instantly on iPhone, Android, tablet, or PC worldwide.

### Method 2: Zero-Install SSH Public Tunnel ($0)
Without installing any software:
```bash
ssh -R 80:localhost:8765 nokey@localhost.run
```
It gives you an immediate public HTTPS URL to share with your friends.

---

## Key Features & Retention Rules

- **Client-Side Privacy (`localStorage`):** Bookmarks (`★ Saved`) and dismissed items are stored directly inside each user's phone or browser. Every friend gets their own private reading experience with zero logins required.
- **Admin PIN Protection:** The `✎ Calibrate` drawer requires an Admin PIN (default `1234`, customizable via `ADMIN_PIN` environment variable) to prevent unauthorized tampering with Myanmar market rates.
- **Refresh Rate Limit Protection:** The "Refresh Feeds" button includes a 60-second cooldown timer to prevent IP blocks from upstream news providers.
- **Strict 7-Day Clean Retention:** Articles older than 7 days are automatically purged from the database and active feeds on startup and every 30 minutes, keeping your reading list lightweight and current.
- **★ Saved (Read Later) Protection:** Click the bookmark icon or press `s` on any article to save it. Bookmarked stories are **never deleted** by the 7-day purge and live in your dedicated `★ Saved` tab.
- **Collapsible Economic Overview:** Click **Hide Market** / **Show Market** to collapse the market rates when focusing on reading news without header obstruction.
- **Keyboard Navigation:**
  - `x` — Skip / Dismiss the currently focused article.
  - `s` — Save / Bookmark article to `★ Saved` tab (or un-save).
  - `j` / `k` — Move focus down / up across article cards.
  - `r` — Refresh all 180 RSS feeds concurrently.
