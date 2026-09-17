# The polite scraper

Collects the first three catalogue pages of **Books to Scrape** and the 60 book
pages they link to, turns the HTML into checked JSON, and writes an honest report
of what happened.

## Target classification

| | |
|---|---|
| **Site** | https://books.toscrape.com/ |
| **Why this one** | It is a practice sandbox. toscrape.com exists to be scraped — that sentence is the permission, and it is the only site this project touches. |
| **How much** | The first 3 catalogue pages and the 60 book pages they link to. Nothing else, ever. |
| **What data** | Title, price, availability, star rating, description, and where each record came from. |
| **robots.txt** | Requested once. **HTTP 404 — no robots file found.** A missing file is not permission; it just means there are no published rules, so the scope above is self-imposed. |

**I will not reuse this code on another site without checking its rules and terms
first.**

### Ethics, in my own words

If a site offers an official API, use that instead — it is cheaper for them and
more reliable for me. Never work around a login, a paywall or a block: those are
a clear "no", and going around one is not a technical problem but a decision to
ignore an answer. Take only the fields you actually need, go slowly enough that
nobody notices you, and be reachable — my User-Agent carries a link back to this
repo so an admin can email me rather than ban a whole range.

## Run it

```bash
pip install requests beautifulsoup4 pydantic
python src/main.py                # the real run
python src/main.py --break-one    # same run plus one URL that cannot work
python src/test_parser.py         # eight parser tests, no network needed
```

First run takes about **70 seconds** -- that is mostly the half-second pause
between requests, on purpose. Every later run reads `cache/` and finishes in
about **1.5 seconds** with zero requests to the site.

Output lands in `output/`: `books.json` (60 records), `errors.json` (records that
failed validation) and `run-report.json`.

## Being a polite guest

| Rule | How |
|---|---|
| Say who you are | `User-Agent: FlyRankInternship-A9/1.0 (+repo link)` so an admin can email me instead of banning me |
| Go slowly | at least **0.5 s** between two real requests |
| Give up politely | **10 s** timeout, so one hanging server can't stall the run |
| Don't ask twice | every page is cached to `cache/`; development never touches the network |
| Know when to stop | retry once on a timeout or a 5xx. **Never retry a 404 or a 403** -- those are answers, and repeating the question is rude |

All five live in one file, `src/fetcher.py`. Nothing else in the project is
allowed to make a request, which is the only reliable way to not forget one.

## The record

```json
{
  "title": "A Light in the Attic",
  "product_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
  "price_text": "\u00a351.77",
  "price_gbp": 51.77,
  "availability_text": "In stock (22 available)",
  "in_stock": true,
  "rating_text": "Three",
  "rating": 3,
  "description": "It's hard to imagine a world without A Light in the Attic. This now-classic collection of poetry and drawings from Shel Silverstein celebrates its 20th anniversary with this special edition. Silverstein's humorous and creative verse can amuse the dowdiest of readers. Lemon-faced adults and fidgety kids sit still and read these rhythmic words and laugh and smile and love th It's hard to imagine a world without A Light in the Attic. This now-classic collection of poetry and drawings from Shel Silverstein celebrates its 20th anniversary with this special edition. Silverstein's humorous and creative verse can amuse the dowdiest of readers. Lemon-faced adults and fidgety kids sit still and read these rhythmic words and laugh and smile and love that Silverstein. Need proof of his genius? RockabyeRockabye baby, in the treetopDon't you know a treetopIs no safe place to rock?And who put you up there,And your cradle, too?Baby, I think someone down here'sGot it in for you. Shel, you never sounded so good. ...more",
  "source_page": "https://books.toscrape.com/catalogue/page-1.html",
  "fetched_at": "2026-09-17T22:02:21Z"
}
```

`price_text` keeps exactly what the page said; `price_gbp` is the number I
derived from it. Keeping both means a parsing mistake is always provable after
the fact. `source_page` and `fetched_at` are **provenance** -- which listing page
found this book, and when. Without them a record is a claim with no receipt.

Every record is checked by a Pydantic schema **before** it is stored: URLs must
really be URLs, the price must be a number above zero, the rating must be 1-5.
Whatever fails goes to `errors.json` with the reason, never silently dropped.

## One real run

```json
{
  "started_at": "2026-09-17T22:02:21Z",
  "duration_seconds": 1.67,
  "catalogue_pages": 3,
  "pages_fetched": 0,
  "cache_hits": 63,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 1,
  "failures": [
    {
      "url": "https://books.toscrape.com/catalogue/this-book-does-not-exist_9999/index.html",
      "reason": "HTTP 404"
    }
  ]
}
```

That is the `--break-one` run: one deliberately dead URL, logged as
`HTTP 404` and skipped, and the other 60 records came through untouched. That is
the whole point of Stage 5 -- a scraper that dies on page 41 of 60 is worse than
useless, because it half-finished and you can't tell which half.

**No browser was needed.** The prices and titles are already in the HTML the
server sends, so `requests` plus a parser is enough. A browser is only worth its
cost when the data arrives later via JavaScript, and you can check which case
you're in with `curl -s <url> | grep price` before writing a line of code.

## Two things that bit me

**A pound sign came out as `Â£`.** The server sends UTF-8 but doesn't say so in
its `Content-Type` header, and when the header is silent `requests` falls back to
ISO-8859-1 -- the old HTTP default -- so each UTF-8 byte gets decoded separately.
Fix: if the header has no charset, set `r.encoding = r.apparent_encoding`, which
looks at the actual bytes.

Worse, I "confirmed" the fix against a cached page and believed it. **Check an
encoding fix on a cold cache, and compare code points rather than reading the
terminal** -- `hex(ord(c)) == '0xa3'` is proof, a `£` on screen is not, because
the terminal has its own encoding and will lie to you in both directions.

**`Path("cache")` is relative to wherever you ran the command.** Running from the
repo root and from `src/` quietly built two separate caches, which is how I ended
up testing against a stale one. Anchoring it with
`Path(__file__).resolve().parent.parent` fixed it.

## Limitation

It only understands this one site's HTML. The selectors (`article.product_pod`,
`p.price_color`) are Books to Scrape's markup, and a redesign there breaks every
one of them. The parser tests are how I'd find out fast -- they run on fixed HTML
scraps, so if they pass and the live run fails, the site changed rather than my code.
