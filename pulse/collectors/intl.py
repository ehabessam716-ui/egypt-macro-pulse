"""World Bank, IMF DataMapper (WEO) and Eurostat (euro-area HICP)."""
from __future__ import annotations

from datetime import date

from ..core import today_cairo
from ..data import catalog
from ..db import add_obs
from . import collector

WB = "https://api.worldbank.org/v2/country/EGY/indicator/NY.GDP.MKTP.KD.ZG"
IMF = "https://www.imf.org/external/datamapper/api/v1/{ind}/EGY"
ESTAT = ("https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/prc_hicp_minr"
         "?geo=EA&coicop18=TOTAL&unit=RCH_A&lastTimePeriod=36")


@collector("intl")
def collect(conn, ctx) -> int:
    rows, errors = 0, []
    # World Bank
    try:
        j = ctx.http.get(WB, params={"format": "json", "per_page": 70}).json()
        for d in j[1] or []:
            if d.get("value") is None:
                continue
            rows += add_obs(conn, "wb_gdp_growth", date(int(d["date"]), 1, 1), float(d["value"]), unit="%",
                            source_name="World Bank WDI (NY.GDP.MKTP.KD.ZG)",
                            source_url="https://data.worldbank.org/indicator/NY.GDP.MKTP.KD.ZG?locations=EG",
                            quality_flag="official") != "same"
    except Exception as e:  # noqa: BLE001
        errors.append(f"worldbank: {e}")
    # IMF DataMapper (WEO)
    this_year = today_cairo().year
    for sid, m in catalog().items():
        if m.get("source") != "imf_datamapper":
            continue
        try:
            j = ctx.http.get(IMF.format(ind=m["endpoint"]), gap=1.5).json()
            vals = j["values"][m["endpoint"]]["EGY"]
        except Exception as e:  # noqa: BLE001
            errors.append(f"imf {m['endpoint']}: {e}")
            continue
        for yr, v in vals.items():
            if v is None or int(yr) < 2010:
                continue
            note = "IMF WEO projection" if int(yr) >= this_year else "IMF WEO (actual or staff estimate)"
            rows += add_obs(conn, sid, date(int(yr), 1, 1), float(v), unit=m.get("unit"),
                            source_name=f"IMF DataMapper — WEO {m['endpoint']}",
                            source_url=f"https://www.imf.org/external/datamapper/{m['endpoint']}@WEO/EGY",
                            quality_flag="official", obs_note=note) != "same"
    # Eurostat HICP (COICOP 2018 dataset)
    try:
        j = ctx.http.get(ESTAT).json()
        idx = j["dimension"]["time"]["category"]["index"]
        for per, pos in idx.items():
            v = j["value"].get(str(pos))
            if v is None:
                continue
            y, mth = map(int, per.split("-"))
            rows += add_obs(conn, "euro_area_hicp", date(y, mth, 1), float(v), unit="%",
                            source_name="Eurostat prc_hicp_minr (HICP, annual rate, euro area)",
                            source_url=ESTAT, quality_flag="official") != "same"
    except Exception as e:  # noqa: BLE001
        errors.append(f"eurostat: {e}")
    if errors and rows == 0:
        raise RuntimeError("; ".join(errors)[:500])
    return rows
