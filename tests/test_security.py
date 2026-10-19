"""Security checks: local API guard, safe links, content-security policy."""
from pathlib import Path

WEB = Path(__file__).resolve().parents[1] / "pulse" / "web"


def test_local_api_blocks_cross_site_and_rebinding():
    import pytest
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient
    from pulse.server import create_app
    c = TestClient(create_app(), base_url="http://127.0.0.1:8765")
    assert c.post("/api/run?job=nope").status_code == 403                     # no X-Pulse header → refused
    assert c.post("/api/run?job=nope", headers={"X-Pulse": "1"}).status_code == 400  # header ok, bad job rejected
    evil = TestClient(create_app(), base_url="http://evil.example")
    assert evil.get("/api/status").status_code == 403                          # DNS-rebinding host refused


def test_page_has_csp_and_no_inline_script():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    assert "Content-Security-Policy" in html and "script-src 'self'" in html and "object-src 'none'" in html
    import re
    assert not re.search(r"<script>(?!\s*</script>)", html), "inline scripts would be blocked by the CSP"


def test_external_links_are_sanitised():
    js = (WEB / "app.js").read_text(encoding="utf-8")
    assert 'href="${esc(' not in js, "external hrefs must go through safeUrl()"
    assert "const safeUrl" in js
