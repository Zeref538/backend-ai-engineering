from fastapi import Body, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

import db

app = FastAPI(
    title="Task API",
    version="1.0",
    description="A to-do list you can create, read, update and delete over HTTP. "
    "Storage is a plain Python list, so restarting the server resets it.",
)

db.init()  # create tasks.db and its table on startup if they aren't there yet


@app.exception_handler(HTTPException)
def json_error(request, exc):
    """Every error leaves as {"error": "..."} instead of FastAPI's {"detail": ...}."""
    return JSONResponse({"error": exc.detail}, status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
def bad_body(request, exc):
    """Body that isn't even valid JSON is a client mistake: 400, same shape."""
    return JSONResponse({"error": "Body must be a JSON object"}, status_code=400)


def clean_title(body: dict) -> str:
    """A title must be present, be text, and not be blank. Anything else is a 400."""
    title = body.get("title")
    if not isinstance(title, str) or not title.strip():
        raise HTTPException(400, "Field 'title' is required and must not be empty")
    return title.strip()


def find(task_id: int):
    task = db.one_task(task_id)
    if task is None:
        raise HTTPException(404, f"Task {task_id} not found")
    return task


@app.get("/", summary="What this API is and where to go next")
def root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health", summary="Say whether the server is alive")
def health():
    return {"status": "ok"}


@app.get("/tasks", summary="List every task")
def list_tasks():
    return db.all_tasks()


@app.get("/tasks/{task_id}", summary="Get one task by id, or 404")
def get_task(task_id: int):
    return find(task_id)


@app.post("/tasks", status_code=201, summary="Create a task from a title")
def create_task(body: dict = Body(...)):
    # SQLite hands out the id now (INTEGER PRIMARY KEY AUTOINCREMENT), so the
    # old max(id)+1 trick is gone -- and so is the chance of two requests racing
    # for the same number.
    return db.insert(clean_title(body))

@app.put("/tasks/{task_id}", summary="Change a task's title, its done flag, or both")
def update_task(task_id: int, body: dict = Body(...)):
    find(task_id)  # 404s before we touch the database
    if "title" not in body and "done" not in body:
        raise HTTPException(400, "Send at least one of 'title' or 'done'")
    title = clean_title(body) if "title" in body else None
    done = None
    if "done" in body:
        if not isinstance(body["done"], bool):
            raise HTTPException(400, "Field 'done' must be true or false")
        done = body["done"]
    return db.update(task_id, title=title, done=done)


@app.delete("/tasks/{task_id}", status_code=204, summary="Delete a task, returning no body")
def delete_task(task_id: int):
    find(task_id)
    db.delete(task_id)
