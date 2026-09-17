"""Run the whole pipeline: discover -> fetch -> extract -> validate -> store -> report."""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from discover import discover
from extract import extract
from fetcher import fetch, stats
from schema import Book, normalize

OUT = Path(__file__).resolve().parent.parent / "output"

# Stage 5 asks for a URL that cannot work, to prove one bad page doesn't end the
# run. Passing --break-one adds it; the run should still finish with 60 good records.
BROKEN = "https://books.toscrape.com/catalogue/this-book-does-not-exist_9999/index.html"


def main(break_one=False):
    started = time.monotonic()
    start_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    pages, links = discover()
    if break_one:
        links.append({"url": BROKEN, "source_page": "deliberate-test"})
    print(f"catalogue_pages={pages} discovered={len(links)}")

    good, bad = [], []
    for link in links:
        html = fetch(link["url"])
        if html is None:
            continue                      # fetcher already recorded why
        raw = extract(html, link["url"], link["source_page"])
        try:
            good.append(Book(**normalize(raw)).model_dump(mode="json"))
        except Exception as exc:
            bad.append({"url": link["url"], "reason": str(exc)[:300]})

    OUT.mkdir(exist_ok=True)
    # Sort by URL so two runs produce byte-identical files, which makes a diff
    # mean "the site changed", not "the order shuffled".
    good.sort(key=lambda b: b["product_url"])
    (OUT / "books.json").write_text(json.dumps(good, indent=2), encoding="utf-8")
    (OUT / "errors.json").write_text(json.dumps(bad, indent=2), encoding="utf-8")

    report = {
        "started_at": start_iso,
        "duration_seconds": round(time.monotonic() - started, 2),
        "catalogue_pages": pages,
        "pages_fetched": stats["fetched"],
        "cache_hits": stats["cache_hits"],
        "valid_records": len(good),
        "invalid_records": len(bad),
        "failed_pages": len(stats["failed"]),
        "failures": stats["failed"],
    }
    (OUT / "run-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    main(break_one="--break-one" in sys.argv)
