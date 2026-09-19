"""Run: python evals/run.py

Puts all eight labelled cases through the endpoint and prints the honest score.
On OpenRouter this is 8 of your 50 calls for the day, so budget two runs.
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402
from llm.client import PROMPT_VERSION  # noqa: E402

cases = json.loads((ROOT / "evals" / "cases.json").read_text(encoding="utf-8"))
client = TestClient(main.app)

mode = "stub" if os.environ.get("LLM_STUB") == "1" else "live model"
print(f"prompt version: {PROMPT_VERSION}   mode: {mode}\n")

hits, failures = 0, []
for case in cases:
    res = client.post("/triage", json={"text": case["text"]})
    if res.status_code != 200:
        failures.append((case["id"], f"HTTP {res.status_code}", res.json()))
        continue
    got = res.json()["category"]
    ok = got == case["category"]
    hits += ok
    print(f"{'ok  ' if ok else 'MISS'} #{case['id']}  want {case['category']:<8} got {got:<8} "
          f"conf {res.json()['confidence']}")
    if not ok:
        failures.append((case["id"], case["category"], got))

print(f"\nscore: {hits}/{len(cases)} on category")
for f in failures:
    print("  miss:", f)
