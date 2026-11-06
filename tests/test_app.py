"""Unit tests for the Personal News Aggregator, Weather & Myanmar Market Tracker."""

from pathlib import Path
import json
import time
from datetime import datetime, timezone

import pytest

from app.database import (
    ArticleCreate,
    MarketCalibration,
    clear_market_calibration,
    compute_article_id,
    dismiss_article,
    dismiss_category_articles,
    get_active_articles,
    get_market_calibration,
    get_unread_counts,
    init_db,
    purge_old_articles,
    save_market_calibration,
    toggle_save_article,
    upsert_articles,
)
from app.feeds_config import FEEDS_CONFIG
from app.fetcher import (
    _build_market_response,
    _parse_street_mmk_html,
    extract_entry_raw_summary,
    is_article_relevant,
    parse_feed_xml,
    sanitize_html_to_brief,
)


def test_feeds_config_has_252_sources() -> None:
    """Verify 14 categories (3 Myanmar + 11 World) with 18 prestigious sources each (252 feeds total)."""
    assert len(FEEDS_CONFIG) == 14
    total = 0
    for category, sources in FEEDS_CONFIG.items():
        assert len(sources) == 18, f"Category {category} does not have 18 sources"
        for src in sources:
            assert src["name"].strip()
            assert src["url"].startswith("http")
            total += 1
    assert total == 252


def test_sanitize_html_to_brief() -> None:
    """Verify HTML tags, scripts, and entities are stripped and capped at 280 chars."""
    dirty = (
        "<div><script>alert(1)</script><p>First &amp; foremost sentence. "
        "<b>Second</b> sentence with &quot;quotes&quot;. "
        "Third sentence here. Fourth sentence should be trimmed.</p></div>"
    )
    cleaned = sanitize_html_to_brief(dirty)
    assert "<" not in cleaned
    assert ">" not in cleaned
    assert "alert(1)" not in cleaned
    assert 'First & foremost sentence. Second sentence with "quotes". Third sentence here.' == cleaned
    assert len(cleaned) <= 280

    long_text = "<p>" + ("word " * 100) + "</p>"
    truncated = sanitize_html_to_brief(long_text)
    assert len(truncated) <= 280
    assert truncated.endswith("…")


def test_extract_entry_raw_summary_fallbacks() -> None:
    """Verify summary -> description -> content fallback order."""
    assert extract_entry_raw_summary({"summary": "From summary"}) == "From summary"
    assert (
        extract_entry_raw_summary({"summary": "", "description": "From description"})
        == "From description"
    )
    assert (
        extract_entry_raw_summary(
            {"content": [{"value": "From content list"}]}
        )
        == "From content list"
    )


def test_sqlite_deduplication_and_permanent_dismiss(tmp_path: Path) -> None:
    """Verify SHA-256 canonical URL deduplication and permanent dismissal across fetches."""
    db_file = tmp_path / "test_news.db"
    init_db(db_file)

    url_clean = "https://www.irrawaddy.com/news/burma/story-123.html"
    url_with_utm = "https://www.irrawaddy.com/news/burma/story-123.html?utm_source=rss&fbclid=abc"

    id1 = compute_article_id(url_clean)
    id2 = compute_article_id(url_with_utm)
    assert id1 == id2

    now_ts = int(time.time())
    now_iso = datetime.now(timezone.utc).isoformat()

    art1 = ArticleCreate(
        id=id1,
        category="Myanmar & World",
        source="The Irrawaddy",
        title="Test Story 1",
        url=url_clean,
        brief="Brief summary of story 1.",
        published_at=now_iso,
        published_ts=now_ts - 3600,
    )
    art2 = ArticleCreate(
        id=compute_article_id("https://www.myanmar-now.org/en/news/story-456"),
        category="Myanmar & World",
        source="Myanmar Now",
        title="Test Story 2",
        url="https://www.myanmar-now.org/en/news/story-456",
        brief="Brief summary of story 2.",
        published_at=now_iso,
        published_ts=now_ts - 1800,
    )

    inserted = upsert_articles([art1, art2], db_file)
    assert inserted == 2

    # Re-inserting same URL with UTM parameters should be ignored (0 inserted)
    duplicate_inserted = upsert_articles([art1], db_file)
    assert duplicate_inserted == 0

    # Dismiss story 1
    assert dismiss_article(id1, db_file) is True

    # Story 1 must not appear in active articles even after another upsert
    upsert_articles([art1, art2], db_file)
    active = get_active_articles(category="Myanmar & World", db_path=db_file)
    assert len(active) == 1
    assert active[0].id == art2.id

    counts = get_unread_counts(db_file)
    assert counts["Myanmar & World"] == 1

    # Dismiss remaining visible in category
    dismissed_cat_count = dismiss_category_articles("Myanmar & World", db_file)
    assert dismissed_cat_count == 1
    assert get_active_articles(db_path=db_file) == []


def test_parse_feed_xml_and_market_rates() -> None:
    """Verify RSS XML parser and Myanmar FX + Gold calculations."""
    sample_rss = """<?xml version="1.0" encoding="UTF-8" ?>
    <rss version="2.0">
      <channel>
        <title>Sample Tech</title>
        <item>
          <title>New AI Breakthrough</title>
          <link>https://example.com/ai-breakthrough</link>
          <description><![CDATA[<p>Researchers unveiled a fast local model. It runs with zero cost.</p>]]></description>
          <pubDate>Thu, 29 Oct 2026 08:00:00 GMT</pubDate>
        </item>
      </channel>
    </rss>
    """
    parsed_articles = parse_feed_xml(sample_rss, "AI", "Sample AI Feed")
    assert len(parsed_articles) == 1
    assert parsed_articles[0].title == "New AI Breakthrough"
    assert parsed_articles[0].brief == "Researchers unveiled a fast local model. It runs with zero cost."

    market = _build_market_response(
        rates={"MMK": 2100.0, "EUR": 0.92, "SGD": 1.34, "THB": 33.8},
        gold_spot_usd=2740.0,
        is_fallback=False,
    )
    codes = [c.code for c in market.currencies]
    assert codes == ["USD", "EUR", "SGD", "THB"]
    assert market.gold.market_16pae_mmk_tical > market.gold.market_15pae_mmk_tical


def test_relevance_filter_for_separated_myanmar_world_and_military_tabs() -> None:
    """Verify strict separation across Myanmar, Crisis & Geopolitics, and Military, Weapons & Defense Tech."""
    # Sports & Ethiopia/Tigray noise must be blocked everywhere
    assert not is_article_relevant(
        "Myanmar: Current Situation & Daily Life",
        "Ethiopia acquires Russian fighter jets and air defence systems amid war in Tigray",
        "The acquisition of the warplanes comes amid ongoing fighting in northern Tigray region.",
        "BBC World",
    )
    assert not is_article_relevant(
        "Crisis & Geopolitics",
        "Ethiopia acquires Russian fighter jets and air defence systems amid war in Tigray",
        "The acquisition of the warplanes comes amid ongoing fighting in northern Tigray region.",
        "BBC World",
    )
    assert not is_article_relevant(
        "Military, Weapons & Defense Tech",
        "Ethiopia acquires Russian fighter jets and air defence systems amid war in Tigray",
        "The acquisition of the warplanes comes amid ongoing fighting in northern Tigray region.",
        "BBC World",
    )

    # 1. Myanmar categories: accepts NUG, passport restrictions, business, rejects non-Myanmar stories
    assert is_article_relevant(
        "Myanmar: Politics & NUG",
        "NUG warns international community against normalizing military junta ties",
        "The National Unity Government and CRPH urged ASEAN to maintain stance against military council.",
        "The Irrawaddy",
    )
    assert is_article_relevant(
        "Myanmar: Current Situation & Daily Life",
        "Junta restricts passport renewals and offloads youths traveling abroad at Yangon airport",
        "Strict OWIC work permit and conscription requirements prevent citizens from moving abroad.",
        "Myanmar Now",
    )
    assert not is_article_relevant(
        "Myanmar: Politics & NUG",
        "Iran warns of retaliation after military airstrikes",
        "Tensions escalate across the Middle East.",
        "Iran War Watch",
    )

    # 2. Crisis & Geopolitics tab: accepts Iran/Ukraine/Taiwan crises, rejects unrelated domestic stories
    assert is_article_relevant(
        "Crisis & Geopolitics",
        "Iran warns of retaliation after Israeli airstrikes near Tehran",
        "Tensions escalate across the Strait of Hormuz as UN Security Council convenes.",
        "Iran, Israel & Middle East War Watch",
    )

    # 3. Military, Weapons & Defense Tech tab: accepts weapons R&D, drones, hypersonics, military AI
    assert is_article_relevant(
        "Military, Weapons & Defense Tech",
        "Pentagon and DARPA test autonomous drone swarm and hypersonic missile defense",
        "New electronic warfare and laser weapon systems deployed on stealth fighter jets.",
        "The War Zone (TWZ)",
    )


def test_section_filtering_myanmar_and_world(tmp_path: Path) -> None:
    """Verify All Myanmar and All World section filtering in database queries."""
    db_file = tmp_path / "test_sections.db"
    init_db(db_file)

    now_ts = int(time.time())
    now_iso = datetime.now(timezone.utc).isoformat()

    art_m1 = ArticleCreate(
        id=compute_article_id("https://example.com/m1"),
        category="Myanmar: Current Situation & Daily Life",
        source="Myanmar Now",
        title="Yangon youth passport and airport exit scrutiny",
        url="https://example.com/m1",
        brief="Brief about passports.",
        published_at=now_iso,
        published_ts=now_ts - 100,
    )
    art_m2 = ArticleCreate(
        id=compute_article_id("https://example.com/m2"),
        category="Myanmar: Politics & NUG",
        source="The Irrawaddy",
        title="NUG announces diplomatic initiative",
        url="https://example.com/m2",
        brief="Brief about NUG.",
        published_at=now_iso,
        published_ts=now_ts - 200,
    )
    art_w1 = ArticleCreate(
        id=compute_article_id("https://example.com/w1"),
        category="Space",
        source="NASA",
        title="Artemis lunar mission advances",
        url="https://example.com/w1",
        brief="Brief about Artemis.",
        published_at=now_iso,
        published_ts=now_ts - 300,
    )
    art_w2 = ArticleCreate(
        id=compute_article_id("https://example.com/w2"),
        category="Politics",
        source="Politico",
        title="Senate debates legislative package",
        url="https://example.com/w2",
        brief="Brief about Senate.",
        published_at=now_iso,
        published_ts=now_ts - 400,
    )

    upsert_articles([art_m1, art_m2, art_w1, art_w2], db_file)

    # 1. All Myanmar returns only Myanmar categories
    myanmar_articles = get_active_articles("All Myanmar", db_path=db_file)
    assert len(myanmar_articles) == 2
    assert {a.id for a in myanmar_articles} == {art_m1.id, art_m2.id}

    # 2. All World returns only World categories
    world_articles = get_active_articles("All World", db_path=db_file)
    assert len(world_articles) == 2
    assert {a.id for a in world_articles} == {art_w1.id, art_w2.id}

    # 3. Unread counts contains roll-up section totals
    counts = get_unread_counts(db_file)
    assert counts["All Myanmar"] == 2
    assert counts["All World"] == 2
    assert counts["Myanmar: Current Situation & Daily Life"] == 1
    assert counts["Space"] == 1


def test_market_calibration_and_yangon_gold_formula(tmp_path: Path) -> None:
    """Verify Yangon street gold formula (1.875 kyattha/oz) and SQLite calibration overrides."""
    db_file = tmp_path / "test_cal.db"
    init_db(db_file)

    assert get_market_calibration(db_file) is None

    cal = MarketCalibration(usd_mmk=4680.0, gold_16pae_mmk=10150000, thb_mmk=135.0)
    saved = save_market_calibration(cal, db_file)
    assert saved.updated_at is not None

    loaded = get_market_calibration(db_file)
    assert loaded is not None
    assert loaded.usd_mmk == 4680.0
    assert loaded.gold_16pae_mmk == 10150000

    resp = _build_market_response(
        rates={"MMK": 2100.0, "EUR": 0.92, "SGD": 1.34, "THB": 33.8},
        gold_spot_usd=4025.0,
        is_fallback=False,
        calibration=loaded,
    )
    assert resp.is_calibrated is True
    assert resp.gold.market_16pae_mmk_tical == 10150000
    assert resp.gold.ygea_ref_mmk_tical == 7100000

    clear_market_calibration(db_file)
    assert get_market_calibration(db_file) is None


def test_save_and_bookmark_read_later(tmp_path: Path) -> None:
    """Verify bookmarking articles into the Saved/Read Later tab."""
    db_file = tmp_path / "test_saved.db"
    init_db(db_file)

    now_ts = int(time.time())
    now_iso = datetime.now(timezone.utc).isoformat()

    art = ArticleCreate(
        id=compute_article_id("https://example.com/defense-tech-drone"),
        category="Military, Weapons & Defense Tech",
        source="The War Zone",
        title="Next Gen Drone Swarm",
        url="https://example.com/defense-tech-drone",
        brief="Autonomous drone defense test.",
        published_at=now_iso,
        published_ts=now_ts - 3600,
    )
    upsert_articles([art], db_file)

    # Initially not saved
    counts = get_unread_counts(db_file)
    assert counts.get("Saved", 0) == 0
    assert len(get_active_articles("Saved", db_path=db_file)) == 0

    # Toggle save ON
    new_state = toggle_save_article(art.id, db_file)
    assert new_state is True

    counts_after = get_unread_counts(db_file)
    assert counts_after["Saved"] == 1

    saved_articles = get_active_articles("Saved", db_path=db_file)
    assert len(saved_articles) == 1
    assert saved_articles[0].id == art.id
    assert saved_articles[0].saved is True

    # Even if dismissed from feeds, it stays in Saved tab
    dismiss_article(art.id, db_file)
    assert len(get_active_articles("Military, Weapons & Defense Tech", db_path=db_file)) == 0
    assert len(get_active_articles("Saved", db_path=db_file)) == 1

    # Toggle save OFF
    new_state_off = toggle_save_article(art.id, db_file)
    assert new_state_off is False
    assert len(get_active_articles("Saved", db_path=db_file)) == 0


def test_purge_old_articles_retention_and_saved_immunity(tmp_path: Path) -> None:
    """Verify articles older than 7 days are purged while saved bookmarks are kept."""
    import time
    db_file = tmp_path / "test_purge.db"
    init_db(db_file)

    now_ts = int(time.time())
    old_ts = now_ts - (10 * 86400)  # 10 days ago (older than 7d)
    fresh_ts = now_ts - (2 * 86400)  # 2 days ago (fresh)

    art_old = ArticleCreate(
        id=compute_article_id("https://example.com/old-story"),
        category="Science",
        source="Nature",
        title="10 Days Old Story",
        url="https://example.com/old-story",
        brief="Old discovery.",
        published_at="2026-10-20T00:00:00Z",
        published_ts=old_ts,
    )
    art_fresh = ArticleCreate(
        id=compute_article_id("https://example.com/fresh-story"),
        category="Science",
        source="Nature",
        title="2 Days Old Fresh Story",
        url="https://example.com/fresh-story",
        brief="Fresh discovery.",
        published_at="2026-10-28T00:00:00Z",
        published_ts=fresh_ts,
    )
    art_old_saved = ArticleCreate(
        id=compute_article_id("https://example.com/old-saved-story"),
        category="AI",
        source="MIT AI",
        title="Old But Bookmarked Story",
        url="https://example.com/old-saved-story",
        brief="Important research paper.",
        published_at="2026-10-18T00:00:00Z",
        published_ts=old_ts,
    )

    upsert_articles([art_old, art_fresh, art_old_saved], db_file)
    toggle_save_article(art_old_saved.id, db_file)

    # Before purge, active feeds only return fresh articles (<7d)
    active = get_active_articles("Science", db_path=db_file)
    assert len(active) == 1
    assert active[0].id == art_fresh.id

    # Purge articles older than 7 days
    purged_count = purge_old_articles(max_age_days=7, db_path=db_file)
    assert purged_count == 1  # Only un-saved old article is deleted

    # Bookmarked old article is safely preserved
    saved = get_active_articles("Saved", db_path=db_file)
    assert len(saved) == 1
    assert saved[0].id == art_old_saved.id


def test_admin_pin_protection_for_calibration(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that market calibration requires the correct admin PIN and cleans up properly."""
    from starlette.testclient import TestClient
    from app.main import app
    import app.database as db_mod

    test_db = tmp_path / "test_api_cal.db"
    db_mod.init_db(test_db)
    monkeypatch.setattr(db_mod, "DEFAULT_DB_PATH", test_db)

    client = TestClient(app)

    # 1. Reject invalid PIN
    res_bad = client.post(
        "/api/market/calibrate",
        json={"usd_mmk": 4700.0, "pin": "wrong_pin"},
    )
    assert res_bad.status_code == 403
    assert "Invalid Admin PIN" in res_bad.text

    # 2. Reject reset without PIN
    res_reset_bad = client.delete("/api/market/calibrate?pin=wrong")
    assert res_reset_bad.status_code == 403

    # 3. Accept admin PIN ($Billionaire3)
    res_good = client.post(
        "/api/market/calibrate",
        json={"usd_mmk": 4700.0, "pin": "$Billionaire3"},
    )
    assert res_good.status_code == 200
    assert res_good.json()["is_calibrated"] is True

    # 4. Clean up / reset calibration
    res_reset = client.delete("/api/market/calibrate?pin=$Billionaire3")
    assert res_reset.status_code == 200
    assert res_reset.json()["is_calibrated"] is False


def test_parse_street_mmk_html_no_crossover() -> None:
    """Verify that street MMK HTML parser correctly extracts SGD, USD, EUR, THB without crossover."""
    sample_json = {
        "data": {
            "currencies": [
                {
                    "code": "USD",
                    "sources": {"market": {"buy": "4860.00", "sell": "4811.40"}},
                },
                {
                    "code": "SGD",
                    "sources": {"market": {"buy": "3796.88", "sell": "3758.91"}},
                },
                {
                    "code": "EUR",
                    "sources": {"market": {"buy": "5400.00", "sell": "5346.00"}},
                },
                {
                    "code": "THB",
                    "sources": {"market": {"buy": "144.00", "sell": "142.56"}},
                },
            ]
        }
    }
    sample_html = f'<html><body><div id="app" data-page=\'{json.dumps(sample_json)}\'></div></body></html>'
    extracted = _parse_street_mmk_html(sample_html)

    assert "USD" in extracted
    assert "SGD" in extracted
    assert "EUR" in extracted
    assert "THB" in extracted

    # Verify SGD does NOT equal USD
    assert extracted["USD"] == (4811.40, 4860.00)
    assert extracted["SGD"] == (3758.91, 3796.88)
    assert extracted["EUR"] == (5346.00, 5400.00)
    assert extracted["THB"] == (142.56, 144.00)





