"""`pulse serve`: local web server for the app (http://localhost:8765).

- serves site/ (the app) and briefs/
- GET  /api/status  -> {"running": bool, "last_exit": int|None, "started": iso, "job": str}
- POST /api/run?job=daily -> starts `python -m pulse.cli run --job <job>` in the background (one at a time)
Binds to 127.0.0.1 only: nothing is exposed to the network.
"""
from __future__ import annotations

import subprocess
import sys
import threading
import webbrowser
from datetime import datetime

from .core import BRIEFS, LOGS, ROOT, SITE

ALLOWED_JOBS = {"daily", "global", "weekly", "gpr", "calendar", "all"}
_state = {"proc": None, "job": None, "started": None, "last_exit": None}
_lock = threading.Lock()


def _status() -> dict:
    p = _state["proc"]
    running = p is not None and p.poll() is None
    if p is not None and not running:
        _state["last_exit"] = p.returncode
        _state["proc"] = None
    return {"running": running, "job": _state["job"], "started": _state["started"], "last_exit": _state["last_exit"]}


def create_app():
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import JSONResponse, RedirectResponse
    from fastapi.staticfiles import StaticFiles

    app = FastAPI(title="Pulse", docs_url=None, redoc_url=None)

    @app.get("/api/status")
    def status():
        return JSONResponse(_status(), headers={"Cache-Control": "no-store"})

    @app.post("/api/run")
    def run(job: str = "daily"):
        if job not in ALLOWED_JOBS:
            raise HTTPException(400, "unknown job")
        with _lock:
            if _status()["running"]:
                return JSONResponse({"started": False, "reason": "already running"}, status_code=409)
            LOGS.mkdir(exist_ok=True)
            log = open(LOGS / "serve_runs.log", "a", encoding="utf-8")
            _state.update(proc=subprocess.Popen([sys.executable, "-m", "pulse.cli", "run", "--job", job], cwd=str(ROOT),
                                                stdout=log, stderr=subprocess.STDOUT),
                          job=job, started=datetime.now().isoformat(timespec="seconds"), last_exit=None)
        return {"started": True, "job": job}

    @app.get("/")
    def root():
        return RedirectResponse("/index.html")

    BRIEFS.mkdir(exist_ok=True)
    app.mount("/briefs", StaticFiles(directory=str(BRIEFS), html=True), name="briefs")
    app.mount("/", StaticFiles(directory=str(SITE), html=True), name="site")
    return app


def serve(port: int = 8765, open_browser: bool = False) -> None:
    import uvicorn

    url = f"http://localhost:{port}/"
    print(f"Pulse is running at {url}  (Ctrl+C to stop)")
    if open_browser:
        threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    try:
        # log_config=None: no console handlers, so it also runs under pythonw (scheduled task, no window)
        uvicorn.run(create_app(), host="127.0.0.1", port=port, log_level="warning", log_config=None)
    except Exception:  # noqa: BLE001
        import traceback
        LOGS.mkdir(exist_ok=True)
        with open(LOGS / "serve.log", "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()} server crashed\n{traceback.format_exc()}\n")
        raise
