"""SQLite database initialization, Pydantic models, and CRUD helpers."""

import hashlib
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from pydantic import BaseModel, ConfigDict, Field

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "news_aggregator.db"

TRACKING_PARAMS = frozenset(
    {
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "utm_content",
        "fbclid",
        "gclid",
        "mc_cid",
        "mc_eid",
        "ref",
    }
)


class ArticleCreate(BaseModel):
    """Validated input model for saving an article."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(..., min_length=64, max_length=64)
    category: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    url: str = Field(..., min_length=1)
    brief: str = Field(default="", max_length=280)
    published_at: str
    published_ts: int


class ArticleOut(BaseModel):
    """Validated output model returned to the API/UI."""

    model_config = ConfigDict(extra="ignore")

    id: str
    category: str
    source: str
    title: str
    url: str
    brief: str
    published_at: str
    published_ts: int
    dismissed: bool = False
    saved: bool = False


class ArticlesResponse(BaseModel):
    """Response payload for GET /api/articles."""

    articles: list[ArticleOut]
    counts: dict[str, int]
    total_unread: int


class DismissCategoryRequest(BaseModel):
    """Request payload for POST /api/articles/dismiss-category."""

    category: str = Field(..., min_length=1)


class MarketCalibration(BaseModel):
    """Optional user-calibrated Yangon street market base rates stored in SQLite."""

    model_config = ConfigDict(extra="ignore")

    usd_mmk: float | None = Field(default=None, gt=0)
    eur_mmk: float | None = Field(default=None, gt=0)
    sgd_mmk: float | None = Field(default=None, gt=0)
    thb_mmk: float | None = Field(default=None, gt=0)
    gold_16pae_mmk: int | None = Field(default=None, gt=0)
    updated_at: str | None = None
    pin: str | None = None


def canonicalize_url(raw_url: str) -> str:
    """Normalize URL by stripping tracking parameters and fragments before hashing."""
    cleaned = raw_url.strip()
    if not cleaned:
        return ""
    try:
        parsed = urlparse(cleaned)
        scheme = (parsed.scheme or "https").lower()
        netloc = parsed.netloc.lower()
        path = parsed.path or "/"
        if path != "/" and path.endswith("/"):
            path = path.rstrip("/")
        filtered_query = [
            (k, v)
            for k, v in parse_qsl(parsed.query, keep_blank_values=True)
            if k.lower() not in TRACKING_PARAMS
        ]
        filtered_query.sort()
        query_str = urlencode(filtered_query)
        return urlunparse((scheme, netloc, path, "", query_str, ""))
    except Exception:
        return cleaned


def compute_article_id(raw_url: str) -> str:
    """Compute SHA-256 hex digest of the canonical URL."""
    canonical = canonicalize_url(raw_url)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def get_db_path() -> Path:
    """Return configured SQLite database file path."""
    env_path = os.environ.get("NEWS_DB_PATH")
    if env_path:
        return Path(env_path)
    return DEFAULT_DB_PATH


@contextmanager
def get_connection(db_path: Path | None = None) -> Iterator[sqlite3.Connection]:
    """Context manager yielding a configured SQLite connection."""
    target_path = db_path or get_db_path()
    conn = sqlite3.connect(str(target_path), timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: Path | None = None) -> None:
    """Create the articles table and indexes if they do not exist, and run migrations."""
    with get_connection(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS articles (
                id TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                source TEXT NOT NULL,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                brief TEXT NOT NULL,
                published_at TEXT NOT NULL,
                published_ts INTEGER NOT NULL,
                dismissed INTEGER NOT NULL DEFAULT 0,
                saved INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );
            """
        )
        try:
            conn.execute("ALTER TABLE articles ADD COLUMN saved INTEGER NOT NULL DEFAULT 0;")
        except sqlite3.OperationalError:
            pass
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_articles_active
            ON articles (dismissed, category, published_ts DESC);
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_articles_saved
            ON articles (saved, published_ts DESC);
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS market_calibration (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                usd_mmk REAL,
                eur_mmk REAL,
                sgd_mmk REAL,
                thb_mmk REAL,
                gold_16pae_mmk INTEGER,
                updated_at TEXT NOT NULL
            );
            """
        )


def upsert_articles(
    articles: list[ArticleCreate], db_path: Path | None = None
) -> int:
    """Insert new articles while ignoring existing canonical URL hashes (preserving dismissed state)."""
    if not articles:
        return 0
    now_iso = datetime.now(timezone.utc).isoformat()
    inserted = 0
    with get_connection(db_path) as conn:
        for article in articles:
            cursor = conn.execute(
                """
                INSERT INTO articles (
                    id, category, source, title, url, brief,
                    published_at, published_ts, dismissed, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
                ON CONFLICT(id) DO NOTHING;
                """,
                (
                    article.id,
                    article.category,
                    article.source,
                    article.title,
                    article.url,
                    article.brief,
                    article.published_at,
                    article.published_ts,
                    now_iso,
                ),
            )
            if cursor.rowcount > 0:
                inserted += 1
    return inserted


def get_active_articles(
    category: str | None = None,
    limit: int = 300,
    db_path: Path | None = None,
) -> list[ArticleOut]:
    """Retrieve articles ordered by newest first (active feeds limited to the last 7 days)."""
    now_ts = int(datetime.now(timezone.utc).timestamp())
    cutoff_ts = now_ts - (7 * 86400)

    with get_connection(db_path) as conn:
        if category == "Saved":
            rows = conn.execute(
                """
                SELECT id, category, source, title, url, brief,
                       published_at, published_ts, dismissed, saved
                FROM articles
                WHERE saved = 1
                ORDER BY published_ts DESC
                LIMIT ?;
                """,
                (limit,),
            ).fetchall()
        elif category and category != "All":
            rows = conn.execute(
                """
                SELECT id, category, source, title, url, brief,
                       published_at, published_ts, dismissed, saved
                FROM articles
                WHERE dismissed = 0 AND published_ts >= ? AND category = ?
                ORDER BY published_ts DESC
                LIMIT ?;
                """,
                (cutoff_ts, category, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, category, source, title, url, brief,
                       published_at, published_ts, dismissed, saved
                FROM articles
                WHERE dismissed = 0 AND published_ts >= ?
                ORDER BY published_ts DESC
                LIMIT ?;
                """,
                (cutoff_ts, limit),
            ).fetchall()

    return [
        ArticleOut(
            id=str(row["id"]),
            category=str(row["category"]),
            source=str(row["source"]),
            title=str(row["title"]),
            url=str(row["url"]),
            brief=str(row["brief"]),
            published_at=str(row["published_at"]),
            published_ts=int(row["published_ts"]),
            dismissed=bool(row["dismissed"]),
            saved=bool(row["saved"]) if "saved" in row.keys() else False,
        )
        for row in rows
    ]


def get_unread_counts(db_path: Path | None = None) -> dict[str, int]:
    """Return unread counts for the last 7 days grouped by category plus total saved count."""
    now_ts = int(datetime.now(timezone.utc).timestamp())
    cutoff_ts = now_ts - (7 * 86400)

    with get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT category, COUNT(*) AS cnt
            FROM articles
            WHERE dismissed = 0 AND published_ts >= ?
            GROUP BY category;
            """,
            (cutoff_ts,),
        ).fetchall()
        counts = {str(row["category"]): int(row["cnt"]) for row in rows}
        saved_row = conn.execute(
            """
            SELECT COUNT(*) AS cnt
            FROM articles
            WHERE saved = 1;
            """
        ).fetchone()
        counts["Saved"] = int(saved_row["cnt"]) if saved_row else 0
        return counts


def toggle_save_article(article_id: str, db_path: Path | None = None) -> bool:
    """Toggle the bookmark/saved status of an article, returning the new state."""
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT saved FROM articles WHERE id = ?;", (article_id,)
        ).fetchone()
        if row is None:
            return False
        current_saved = int(row["saved"]) if "saved" in row.keys() else 0
        new_saved = 0 if current_saved == 1 else 1
        conn.execute(
            "UPDATE articles SET saved = ? WHERE id = ?;",
            (new_saved, article_id),
        )
        return bool(new_saved)


def dismiss_article(article_id: str, db_path: Path | None = None) -> bool:
    """Flag a single article as dismissed so it never appears again."""
    with get_connection(db_path) as conn:
        cursor = conn.execute(
            """
            UPDATE articles
            SET dismissed = 1
            WHERE id = ?;
            """,
            (article_id,),
        )
        return cursor.rowcount > 0


def dismiss_category_articles(
    category: str, db_path: Path | None = None
) -> int:
    """Flag all currently visible articles in a category (or 'All') as dismissed."""
    with get_connection(db_path) as conn:
        if category == "All":
            cursor = conn.execute(
                """
                UPDATE articles
                SET dismissed = 1
                WHERE dismissed = 0;
                """
            )
        else:
            cursor = conn.execute(
                """
                UPDATE articles
                SET dismissed = 1
                WHERE dismissed = 0 AND category = ?;
                """,
                (category,),
            )
        return int(cursor.rowcount)


def purge_non_dismissed_by_categories(
    categories: list[str], db_path: Path | None = None
) -> int:
    """Delete non-dismissed articles in given categories so fresh filtered feeds replace them."""
    if not categories:
        return 0
    placeholders = ", ".join("?" for _ in categories)
    with get_connection(db_path) as conn:
        cursor = conn.execute(
            f"""
            DELETE FROM articles
            WHERE dismissed = 0 AND category IN ({placeholders});
            """,
            tuple(categories),
        )
        return int(cursor.rowcount)


def purge_old_articles(max_age_days: int = 7, db_path: Path | None = None) -> int:
    """Permanently delete un-saved articles older than max_age_days (default 7 days)."""
    now_ts = int(datetime.now(timezone.utc).timestamp())
    cutoff_ts = now_ts - (max_age_days * 86400)
    with get_connection(db_path) as conn:
        cursor = conn.execute(
            """
            DELETE FROM articles
            WHERE published_ts < ? AND saved = 0;
            """,
            (cutoff_ts,),
        )
        return int(cursor.rowcount)


def get_market_calibration(db_path: Path | None = None) -> MarketCalibration | None:
    """Retrieve user-calibrated Yangon street rates if configured."""
    with get_connection(db_path) as conn:
        row = conn.execute(
            """
            SELECT usd_mmk, eur_mmk, sgd_mmk, thb_mmk, gold_16pae_mmk, updated_at
            FROM market_calibration
            WHERE id = 1;
            """
        ).fetchone()
    if row is None:
        return None
    return MarketCalibration(
        usd_mmk=float(row["usd_mmk"]) if row["usd_mmk"] is not None else None,
        eur_mmk=float(row["eur_mmk"]) if row["eur_mmk"] is not None else None,
        sgd_mmk=float(row["sgd_mmk"]) if row["sgd_mmk"] is not None else None,
        thb_mmk=float(row["thb_mmk"]) if row["thb_mmk"] is not None else None,
        gold_16pae_mmk=int(row["gold_16pae_mmk"]) if row["gold_16pae_mmk"] is not None else None,
        updated_at=str(row["updated_at"]) if row["updated_at"] is not None else None,
    )


def save_market_calibration(
    cal: MarketCalibration, db_path: Path | None = None
) -> MarketCalibration:
    """Save or update user-calibrated Yangon street market rates."""
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    with get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO market_calibration (
                id, usd_mmk, eur_mmk, sgd_mmk, thb_mmk, gold_16pae_mmk, updated_at
            )
            VALUES (1, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                usd_mmk = excluded.usd_mmk,
                eur_mmk = excluded.eur_mmk,
                sgd_mmk = excluded.sgd_mmk,
                thb_mmk = excluded.thb_mmk,
                gold_16pae_mmk = excluded.gold_16pae_mmk,
                updated_at = excluded.updated_at;
            """,
            (
                cal.usd_mmk,
                cal.eur_mmk,
                cal.sgd_mmk,
                cal.thb_mmk,
                cal.gold_16pae_mmk,
                now_str,
            ),
        )
    return cal.model_copy(update={"updated_at": now_str})


def clear_market_calibration(db_path: Path | None = None) -> None:
    """Clear manual calibration and revert to live scraped/calculated street rates."""
    with get_connection(db_path) as conn:
        conn.execute("DELETE FROM market_calibration WHERE id = 1;")


