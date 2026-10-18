"""Local Egyptian gold prices (banklive primary; iSagha 24K fallback). quality_flag='secondary'."""
from __future__ import annotations

import re
from datetime import datetime

from ..core import now_cairo
from ..db import add_obs, save_raw
from . import collector
from .cbe import page_text

BANKLIVE = "https://banklive.net/en/gold-price-today-in-egypt"
ISAGHA = "https://market.isagha.com/prices"


def parse_banklive(text: str) -> dict:
    out: dict = {}
    m = re.search(r"Last Updated \|\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", text)
    if m:
        out["ts"] = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
    m = re.search(r"XAU/USD \$([\d,]+\.\d+)", text)
    if m:
        out["xauusd_spot"] = float(m.group(1).replace(",", ""))
    for sid, label in (("gold_eg_24k", "Gold 24 Karat"), ("gold_eg_21k", "Gold 21 Karat"), ("gold_eg_pound", "Gold Pound")):
        m = re.search(label + r" ([\d,]+(?:\.\d+)?) ", text)
        if m:
            out[sid] = float(m.group(1).replace(",", ""))
    return out


def parse_isagha(text: str) -> dict:
    out = {}
    m = re.search(r"ذهب عيار 24\s+([\d,]+(?:\.\d+)?)\s*ج\.م", text)
    if m:
        out["gold_eg_24k"] = float(m.group(1).replace(",", ""))
    return out


@collector("gold_eg")
def collect(conn, ctx) -> int:
    rows = 0
    try:
        r = ctx.http.get(BANKLIVE)
        save_raw(conn, "gold_banklive", BANKLIVE, r.content, "html")
        p = parse_banklive(page_text(r.text))
        if "gold_eg_21k" not in p or "ts" not in p:
            raise RuntimeError("banklive layout changed (21K or timestamp not found)")
        ts = p.pop("ts")
        for sid, v in p.items():
            unit = "USD/oz" if sid == "xauusd_spot" else ("EGP" if sid == "gold_eg_pound" else "EGP/gram")
            rows += add_obs(conn, sid, ts.date(), v, unit=unit, source_name="banklive.net (Egypt gold, secondary)",
                            source_url=BANKLIVE, quality_flag="secondary", obs_time=ts.isoformat(),
                            obs_note="'Buying Price' column; site timestamp (Cairo)") != "same"
        return rows
    except Exception as e:  # noqa: BLE001
        err = e
    r = ctx.http.get(ISAGHA)
    save_raw(conn, "gold_isagha", ISAGHA, r.content, "html")
    p = parse_isagha(page_text(r.text))
    if not p:
        raise RuntimeError(f"banklive failed ({err}); iSagha 24K not found either")
    ts = now_cairo().replace(microsecond=0, tzinfo=None)
    for sid, v in p.items():
        rows += add_obs(conn, sid, ts.date(), v, unit="EGP/gram", source_name="iSagha (Egypt gold, secondary)",
                        source_url=ISAGHA, quality_flag="secondary", obs_time=ts.isoformat(),
                        obs_note="fallback source; time = retrieval time") != "same"
    return rows
