"""Impact outlook: built only from data, leave-one-out accuracy, honest odds."""
from datetime import date

import numpy as np

from pulse.data import DataView
from tests.conftest import put


def _months(n, start=(2008, 7)):
    y, m = start
    for _ in range(n):
        yield date(y, m, 1)
        m += 1
        if m == 13:
            y, m = y + 1, 1


def test_impact_outlook_from_synthetic_history(conn):
    rng = np.random.default_rng(1)
    fx, p = 5.0, 100.0
    for i, d in enumerate(_months(220)):
        jump = 6.0 if i % 24 == 0 and i else 0.0           # a 6% dollar jump every two years
        fx *= 1 + (jump + rng.normal(0, 0.3)) / 100
        p *= 1 + (0.8 + 0.05 * jump + rng.normal(0, 0.2)) / 100   # steady inflation + a little pass-through
        put(conn, "fx_imf_avg", d, fx)
        if d >= date(2010, 1, 1):
            put(conn, "cpi_imf_all", d, p)
            put(conn, "cpi_imf_food", d, p * 1.01)
    from pulse.impact import build_impact
    I = build_impact(DataView(conn, as_of=date(2026, 12, 31)), 3.0, 6.0)
    assert I is not None
    allc = next(c for c in I["cats"] if c["id"] == "all")
    assert 3 < allc["pace"] < 7                       # ~0.8%/month → ~4.9% per 6 months
    t = allc["test"]["moderate"]
    assert t and t["n"] >= 5 and t["hits"] <= t["n"] and t["mae"] >= 0
    assert I["odds"]["keeps_rising"]["n"] >= 5
