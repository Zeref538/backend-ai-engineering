"""An API with a public door, a locked door, and a guard on the locked one."""
from fastapi import Body, Depends, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

import identity

app = FastAPI(
    title="Auth API",
    version="1.0",
    description="Sign up, log in, and get a token that opens the protected routes.",
)

# Telling Swagger the scheme exists is what puts the Authorize padlock on /docs.
# auto_error=False so a missing header reaches my code and gets my error shape
# rather than FastAPI's {"detail": ...}.
bearer = HTTPBearer(auto_error=False)


@app.exception_handler(HTTPException)
def json_error(request, exc):
    return JSONResponse({"error": exc.detail}, status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
def bad_body(request, exc):
    return JSONResponse({"error": "Body must be a JSON object"}, status_code=400)


@app.exception_handler(identity.AuthError)
def auth_error(request, exc):
    return JSONResponse({"error": str(exc)}, status_code=exc.status)


def credentials(body: dict) -> tuple[str, str]:
    email, password = body.get("email"), body.get("password")
    if not isinstance(email, str) or not email.strip():
        raise HTTPException(400, "Field 'email' is required")
    if not isinstance(password, str) or not password:
        raise HTTPException(400, "Field 'password' is required")
    return email.strip(), password


def current_user(creds: HTTPAuthorizationCredentials | None = Depends(bearer)) -> dict:
    """The guard. Every protected route depends on this, so the check can't be
    forgotten on a new route -- you either ask for the user or you don't."""
    if creds is None or not creds.credentials:
        # No header, or a header that isn't "Bearer <something>".
        raise HTTPException(401, "Access token required")
    return identity.user_from_token(creds.credentials)


def bearer_token(creds: HTTPAuthorizationCredentials | None = Depends(bearer)) -> str:
    if creds is None or not creds.credentials:
        raise HTTPException(401, "Access token required")
    return creds.credentials


@app.post("/auth/signup", status_code=201, summary="Create an account")
def signup(body: dict = Body(...)):
    email, password = credentials(body)
    return identity.sign_up(email, password)


@app.post("/auth/login", summary="Exchange email and password for a token")
def login(body: dict = Body(...)):
    email, password = credentials(body)
    return identity.log_in(email, password)


@app.get("/health")
def health():
    return {"status": "ok"}
