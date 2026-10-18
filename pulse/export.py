"""Power BI export (SPEC §8.4): star schema as CSV (UTF-8 BOM) + Parquet in exports/."""
from __future__ import annotations

import pandas as pd

from .core import EXPORTS, is_business_day, load_yaml
from .data import catalog

TABLES = ["fact_observations", "fact_index_values", "fact_rule_hits", "fact_events", "dim_series", "dim_date", "dim_source"]


def export_powerbi(conn) -> dict:
    EXPORTS.mkdir(parents=True, exist_ok=True)
    obs = pd.read_sql_query("""SELECT series_id, obs_date, value, unit, release_date, retrieved_at, source_name, source_url,
                               vintage, quality_flag, null_reason, obs_time, obs_note, conflict FROM observations""", conn)
    obs["is_latest_vintage"] = obs.groupby(["series_id", "obs_date", "source_name"])["vintage"].transform("max") == obs["vintage"]
    obs["source_id"] = obs["series_id"].map(lambda s: catalog().get(s, {}).get("source"))
    idx = pd.read_sql_query("SELECT run_date, index_id, value, coverage_pct, kind, components_json FROM index_values", conn)
    rules = pd.read_sql_query("SELECT * FROM rule_hits", conn)
    events = pd.read_sql_query("SELECT * FROM events", conn)
    dim_series = pd.DataFrame([{k: m.get(k) for k in ("id", "name_en", "name_ar", "domain", "frequency", "unit", "source",
                                                       "endpoint", "fallback", "access", "definition_note",
                                                       "release_lag_days", "stale_after_days", "calendar", "step")}
                               for m in catalog().values()]).rename(columns={"id": "series_id"})
    src = [{"source_id": s["id"], "name": s["name"], "url": s.get("url"), "kind": s["kind"], "access": s["access"],
            "manual_reason": s.get("manual_reason")} for s in load_yaml("sources.yaml")["sources"]]
    src.append({"source_id": "derived", "name": "Egypt Macro Pulse (derived)", "url": "pulse/derive.py", "kind": "derived",
                "access": "DERIVED", "manual_reason": None})
    src.append({"source_id": "manual", "name": "Manual inputs workbook", "url": "data/manual/manual_inputs.xlsx",
                "kind": "manual", "access": "MANUAL", "manual_reason": None})
    dim_source = pd.DataFrame(src)
    dates = pd.to_datetime(pd.concat([obs["obs_date"], idx["run_date"], events["event_date"]]), errors="coerce").dropna()
    rng = pd.date_range(max(dates.min(), pd.Timestamp("2000-01-01")), max(dates.max(), pd.Timestamp.today()), freq="D")
    dim_date = pd.DataFrame({"date": rng.date})
    dim_date["year"] = rng.year
    dim_date["quarter"] = rng.quarter
    dim_date["month"] = rng.month
    dim_date["weekday"] = rng.day_name()
    dim_date["egypt_fy"] = [f"FY{y}/{str(y + 1)[-2:]}" if m >= 7 else f"FY{y - 1}/{str(y)[-2:]}" for y, m in zip(rng.year, rng.month)]
    dim_date["cairo_business_day"] = [is_business_day(d, "egypt") for d in rng.date]
    dim_date["global_business_day"] = [is_business_day(d, "global") for d in rng.date]
    frames = {"fact_observations": obs, "fact_index_values": idx, "fact_rule_hits": rules, "fact_events": events,
              "dim_series": dim_series, "dim_date": dim_date, "dim_source": dim_source}
    for name, df in frames.items():
        df = df.copy()
        for c in df.columns:
            if c.endswith("date") or c in ("date",):
                df[c] = pd.to_datetime(df[c], errors="coerce").dt.strftime("%Y-%m-%d")
        df.to_csv(EXPORTS / f"{name}.csv", index=False, encoding="utf-8-sig")
        df.to_parquet(EXPORTS / f"{name}.parquet", index=False)
    return {k: len(v) for k, v in frames.items()}
