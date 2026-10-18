"""Outputs: dashboard, Arabic daily brief, weekly deep-dive."""
from __future__ import annotations

import math


def fmt(value, unit: str | None = None, digits: int | None = None) -> str:
    """Human formatting with the unit; never shows NaN."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "no data"
    u = unit or ""
    v = float(value)
    if digits is None:
        a = abs(v)
        digits = 0 if a >= 1000 else (2 if a < 100 or u in ("EGP per USD", "%", "pp") else 1)
        if u in ("ratio",):
            digits = 2
    s = f"{v:,.{digits}f}"
    if u in ("%",):
        return f"{s}%"
    if u == "pp":
        return f"{v:+.{digits}f} pp"
    if u in ("index", "code", "score", "tone", "", None):
        return s
    return f"{s} {u}"
