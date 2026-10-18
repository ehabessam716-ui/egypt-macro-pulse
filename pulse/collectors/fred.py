"""FRED keyless graph CSV (https://fred.stlouisfed.org/graph/fredgraph.csv?id=SERIES_ID)."""
from __future__ import annotations

import io
from datetime import timedelta

import pandas as pd

from ..core import today_cairo
from ..data import catalog
from ..db import add_obs, save_raw
from . import collector

URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
ORIGIN = {"DCOILBRENTEU": "EIA via FRED", "DCOILWTICO": "EIA via FRED", "DHHNGSP": "EIA via FRED",
          "PNGASEUUSDM": "IMF via FRED", "PWHEAMTUSDM": "IMF via FRED", "BAMLEMCBPIOAS": "ICE BofA via FRED",
          "VIXCLS": "CBOE via FRED", "CPIAUCSL": "BLS via FRED", "CPILFESL": "BLS via FRED",
          "PAYEMS": "BLS via FRED", "UNRATE": "BLS via FRED"}


def fred_map() -> dict[str, str]:
    return {m["endpoint"]: sid for sid, m in catalog().items() if m.get("source") == "fred_csv"}


@collector("fred")
def collect(conn, ctx) -> int:
    rows = 0
    errors = []
    for fred_id, sid in fred_map().items():
        backfill = ctx.backfill or not ctx.has_rows(conn, sid)
        start = "2016-01-01" if backfill else (today_cairo() - timedelta(days=400)).isoformat()
        try:
            r = ctx.http.get(URL, params={"id": fred_id, "cosd": start}, gap=1.0)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{fred_id}: {e}")
            continue
        save_raw(conn, f"fred_{fred_id}", r.url, r.content, "csv")
        df = pd.read_csv(io.StringIO(r.text))
        df.columns = ["date", "value"]
        df["value"] = pd.to_numeric(df["value"], errors="coerce")  # FRED uses '.' for no trading
        df = df.dropna()
        unit = catalog()[sid].get("unit")
        src = f"FRED {fred_id}" + (f" ({ORIGIN[fred_id]})" if fred_id in ORIGIN else "")
        for d, v in zip(df["date"], df["value"]):
            res = add_obs(conn, sid, d, float(v), unit=unit, source_name=src,
                          source_url=f"https://fred.stlouisfed.org/series/{fred_id}", quality_flag="official")
            rows += res in ("new", "revised", "conflict")
    if errors and rows == 0:
        raise RuntimeError("; ".join(errors)[:500])
    return rows
