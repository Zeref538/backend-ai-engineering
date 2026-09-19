"""An API that answers instantly and does the slow work somewhere else.

Three ways work can start, and this file has all three:
  - a request that waits            -> GET /health
  - a request that hands work off   -> POST /reports, done later by a background job
  - nobody asks at all              -> the cron function, started by the clock
"""
import inngest
import inngest.fast_api
from fastapi import Body, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

app = FastAPI(title="Report API", version="1.0")

inngest_client = inngest.Inngest(
    app_id="report-api",
    is_production=False,  # talk to the local Dev Server, not Inngest Cloud
)

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


@app.post("/reports", status_code=202)
def request_report(body: dict = Body(...)):
    """Accept fast. Do nothing slow here -- that's the whole idea.

    202 means "I have taken this, it is not finished". 200 would be a lie.
    """
    topic = body.get("topic")
    if not isinstance(topic, str) or not topic.strip():
        # A wrong *input* is rejected at the door and no job is created. Only a
        # wrong *moment* -- a service being down -- deserves a retry.
        raise HTTPException(400, "Field 'topic' is required and must not be empty")

    report_id = f"rep_{len(reports) + 1}"
    reports[report_id] = {"id": report_id, "topic": topic.strip(), "status": "pending"}
    inngest_client.send_sync(
        inngest.Event(name="report/requested", data={"id": report_id, "topic": topic.strip()})
    )
    return {"id": report_id, "status": "pending"}


@app.get("/reports/{report_id}")
def get_report(report_id: str):
    """Asking this over and over is called polling. Until it flips to done, the
    client and the server disagree about the world -- eventual consistency."""
    if report_id not in reports:
        raise HTTPException(404, f"Report {report_id} not found")
    return reports[report_id]


@app.get("/reports")
def list_reports():
    return list(reports.values())


@inngest_client.create_function(
    fn_id="say-hello",
    trigger=inngest.TriggerEvent(event="test/hello"),
)
async def say_hello(ctx: inngest.Context) -> str:
    await ctx.step.sleep("nap", 5000)
    return "Hello from the background!"


@inngest_client.create_function(
    fn_id="make-report",
    trigger=inngest.TriggerEvent(event="report/requested"),
    retries=2,  # so a failure shows 3 attempts in total: the first, then two more
)
async def make_report(ctx: inngest.Context) -> dict:
    report_id = ctx.event.data["id"]
    topic = ctx.event.data["topic"]

    # Two steps, so the dashboard shows them separately and a crash between them
    # does not redo the first one.
    await ctx.step.sleep("do-the-slow-work", 8000)

    async def build() -> str:
        if topic == "fail":
            raise Exception("The report oven is broken!")
        return f"Report about {topic}: 3 findings, 1 recommendation."

    result = await ctx.step.run("build-report", build)
    reports[report_id] = {"id": report_id, "topic": topic, "status": "done", "result": result}
    return reports[report_id]


@inngest_client.create_function(
    fn_id="heartbeat",
    trigger=inngest.TriggerCron(cron="* * * * *"),  # every minute, for testing only
)
async def heartbeat(ctx: inngest.Context) -> str:
    counts = {"pending": 0, "done": 0, "failed": 0}
    for r in reports.values():
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    line = f"heartbeat: pending={counts['pending']} done={counts['done']} failed={counts['failed']}"
    print(line)
    return line


inngest.fast_api.serve(app, inngest_client, [say_hello, make_report, heartbeat])
