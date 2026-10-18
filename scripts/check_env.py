"""Environment health check — run any time to confirm the toolchain still works.

  .venv\\Scripts\\python.exe scripts\\check_env.py

Each check prints PASS / FAIL with a short detail. Exit code = number of failures.
"""
from __future__ import annotations

import importlib
import io
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "env_check"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) EgyptMacroPulse/0.1 (personal learning tool)"
results: list[tuple[str, bool, str]] = []


def check(name: str):
    def wrap(fn):
        t0 = time.perf_counter()
        try:
            detail = fn() or ""
            ok = True
        except Exception as e:  # noqa: BLE001
            detail, ok = f"{type(e).__name__}: {str(e)[:160]}", False
        results.append((name, ok, f"{detail} ({time.perf_counter() - t0:.1f}s)"))
        print(f"{'PASS' if ok else 'FAIL'}  {name:<34} {results[-1][2]}", flush=True)
        return fn
    return wrap


@check("Python version >= 3.11")
def _():
    assert sys.version_info >= (3, 11), sys.version
    return sys.version.split()[0]


@check("Python packages import")
def _():
    pkgs = ["requests", "httpx", "bs4", "lxml", "feedparser", "pandas", "pyarrow", "pydantic", "yaml",
            "sqlalchemy", "pdfplumber", "openpyxl", "xlrd", "yfinance", "gdeltdoc", "plotly", "jinja2",
            "pytest", "dateutil", "dotenv", "fastapi", "uvicorn", "playwright", "apscheduler"]
    missing = []
    for p in pkgs:
        try:
            importlib.import_module(p)
        except ImportError:
            missing.append(p)
    assert not missing, f"missing: {missing}"
    return f"{len(pkgs)} packages OK"


@check("Command-line tools on PATH")
def _():
    found, missing = [], []
    for tool, args in [("git", ["--version"]), ("node", ["--version"]), ("npm", ["--version"]),
                       ("code", ["--version"]), ("claude", ["--version"])]:
        exe = shutil.which(tool)
        if not exe:
            missing.append(tool)
            continue
        v = subprocess.run([exe, *args], capture_output=True, text=True, timeout=30).stdout.strip().splitlines()[0]
        found.append(f"{tool} {v}")
    assert not missing, f"not on PATH: {missing} (open a NEW terminal after installs)"
    return "; ".join(found)


@check("Timezone Africa/Cairo")
def _():
    from datetime import datetime
    from zoneinfo import ZoneInfo
    return datetime.now(ZoneInfo("Africa/Cairo")).strftime("%Y-%m-%d %H:%M %Z")


@check("Static scrape (requests + bs4)")
def _():
    import requests
    from bs4 import BeautifulSoup
    r = requests.get("https://banklive.net/en/gold-price-today-in-egypt", headers={"User-Agent": UA}, timeout=30)
    r.raise_for_status()
    title = BeautifulSoup(r.text, "lxml").title.get_text(strip=True)
    return f"HTTP {r.status_code}, title='{title[:50]}'"


@check("RSS feed (feedparser)")
def _():
    import feedparser
    f = feedparser.parse("https://www.dailynewsegypt.com/feed/", agent=UA)
    assert f.entries, "no entries"
    return f"{len(f.entries)} items, latest: {f.entries[0].title[:50]}"


@check("Data API (FRED keyless CSV)")
def _():
    import pandas as pd
    import requests
    r = requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILBRENTEU", headers={"User-Agent": UA}, timeout=30)
    df = pd.read_csv(io.StringIO(r.text))
    df.iloc[:, 1] = pd.to_numeric(df.iloc[:, 1], errors="coerce")
    last = df.dropna().iloc[-1]
    return f"Brent {last.iloc[1]} on {last.iloc[0]}"


@check("Headless browser (Playwright)")
def _():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page(user_agent=UA)
        page.goto("https://www.capmas.gov.eg/", wait_until="networkidle", timeout=60000)
        text = page.inner_text("body")
        b.close()
    assert len(text) > 200, f"only {len(text)} chars rendered"
    return f"CAPMAS JS app rendered {len(text)} chars of text"


@check("CBE official FX (off-screen browser)")
def _():
    # CBE's firewall rejects headless Chromium (even new-headless); a headed window placed off-screen passes.
    import re
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(headless=False, args=["--window-position=-32000,-32000"])
        page = b.new_page()
        page.goto("https://www.cbe.org.eg/en/economic-research/statistics/exchange-rates",
                  wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(8000)
        text = page.inner_text("body")
        b.close()
    assert "requested URL was rejected" not in text, "CBE firewall rejected the browser"
    m = re.search(r"US Dollar\s+([\d.]+)\s+([\d.]+)", text)
    assert m, f"USD row not found in {len(text)} chars"
    return f"USD/EGP buy {m[1]} / sell {m[2]}"


@check("Charts (plotly -> HTML)")
def _():
    import plotly.graph_objects as go
    OUT.mkdir(parents=True, exist_ok=True)
    fig = go.Figure(go.Scatter(x=[1, 2, 3], y=[53.1, 53.4, 53.45], name="USD/EGP"))
    fig.update_layout(title="اختبار — USD/EGP test chart")
    path = OUT / "test_chart.html"
    fig.write_html(path, include_plotlyjs="cdn")
    return str(path.relative_to(ROOT))


@check("Storage (SQLite + Parquet, Arabic)")
def _():
    import pandas as pd
    df = pd.DataFrame({"series": ["fx", "cpi"], "name_ar": ["سعر الصرف", "التضخم"], "value": [53.45, 13.9]})
    with tempfile.TemporaryDirectory() as d:
        con = sqlite3.connect(Path(d) / "t.db")
        df.to_sql("obs", con, index=False)
        back = pd.read_sql("select * from obs", con)
        con.close()
        df.to_parquet(Path(d) / "t.parquet")
        pq = pd.read_parquet(Path(d) / "t.parquet")
    assert back.equals(df) and pq.equals(df)
    return f"sqlite {sqlite3.sqlite_version}, round-trip OK"


@check("Excel + PDF readers")
def _():
    import pandas as pd
    import pdfplumber  # noqa: F401
    buf = io.BytesIO()
    pd.DataFrame({"a": [1]}).to_excel(buf, index=False)
    buf.seek(0)
    assert pd.read_excel(buf).iloc[0, 0] == 1
    return "openpyxl write/read OK, pdfplumber importable"


@check("Web server (FastAPI)")
def _():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    app = FastAPI()

    @app.get("/health")
    def health():
        return {"status": "ok", "ar": "تمام"}

    r = TestClient(app).get("/health")
    assert r.status_code == 200 and r.json()["ar"] == "تمام"
    return "GET /health -> 200"


@check("Scheduler (APScheduler)")
def _():
    from apscheduler.schedulers.background import BackgroundScheduler
    hits = []
    s = BackgroundScheduler(timezone="Africa/Cairo")
    s.add_job(lambda: hits.append(1), "interval", seconds=1)
    s.start()
    time.sleep(2.2)
    s.shutdown()
    assert hits
    return f"{len(hits)} job runs"


if __name__ == "__main__":
    fails = [n for n, ok, _ in results if not ok]
    print(f"\n{len(results) - len(fails)}/{len(results)} checks passed" + (f" — failed: {', '.join(fails)}" if fails else ""))
    sys.exit(len(fails))
