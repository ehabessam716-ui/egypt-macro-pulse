"""IMF PortWatch 'Daily Chokepoints Data' (ArcGIS feature service, no key)."""
from __future__ import annotations

from datetime import datetime, timezone

from ..db import add_obs
from . import collector

SEARCH = "https://www.arcgis.com/sharing/rest/search"
PAGE = "https://portwatch.imf.org/datasets/imf-dataviz::daily-chokepoints-data"
POINTS = {"chokepoint1": "suez", "chokepoint4": "babelmandeb", "chokepoint6": "hormuz"}


def find_layer(ctx) -> str:
    j = ctx.http.get(SEARCH, params={"q": '"Daily Chokepoints Data" type:"Feature Service"', "f": "json",
                                     "num": 20}).json()
    items = [i for i in j.get("results", []) if i.get("url")]
    items.sort(key=lambda i: ("imf" not in (i.get("owner") or "").lower(), i.get("title") != "Daily_Chokepoints_Data"))
    if not items:
        raise RuntimeError("PortWatch feature service not found")
    url = items[0]["url"].rstrip("/")
    return url if url.split("/")[-1].isdigit() else url + "/0"


@collector("portwatch")
def collect(conn, ctx) -> int:
    layer = find_layer(ctx)
    rows = 0
    for pid, key in POINTS.items():
        last = conn.execute("SELECT MAX(obs_date) FROM observations WHERE series_id=?", (f"{key}_transits",)).fetchone()[0]
        start = "2022-01-01" if (ctx.backfill or not last) else last
        offset = 0
        while True:
            j = ctx.http.get(f"{layer}/query", params={
                "where": f"portid='{pid}' AND date >= DATE '{start}'", "outFields": "date,portid,portname,n_total,capacity",
                "orderByFields": "date ASC", "resultOffset": offset, "resultRecordCount": 2000,
                "returnGeometry": "false", "f": "json"}, gap=1.0).json()
            feats = [f["attributes"] for f in j.get("features", [])]
            if "error" in j:
                raise RuntimeError(f"PortWatch query error: {j['error']}")
            for a in feats:
                d = a["date"]
                od = datetime.fromtimestamp(d / 1000, tz=timezone.utc).date() if isinstance(d, (int, float)) else str(d)[:10]
                for suffix, field, unit in (("transits", "n_total", "vessels"), ("capacity", "capacity", "metric tons")):
                    if a.get(field) is None:
                        continue
                    rows += add_obs(conn, f"{key}_{suffix}", od, float(a[field]), unit=unit,
                                    source_name=f"IMF PortWatch — {a.get('portname')} ({pid})", source_url=PAGE,
                                    quality_flag="official") != "same"
            if len(feats) < 2000 and not j.get("exceededTransferLimit"):
                break
            offset += len(feats)
    return rows
