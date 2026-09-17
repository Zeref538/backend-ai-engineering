# Auth API — login and protect

Sign up, log in, get a token, and use that token to open doors that are shut to
everyone else. Supabase handles accounts and passwords; this API decides who gets
in.

> **Status: the guard is tested, the Supabase round-trip is not.** Every route,
> status code and header case below is covered by `test_auth.py` against a fake
> identity provider. I have not yet run it against a real Supabase project,
> because that needs an account and keys. Nothing here claims otherwise.

## The trust triangle

Three parties, and your server is only one of them:

1. The client sends email and password **to Supabase**, not to me.
2. Supabase checks them and returns a **JWT** — a signed string that says "this
   is user 123". Signed means I can tell if someone edited it.
3. The client calls my API with that token in the `Authorization` header.
4. I ask Supabase "whose token is this?" and serve the route if the answer is a
   real person.

My server never sees a password. That is the point — the thing I don't store I
can't leak.

## Setup

```bash
pip install "fastapi[standard]" uvicorn supabase python-dotenv
cp .env.example .env        # then paste your own values in
python -m uvicorn main:app --port 3000
```

Get the two values from the Supabase dashboard: **Project Settings → API** gives
you the **Project URL** and the **anon public** key.

```
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your_anon_public_key
```

**`.env` is in `.gitignore`, and it was there before the first commit.** That
order matters more than it sounds. A key pushed once lives in git history
forever — deleting the file in a later commit does nothing, because the old
commit is already in every clone anyone made. `.env.example` is committed instead:
the names, never the values.

```bash
python test_auth.py     # nine checks, no account and no network needed
```

## Routes

| Method | Path | Needs a token | Answers |
|---|---|---|---|
| POST | `/auth/signup` | no | **201** + the new user · 400 missing email or password |
| POST | `/auth/login` | no | 200 + `access_token` · 400 missing fields · **401** wrong password |
| POST | `/auth/logout` | **yes** | **204**, empty body · 401 without a token |
| GET | `/public/info` | no | 200 — open to anyone |
| GET | `/protected/profile` | **yes** | 200 + id, email, created-at · 401 otherwise |
| GET | `/protected/dashboard` | **yes** | 200 — proves the guard is reusable |

![Swagger UI with padlocks on the protected routes](docs/swagger-auth.png)

The padlock appears on exactly three rows. Click **Authorize**, paste a token
from `/auth/login`, and **Try it out** works on the protected endpoints.

## 400 and 401 are different answers

- **400** — you sent me a broken request. No email field at all.
- **401** — I read your credentials and they were wrong, or absent.

Mixing them leaks information. Answering 401 to a request with no password tells
someone "your credentials failed" when I never looked at any. And Supabase
deliberately says `Invalid login credentials` for *both* a wrong password and an
unknown email, so nobody can use the login form to find out which addresses have
accounts here.

## The guard is a dependency, not a copy-pasted check

```python
def current_user(creds = Depends(bearer)) -> dict:
    if creds is None or not creds.credentials:
        raise HTTPException(401, "Access token required")
    return identity.user_from_token(creds.credentials)
```

Any route that wants a logged-in user writes `user: dict = Depends(current_user)`
and gets one. FastAPI runs the guard first and the route body never starts if it
raises. `/protected/dashboard` exists purely to prove that adding a second locked
route is one line, not a second copy of the check — and a copy is exactly how a
route ends up accidentally unprotected six months later.

`HTTPBearer(auto_error=False)` is deliberate: with the default, FastAPI rejects a
missing header itself and answers `{"detail": ...}`. Turning it off lets the
header reach my code so every error in this API has the same `{"error": ...}` shape.

The test that matters most fires six broken headers at both protected routes —
no header, empty header, a token with no `Bearer ` prefix, `Bearer` with nothing
after it, the wrong scheme, and a valid token with **one character changed**. All
six must be 401.

## Two things to watch when you wire up real Supabase

**Email confirmation.** A new project may require confirming the address before
`sign_in_with_password` works, so Stage 1 can fail with the right password. Check
the Auth settings before blaming the code.

**`sign_out`.** The brief writes `signOut(token)`, but the SDK's `sign_out()`
ends the client's *own* session — it does not take someone else's token and
revoke it. Killing another session server-side goes through the admin API with
the service-role key, which is not the anon key and must never reach a browser.
