"""Caldara–Iacoviello Geopolitical Risk index (CC BY). Monthly file ~1st of month, daily file Mondays."""
from __future__ import annotations

import io

import pandas as pd

from ..data import catalog
from ..db import add_obs, save_raw
from . import collector

FILES = {"gpr_monthly": "https://www.matteoiacoviello.com/gpr_files/data_gpr_export.xls",
         "gpr_daily": "https://www.matteoiacoviello.com/gpr_files/data_gpr_daily_recent.xls"}
PAGE = "https://www.matteoiacoviello.com/gpr.htm"
CREDIT = "Caldara & Iacoviello GPR (CC BY)"


def _dates(col: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(col) and col.dropna().astype("int64").between(19000101, 21001231).all():
        return pd.to_datetime(col.astype("Int64").astype(str), format="%Y%m%d", errors="coerce")
    return pd.to_datetime(col, errors="coerce")


@collector("gpr")
def collect(conn, ctx) -> int:
    rows = 0
    for src, url in FILES.items():
        r = ctx.http.get(url)
        save_raw(conn, src, url, r.content, "xls")
        df = pd.read_excel(io.BytesIO(r.content))
        date_col = next(c for c in df.columns if str(c).lower() in ("month", "date", "day"))
        df["_d"] = _dates(df[date_col])
        start = pd.Timestamp("1985-01-01" if src == "gpr_monthly" else "2016-01-01")
        df = df[df["_d"] >= start]
        for sid, meta in catalog().items():
            if meta.get("source") != src or meta["endpoint"] not in df.columns:
                continue
            sub = df[["_d", meta["endpoint"]]].dropna()
            for d, v in zip(sub["_d"], sub[meta["endpoint"]]):
                rows += add_obs(conn, sid, d.date(), float(v), unit="index", source_name=f"{CREDIT} — {meta['endpoint']}",
                                source_url=PAGE, quality_flag="official") != "same"
    return rows
