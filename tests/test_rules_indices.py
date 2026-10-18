from datetime import date, timedelta

import numpy as np
import pytest

from pulse.events import upsert_event
from pulse.indices import compute, score_input
from pulse.rules import evaluate
from tests.conftest import daily, put

AS_OF = date(2026, 10, 18)


def _fx(conn, values, end=date(2026, 10, 15)):
    # Egyptian business days ending `end`
    days, d = [], end
    while len(days) < len(values):
        if d.weekday() in (6, 0, 1, 2, 3):
            days.append(d)
        d -= timedelta(days=1)
    for day, v in zip(reversed(days), values):
        put(conn, "fx_cbe_official", day, v)


def test_sharp_move_fires_on_synthetic_fixture(conn):
    from pulse.derive import compute_all
    _fx(conn, [50.0] * 25 + [51.0, 51.5, 52.0, 52.5, 53.0])
    compute_all(conn)
    res = evaluate(conn, AS_OF)
    assert res["FX05"].fired and res["FX05"].direction == 1
    assert "5 CBE business days" in res["FX05"].explanation_en


def test_parallel_gap_levels_and_noise(conn):
    put(conn, "gold_gap_pct", AS_OF, 0.5, quality="derived")
    r = evaluate(conn, AS_OF)["FX02"]
    assert r.evaluable and not r.fired  # inside ±0.8% noise
    put(conn, "gold_gap_pct", AS_OF + timedelta(days=0), 6.0, quality="derived", source="other")
    conn.execute("DELETE FROM observations WHERE series_id='gold_gap_pct' AND value=0.5")
    r = evaluate(conn, AS_OF)["FX02"]
    assert r.fired and r.vals["level"] == "alert"


def test_real_rate_cushion_relief(conn):
    put(conn, "real_headline", "2026-09-01", 5.1, quality="derived")
    put(conn, "cpi_urban_yoy", "2026-09-01", 13.9)
    put(conn, "cbe_odr", "2026-02-15", 19.0)
    r = evaluate(conn, AS_OF)["MO01"]
    assert r.fired and r.direction == -1


def test_oil_budget_gap_strong(conn):
    put(conn, "budget_oil_assumption", "2026-07-01", 75)
    put(conn, "brent_gap", "2026-10-14", 34.86, quality="derived")
    r = evaluate(conn, AS_OF)["EC01"]
    assert r.fired and r.strength == pytest.approx(1.0)


def test_missing_inputs_are_not_evaluable(conn):
    res = evaluate(conn, AS_OF)
    assert not res["MO03"].evaluable  # consensus is paid/manual
    assert not res["FX01"].evaluable
    assert all(not r.fired for r in res.values() if not r.evaluable)


def test_rating_upgrade_event_relief(conn):
    upsert_event(conn, event_date=date(2026, 10, 16), event_type="rating_upgrade", title_en="Moody's upgrades Egypt to B3",
                 title_ar="رفع التصنيف", confidence="confirmed", source_name="x", source_url="https://x", entered_by="manual")
    r = evaluate(conn, AS_OF)["FD04"]
    assert r.fired and r.direction == -1


def test_candidate_events_never_count(conn):
    upsert_event(conn, event_date=date(2026, 10, 17), event_type="regional_war_escalation", title_en="x", title_ar="",
                 confidence="candidate", source_name="x", source_url="https://x", entered_by="auto_candidate")
    r = evaluate(conn, AS_OF)["GP04"]
    assert not r.fired and r.vals["n"] == 0


def test_score_input_bounds_and_min_obs():
    import pandas as pd
    s = pd.Series(np.r_[np.zeros(30), 1000.0], index=pd.date_range("2025-01-01", periods=31, freq="W"))
    z, sc = score_input(s, date(2025, 8, 10))
    assert -100 <= sc <= 100 and z == pytest.approx(3.0)  # clipped
    assert score_input(s.iloc[:10], date(2025, 3, 10)) is None  # < 24 obs


def test_index_bounds_and_coverage(conn):
    rng = np.random.default_rng(1)
    daily(conn, "vix", date(2024, 1, 1), list(15 + rng.normal(0, 2, 1000)))
    put(conn, "vix", "2026-10-16", 80.0)
    res = compute(conn, AS_OF)
    assert -100 <= res["subindices"]["global"]["value"] <= 100
    assert res["subindices"]["global"]["coverage_pct"] == pytest.approx(20.0)
    assert res["ppi"]["coverage_pct"] < 60 and res["ppi"]["sufficient"] is False
    for s in res["subindices"].values():
        assert s["value"] is None or -100 <= s["value"] <= 100


def test_event_points_capped(conn):
    for i in range(20):
        upsert_event(conn, event_date=AS_OF, event_type="regional_war_escalation", title_en=f"e{i}", title_ar="",
                     confidence="reported", source_name="x", source_url=f"https://x/{i}", entered_by="manual")
    res = compute(conn, AS_OF)
    assert res["subindices"]["geopolitical"]["event_points"] == 40
    assert res["subindices"]["geopolitical"]["value"] <= 100
