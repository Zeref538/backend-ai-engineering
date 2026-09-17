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
