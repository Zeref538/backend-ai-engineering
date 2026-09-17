"""Run: python test_report.py

Works on a throwaway copy of the database in a temp folder, so it never touches
your real report.db or reports/.
"""
import os
import shutil
import sqlite3
import tempfile
from pathlib import Path

WORK = Path(tempfile.mkdtemp())
HERE = Path(__file__).resolve().parent
os.chdir(WORK)                      # every module uses paths relative to cwd

import sys  # noqa: E402
sys.path.insert(0, str(HERE))

import seed  # noqa: E402
seed.seed()

from fastapi.testclient import TestClient  # noqa: E402

import app as api  # noqa: E402
from render import build_html  # noqa: E402
from report_data import get_report_data  # noqa: E402

c = TestClient(api.app)


def test_seeding_twice_leaves_one_clean_copy():
    seed.seed()
    seed.seed()
    con = sqlite3.connect("report.db")
    assert con.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 200
    con.close()


def test_the_numbers_add_up():
    d = get_report_data()
    assert d["total_orders"] == 200
    assert len(d["top_products"]) == 5
    # No single product can out-earn the whole shop. If this ever fails, the
    # GROUP BY and the total are counting different sets of rows.
    assert all(p["revenue"] <= d["total_revenue"] for p in d["top_products"])
    assert len(d["orders_per_day"]) <= 7
    assert d["top_products"] == sorted(d["top_products"], key=lambda p: -p["revenue"])


def test_the_page_break_rules_are_actually_in_the_html():
    html = build_html(get_report_data())
    # These two lines are the whole fix for rows sliced across a page boundary.
    assert "break-inside: avoid" in html
    assert "display: table-header-group" in html
    assert html.count("<thead>") == 3


def test_generating_a_report_returns_201_and_a_link_not_bytes():
    # force, so this test doesn't depend on whether another test already made
    # today's report. Tests that share a database must not share assumptions.
    r = c.post("/reports", json={"force": True})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["file"] == f"/reports/{body['id']}/file"
    # The JSON must stay tiny -- the PDF goes over the file endpoint only.
    assert len(r.content) < 500, "the response body is carrying the PDF"


def test_asking_twice_in_a_day_makes_one_report():
    first = c.post("/reports")
    # Count *after* the first call: that one is allowed to create a file. The
    # claim under test is that the second one does not.
    before = sorted(Path("reports").glob("*.pdf"))
    second = c.post("/reports")
    assert second.status_code == 200, second.status_code
    assert second.json()["id"] == first.json()["id"]
    after = sorted(Path("reports").glob("*.pdf"))
    assert len(after) == len(before), (before, after)


def test_force_makes_a_new_one():
    first = c.post("/reports").json()["id"]
    forced = c.post("/reports", json={"force": True})
    assert forced.status_code == 201
    assert forced.json()["id"] != first


def test_the_file_endpoint_serves_a_real_pdf():
    rid = c.post("/reports").json()["id"]
    r = c.get(f"/reports/{rid}/file")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content[:5] == b"%PDF-", r.content[:20]
    assert len(r.content) > 10_000


def test_unknown_report_is_404():
    r = c.get("/reports/9999")
    assert r.status_code == 404 and "error" in r.json()
    assert c.get("/reports/9999/file").status_code == 404


if __name__ == "__main__":
    try:
        for name, fn in sorted(globals().items()):
            if name.startswith("test_"):
                fn()
                print("ok  ", name)
        print("all checks passed")
    finally:
        os.chdir(HERE)
        shutil.rmtree(WORK, ignore_errors=True)
