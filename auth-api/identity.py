"""The only file that talks to Supabase.

Keeping it alone in here means the rest of the app can be tested without a
network, an account, or a key -- the tests swap this module for a fake.
"""
import os

from dotenv import load_dotenv

load_dotenv()

URL = os.environ.get("SUPABASE_URL", "")
KEY = os.environ.get("SUPABASE_KEY", "")


class AuthError(Exception):
    """Supabase said no. Carries the status the client should see."""

    def __init__(self, message, status=401):
        super().__init__(message)
        self.status = status


def _client():
    if not URL or not KEY:
        raise AuthError(
            "Server is not configured: set SUPABASE_URL and SUPABASE_KEY in .env", 500
        )
    from supabase import create_client  # imported late so tests never need the package
    return create_client(URL, KEY)


def sign_up(email: str, password: str) -> dict:
    try:
        res = _client().auth.sign_up({"email": email, "password": password})
    except Exception as exc:
        raise AuthError(str(exc), 400) from exc
    if res.user is None:
        raise AuthError("Sign up failed", 400)
    return {"id": res.user.id, "email": res.user.email,
            "created_at": str(res.user.created_at)}


def log_in(email: str, password: str) -> dict:
    try:
        res = _client().auth.sign_in_with_password({"email": email, "password": password})
    except Exception as exc:
        # Supabase says "Invalid login credentials" for both a wrong password and
        # an unknown email, on purpose: telling them apart would let anyone test
        # which addresses have accounts.
        raise AuthError("Invalid login credentials", 401) from exc
    return {"access_token": res.session.access_token,
            "refresh_token": res.session.refresh_token,
            "token_type": "bearer",
            "expires_in": res.session.expires_in}


def user_from_token(token: str) -> dict:
    """Ask Supabase who this token belongs to. Tampered or expired -> AuthError."""
    try:
        res = _client().auth.get_user(token)
    except Exception as exc:
        raise AuthError("Invalid or expired token") from exc
    if res is None or res.user is None:
        raise AuthError("Invalid or expired token")
    return {"id": res.user.id, "email": res.user.email,
            "created_at": str(res.user.created_at)}


def log_out(token: str) -> None:
    try:
        _client().auth.sign_out()
    except Exception as exc:
        raise AuthError("Could not end the session") from exc
