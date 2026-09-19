"""The API: ask for a report, wait a moment, download it by link.

The rule this file exists to demonstrate: a PDF is an artifact. It lives on
disk and everything else carries only its address. JSON responses never carry
the bytes -- only GET /reports/{id}/file moves megabytes.
"""
import sqlite3
from contextlib import closing
from datetime import date
from pathlib import Path

from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from render import render_pdf
from report_data import get_report_data

DB = "report.db"
REPORTS = Path("reports")

app = FastAPI(title="PDF report generator", version="1.0")


@app.exception_handler(HTTPException)
def json_error(request, exc):
    return JSONResponse({"error": exc.detail}, status_code=exc.status_code)


def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


with closing(db()) as con, con:
    con.execute(
        "CREATE TABLE IF NOT EXISTS reports ("
        "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "  path TEXT NOT NULL,"
        "  created_at DATE NOT NULL)"
    )


def row_to_json(row):
    return {"id": row["id"], "created_at": row["created_at"],
            "file": f"/reports/{row['id']}/file"}


@app.post("/reports")
def create_report(body: dict = Body(default={})):
    """Query, render, save, record -- all inside the request, so you feel the wait."""
    today = date.today().isoformat()

    if not body.get("force"):
        # Ask twice on the same day, get one report back. Without this, a
        # double-clicked button is two PDFs, and if the next step emails them,
        # it's two emails to a customer.
        with closing(db()) as con:
            existing = con.execute(
                "SELECT * FROM reports WHERE created_at = ? ORDER BY id LIMIT 1", (today,)
            ).fetchone()
        if existing:
            return JSONResponse(row_to_json(existing), status_code=200)

    with closing(db()) as con, con:
        cur = con.execute("INSERT INTO reports (path, created_at) VALUES ('', ?)", (today,))
        report_id = cur.lastrowid
        path = REPORTS / f"{report_id}.pdf"
        render_pdf(get_report_data(), path)
        con.execute("UPDATE reports SET path = ? WHERE id = ?", (str(path), report_id))
        row = con.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()

    return JSONResponse(row_to_json(row), status_code=201)


def find(report_id: int):
    with closing(db()) as con:
        row = con.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
    if row is None:
        raise HTTPException(404, f"Report {report_id} not found")
    return row


@app.get("/reports")
def list_reports():
    with closing(db()) as con:
        return [row_to_json(r) for r in con.execute("SELECT * FROM reports ORDER BY id DESC")]


@app.get("/reports/{report_id}")
def get_report(report_id: int):
    return row_to_json(find(report_id))


@app.get("/reports/{report_id}/file")
def get_report_file(report_id: int):
    row = find(report_id)
    path = Path(row["path"])
    if not path.exists():
        # The row says there is a file and there isn't. Say so plainly rather
        # than serving an empty download.
        raise HTTPException(404, f"Report {report_id} has no file on disk")
    return FileResponse(path, media_type="application/pdf",
                        filename=f"sales-report-{row['created_at']}.pdf")


@app.get("/health")
def health():
    return {"status": "ok"}
