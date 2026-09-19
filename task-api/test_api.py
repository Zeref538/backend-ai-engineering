"""One runnable check: python test_api.py

Uses FastAPI's TestClient, which calls the app directly in this process -- no
server to start, no port to pick. Runs against a throwaway database file so it
can never touch the real tasks.db.
"""
import os
import subprocess
import sys
import tempfile

DB = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ["TASKS_DB"] = DB  # must be set before main imports db and calls init()

from fastapi.testclient import TestClient  # noqa: E402

import db  # noqa: E402
from main import app  # noqa: E402

c = TestClient(app)


def test_crud():
    assert c.get("/health").json() == {"status": "ok"}
    assert len(c.get("/tasks").json()) == 3

    made = c.post("/tasks", json={"title": "Buy milk"})
    assert made.status_code == 201, made.status_code
    tid = made.json()["id"]
    assert made.json()["done"] is False

    assert c.get(f"/tasks/{tid}").json()["title"] == "Buy milk"
    got = c.put(f"/tasks/{tid}", json={"done": True}).json()
    assert got["done"] is True and got["title"] == "Buy milk", got
    assert c.put(f"/tasks/{tid}", json={"title": "Buy oat milk"}).json()["done"] is True

    assert c.delete(f"/tasks/{tid}").status_code == 204
    assert c.get(f"/tasks/{tid}").status_code == 404


def test_errors():
    # Every unhappy path answers with {"error": ...}, never {"detail": ...}.
    for call, code in [
        (lambda: c.get("/tasks/99"), 404),
        (lambda: c.put("/tasks/99", json={"done": True}), 404),
        (lambda: c.delete("/tasks/99"), 404),
        (lambda: c.post("/tasks", json={}), 400),
        (lambda: c.post("/tasks", json={"title": "   "}), 400),
        (lambda: c.post("/tasks", json={"title": 42}), 400),
        (lambda: c.put("/tasks/1", json={}), 400),
        (lambda: c.put("/tasks/1", json={"done": "yes"}), 400),
        (lambda: c.post("/tasks", content="not json"), 400),
    ]:
        r = call()
        assert r.status_code == code, (code, r.status_code, r.text)
        assert "error" in r.json(), r.text


def test_seed_runs_once():
    before = len(c.get("/tasks").json())
    db.init()
    db.init()
    assert len(c.get("/tasks").json()) == before


def test_survives_restart():
    """The real point of this assignment: a separate process sees the same data."""
    made = c.post("/tasks", json={"title": "Outlive the server"})
    tid = made.json()["id"]
    out = subprocess.run(
        [sys.executable, "-c",
         "import db, json; print(json.dumps(db.one_task(%d)))" % tid],
        capture_output=True, text=True, env={**os.environ, "TASKS_DB": DB},
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )
    assert out.returncode == 0, out.stderr
    assert '"Outlive the server"' in out.stdout, out.stdout
    c.delete(f"/tasks/{tid}")


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok  ", name)
    print("all checks passed")
