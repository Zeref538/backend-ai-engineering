from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()

# The whole "database". It lives in RAM, so restarting the server wipes it.
tasks = [
    {"id": 1, "title": "Read the assignment brief", "done": True},
    {"id": 2, "title": "Build the task API", "done": False},
    {"id": 3, "title": "Publish it to GitHub", "done": False},
]


@app.exception_handler(HTTPException)
def json_error(request, exc):
    """Every error leaves as {"error": "..."} instead of FastAPI's {"detail": ...}."""
    return JSONResponse({"error": exc.detail}, status_code=exc.status_code)


def find(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task
    raise HTTPException(404, f"Task {task_id} not found")


@app.get("/")
def root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks():
    return tasks


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    return find(task_id)
