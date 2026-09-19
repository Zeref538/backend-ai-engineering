"""Every outgoing request goes through here, so politeness can't be forgotten.

Four rules live in one function:
  - say who you are (User-Agent), so an admin can contact you instead of banning you
  - give up after a few seconds (timeout), so one dead page can't hang the run
  - only 200 is a page; anything else is a problem, not content
  - wait between real requests, and never re-download what's already cached
"""
import time
from pathlib import Path

import requests

USER_AGENT = "FlyRankInternship-A9/1.0 (+https://github.com/Zeref538/polite-scraper)"
TIMEOUT = 10          # seconds before we give up on a slow server
DELAY = 0.5           # minimum gap between two real requests
# Anchored to the project folder, not the current directory: running from the
# repo root and from src/ must share one cache, not quietly make two.
CACHE = Path(__file__).resolve().parent.parent / "cache"

_last_request_at = 0.0
stats = {"fetched": 0, "cache_hits": 0, "failed": []}


def _cache_path(url: str) -> Path:
    """A readable filename per URL: the last two path pieces, slashes flattened."""
    name = url.replace("https://", "").replace("http://", "").strip("/").replace("/", "_")
    return CACHE / (name[-120:] + ".html")


def _sleep_if_needed():
    global _last_request_at
    gap = time.monotonic() - _last_request_at
    if gap < DELAY:
        time.sleep(DELAY - gap)
    _last_request_at = time.monotonic()


def fetch(url: str, retry: bool = True) -> str | None:
    """Return the page HTML, or None if this page is a lost cause.

    Returning None rather than raising is deliberate: one broken page must not
    end a 60-page run.
    """
    path = _cache_path(url)
    if path.exists():
        stats["cache_hits"] += 1
        print(f"CACHE HIT  {len(path.read_bytes()):>7,} bytes  {url}")
        return path.read_text(encoding="utf-8")

    _sleep_if_needed()
    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
    except requests.RequestException as exc:
        # A timeout or a dropped connection is a bad moment, not a bad URL, so
        # it is worth exactly one more try.
        if retry:
            print(f"RETRY      {type(exc).__name__}  {url}")
            time.sleep(2)
            return fetch(url, retry=False)
        stats["failed"].append({"url": url, "reason": type(exc).__name__})
        return None

    if r.status_code == 200:
        # If the server never says which character set it used, requests falls
        # back to ISO-8859-1 (the old HTTP default) and a UTF-8 pound sign comes
        # out as "A-circumflex pound". Let chardet look at the actual bytes.
        if "charset" not in r.headers.get("Content-Type", "").lower():
            r.encoding = r.apparent_encoding
        stats["fetched"] += 1
        CACHE.mkdir(exist_ok=True)
        path.write_text(r.text, encoding="utf-8")
        print(f"FETCH      {len(r.content):>7,} bytes  {url}")
        return r.text

    # 404 and 403 are answers, not accidents. Retrying them is rude and pointless.
    if r.status_code >= 500 and retry:
        print(f"RETRY      HTTP {r.status_code}  {url}")
        time.sleep(2)
        return fetch(url, retry=False)
    stats["failed"].append({"url": url, "reason": f"HTTP {r.status_code}"})
    print(f"FAILED     HTTP {r.status_code}  {url}")
    return None
