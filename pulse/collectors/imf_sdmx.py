"""IMF SDMX API (keyless): long monthly history for Egypt's CPI (headline + categories) and the USD/EGP average rate.

Used by the impact model (pulse/impact.py) to estimate how a weaker pound feeds into prices, and to test those
estimates on past episodes (2016 float, 2022–24 devaluations). Values are stored as published by the IMF.
"""
from __future__ import annotations

from datetime import date

from ..core import get_logger
from ..db import add_obs
from . import collector

log = get_logger("pulse.imf")

BASE = "https://api.imf.org/external/sdmx/2.1/data/IMF.STA,{flow}/{key}?startPeriod=2005"
PAGE = "https://data.imf.org/en/datasets/IMF.STA:{flow}"
SERIES = [  # (series_id, dataflow, key, unit)
    ("cpi_imf_all", "CPI", "EGY.CPI._T.IX.M", "index"),
    ("cpi_imf_food", "CPI", "EGY.CPI.CP01.IX.M", "index"),
    ("cpi_imf_housing", "CPI", "EGY.CPI.CP04.IX.M", "index"),
    ("cpi_imf_health", "CPI", "EGY.CPI.CP06.IX.M", "index"),
    ("cpi_imf_transport", "CPI", "EGY.CPI.CP07.IX.M", "index"),
    ("fx_imf_avg", "ER", "EGY.XDC_USD.PA_RT.M", "EGP per USD"),
]


def parse_sdmx_json(j: dict) -> dict[str, float]:
    """SDMX-JSON (2.1 or 3.0 layout) → {'2026-M08': value} for the first series."""
    root = j.get("data", j)
    ds = root["dataSets"][0]
    st = root.get("structure") or root.get("structures", [None])[0] or j.get("structure")
    times = st["dimensions"]["observation"][0]["values"]
    out: dict[str, float] = {}
    for s in ds.get("series", {}).values():
        for i, v in s["observations"].items():
            if v and v[0] not in (None, "", "NaN"):
                out[times[int(i)]["id"]] = float(v[0])
        break
    return out


def _period(p: str) -> date:
    y, m = p.split("-M")
    return date(int(y), int(m), 1)


@collector("imf_sdmx")
def collect(conn, ctx) -> int:
    rows = 0
    for sid, flow, key, unit in SERIES:
        url = BASE.format(flow=flow, key=key)
        try:
            r = ctx.http.get(url, headers={"Accept": "application/json"})
            obs = parse_sdmx_json(r.json())
        except Exception as e:  # noqa: BLE001 — one series failing never stops the rest
            log.warning("IMF %s failed: %s", sid, e)
            continue
        for p, val in obs.items():
            rows += add_obs(conn, sid, _period(p), val, unit=unit, source_name=f"IMF {flow} database (SDMX API)",
                            source_url=url, quality_flag="official") != "same"
    return rows
