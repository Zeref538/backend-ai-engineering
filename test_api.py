"""One runnable check: python test_api.py

Uses FastAPI's TestClient, which calls the app directly in this process -- no
server to start, no port to pick. If a status code ever drifts, this shouts.
"""
from fastapi.testclient import TestClient

from main import app

c = TestClient(app)


def test():
    assert c.get("/health").json() == {"status": "ok"}
    assert len(c.get("/tasks").json()) == 3

    made = c.post("/tasks", json={"title": "Buy milk"})
    assert made.status_code == 201, made.status_code
    tid = made.json()["id"]
    assert made.json()["done"] is False

    assert c.get(f"/tasks/{tid}").json()["title"] == "Buy milk"
    assert c.put(f"/tasks/{tid}", json={"done": True}).json()["done"] is True

    # Every unhappy path answers with {"error": ...}, never {"detail": ...}.
    for call, code in [
        (lambda: c.get("/tasks/99"), 404),
        (lambda: c.put("/tasks/99", json={"done": True}), 404),
        (lambda: c.delete("/tasks/99"), 404),
        (lambda: c.post("/tasks", json={}), 400),
        (lambda: c.post("/tasks", json={"title": "   "}), 400),
        (lambda: c.put(f"/tasks/{tid}", json={}), 400),
        (lambda: c.put(f"/tasks/{tid}", json={"done": "yes"}), 400),
        (lambda: c.post("/tasks", content="not json"), 400),
    ]:
        r = call()
        assert r.status_code == code, (code, r.status_code, r.text)
        assert "error" in r.json(), r.text

    assert c.delete(f"/tasks/{tid}").status_code == 204
    assert c.get(f"/tasks/{tid}").status_code == 404
    print("all checks passed")


if __name__ == "__main__":
    test()
