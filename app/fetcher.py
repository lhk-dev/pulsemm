"""Asynchronous RSS feed batch fetcher, HTML sanitizer, relevance filter, and Weather/Market integrations."""

import asyncio
import calendar
import html
import json
import re
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import feedparser  # type: ignore[import-untyped]
import httpx
from pydantic import BaseModel, ConfigDict

from app.database import (
    ArticleCreate,
    MarketCalibration,
    compute_article_id,
    get_market_calibration,
)
from app.feeds_config import FEEDS_CONFIG, FeedSource

BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)

FEED_TIMEOUT_SECONDS = 8.0
MAX_CONCURRENT_FEEDS = 30
MAX_ENTRIES_PER_FEED = 12
MAX_BRIEF_CHARS = 280

OPEN_METEO_YANGON_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude=16.8409&longitude=96.1735"
    "&current_weather=true"
    "&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max"
    "&timezone=auto"
)

FOREX_API_URL = "https://open.er-api.com/v6/latest/USD"
GOLD_API_URL = "https://api.gold-api.com/price/XAU"
GOLD_PAXG_API_URL = "https://api.coinbase.com/v2/prices/PAXG-USD/spot"
MYANMAR_STREET_FX_URL = "https://egcurrency.com/en/currency/mmk"

# Traditional Yangon goldsmith (Shwe Bon Thar) formula: 1 Troy Ounce = 1.875 Kyattha (Tical)
# (Spot_USD / 1.875 * Street_USD_MMK = 16 Pae Academy Gold price per Kyattha)
KYATTHA_PER_TROY_OZ = 1.875
TROY_OZ_PER_TICAL = 1.0 / KYATTHA_PER_TROY_OZ
YGEA_OFFICIAL_REF_MMK = 7100000

SCRIPT_STYLE_RE = re.compile(
    r"<(script|style|noscript|iframe|svg)[^>]*>.*?</\1>",
    re.IGNORECASE | re.DOTALL,
)
HTML_TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?။])\s*")
WORD_TOKEN_RE = re.compile(r"\w+")

# Global noise filter: block sports, football, NBA, entertainment gossip, and unrelated African/LatAm local news
IRRELEVANT_NOISE_RE = re.compile(
    r"\b("
    r"ballon d'or|ballon dor|premier league|champions league|league cup|fa cup|"
    r"la liga|serie a|bundesliga|europa league|world cup qualifier|"
    r"man city|manchester city|man united|manchester united|real madrid|barcelona|"
    r"bayern|liverpool fc|arsenal fc|chelsea fc|tottenham|juventus|psg|"
    r"neymar|messi|ronaldo|mbappe|haaland|harry kane|guardiola|mourinho|"
    r"nba|nfl|nhl|mlb|super bowl|touchdown|playoffs|timberwolves|lakers|warriors|celtics|pacers|cavaliers|"
    r"stephen curry|lebron|nikola jokic|kevin durant|"
    r"red card|penalty shootout|hat-trick|midfielder|striker|goalkeeper|"
    r"grand slam|wimbledon|atp tour|wta|formula 1|grand prix|motogp|"
    r"love island|kardashian|grammy awards|academy awards|red carpet|horoscope|"
    r"ethiopia|tigray|addis ababa|eritrea|sudan|khartoum|darfur|south sudan|"
    r"somalia|mogadishu|al-shabaab|congo|kinshasa|goma|rwanda|burundi|uganda|"
    r"nigeria|boko haram|mali|burkina faso|niger|chad|mozambique|zimbabwe|haiti|el salvador"
    r")\b",
    re.IGNORECASE,
)

# Myanmar keywords (strictly required for Myanmar categories)
MYANMAR_RELEVANCE_RE = re.compile(
    r"\b("
    r"myanmar|burma|burmese|yangon|rangoon|mandalay|naypyidaw|nay pyi taw|"
    r"rakhine|arakan|kachin|shan state|karen|kayin|kayah|karenni|chin state|"
    r"sagaing|magway|bago|tanintharyi|mon state|ayeyarwady|irrawaddy|mizzima|"
    r"nug|national unity government|crph|spring revolution|sac|junta|tatmadaw|pdf|"
    r"min aung hlaing|aung san suu kyi|tnla|mndaa|kia|knu|aa|arakan army|brotherhood alliance|eao|"
    r"rohingya|kyat|myawaddy|muse|lashio|sittwe|kyaukphyu|dawei|thilawa|"
    r"passport|passports|owic|conscription|moving abroad|offloaded|exodus|travel restrictions"
    r")\b",
    re.IGNORECASE,
)

# Myanmar Unicode script pattern (standard Myanmar block, Myanmar extended A & B)
MYANMAR_BURMESE_UNICODE_RE = re.compile(r"[\u1000-\u109F\uAA60-\uAA7F\uA9E0-\uA9FE]")

# Curated dedicated Myanmar independent publishers
DEDICATED_MYANMAR_SOURCES = (
    "frontier",
    "myanmar now",
    "irrawaddy",
    "dvb",
    "mizzima",
    "bni",
    "cj platform",
    "rfa",
    "bbc news မြန်မာ",
    "bbc burmese",
)

# Weapons development, defense R&D, and using technology in the military
WEAPONS_MILTECH_RE = re.compile(
    r"\b("
    r"weapon|weapons|weaponry|munition|munitions|loitering munition|ammunition|warhead|"
    r"military tech|defense tech|defence tech|battlefield tech|dual-use|"
    r"drone|drones|uav|ucav|fpv drone|drone swarm|unmanned|autonomous weapon|counter-uas|c-uas|"
    r"hypersonic|ballistic missile|cruise missile|icbm|intercontinental|anti-ship missile|"
    r"air defense|air defence|iron dome|patriot battery|thaad|s-400|s-500|aegis|"
    r"stealth fighter|fifth-gen|sixth-gen|f-35|f-22|b-21|j-20|su-57|ngad|cca|loyal wingman|"
    r"bomber|warplane|fighter jet|attack helicopter|apache|himars|artillery|howitzer|tank|abrams|leopard|"
    r"electronic warfare|jamming|spoofing|directed energy|laser weapon|high-energy laser|microwave weapon|railgun|"
    r"radar|sonar|awacs|isr|c4isr|reconnaissance|surveillance|targeting|kill chain|"
    r"submarine|nuclear-powered|ssn|ssbn|aukus|aircraft carrier|destroyer|frigate|corvette|usv|uuv|"
    r"darpa|pentagon|dod|lockheed|raytheon|rtx|northrop grumman|general dynamics|bae systems|"
    r"anduril|palantir|shield ai|rheinmetall|saab|thales|leonardo|norinco|rostec|"
    r"space force|anti-satellite|asat|cyber warfare|military ai"
    r")\b",
    re.IGNORECASE,
)

# Critical world politics & major power conflicts (US, China, Russia, Iran, Israel, Taiwan, Korea, NATO)
CRITICAL_WORLD_RE = re.compile(
    r"\b("
    r"iran|tehran|israel|idf|gaza|hezbollah|houthi|red sea|strait of hormuz|centcom|"
    r"ukraine|kyiv|russia|moscow|kremlin|putin|zelensky|nato|donbas|crimea|"
    r"taiwan|taipei|south china sea|beijing|xi jinping|pla|indo-pacific|"
    r"north korea|pyongyang|kim jong un|korean peninsula|"
    r"nuclear war|nuclear weapon|uranium enrichment|nuclear deterrence|"
    r"world war|superpower|trade war|sanctions|tariffs|un security council"
    r")\b",
    re.IGNORECASE,
)


class RefreshSummary(BaseModel):
    """Summary returned after batch fetching all 90 feeds."""

    total_feeds: int
    succeeded_feeds: int
    failed_feeds: int
    fetched_articles: int
    inserted_articles: int
    duration_seconds: float


class WeatherResponse(BaseModel):
    """Validated weather forecast response for the top-bar widget."""

    model_config = ConfigDict(extra="ignore")

    location: str
    temperature_c: float
    windspeed_kmh: float
    weather_code: int
    condition_label: str
    temp_max_c: float
    temp_min_c: float
    rain_prob_pct: int
    updated_at: str
    is_fallback: bool = False


class CurrencyRate(BaseModel):
    """Single currency pair rate against MMK (Street Buy/Sell + CBM Reference)."""

    code: str
    name: str
    cbm_ref_mmk: float
    market_est_mmk: float
    buy_mmk: float = 0.0
    sell_mmk: float = 0.0


class GoldRate(BaseModel):
    """Myanmar Gold price reference per tical (Kyattha)."""

    world_spot_usd_oz: float
    world_equiv_mmk_tical: int
    ygea_ref_mmk_tical: int
    market_16pae_mmk_tical: int
    market_15pae_mmk_tical: int


class MarketResponse(BaseModel):
    """Validated market & gold exchange response for the top-bar widget."""

    currencies: list[CurrencyRate]
    gold: GoldRate
    updated_at: str
    is_fallback: bool = False
    is_calibrated: bool = False


WMO_WEATHER_LABELS: dict[int, str] = {
    0: "Clear Sky",
    1: "Mainly Clear",
    2: "Partly Cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Rime Fog",
    51: "Light Drizzle",
    53: "Moderate Drizzle",
    55: "Dense Drizzle",
    61: "Slight Rain",
    63: "Moderate Rain",
    65: "Heavy Rain",
    80: "Rain Showers",
    81: "Mod. Showers",
    82: "Heavy Showers",
    95: "Thunderstorm",
    96: "Storm & Hail",
    99: "Heavy Thunderstorm",
}


def sanitize_html_to_brief(
    raw_text: str | None, max_chars: int = MAX_BRIEF_CHARS
) -> str:
    """Strip all HTML tags, unescape entities, keep 2-3 clean sentences, max 280 chars."""
    if not raw_text:
        return ""
    text = html.unescape(html.unescape(raw_text))
    text = SCRIPT_STYLE_RE.sub(" ", text)
    text = HTML_TAG_RE.sub(" ", text)
    text = html.unescape(text)
    text = WHITESPACE_RE.sub(" ", text).strip()

    if not text:
        return ""

    sentences = SENTENCE_SPLIT_RE.split(text)
    if len(sentences) > 3:
        text = " ".join(sentences[:3]).strip()

    if len(text) <= max_chars:
        return text

    truncated = text[: max_chars - 1].rsplit(" ", 1)[0].rstrip(".,;:- ")
    if not truncated:
        truncated = text[: max_chars - 1]
    return f"{truncated}…"


def _is_duplicate_of_title(title: str, brief: str) -> bool:
    """Return True if the brief merely repeats the article headline (common in Google News RSS)."""
    if not brief:
        return True
    title_tokens = WORD_TOKEN_RE.findall(title.lower())
    brief_tokens = WORD_TOKEN_RE.findall(brief.lower())
    if not brief_tokens:
        return True
    if title_tokens == brief_tokens:
        return True
    # Check if >80% of brief tokens are just the title tokens
    title_set = set(title_tokens)
    overlap = sum(1 for tok in brief_tokens if tok in title_set)
    if len(brief_tokens) <= len(title_tokens) + 4 and overlap / max(1, len(brief_tokens)) >= 0.80:
        return True
    return False


def is_article_relevant(category: str, title: str, brief: str, source_name: str) -> bool:
    """Enforce dedicated relevance rules for Myanmar, World Crises & Geopolitics, and Military, Weapons & Defense Tech."""
    combined = f"{title} {brief}"

    # 1. Globally drop sports, celebrity tabloid noise, and unrelated African/LatAm local conflicts (e.g. Ethiopia/Tigray)
    if IRRELEVANT_NOISE_RE.search(combined):
        return False

    # 2. Myanmar categories: strictly Myanmar politics, business, economics, situation, and opportunities
    if category.startswith("Myanmar"):
        src_lower = source_name.lower()
        if any(d in src_lower for d in DEDICATED_MYANMAR_SOURCES):
            return True
        if MYANMAR_BURMESE_UNICODE_RE.search(combined):
            return True
        return bool(MYANMAR_RELEVANCE_RE.search(combined))

    # 3. "Crisis & Geopolitics" tab: strictly critical wars, superpower flashpoints, sanctions & nuclear deterrence
    if category in ("Crisis & Geopolitics", "World Crises & Geopolitics"):
        return bool(CRITICAL_WORLD_RE.search(combined))

    # 4. "Military, Weapons & Defense Tech" tab: strictly weapons R&D, military technology, drones, missiles & defense systems
    if category == "Military, Weapons & Defense Tech":
        return bool(WEAPONS_MILTECH_RE.search(combined))

    return True


def extract_entry_raw_summary(entry: dict[str, Any]) -> str:
    """Safely inspect entry.get('summary'), entry.get('description'), or entry.get('content')."""
    summary = entry.get("summary")
    if isinstance(summary, str) and summary.strip():
        return summary

    description = entry.get("description")
    if isinstance(description, str) and description.strip():
        return description

    content_list = entry.get("content")
    if isinstance(content_list, list) and content_list:
        first_item = content_list[0]
        if isinstance(first_item, dict):
            val = first_item.get("value")
            if isinstance(val, str) and val.strip():
                return val

    title_fallback = entry.get("title")
    return str(title_fallback) if title_fallback else ""


def parse_entry_timestamp(entry: dict[str, Any]) -> tuple[str, int]:
    """Extract ISO-8601 UTC publication string and epoch timestamp from a feed entry."""
    for struct_key in ("published_parsed", "updated_parsed", "created_parsed"):
        parsed_struct = entry.get(struct_key)
        if parsed_struct is not None:
            try:
                ts = int(calendar.timegm(parsed_struct))
                dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                return dt.isoformat(), ts
            except Exception:
                continue

    for str_key in ("published", "updated", "created"):
        raw_date = entry.get(str_key)
        if isinstance(raw_date, str) and raw_date.strip():
            try:
                dt = parsedate_to_datetime(raw_date.strip())
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                else:
                    dt = dt.astimezone(timezone.utc)
                return dt.isoformat(), int(dt.timestamp())
            except Exception:
                continue

    now_dt = datetime.now(timezone.utc)
    return now_dt.isoformat(), int(now_dt.timestamp())


def parse_feed_xml(
    xml_content: bytes | str,
    category: str,
    source_name: str,
    max_entries: int = MAX_ENTRIES_PER_FEED,
) -> list[ArticleCreate]:
    """Parse RSS/Atom XML into validated, relevance-filtered ArticleCreate models safely."""
    parsed = feedparser.parse(xml_content)
    entries = parsed.get("entries", [])
    if not isinstance(entries, list):
        return []

    results: list[ArticleCreate] = []
    for raw_entry in entries[:max_entries]:
        if not isinstance(raw_entry, dict):
            continue
        raw_link = raw_entry.get("link")
        raw_title = raw_entry.get("title")
        if not isinstance(raw_link, str) or not raw_link.strip():
            continue
        if not isinstance(raw_title, str) or not raw_title.strip():
            continue

        clean_url = raw_link.strip()
        clean_title = sanitize_html_to_brief(raw_title, max_chars=220)
        if not clean_title:
            continue

        raw_summary = extract_entry_raw_summary(raw_entry)
        clean_brief = sanitize_html_to_brief(raw_summary, max_chars=MAX_BRIEF_CHARS)

        if not is_article_relevant(category, clean_title, clean_brief, source_name):
            continue

        if _is_duplicate_of_title(clean_title, clean_brief):
            # Extract publisher suffix if present in Google News titles ("Headline - Publisher")
            if " - " in clean_title:
                headline_part, publisher_part = clean_title.rsplit(" - ", 1)
                clean_title = headline_part.strip()
                clean_brief = (
                    f"Reported via {publisher_part.strip()} ({source_name}). "
                    f"Click 'Read Article' for the full report."
                )
            else:
                clean_brief = (
                    f"Direct dispatch from {source_name} under {category}. "
                    f"Open article for full details."
                )

        pub_iso, pub_ts = parse_entry_timestamp(raw_entry)
        article_id = compute_article_id(clean_url)

        try:
            article = ArticleCreate(
                id=article_id,
                category=category,
                source=source_name,
                title=clean_title,
                url=clean_url,
                brief=clean_brief,
                published_at=pub_iso,
                published_ts=pub_ts,
            )
            results.append(article)
        except Exception:
            continue

    return results


async def fetch_single_feed(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    category: str,
    source: FeedSource,
) -> tuple[bool, list[ArticleCreate]]:
    """Fetch and parse a single RSS feed with an 8s timeout and full exception isolation."""
    async with semaphore:
        try:
            response = await client.get(
                source["url"],
                timeout=FEED_TIMEOUT_SECONDS,
                follow_redirects=True,
            )
            if response.status_code >= 400 or not response.content:
                return False, []
            articles = await asyncio.to_thread(
                parse_feed_xml,
                response.content,
                category,
                source["name"],
            )
            return True, articles
        except Exception:
            return False, []


async def fetch_all_feeds(
    feeds_by_category: dict[str, list[FeedSource]] | None = None,
) -> tuple[list[ArticleCreate], RefreshSummary]:
    """Fetch all 90 feeds concurrently with strict error handling and timeout controls."""
    start_time = time.monotonic()
    config = feeds_by_category if feeds_by_category is not None else FEEDS_CONFIG
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_FEEDS)

    headers = {
        "User-Agent": BROWSER_USER_AGENT,
        "Accept": (
            "application/rss+xml, application/atom+xml, "
            "application/xml, text/xml;q=0.9, */*;q=0.8"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    tasks: list[asyncio.Task[tuple[bool, list[ArticleCreate]]]] = []
    async with httpx.AsyncClient(
        headers=headers,
        timeout=httpx.Timeout(FEED_TIMEOUT_SECONDS),
        follow_redirects=True,
    ) as client:
        for category, sources in config.items():
            for source in sources:
                tasks.append(
                    asyncio.create_task(
                        fetch_single_feed(client, semaphore, category, source)
                    )
                )
        results = await asyncio.gather(*tasks, return_exceptions=True)

    all_articles: list[ArticleCreate] = []
    succeeded = 0
    failed = 0

    for res in results:
        if isinstance(res, BaseException):
            failed += 1
            continue
        ok, feed_articles = res
        if ok:
            succeeded += 1
            all_articles.extend(feed_articles)
        else:
            failed += 1

    duration = round(time.monotonic() - start_time, 2)
    summary = RefreshSummary(
        total_feeds=len(tasks),
        succeeded_feeds=succeeded,
        failed_feeds=failed,
        fetched_articles=len(all_articles),
        inserted_articles=0,
        duration_seconds=duration,
    )
    return all_articles, summary


async def fetch_weather() -> WeatherResponse:
    """Fetch current weather and daily high/low + rain probability from Open-Meteo."""
    now_str = datetime.now(timezone.utc).strftime("%H:%M UTC")
    try:
        async with httpx.AsyncClient(
            headers={"User-Agent": BROWSER_USER_AGENT},
            timeout=httpx.Timeout(6.0),
        ) as client:
            resp = await client.get(OPEN_METEO_YANGON_URL)
            resp.raise_for_status()
            data: dict[str, Any] = resp.json()

        current = data.get("current_weather", {})
        daily = data.get("daily", {})

        temp_c = float(current.get("temperature", 31.0))
        wind_kmh = float(current.get("windspeed", 11.0))
        code = int(current.get("weathercode", 2))

        max_list = daily.get("temperature_2m_max", [34.0])
        min_list = daily.get("temperature_2m_min", [25.0])
        rain_list = daily.get("precipitation_probability_max", [30])

        temp_max = float(max_list[0]) if max_list else temp_c
        temp_min = float(min_list[0]) if min_list else temp_c
        rain_prob = int(rain_list[0]) if rain_list and rain_list[0] is not None else 0

        label = WMO_WEATHER_LABELS.get(code, "Partly Cloudy")
        return WeatherResponse(
            location="Yangon, MM",
            temperature_c=round(temp_c, 1),
            windspeed_kmh=round(wind_kmh, 1),
            weather_code=code,
            condition_label=label,
            temp_max_c=round(temp_max, 1),
            temp_min_c=round(temp_min, 1),
            rain_prob_pct=rain_prob,
            updated_at=now_str,
            is_fallback=False,
        )
    except Exception:
        return WeatherResponse(
            location="Yangon, MM",
            temperature_c=31.5,
            windspeed_kmh=10.5,
            weather_code=2,
            condition_label="Partly Cloudy",
            temp_max_c=34.0,
            temp_min_c=25.0,
            rain_prob_pct=20,
            updated_at=now_str,
            is_fallback=True,
        )


def _parse_street_mmk_html(raw_html: str) -> dict[str, tuple[float, float]]:
    """Extract live Myanmar street market (buy, sell) rates from egcurrency MMK page."""
    extracted: dict[str, tuple[float, float]] = {}
    # 1. Primary method: structured data-page JSON embedded in HTML
    try:
        m = re.search(r'data-page=([\'"])(.*?)\1', raw_html, re.DOTALL)
        if m:
            page_data = json.loads(html.unescape(m.group(2)))
            currencies = (
                page_data.get("data", {}).get("currencies", [])
                or page_data.get("props", {}).get("currencies", [])
                or page_data.get("props", {}).get("data", {}).get("currencies", [])
            )
            for c in currencies:
                code = str(c.get("code", "")).upper()
                if code in ("USD", "EUR", "SGD", "THB"):
                    market = c.get("sources", {}).get("market", {})
                    if market:
                        buy_val = float(market.get("buy", 0))
                        sell_val = float(market.get("sell", 0))
                        if buy_val > 0 and sell_val > 0:
                            extracted[code] = (min(buy_val, sell_val), max(buy_val, sell_val))
    except Exception:
        pass

    # 2. Resilient fallback regex if data-page structure changes (scoped strictly per currency block)
    if not extracted:
        unescaped = html.unescape(raw_html)
        for code in ("USD", "EUR", "SGD", "THB"):
            pattern = (
                r'\{[^{}]*?"code"\s*:\s*"'
                + code
                + r'"[^{}]*?"market"\s*:\s*\{[^{}]*?"buy"\s*:\s*"([0-9.]+)"[^{}]*?"sell"\s*:\s*"([0-9.]+)"'
            )
            match = re.search(pattern, unescaped)
            if not match:
                pattern_rev = (
                    r'\{[^{}]*?"code"\s*:\s*"'
                    + code
                    + r'"[^{}]*?"market"\s*:\s*\{[^{}]*?"sell"\s*:\s*"([0-9.]+)"[^{}]*?"buy"\s*:\s*"([0-9.]+)"'
                )
                match = re.search(pattern_rev, unescaped)
            if match:
                try:
                    v1 = float(match.group(1))
                    v2 = float(match.group(2))
                    if v1 > 0 and v2 > 0:
                        extracted[code] = (min(v1, v2), max(v1, v2))
                except Exception:
                    continue

    return extracted


def _build_market_response(
    rates: dict[str, Any],
    gold_spot_usd: float,
    is_fallback: bool,
    street_rates: dict[str, tuple[float, float]] | None = None,
    calibration: MarketCalibration | None = None,
) -> MarketResponse:
    """Compute Myanmar street market currency & 16-Pae gold rates (with optional user calibration)."""
    now_str = datetime.now(timezone.utc).strftime("%H:%M UTC")

    raw_mmk = float(rates.get("MMK", 2100.0))
    cbm_usd_mmk = raw_mmk if 1000 <= raw_mmk <= 2500 else 2100.0

    eur_per_usd = float(rates.get("EUR", 0.92)) or 0.92
    sgd_per_usd = float(rates.get("SGD", 1.34)) or 1.34
    thb_per_usd = float(rates.get("THB", 33.8)) or 33.8

    # Default Yangon open market USD/MMK (~4,835 Ks) or live scraped street rate
    street = street_rates or {}
    if "USD" in street:
        usd_buy, usd_sell = street["USD"]
        market_usd_mmk = round((usd_buy + usd_sell) / 2.0, 0)
    else:
        market_usd_mmk = 4835.0
        usd_buy, usd_sell = 4810.0, 4860.0

    is_calibrated = False
    if calibration is not None and (
        calibration.usd_mmk
        or calibration.eur_mmk
        or calibration.sgd_mmk
        or calibration.thb_mmk
        or calibration.gold_16pae_mmk
    ):
        is_calibrated = True
        if calibration.usd_mmk:
            market_usd_mmk = round(calibration.usd_mmk, 0)
            usd_buy = round(market_usd_mmk - 25, 0)
            usd_sell = round(market_usd_mmk + 25, 0)

    # Compute EUR, SGD, THB street rates from live street data, calibration, or cross-rates
    if calibration and calibration.eur_mmk:
        eur_mid = round(calibration.eur_mmk, 0)
        eur_buy, eur_sell = round(eur_mid - 30, 0), round(eur_mid + 30, 0)
    elif "EUR" in street:
        eur_buy, eur_sell = round(street["EUR"][0], 0), round(street["EUR"][1], 0)
        eur_mid = round((eur_buy + eur_sell) / 2.0, 0)
    else:
        eur_mid = round(market_usd_mmk / eur_per_usd, 0)
        eur_buy, eur_sell = round(eur_mid - 30, 0), round(eur_mid + 30, 0)

    if calibration and calibration.sgd_mmk:
        sgd_mid = round(calibration.sgd_mmk, 0)
        sgd_buy, sgd_sell = round(sgd_mid - 20, 0), round(sgd_mid + 20, 0)
    elif "SGD" in street:
        sgd_buy, sgd_sell = round(street["SGD"][0], 0), round(street["SGD"][1], 0)
        sgd_mid = round((sgd_buy + sgd_sell) / 2.0, 0)
    else:
        sgd_mid = round(market_usd_mmk / sgd_per_usd, 0)
        sgd_buy, sgd_sell = round(sgd_mid - 20, 0), round(sgd_mid + 20, 0)

    if calibration and calibration.thb_mmk:
        thb_mid = round(calibration.thb_mmk, 1)
        thb_buy, thb_sell = round(thb_mid - 1.0, 1), round(thb_mid + 1.0, 1)
    elif "THB" in street:
        thb_buy, thb_sell = round(street["THB"][0], 1), round(street["THB"][1], 1)
        thb_mid = round((thb_buy + thb_sell) / 2.0, 1)
    else:
        thb_mid = round(market_usd_mmk / thb_per_usd, 1)
        thb_buy, thb_sell = round(thb_mid - 1.0, 1), round(thb_mid + 1.0, 1)

    currencies = [
        CurrencyRate(
            code="USD",
            name="US Dollar",
            cbm_ref_mmk=round(cbm_usd_mmk, 0),
            market_est_mmk=market_usd_mmk,
            buy_mmk=round(usd_buy, 0),
            sell_mmk=round(usd_sell, 0),
        ),
        CurrencyRate(
            code="EUR",
            name="Euro",
            cbm_ref_mmk=round(cbm_usd_mmk / eur_per_usd, 0),
            market_est_mmk=eur_mid,
            buy_mmk=eur_buy,
            sell_mmk=eur_sell,
        ),
        CurrencyRate(
            code="SGD",
            name="Singapore Dollar",
            cbm_ref_mmk=round(cbm_usd_mmk / sgd_per_usd, 0),
            market_est_mmk=sgd_mid,
            buy_mmk=sgd_buy,
            sell_mmk=sgd_sell,
        ),
        CurrencyRate(
            code="THB",
            name="Thai Baht",
            cbm_ref_mmk=round(cbm_usd_mmk / thb_per_usd, 1),
            market_est_mmk=thb_mid,
            buy_mmk=thb_buy,
            sell_mmk=thb_sell,
        ),
    ]

    # Yangon Shwe Bon Thar Street Formula: (World_Spot_USD / 1.875) * Street_USD_MMK
    tical_usd = gold_spot_usd * TROY_OZ_PER_TICAL
    world_equiv_cbm_mmk = int(round(tical_usd * cbm_usd_mmk, -3))

    if calibration and calibration.gold_16pae_mmk:
        market_16pae_mmk = int(calibration.gold_16pae_mmk)
    else:
        # Standard Shwe Bon Thar bullion rounding to nearest 5,000 Ks
        raw_16pae = (gold_spot_usd / KYATTHA_PER_TROY_OZ) * market_usd_mmk
        market_16pae_mmk = int(round(raw_16pae / 5000.0) * 5000)

    # 15 Pae Yway (93.75% jewelry gold) in Myanmar gold shops is (16_Pae / 16) * 15
    market_15pae_mmk = int(round((market_16pae_mmk * 15.0 / 16.0) / 5000.0) * 5000)

    gold = GoldRate(
        world_spot_usd_oz=round(gold_spot_usd, 2),
        world_equiv_mmk_tical=world_equiv_cbm_mmk,
        ygea_ref_mmk_tical=YGEA_OFFICIAL_REF_MMK,
        market_16pae_mmk_tical=market_16pae_mmk,
        market_15pae_mmk_tical=market_15pae_mmk,
    )

    return MarketResponse(
        currencies=currencies,
        gold=gold,
        updated_at=now_str,
        is_fallback=is_fallback,
        is_calibrated=is_calibrated,
    )


async def fetch_market_rates() -> MarketResponse:
    """Fetch live Yangon street market forex & gold rates with user calibration support."""
    default_gold_usd = 3909.0
    calibration = await asyncio.to_thread(get_market_calibration)
    try:
        async with httpx.AsyncClient(
            headers={"User-Agent": BROWSER_USER_AGENT},
            timeout=httpx.Timeout(6.5),
            follow_redirects=True,
        ) as client:
            forex_task = client.get(FOREX_API_URL)
            gold_task = client.get(GOLD_PAXG_API_URL)
            gold_api_task = client.get(GOLD_API_URL)
            street_task = client.get(MYANMAR_STREET_FX_URL)
            forex_resp, gold_resp, gold_api_resp, street_resp = await asyncio.gather(
                forex_task, gold_task, gold_api_task, street_task, return_exceptions=True
            )

        if isinstance(forex_resp, BaseException):
            raise RuntimeError("Forex endpoint unreachable")
        forex_resp.raise_for_status()
        forex_payload: dict[str, Any] = forex_resp.json()
        rates: dict[str, Any] = forex_payload.get("rates", {})
        if not rates:
            raise RuntimeError("Empty forex rates payload")

        gold_spot_usd = default_gold_usd
        if not isinstance(gold_api_resp, BaseException) and gold_api_resp.status_code == 200:
            try:
                g_price = float(gold_api_resp.json().get("price", 0))
                if g_price > 1000:
                    gold_spot_usd = g_price
            except Exception:
                pass

        if gold_spot_usd == default_gold_usd:
            if "XAU" in rates and float(rates["XAU"]) > 0:
                gold_spot_usd = 1.0 / float(rates["XAU"])
            elif not isinstance(gold_resp, BaseException) and gold_resp.status_code == 200:
                gold_data = gold_resp.json().get("data", {})
                amount_str = gold_data.get("amount")
                if amount_str:
                    gold_spot_usd = float(amount_str)

        street_rates: dict[str, tuple[float, float]] = {}
        if not isinstance(street_resp, BaseException) and street_resp.status_code == 200:
            street_rates = _parse_street_mmk_html(street_resp.text)

        return _build_market_response(
            rates=rates,
            gold_spot_usd=gold_spot_usd,
            is_fallback=False,
            street_rates=street_rates,
            calibration=calibration,
        )
    except Exception:
        fallback_rates: dict[str, float] = {
            "MMK": 2100.0,
            "EUR": 0.923,
            "SGD": 1.342,
            "THB": 33.75,
        }
        return _build_market_response(
            rates=fallback_rates,
            gold_spot_usd=default_gold_usd,
            is_fallback=True,
            street_rates=None,
            calibration=calibration,
        )
