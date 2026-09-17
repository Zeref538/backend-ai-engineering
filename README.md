# Task API

A to-do list you can talk to over HTTP. Create a task, read one or all of them,
change one, delete one — the four CRUD operations, which is the shape almost
every backend in the world has underneath.

Storage is **SQLite**, a database that is just a file on disk -- no server to
install, no password, nothing to start. Your tasks survive a restart.

It did not start that way. The first version kept tasks in a Python list in
memory and lost everything on restart. Swapping in a database touched exactly one
new file, `db.py`, and left every URL, request body and response byte-for-byte
identical. That is the point of the exercise.

## Run it

```bash
pip install "fastapi[standard]" uvicorn
python -m uvicorn main:app --reload --port 8000
```

`tasks.db` is created next to `main.py` on first run, the `tasks` table with it,
and three example tasks are inserted **only if the table is empty** -- so
restarting never duplicates them. The file is gitignored; the code is its recipe.
Point it somewhere else with the `TASKS_DB` environment variable, which is how
the tests keep their hands off your real data.

Then open **http://localhost:8000/docs** — that's Swagger UI, a page FastAPI
generates from your code that lets you fire every endpoint from a browser with
no curl at all.

Run the checks:

```bash
python test_api.py     # prints "all checks passed"
```

## Endpoints

| CRUD | Method | Path | Success | Errors |
|---|---|---|---|---|
| — | GET | `/` | 200 — name, version, endpoints | — |
| — | GET | `/health` | 200 `{"status":"ok"}` | — |
| Read | GET | `/tasks` | 200 — the whole list | — |
| Read | GET | `/tasks/{id}` | 200 — one task | 404 unknown id |
| Create | POST | `/tasks` | 201 — the new task | 400 missing/blank title |
| Update | PUT | `/tasks/{id}` | 200 — the updated task | 400 bad body · 404 unknown id |
| Delete | DELETE | `/tasks/{id}` | 204 — no body at all | 404 unknown id |

A task looks like `{"id": 1, "title": "Buy milk", "done": false}`. `PUT` takes
`title`, `done`, or both.

**Every error comes back the same shape** — `{"error": "..."}` — including the
ones FastAPI raises itself before reaching my code. Two exception handlers at the
top of `main.py` do that. Without them, a body that isn't valid JSON answers
`422` with a nested `{"detail": [...]}`, and a client would need two different
ways to read one API's errors.

## Proof — one real session

Headers trimmed to the status line; these are actual responses.

```
$ curl -i -X POST http://localhost:8000/tasks -H "Content-Type: application/json" -d '{"title":"Buy milk"}'
HTTP/1.1 201 Created
{"id":4,"title":"Buy milk","done":false}

$ curl -i http://localhost:8000/tasks/4
HTTP/1.1 200 OK
{"id":4,"title":"Buy milk","done":false}

$ curl -i -X PUT http://localhost:8000/tasks/4 -H "Content-Type: application/json" -d '{"done":true}'
HTTP/1.1 200 OK
{"id":4,"title":"Buy milk","done":true}

$ curl -i -X POST http://localhost:8000/tasks -H "Content-Type: application/json" -d '{}'
HTTP/1.1 400 Bad Request
{"error":"Field 'title' is required and must not be empty"}

$ curl -i http://localhost:8000/tasks/99
HTTP/1.1 404 Not Found
{"error":"Task 99 not found"}

$ curl -i -X DELETE http://localhost:8000/tasks/4
HTTP/1.1 204 No Content

$ curl -i -X POST http://localhost:8000/tasks -H "Content-Type: application/json" -d "not json"
HTTP/1.1 400 Bad Request
{"error":"Body must be a JSON object"}
```

## Swagger UI

FastAPI reads my function names, type hints and `summary=` text and builds this
page itself. There is no hand-written spec file in this repo.

![Swagger UI showing all seven endpoints](docs/swagger.png)

Full CRUD works from this page with no curl. Here is **Try it out** on
`POST /tasks`, executed live against the running server:

![Try it out on POST /tasks returning 201 and the new task](docs/swagger-try-it-out.png)

## Notes

**404, never an empty 200.** Asking for a task that doesn't exist is a different
answer from "here is nothing". One `find()` helper raises the 404, so every
endpoint that takes an id gets the same behaviour for free — including `DELETE`,
which deletes by handing `find()`'s result straight to `list.remove`.

**Blank is not a title.** `{"title": "   "}` is rejected the same as `{}`. The
check is `.strip()`, and the stripped version is what gets stored.

**Ids come from SQLite, not from me.** The column is
`INTEGER PRIMARY KEY AUTOINCREMENT`, so the database hands out the next number
and never reuses one. The in-memory version computed `max(id) + 1` in Python,
which two requests arriving together could both read before either wrote.

**SQLite has no boolean.** `done` is stored as `0` or `1`, so `db.as_task()`
converts it back to `true`/`false` on the way out. Without that one line the API
would quietly start answering `"done": 1`, and every client comparing to `true`
would break.

**`with sqlite3.connect(...)` does not close the connection.** It only commits or
rolls back the transaction. I found out because a test could not delete its own
database file -- Windows refuses to delete a file something still has open. The
fix is `contextlib.closing` around it, in `db.py`.

## The database

`db.py` is the only file that writes SQL. `main.py` calls `db.all_tasks()`,
`db.insert()` and so on, and would not notice if the storage underneath changed.

### Seeing inside it

```bash
pip install sqlite-web
python -m sqlite_web.sqlite_web --port 8090 tasks.db
```

![sqlite-web showing the tasks table with four rows](docs/sqlite-viewer.png)

(Note: `python -m sqlite_web` crashes with an `ImportError` in version 0.8.1 --
its `__main__.py` imports a `main` that no longer exists. `sqlite_web.sqlite_web`
is the module that actually runs.)

### The API is only a window onto the file

Here is the lesson of this stage. With the server running and untouched, I
changed the data by hand:

```
$ curl -s localhost:8000/tasks
[{"id":1,...},{"id":2,...},{"id":3,...}]          # three tasks

sqlite> UPDATE tasks SET done = 1;
sqlite> DELETE FROM tasks WHERE done = 1;

$ curl -s localhost:8000/tasks
[]                                                 # no restart, no code change
```

The API had no cached copy to go stale, because it never held one. Every request
asks the file. A few queries worth knowing:

```sql
SELECT * FROM tasks;                  -- everything
SELECT * FROM tasks WHERE done = 1;   -- just the finished ones
SELECT COUNT(*) FROM tasks;           -- how many rows
```
