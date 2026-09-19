"""Run: python test_api.py

Tests the fast door only -- the part that must answer in milliseconds. The
background function itself is proved by the dashboard and the poll in the
README, because that is what "it ran somewhere else" means.

The event send is swapped for a recorder, so these tests need no Dev Server.
"""
import time

from fastapi.testclient import TestClient

import main

sent = []
main.inngest_client.send_sync = lambda event: sent.append(event)  # no network

c = TestClient(main.app)


def test_accepting_a_report_is_fast_and_says_202():
    started = time.monotonic()
    r = c.post("/reports", json={"topic": "cats"})
    elapsed = time.monotonic() - started
    assert r.status_code == 202, r.text
    assert r.json()["status"] == "pending"
    # The real job sleeps 8 seconds. If that ever leaks into the endpoint, this
    # is the test that catches it.
    assert elapsed < 1.0, f"endpoint took {elapsed:.2f}s -- slow work crept back in"


def test_an_event_is_sent_with_the_id_and_topic():
    sent.clear()
    rid = c.post("/reports", json={"topic": "dogs"}).json()["id"]
    assert len(sent) == 1, sent
    assert sent[0].name == "report/requested"
    assert sent[0].data == {"id": rid, "topic": "dogs"}


def test_bad_input_is_rejected_at_the_door_and_makes_no_job():
    sent.clear()
    for body in [{}, {"topic": ""}, {"topic": "   "}, {"topic": 7}]:
        r = c.post("/reports", json=body)
        assert r.status_code == 400, (body, r.status_code)
        assert "error" in r.json()
    assert sent == [], "a rejected request must not create a background job"


def test_unknown_report_is_404():
    r = c.get("/reports/rep_does_not_exist")
    assert r.status_code == 404 and "error" in r.json()


def test_a_fresh_report_starts_pending():
    rid = c.post("/reports", json={"topic": "birds"}).json()["id"]
    assert c.get(f"/reports/{rid}").json()["status"] == "pending"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok  ", name)
    print("all checks passed")
