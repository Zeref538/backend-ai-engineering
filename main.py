"""An API that answers instantly and does the slow work somewhere else.

Three ways work can start, and this file has all three:
  - a request that waits            -> GET /health
  - a request that hands work off   -> POST /reports, done later by a background job
  - nobody asks at all              -> the cron function, started by the clock
"""
from fastapi import Body, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

app = FastAPI(title="Report API", version="1.0")

# Reports live in a dict, so a restart forgets them. That is fine here -- the
# assignment is about where work runs, not about storage.
reports: dict[str, dict] = {}


@app.exception_handler(HTTPException)
def json_error(request, exc):
    return JSONResponse({"error": exc.detail}, status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
def bad_body(request, exc):
    return JSONResponse({"error": "Body must be a JSON object"}, status_code=400)


@app.get("/health")
def health():
    return {"status": "ok"}


