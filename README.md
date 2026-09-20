# Backend AI Engineering — FlyRank internship

Six projects covering nine assignments. Each folder is self-contained: its own
README, its own run command, its own tests.

| Folder | What it is | Assignments | State |
|---|---|---|---|
| [task-api](task-api/) | A to-do API that stores tasks three different ways — a list in memory, then a SQLite file, then PostgreSQL in a container — behind routes that never change. Plus `POST /triage`, an LLM endpoint with validation, repair and a kill switch. | BE-01, BE-02, BE-04, BE-07 | CRUD verified · Postgres and the live model are not |
| [polite-scraper](polite-scraper/) | Scrapes 60 books from a practice sandbox into checked JSON, slowly and with its name on every request. | BE-05 | Verified |
| [background-job](background-job/) | An API that answers in 0.4 seconds and does 8 seconds of work elsewhere, with retries and a cron job. | BE-06 | Verified |
| [pdf-report-generator](pdf-report-generator/) | 200 orders → one SQL query → an HTML page → a real 7-page PDF, served by link. | BE-08 | Verified |
| [auth-api](auth-api/) | Sign up, log in, and a guard that stands in front of the protected routes. | BE-03 | **Verified** end to end against a live project |
| [ai-decision-flow](ai-decision-flow/) | A flowchart you draw in the browser where every box is a yes/no question and the answer picks the arrow. | BE-09 | Execution verified · the model is a stub |

## Run the tests

Every project has one command and no test framework to install.

```bash
cd task-api             && python test_api.py && python test_triage.py
cd polite-scraper       && python src/test_parser.py
cd background-job       && python test_api.py
cd pdf-report-generator && python test_report.py
cd auth-api             && python test_auth.py
cd ai-decision-flow     && npm install && npm test
```

61 checks in total, all passing as of 20 Sep 2026.

## What is honestly not finished

Three things need an account or an install I do not have, and every affected
README says so at the top rather than quietly implying otherwise:

- **Postgres (BE-04)** — written, never run. Docker is not installed. The
  Postgres module is asserted to expose the same eight functions with the same
  signatures as the SQLite one, and `compose.yaml` parses, but no container has
  ever started.
- ~~**Supabase (BE-03)**~~ — done. Verified against a live project on
  20 Sep 2026: signup, login, both protected routes, a tampered token, a wrong
  password and logout all returned the right codes.
- **The model (BE-07, BE-09)** — both run on a deterministic stub. The `6/8` eval
  score in `task-api/README.md` is the **stub's** score. Switching to a real
  model is three lines in `.env` and no code change.

A stub score presented as a model score would be the real failure here. Marking
it is the point.

## One repo, not six

The assignment briefs allow it. BE-06: *"own repo or a clearly named folder
(e.g. `background-job/`) in a shared one."* BE-08 says the same.

Each folder was merged in with `git subtree`, so **every stage commit survived** —
56 of them, one per stage as the briefs require. `git log --oneline` shows the
whole history. A copy-paste would have thrown that away, and the commit history
is part of what is being marked.
