"""Run: python test_auth.py

No Supabase account, no network, no key. The identity module is replaced by a
fake that behaves the way Supabase does: one valid token, everything else
rejected. That is exactly the boundary worth testing -- whether *my* routes let
the wrong person through, not whether Supabase can check a signature.
"""
from fastapi.testclient import TestClient

import identity
import main

GOOD = "a.valid.token"
USER = {"id": "user-123", "email": "test@example.com", "created_at": "2026-09-18"}


def fake_user_from_token(token):
    if token != GOOD:
        raise identity.AuthError("Invalid or expired token")
    return USER


identity.user_from_token = main.identity.user_from_token = fake_user_from_token
main.identity.sign_up = lambda e, p: {**USER, "email": e}
main.identity.log_in = lambda e, p: (
    {"access_token": GOOD, "refresh_token": "r", "token_type": "bearer", "expires_in": 3600}
    if p == "password123" else (_ for _ in ()).throw(identity.AuthError("Invalid login credentials"))
)
main.identity.log_out = lambda token: None

c = TestClient(main.app)
AUTH = {"Authorization": f"Bearer {GOOD}"}


def test_public_route_needs_nothing():
    r = c.get("/public/info")
    assert r.status_code == 200 and "public" in r.json()["message"]


def test_signup_returns_201():
    r = c.post("/auth/signup", json={"email": "new@example.com", "password": "password123"})
    assert r.status_code == 201, r.text
    assert r.json()["email"] == "new@example.com"


def test_missing_fields_are_400_not_401():
    # A malformed request is not an authentication failure. Getting this wrong
    # tells an attacker "your credentials were wrong" when you never read them.
    for body in [{}, {"email": "a@b.c"}, {"password": "x"}, {"email": "  ", "password": "x"}]:
        for path in ("/auth/signup", "/auth/login"):
            r = c.post(path, json=body)
            assert r.status_code == 400, (path, body, r.status_code)
            assert "error" in r.json()


def test_wrong_password_is_401():
    r = c.post("/auth/login", json={"email": "test@example.com", "password": "nope"})
    assert r.status_code == 401
    assert r.json()["error"] == "Invalid login credentials"


def test_login_returns_a_token():
    r = c.post("/auth/login", json={"email": "test@example.com", "password": "password123"})
    assert r.status_code == 200
    assert isinstance(r.json()["access_token"], str) and r.json()["access_token"]


def test_protected_routes_reject_every_broken_header():
    for headers, why in [
        ({}, "no header at all"),
        ({"Authorization": ""}, "empty header"),
        ({"Authorization": GOOD}, "token with no Bearer prefix"),
        ({"Authorization": "Bearer"}, "prefix with no token"),
        ({"Authorization": "Basic " + GOOD}, "wrong scheme"),
        ({"Authorization": "Bearer a.valid.tokenX"}, "one character changed"),
    ]:
        for path in ("/protected/profile", "/protected/dashboard"):
            r = c.get(path, headers=headers)
            assert r.status_code == 401, (why, path, r.status_code)
            assert "error" in r.json(), why


def test_a_valid_token_opens_both_protected_routes():
    assert c.get("/protected/profile", headers=AUTH).json() == USER
    dash = c.get("/protected/dashboard", headers=AUTH)
    assert dash.status_code == 200 and dash.json()["user_id"] == USER["id"]


def test_logout_is_204_and_still_needs_a_token():
    assert c.post("/auth/logout", headers=AUTH).status_code == 204
    assert c.post("/auth/logout").status_code == 401


def test_swagger_shows_the_padlock_on_protected_routes_only():
    spec = c.get("/openapi.json").json()
    assert "HTTPBearer" in spec["components"]["securitySchemes"]
    assert spec["paths"]["/protected/profile"]["get"].get("security")
    assert not spec["paths"]["/public/info"]["get"].get("security")


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok  ", name)
    print("all checks passed")
