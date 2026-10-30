"""FastAPI entrypoint serving the Personal News Aggregator, Weather & Myanmar Market API and UI."""

import asyncio
from contextlib import asynccontextmanager
import os
from pathlib import Path
import time
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.database import (
    ArticlesResponse,
    DismissCategoryRequest,
    MarketCalibration,
    clear_market_calibration,
    dismiss_article,
    dismiss_category_articles,
    get_active_articles,
    get_unread_counts,
    init_db,
    purge_old_articles,
    save_market_calibration,
    toggle_save_article,
    upsert_articles,
)
from app.feeds_config import FEEDS_CONFIG
from app.fetcher import (
    MarketResponse,
    RefreshSummary,
    WeatherResponse,
    fetch_all_feeds,
    fetch_market_rates,
    fetch_weather,
)

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"


class DismissSingleResponse(BaseModel):
    """Response model for dismissing a single article."""

    id: str
    dismissed: bool


class ToggleSaveResponse(BaseModel):
    """Response model for toggling save/bookmark status of an article."""

    id: str
    saved: bool


class DismissCategoryResponse(BaseModel):
    """Response model for dismissing all visible articles in a category."""

    category: str
    dismissed_count: int


AUTO_REFRESH_INTERVAL_SECONDS = 1800  # 30 minutes


async def _background_auto_refresh_loop() -> None:
    """Periodically fetch all 90 feeds every 30 minutes so news stays fresh every day."""
    while True:
        await asyncio.sleep(AUTO_REFRESH_INTERVAL_SECONDS)
        try:
            articles, _ = await fetch_all_feeds()
            await asyncio.to_thread(upsert_articles, articles)
            await asyncio.to_thread(purge_old_articles, 7)
        except Exception:
            continue


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Initialize SQLite schema, purge expired articles (>7d), and start background auto-refresh task."""
    init_db()
    await asyncio.to_thread(purge_old_articles, 7)
    refresh_task = asyncio.create_task(_background_auto_refresh_loop())
    try:
        yield
    finally:
        refresh_task.cancel()


app = FastAPI(
    title="Personal News & Myanmar Market Hub",
    description="Zero-cost local RSS aggregator (90 feeds), Yangon weather, and Myanmar currency & gold tracker.",
    version="1.0.0",
    lifespan=lifespan,
)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
async def serve_index() -> HTMLResponse:
    """Serve the single-page minimalist news dashboard."""
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Frontend index.html not found")
    content = await asyncio.to_thread(index_file.read_text, encoding="utf-8")
    return HTMLResponse(content=content)


@app.get("/api/categories")
async def list_categories() -> dict[str, list[str]]:
    """Return the ordered list of 9 configured categories."""
    return {"categories": list(FEEDS_CONFIG.keys())}


@app.get("/api/articles", response_model=ArticlesResponse)
async def list_articles(
    category: str | None = Query(default=None, description="Filter by category name"),
    limit: int = Query(default=300, ge=1, le=1000),
) -> ArticlesResponse:
    """Return non-dismissed articles (or saved articles) and unread counts per category."""
    articles = await asyncio.to_thread(get_active_articles, category, limit)
    raw_counts = await asyncio.to_thread(get_unread_counts)

    ordered_counts: dict[str, int] = {}
    ordered_counts["Saved"] = raw_counts.get("Saved", 0)
    for cat in FEEDS_CONFIG:
        ordered_counts[cat] = raw_counts.get(cat, 0)

    total_unread = sum(v for k, v in raw_counts.items() if k != "Saved")
    return ArticlesResponse(
        articles=articles,
        counts=ordered_counts,
        total_unread=total_unread,
    )


_last_refresh_ts: float = 0.0
REFRESH_COOLDOWN_SECONDS: float = 60.0


@app.post("/api/refresh", response_model=RefreshSummary)
async def refresh_feeds() -> RefreshSummary:
    """Fetch all 180 RSS feeds concurrently, store new articles in SQLite, and purge >7d stories with 60s cooldown."""
    global _last_refresh_ts
    now = time.monotonic()
    if now - _last_refresh_ts < REFRESH_COOLDOWN_SECONDS:
        remaining = int(REFRESH_COOLDOWN_SECONDS - (now - _last_refresh_ts))
        raise HTTPException(
            status_code=429,
            detail=f"Cooldown active. Please wait {remaining} seconds before refreshing feeds again.",
        )
    _last_refresh_ts = now
    articles, summary = await fetch_all_feeds()
    inserted = await asyncio.to_thread(upsert_articles, articles)
    await asyncio.to_thread(purge_old_articles, 7)
    return summary.model_copy(update={"inserted_articles": inserted})


@app.post("/api/articles/{article_id}/toggle-save", response_model=ToggleSaveResponse)
async def toggle_save(article_id: str) -> ToggleSaveResponse:
    """Toggle saved/bookmark status of an article for the Read Later tab."""
    new_state = await asyncio.to_thread(toggle_save_article, article_id)
    return ToggleSaveResponse(id=article_id, saved=new_state)


@app.post("/api/articles/{article_id}/dismiss", response_model=DismissSingleResponse)
async def dismiss_single_article(article_id: str) -> DismissSingleResponse:
    """Mark a single article as dismissed in SQLite so it never appears again."""
    updated = await asyncio.to_thread(dismiss_article, article_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Article not found")
    return DismissSingleResponse(id=article_id, dismissed=True)


@app.post("/api/articles/dismiss-category", response_model=DismissCategoryResponse)
async def dismiss_category(payload: DismissCategoryRequest) -> DismissCategoryResponse:
    """Mark all visible articles in the specified category (or 'All') as dismissed."""
    count = await asyncio.to_thread(dismiss_category_articles, payload.category)
    return DismissCategoryResponse(
        category=payload.category,
        dismissed_count=count,
    )


@app.get("/api/weather", response_model=WeatherResponse)
async def get_weather() -> WeatherResponse:
    """Return current Yangon weather and daily forecast from Open-Meteo."""
    return await fetch_weather()


@app.get("/api/market", response_model=MarketResponse)
async def get_market() -> MarketResponse:
    """Return live Myanmar currency exchange rates (USD, EUR, SGD, THB) and Myanmar Gold reference."""
    return await fetch_market_rates()


@app.post("/api/market/calibrate", response_model=MarketResponse)
async def calibrate_market(payload: MarketCalibration) -> MarketResponse:
    """Save custom Yangon street market rates (protected by ADMIN_PIN)."""
    expected_pin = os.getenv("ADMIN_PIN", "$Billionaire3")
    if payload.pin != expected_pin:
        raise HTTPException(status_code=403, detail="Invalid Admin PIN")
    await asyncio.to_thread(save_market_calibration, payload)
    return await fetch_market_rates()


@app.delete("/api/market/calibrate", response_model=MarketResponse)
async def reset_market_calibration(
    pin: str | None = Query(default=None),
) -> MarketResponse:
    """Clear manual calibration and revert to live auto-scraped Yangon street rates (protected by ADMIN_PIN)."""
    expected_pin = os.getenv("ADMIN_PIN", "$Billionaire3")
    if pin != expected_pin:
        raise HTTPException(status_code=403, detail="Invalid Admin PIN")
    await asyncio.to_thread(clear_market_calibration)
    return await fetch_market_rates()

