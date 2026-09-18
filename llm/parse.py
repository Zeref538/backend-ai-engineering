"""Turn whatever the model said into a valid object, or admit it couldn't.

Model output is untrusted input. It arrives wrapped in code fences, prefixed with
"Sure! Here's the JSON:", or as valid JSON with a category nobody allows.
"""
import json
import re

from pydantic import ValidationError

from .schema import Triage

FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.S)


def extract_json(text: str) -> str | None:
    """Find the JSON object inside a reply that may be wrapped in chatter."""
    if not text:
        return None
    fenced = FENCE.search(text)
    if fenced:
        return fenced.group(1).strip()
    # Otherwise take the outermost {...}: a model that says "Here you go:" first
    # still usually gets the object right.
    start, end = text.find("{"), text.rfind("}")
    return text[start:end + 1] if start != -1 and end > start else None


def parse(text: str) -> tuple[Triage | None, str | None]:
    """Return (result, error). Never raises -- a bad reply is an outcome, not a crash."""
    blob = extract_json(text)
    if blob is None:
        return None, "No JSON object found in the reply"
    try:
        data = json.loads(blob)
    except json.JSONDecodeError as exc:
        return None, f"Reply was not valid JSON: {exc}"
    if not isinstance(data, dict):
        return None, "Reply was JSON but not an object"
    try:
        return Triage(**data), None
    except ValidationError as exc:
        # The exact message is handed back to the model on the repair attempt,
        # so it must say what was wrong, not just that something was.
        return None, "; ".join(
            f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors()
        )
