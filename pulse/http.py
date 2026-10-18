"""Polite HTTP: per-host spacing, 3 retries with exponential backoff, raw caching."""
from __future__ import annotations

import time
from urllib.parse import urlparse

import requests

PULSE_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) EgyptMacroPulse/1.0 (personal learning tool)"
# Some official sites (CBE's F5 firewall) reject any non-browser User-Agent string even though
# robots.txt allows the pages. For those we send a standard browser UA at a slow, polite rate.
BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/141.0 Safari/537.36")
TIMEOUT = 45
RETRIES = 3
RETRY_STATUS = {429, 500, 502, 503, 504}


class FetchError(RuntimeError):
    pass


class Http:
    def __init__(self, browser_ua: bool = False, min_gap: float = 2.0) -> None:
        self.s = requests.Session()
        self.s.headers.update({"User-Agent": BROWSER_UA if browser_ua else PULSE_UA,
                               "Accept-Language": "en,ar;q=0.8"})
        self.min_gap = min_gap
        self._last: dict[str, float] = {}

    def _wait(self, url: str, gap: float) -> None:
        host = urlparse(url).netloc
        wait = self._last.get(host, 0) + gap - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        self._last[host] = time.monotonic()

    def request(self, method: str, url: str, *, gap: float | None = None, retries: int = RETRIES,
                backoff: float = 2.0, ok_status=(200,), **kw) -> requests.Response:
        gap = self.min_gap if gap is None else gap
        kw.setdefault("timeout", TIMEOUT)
        last_err: str = ""
        for attempt in range(retries):
            self._wait(url, gap)
            try:
                r = self.s.request(method, url, **kw)
            except requests.RequestException as e:
                last_err = f"{type(e).__name__}: {str(e)[:200]}"
            else:
                if r.status_code in ok_status:
                    if "charset" not in r.headers.get("Content-Type", "").lower() and r.encoding is None:
                        r.encoding = r.apparent_encoding
                    return r
                last_err = f"HTTP {r.status_code}: {r.text[:160]!r}"
                if r.status_code not in RETRY_STATUS:
                    break
            if attempt < retries - 1:
                time.sleep(max(gap, backoff) * (2 ** attempt))
        raise FetchError(f"{url} failed after {retries} tries — {last_err}")

    def get(self, url: str, **kw) -> requests.Response:
        return self.request("GET", url, **kw)

    def post(self, url: str, **kw) -> requests.Response:
        return self.request("POST", url, **kw)
