# Week 4: Auth, config, logging, Docker, and the Ticket API project

Goal: make an API something you could hand to a customer: authenticated, configurable, observable, testable, containerised. You finish with a small deployable ticket API. Budget ~7-8 hours: lesson + building blocks (exercises 1-8) ~3h, project (9-14) ~3.5h, review checklist + Docker read-through ~1h.

## 1. Configuration and secrets
Twelve-factor rule: **config lives in environment variables, not in code**. Secrets (API keys, DB passwords, tokens) never go in git.
```python
import os
os.environ["DATABASE_URL"]          # KeyError if missing (good for required values)
os.environ.get("LOG_LEVEL", "INFO") # with a default
```
- Load and validate **once at startup** into a typed `Settings` object; fail fast with a clear error (`ConfigError("API_KEYS is required")`) instead of a mysterious 500 later.
- Take the env as a parameter (`load_settings(os.environ)`) so tests pass a plain dict.
- Commit a `.env.example` with fake values; put the real `.env` in `.gitignore`. Locally: `export API_KEYS=dev-key-1` or `API_KEYS=dev-key-1 uvicorn ...`. In production the platform injects them (Docker `-e`, `--env-file`, Kubernetes secrets, a vault).
- **Never log secrets.** If you must show one, mask it (`*********1234`). Never put them in URLs or error messages.
- Leaked a key? Rotate it first, clean git history second.
- (Libraries like `pydantic-settings` do this declaratively; learn the manual version first.)

## 2. Authentication
- **Authentication (authn)** = who are you? -> failure **401** (+ `WWW-Authenticate` header).
- **Authorization (authz)** = what may you do? -> failure **403**.

**API key** (simplest; machine-to-machine, internal tools, partner integrations): client sends `X-API-Key: <key>`.
```python
from fastapi import Security
from fastapi.security import APIKeyHeader

def require_api_key(key: str | None = Security(APIKeyHeader(name="X-API-Key", auto_error=False))):
    ...  # compare with hmac.compare_digest; raise HTTPException(401) if bad
```
Use `Security(...)` rather than `Header(...)` and `/docs` gets an **Authorize** button for free. Protect a whole group of routes with a router: `APIRouter(dependencies=[Depends(require_api_key)])`.

**Bearer token** (users/sessions): `Authorization: Bearer <token>`. The token carries *who* (subject) and *until when* (expiry), signed so it can't be forged. Real systems: JWTs issued by an identity provider (Auth0, Okta, Cognito, Salesforce) and verified with a library (PyJWT/authlib). Our exercise builds a tiny HMAC-signed token so you understand the mechanics: sign the payload, verify the signature **before** trusting it, check expiry, compare with `hmac.compare_digest`.

Rules: always HTTPS in real deployments; keys are long and random (`secrets.token_urlsafe(32)`); store only hashes of user passwords (argon2/bcrypt); support more than one valid key so you can rotate without downtime; don't reveal *why* auth failed.

## 3. Logging
`print` is not logging. Use the `logging` module:
```python
log = logging.getLogger("ticketapi")
log.info("created ticket %s", ticket_id)       # lazy %-formatting, not f-strings
log.warning("notify failed: %s", err)
log.exception("boom")                           # inside except: logs ERROR + traceback
```
Levels: DEBUG (dev detail) < INFO (normal events) < WARNING (recoverable surprise) < ERROR (request failed) < CRITICAL.
- **Structured (JSON) logs**: one JSON object per line; log platforms can filter by field.
- **Request IDs**: generate (or accept `X-Request-ID`), attach to every log line and echo in the response header. When a customer says "request failed at 14:03", you grep one id and see the whole story. Pass it onward to downstream calls.
- A **middleware** wraps every request: `@app.middleware("http") async def mw(request, call_next): ...`.
- Log decisions and failures, not payloads full of personal data or secrets.

## 4. Testing an app you will deploy
- **App factory**: `create_app(settings)` returns a fresh app and fresh database; each test gets isolation, and production passes settings from env. Avoid import-time side effects (reading env, opening DB files).
- `TestClient(create_app(settings))` for HTTP-level tests; plain function tests for services (pass a `Session` on an in-memory engine).
- Replace outbound calls with `httpx.MockTransport`; assert failures of *their* system don't break *yours*.
- Test the unhappy paths first: no key, bad key, missing id, invalid input, closed ticket.
- `caplog` (pytest fixture) lets you assert on log records; `monkeypatch.setenv` for env vars.
- Layering that made this testable: **routes are thin**, **service functions hold rules**, **domain exceptions** are translated to HTTP in one place.

## 5. Dockerfile basics
A container packages your app plus Python plus dependencies so it runs the same everywhere. You don't need Docker installed for this course; read this so you recognise it on a customer call.
```dockerfile
FROM python:3.14-slim                      # base image: pin the version

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1   # no .pyc files; logs flush immediately
WORKDIR /app

COPY requirements.txt .                    # copy deps first: this layer is cached
RUN pip install --no-cache-dir -r requirements.txt

COPY . .                                   # then your code (changes often)

RUN useradd --create-home appuser          # don't run as root
USER appuser

EXPOSE 8000                                # documentation only; publishing happens at `docker run`
CMD ["uvicorn", "--factory", "main:build_app_from_env", "--host", "0.0.0.0", "--port", "8000"]
```
Notes: bind to `0.0.0.0` inside a container (127.0.0.1 is unreachable from outside). Config comes in at run time, not build time:
```bash
docker build -t ticket-api .
docker run --rm -p 8000:8000 -e API_KEYS=dev-key-1 -e LOG_LEVEL=INFO ticket-api
curl -H "X-API-Key: dev-key-1" localhost:8000/tickets
```
Add a `.dockerignore` (`.venv`, `__pycache__`, `.git`, `.env`, `*.db`) so secrets and junk don't end up in the image. For SQLite in a container, a file path needs a mounted volume (`-v data:/data -e DATABASE_URL=sqlite:////data/app.db`) or the data vanishes when the container stops: another reason real deployments use Postgres. In this course `exercises.py` plays the role of `main.py`; if you split it into modules, update the `CMD` target.

Also know: `--workers N` (several processes; in-memory state is not shared between them!), health checks (`GET /health`), and that the platform (Fly, Render, ECS, Kubernetes) mostly wants: image + port + env vars + a health endpoint.

## 6. Project: Ticket API (support tickets with comments)

**Story.** A customer's support team wants a small internal API: create tickets, comment on them, work them to closed, and get a Slack-style ping when something is urgent. You own it end to end.

### Spec
| Route | Auth | Behaviour |
|---|---|---|
| `GET /health` | none | `{"status": "ok"}` |
| `POST /tickets` | key | body `title` (1-120), `description` (default ""), `priority` low/medium/high (default medium). 201 with the ticket. High priority also notifies `NOTIFY_URL` |
| `GET /tickets` | key | filters `status`, `priority`; `limit` (default `min(20, MAX_PAGE_SIZE)`, 422 if outside 1..MAX_PAGE_SIZE), `offset` >= 0; ordered by id |
| `GET /tickets/{id}` | key | 404 `{"detail": "Ticket not found"}` |
| `PATCH /tickets/{id}` | key | partial update of title/description/priority/status (open, in_progress, closed). A **closed** ticket accepts only `{"status": "open"}` (reopen); anything else -> 409 `Ticket is closed` |
| `DELETE /tickets/{id}` | key | 204; deletes its comments too |
| `POST /tickets/{id}/comments` | key | body `body` (1-1000); 201; 404 if no ticket; 409 if closed |
| `GET /tickets/{id}/comments` | key | ordered by id; 404 if no ticket |
| `GET /stats` | key | `{"open", "in_progress", "closed", "total"}` always all four keys |

Cross-cutting: every request logs one JSON line with a request id (`X-Request-ID` echoed); config only from env vars (`API_KEYS`, `DATABASE_URL`, `LOG_LEVEL`, `MAX_PAGE_SIZE`, `NOTIFY_URL`); a failing notifier must never fail ticket creation; secrets never logged.

### How exercises map to the project
Exercises 1-8 are the reusable building blocks (settings, masking, API key + bearer auth, JSON logs, request-id middleware). Exercises 9-13 are the service layer and notifier. Exercise 14 (`create_app`) wires it all. Do them in order; the tests for 1-13 don't need the app at all.

### Suggested schedule
1. (1h) Read this lesson; do 1-3.
2. (1.5h) 4-8: tokens, bearer dependency, logging, middleware.
3. (1.5h) 9-12: services against an in-memory session.
4. (1h) 13-14: notifier + wiring; all tests green.
5. (1.5h) Stage review below, then run it for real with uvicorn and curl.

### Stage review checklist
Work through it honestly, as if reviewing a colleague's PR before handing the service to a customer. Write down one improvement per stage.

**Stage 1: Contract**
- [ ] Every route in the spec exists with the right method, path, status code.
- [ ] `/docs` reads like documentation: titles, response models, Authorize button works.
- [ ] Error bodies are consistent (`{"detail": ...}`) and the status codes are the right ones (401 vs 403 vs 404 vs 409 vs 422).
- [ ] Response models never expose internal fields.

**Stage 2: Correctness and data**
- [ ] Business rules live in service functions, not scattered in routes.
- [ ] Deleting a ticket leaves no orphan comments; failed requests leave no half-written data (rollback).
- [ ] Pagination bounded; no unbounded `SELECT *` responses.
- [ ] Time handling consistent (timezone-aware UTC).

**Stage 3: Security and config**
- [ ] No secret in code, tests, logs, or git; `.env` ignored; `.env.example` provided.
- [ ] Auth on every route except health; constant-time key comparison; keys rotatable (multiple allowed).
- [ ] App refuses to start with missing/invalid config, with a readable message.
- [ ] Input validated (lengths, enums); no raw SQL string-building.

**Stage 4: Reliability and operations**
- [ ] Outbound calls have timeouts; failures are contained (notifier test proves it).
- [ ] Logs are structured, include request ids, contain no personal data/secrets.
- [ ] `/health` exists and is cheap.
- [ ] Dockerfile: pinned base, deps layer cached, non-root user, config via env, `.dockerignore` present.
- [ ] You know what breaks at scale: in-memory SQLite, multiple workers, no migrations, no rate limiting.

**Stage 5: Tests and hand-off**
- [ ] Unhappy paths tested (auth, 404, 409, 422, upstream down).
- [ ] Tests are offline, isolated, and fast (< a few seconds).
- [ ] A 10-line README-style note: how to run, env vars, example curl calls, known limitations. (Write it in your own notes; practise explaining it to a non-technical customer in two minutes.)

## Common mistakes
- Reading env vars at import time inside library code so tests can't control them (use a factory + settings object).
- Comparing keys with `==`; returning 403 when you mean 401 (or the reverse).
- Logging the Authorization header or the full request body.
- Catching `Exception` around the notifier and hiding bugs; instead catch `httpx.HTTPError`, log, move on.
- `0.0.0.0` vs `127.0.0.1` confusion in containers; copying `.env` into the image.
- Running multiple workers with in-memory SQLite and wondering where the data went.
- Forgetting `--factory` when `uvicorn` is pointed at a function rather than an app object.
- Trusting token payload before verifying its signature.

## Your task
1. Complete `exercises.py` (all 14 exercises) until `../../.venv/bin/pytest -q` is green.
2. Run it for real: `API_KEYS=dev-key-1 ../../.venv/bin/uvicorn --factory exercises:build_app_from_env`, open `/docs`, click Authorize, and create a ticket; then try curl without a key.
3. Do the stage review checklist and write down one improvement per stage.
4. Stretch: add `GET /tickets?q=` text search, a `/me` route protected by your bearer dependency with a `POST /token` that trades an API key for a token, and a Dockerfile in a scratch folder (build it only if you have Docker).
