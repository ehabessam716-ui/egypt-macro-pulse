import sqlite3
from datetime import date, timedelta

import pytest

from pulse import db as dbm
from pulse.data import sync_catalog
from pulse.events import sync_types


@pytest.fixture()
def conn(tmp_path):
    c = dbm.connect(tmp_path / "test.db")
    sync_catalog(c)
    sync_types(c)
    yield c
    c.close()


def put(conn, sid, d, value, quality="official", url="https://example.org/src", source="Test source", **kw):
    return dbm.add_obs(conn, sid, d, value, unit=kw.pop("unit", ""), source_name=source, source_url=url,
                       quality_flag=quality, **kw)


def daily(conn, sid, start: date, values, step_days=1, **kw):
    d = start
    for v in values:
        put(conn, sid, d, v, **kw)
        d += timedelta(days=step_days)
