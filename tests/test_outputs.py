import re
from datetime import date, datetime, timedelta, timezone

import pandas as pd
import pytest

from pulse import calendar as cal
from pulse.core import load_yaml
from pulse.events import should_promote, classify, scan_candidates
from pulse.export import TABLES, export_powerbi
from pulse.news import store_news
from pulse.outputs.brief import BODY_END, body_of, build_brief
from tests.conftest import put

LATIN = re.compile(r"[A-Za-z]")


def test_rule_arabic_templates_have_no_latin():
    for rid, r in load_yaml("rules.yaml")["rules"].items():
        tpl = re.sub(r"\{[^}]*\}", "", r["ar"])
        assert not LATIN.search(tpl), rid


def test_brief_body_has_no_latin_and_has_glossary(conn):
    put(conn, "fx_cbe_official", "2026-10-15", 53.41)
    put(conn, "cpi_urban_yoy", "2026-09-01", 13.9)
    put(conn, "brent", "2026-10-14", 126.55, source="FRED DCOILBRENTEU (EIA via FRED)")
    put(conn, "budget_oil_assumption", "2026-07-01", 75, quality="secondary")
    cal.refresh(conn)
    md = build_brief(conn, date(2026, 10, 18))
    body = body_of(md)
    assert not LATIN.search(body), [l for l in body.splitlines() if LATIN.search(l)][:3]
    for h in ("الخلاصة", "الجنيه النهارده", "الفلوس الداخلة والخارجة", "الفايدة والتضخم", "البترول والدهب",
              "السياسة والمنطقة", "إيه اللي جاي في الأجندة"):
        assert f"## {h}" in body
    assert "| المصطلح بالعربي | English term | شرح بسيط |" in md
    assert md.rstrip().splitlines()[-1].startswith("|")  # glossary is the last section
    assert BODY_END in md and "https://example.org/src" in md.split(BODY_END)[1]


def test_export_schema(conn, tmp_path, monkeypatch):
    import pulse.export as ex
    monkeypatch.setattr(ex, "EXPORTS", tmp_path)
    put(conn, "nir", "2026-09-01", 57348.2)
    out = export_powerbi(conn)
    assert set(out) == set(TABLES)
    for t in TABLES:
        assert (tmp_path / f"{t}.csv").exists() and (tmp_path / f"{t}.parquet").exists()
        assert (tmp_path / f"{t}.csv").read_bytes()[:3] == b"\xef\xbb\xbf"  # UTF-8 BOM for Arabic
    fo = pd.read_csv(tmp_path / "fact_observations.csv")
    for col in ("series_id", "obs_date", "value", "source_name", "source_url", "release_date", "retrieved_at", "quality_flag"):
        assert col in fo.columns
    dd = pd.read_csv(tmp_path / "dim_date.csv")
    assert {"cairo_business_day", "egypt_fy"} <= set(dd.columns)
    assert re.match(r"\d{4}-\d{2}-\d{2}$", str(fo["obs_date"].iloc[0]))


def test_calendar_timezones():
    # PortWatch Tuesday 09:00 ET → Cairo: 16:00 while both are on summer time (Oct 2026)
    rec = [r for r in cal.generate_recurring(date(2026, 10, 18), 10) if r["kind"] == "portwatch"]
    assert rec and rec[0]["date"].weekday() == 1 and rec[0]["time"] == "16:00"
    # FOMC decision 14:00 ET on 9 Dec 2026 → 21:00 Cairo (EST UTC-5, Cairo UTC+2)
    assert cal._to_cairo(date(2026, 12, 9), "14:00", cal.ET) == "21:00"
    assert cal.nth_business_day(2026, 11, 3, "global") == date(2026, 11, 4)


def test_fomc_parser():
    html = """<div class="panel"><h4>2026 FOMC Meetings</h4><div class="fomc-meeting"><div class="fomc-meeting__month">October</div>
    <div class="fomc-meeting__date">27-28</div></div><div class="fomc-meeting"><div class="fomc-meeting__month">December</div>
    <div class="fomc-meeting__date">8-9*</div></div></div>"""
    assert cal.parse_fomc(html) == [date(2026, 10, 28), date(2026, 12, 9)]


def test_two_outlet_promotion_rule():
    t = datetime(2026, 10, 16, 10, tzinfo=timezone.utc)
    assert not should_promote([("EnterpriseAM", t)])
    assert not should_promote([("EnterpriseAM", t), ("EnterpriseAM", t + timedelta(hours=1))])
    assert not should_promote([("EnterpriseAM", t), ("Mada Masr", t + timedelta(hours=49))])
    assert not should_promote([("EnterpriseAM", t), ("GDELT: example.com", t + timedelta(hours=1))])
    assert should_promote([("EnterpriseAM", t), ("Daily News Egypt", t + timedelta(hours=47))])


def test_scan_candidates_promotes_with_two_outlets(conn):
    now = datetime.now(timezone.utc)
    store_news(conn, "EnterpriseAM", "https://a/1", "Moody's raises Egypt's ratings to B3", "", (now - timedelta(hours=5)).isoformat())
    store_news(conn, "Daily News Egypt", "https://b/1", "Moody's upgrades Egypt rating to B3", "", (now - timedelta(hours=2)).isoformat())
    stats = scan_candidates(conn, now)
    ev = conn.execute("SELECT confidence FROM events WHERE event_type='rating_upgrade'").fetchall()
    assert stats["promoted"] == 1 and [e[0] for e in ev] == ["reported"]
    assert classify("Fitch affirms Egypt at B with stable outlook") == ["rating_affirmation"]


def test_site_bundle_is_valid_js(conn, tmp_path, monkeypatch):
    import json
    import pulse.outputs.site_data as sd
    put(conn, "fx_cbe_official", "2026-10-15", 53.41)
    put(conn, "fx_cbe_official", "2026-10-18", 53.47)
    monkeypatch.setattr(sd, "SITE", tmp_path)
    sd.write_site(conn)
    js = (tmp_path / "data" / "pulse-data.js").read_text(encoding="utf-8")
    assert js.startswith("window.__pulseData(") and js.rstrip().endswith(");")
    b = json.loads(js[len("window.__pulseData("):-3])
    s = b["series"]["fx_cbe_official"]
    assert s["value"] == 53.47 and s["sign"] == 1 and s["change"] == pytest.approx(0.06)
    assert b["series"]["cds_5y"]["empty"] is True
    assert {"ppi", "subindices", "rules", "calendar", "domains", "brief", "next_runs"} <= set(b)
    assert (tmp_path / "data" / "manifest.js").exists() and (tmp_path / "index.html").exists()
    assert (tmp_path / "data" / "series" / "fx_cbe_official.js").exists()
