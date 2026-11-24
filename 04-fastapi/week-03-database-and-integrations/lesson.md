# Week 3: Databases, dependency injection, and integration skills

Goal: persist data, structure an app with dependency injection, and learn the day-to-day FDE toolkit: calling other people's APIs reliably, receiving their webhooks safely, and taming messy customer data. This is the heaviest week; budget ~8 hours (A: 2.5h, B: 2h, C: 1.5h, D: 1.5h, review: 0.5h).

## A. SQLModel + SQLite

SQLModel = Pydantic + SQLAlchemy. One class can be a table.
```python
from sqlmodel import SQLModel, Field, Session, create_engine, select

class Contact(SQLModel, table=True):                  # table=True -> a real DB table "contact"
    id: int | None = Field(default=None, primary_key=True)
    name: str
    email: str = Field(unique=True, index=True)
    company: str | None = None

engine = create_engine("sqlite:///app.db")
SQLModel.metadata.create_all(engine)                  # creates missing tables (no migrations!)

with Session(engine) as session:
    c = Contact(name="Ada", email="ada@x.co")
    session.add(c); session.commit(); session.refresh(c)      # refresh loads the generated id
    session.get(Contact, 1)                                    # by primary key, or None
    session.exec(select(Contact).where(Contact.company == "Acme").order_by(Contact.id).limit(10)).all()
    c.company = "New"; session.add(c); session.commit()        # update
    session.delete(c); session.commit()                        # delete
```
- **Table model vs API schemas**: a `table=True` class is not validated on construction. Keep separate non-table classes (`ContactCreate`, `ContactUpdate`, `ContactRead`) for request/response, exactly as in week 2.
- A failed `commit()` leaves the session unusable until `session.rollback()`.
- `IntegrityError` (from `sqlalchemy.exc`) is how unique-constraint violations arrive -> translate to 409.
- **In-memory SQLite in tests**: each new connection to `sqlite://` is a fresh empty DB. Use `poolclass=StaticPool` and `check_same_thread=False` so every session shares one connection. A file URL (`sqlite:///app.db`, `tmp_path` in tests) needs only `check_same_thread=False`.
- `create_all` only creates *missing tables*; it never alters existing ones. Real projects use Alembic for migrations (read about it; not needed yet).

## Dependency injection
```python
def get_session():
    with Session(engine) as session:
        yield session                      # code after yield runs after the response (cleanup)

@app.get("/contacts/{id}")
def get(id: int, session: Session = Depends(get_session)): ...
```
FastAPI calls `get_session` per request and hands the result to your route. Why bother? **Tests replace it**:
```python
app.dependency_overrides[get_session] = lambda_or_function_returning_test_session
```
Same trick swaps a real `httpx.Client` for one wired to `httpx.MockTransport`. Dependencies can depend on other dependencies. Clean overrides after each test (`app.dependency_overrides.clear()`).

## B. Calling other APIs with httpx
```python
client = httpx.Client(base_url="https://api.partner.com", timeout=httpx.Timeout(5.0),
                      headers={"Authorization": "Bearer ..."})
r = client.get("/companies/acme.com", params={"x": 1})
r.status_code; r.json(); r.raise_for_status()      # raises httpx.HTTPStatusError on 4xx/5xx
```
Rules of thumb for integrations:
1. **Always set timeouts.** A hung partner must not hang you.
2. **Retry only what is safe to retry**: network errors, timeouts, 429, 5xx on idempotent calls (GET, or POST with an idempotency key). Never retry 400/401/403/404; they won't fix themselves.
3. **Exponential backoff** (0.5s, 1s, 2s...) with a cap; add jitter in production. Honour `Retry-After` on 429s when present.
4. **Translate failures** into your own exception (`UpstreamError`) and a clear API answer: 502 Bad Gateway / 504 Gateway Timeout for "our dependency is broken", not a 500 stack trace.
5. **Reuse clients** (connection pooling); create them in a dependency or at startup.

**Testing without network**: `httpx.MockTransport(handler)` where `handler(request) -> httpx.Response`. Raise `httpx.ConnectError("...")` / `httpx.ReadTimeout("...")` inside the handler to simulate failures. Inject `sleep` as a parameter so tests don't actually wait.

Async note: `httpx.AsyncClient` + `async def` routes is the same API with `await`. Use it when one request fans out to many calls (e.g. 20 LLM or API calls in parallel with `asyncio.gather`). The sync client is simpler; start there.

## C. Receiving webhooks
A webhook = the other system POSTs to *your* URL when something happens. Properties you must design for:
- **Verify authenticity**: the sender signs the *raw bytes* of the body with a shared secret (HMAC-SHA256) and sends the signature in a header. Recompute it over `await request.body()` (not over re-serialised JSON, which changes bytes!) and compare with `hmac.compare_digest`.
- **Idempotency**: senders retry, so the same event id arrives twice. Track processed ids (a DB table with a unique constraint in real life) and do nothing the second time.
- **Respond fast** (2xx within a few seconds) and do heavy work afterwards (background task/queue), otherwise the sender retries and floods you.
- **Be strict about 4xx vs 2xx**: bad signature 401; malformed 400; accepted 2xx. A 5xx makes the sender retry later, which is what you want for transient failures only.
- Out-of-order delivery happens; use event timestamps/versions if order matters.

## D. Cleaning messy CSV/JSON
Customer data is never clean. Pattern: **parse -> normalise -> validate -> split into good rows and rejected rows with reasons**. Never silently drop data; return the rejects so a human can fix them.
```python
reader = csv.DictReader(io.StringIO(text))     # first row = headers; each row = dict
```
Normalise headers (`\ufeff` at file start from Excel), blank rows, missing cells (`None` from short rows), duplicates (decide: first wins), phone formats (E.164). For nested JSON from vendors, write a safe accessor (`get_path(doc, "a.b.0.c", default)`) instead of chains of `[...]` that raise `KeyError`.

## Common mistakes
- In-memory SQLite without `StaticPool`: "no such table" in tests.
- Forgetting `session.refresh()` then returning an object with `id=None`.
- Not rolling back after `IntegrityError` -> every later query fails.
- Building the dependency's resource at import time so tests can't swap it; resolve `engine` when the function runs.
- Retrying non-idempotent or permanently failing calls; retrying without a limit; sleeping in tests.
- No timeout on `httpx` calls (or `timeout=None`).
- Verifying webhook signatures with `==` (timing attack) or over parsed-then-dumped JSON.
- Returning 500 when a partner is down; clients can't tell your bug from theirs.
- Dropping bad CSV rows silently; or crashing the whole import on the first bad row.

## Your task
1. Work through the code snippets in a scratch file (use a tmp SQLite file, delete it after).
2. Complete `exercises.py` in order (A, B, C, D). Run `../../.venv/bin/pytest -q` after each section; the file is organised so each section's tests pass independently.
3. Stretch: add `created_at` to `Contact` and a `?q=` search on name; write a test that proves a retry wrapper never sleeps after the final attempt.
