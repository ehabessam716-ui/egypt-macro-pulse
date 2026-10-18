from datetime import date

import pytest

from pulse import db as dbm
from pulse.core import business_days_between, is_business_day, period_end
from pulse.data import DataView, staleness
from tests.conftest import put


def test_null_needs_reason_and_source(conn):
    with pytest.raises(ValueError):
        dbm.add_obs(conn, "nir", "2026-09-01", None, unit="USD mn", source_name="x", source_url="https://x", quality_flag="official")
    with pytest.raises(ValueError):
        dbm.add_obs(conn, "nir", "2026-09-01", 1.0, unit="USD mn", source_name="x", source_url="", quality_flag="official")
    with pytest.raises(ValueError):
        dbm.add_obs(conn, "nir", "2026-09-01", 1.0, unit="USD mn", source_name="x", source_url="https://x", quality_flag="guess")
    assert dbm.add_obs(conn, "nir", "2026-09-01", None, unit="USD mn", source_name="x", source_url="https://x",
                       quality_flag="official", null_reason="not published") == "new"


def test_revision_creates_vintage_and_conflict_flag(conn):
    assert put(conn, "cpi_urban_yoy", "2026-09-01", 13.9) == "new"
    assert put(conn, "cpi_urban_yoy", "2026-09-01", 13.9) == "same"
    assert put(conn, "cpi_urban_yoy", "2026-09-01", 14.0) == "revised"
    assert put(conn, "cpi_urban_yoy", "2026-09-01", 15.0, source="Other outlet", quality="secondary") == "conflict"
    n = conn.execute("SELECT COUNT(*) FROM observations WHERE series_id='cpi_urban_yoy'").fetchone()[0]
    assert n == 3
    v = DataView(conn, date(2026, 10, 18))
    o = v.latest("cpi_urban_yoy")
    assert o.value == 14.0 and o.quality == "official"  # official beats secondary, latest vintage wins


def test_fri_sat_handling_and_business_days():
    fri, sat, sun = date(2026, 10, 16), date(2026, 10, 17), date(2026, 10, 18)
    assert not is_business_day(fri, "egypt") and not is_business_day(sat, "egypt") and is_business_day(sun, "egypt")
    assert is_business_day(fri, "global") and not is_business_day(sun, "global")
    assert business_days_between(date(2026, 10, 15), sun, "egypt") == 1  # Thu → Sun skips Fri/Sat


def test_stale_rules_daily_and_monthly(conn):
    # Thursday official FX is NOT stale on Sunday (1 business day)
    assert staleness("fx_cbe_official", date(2026, 10, 15), date(2026, 10, 18))[0] == 0
    assert staleness("fx_cbe_official", date(2026, 10, 1), date(2026, 10, 18))[0] == 2
    # monthly CPI for September measured from period end
    assert staleness("cpi_urban_yoy", date(2026, 9, 1), date(2026, 10, 18))[0] == 0
    assert staleness("cpi_urban_yoy", date(2026, 8, 1), date(2026, 10, 18))[0] == 1
    assert staleness("cpi_urban_yoy", date(2026, 6, 1), date(2026, 10, 18))[0] == 2


def test_period_end_conventions():
    assert period_end(date(2026, 2, 1), "monthly") == date(2026, 2, 28)
    assert period_end(date(2026, 4, 1), "quarterly") == date(2026, 6, 30)
    assert period_end(date(2025, 7, 1), "fiscal_year") == date(2026, 6, 30)


def test_point_in_time_view_hides_future_releases(conn):
    put(conn, "cpi_urban_yoy", "2026-09-01", 13.9, release_date="2026-10-10")
    assert DataView(conn, date(2026, 10, 5), point_in_time=True).latest("cpi_urban_yoy") is None
    assert DataView(conn, date(2026, 10, 11), point_in_time=True).latest("cpi_urban_yoy").value == 13.9


def test_fallback_resolution(conn):
    put(conn, "brent", "2026-08-01", 100.0)
    put(conn, "brent_fut", "2026-10-16", 109.86, quality="unofficial")
    o = DataView(conn, date(2026, 10, 18)).resolved("brent")
    assert o.series_id == "brent_fut" and o.via_fallback == "brent"
