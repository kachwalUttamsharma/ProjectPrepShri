# Week 1: First endpoints

Goal: by the end you can stand up a small HTTP API, call it with a browser/curl/tests, and read the auto-generated docs. Budget ~7-8 hours: lesson + experiments (2h), exercises (4h), poking at `/docs` and curl (1-2h).

## 1. HTTP in five minutes
A request = **method + URL + headers + optional body**. A response = **status code + headers + body**.

| Method | Meaning | Typical status |
|---|---|---|
| GET | read, no side effects | 200 |
| POST | create / trigger an action | 201 (created), 200 |
| PUT / PATCH | replace / partially update | 200 |
| DELETE | remove | 204 (no body) |

Status classes: `2xx` success, `3xx` redirect, `4xx` **you** (the client) did something wrong, `5xx` **we** (the server) broke. Remember: 400 bad input, 401 not authenticated, 403 not allowed, 404 not found, 409 conflict, 422 validation failed, 429 slow down, 502/503/504 upstream trouble.

JSON is the body format: `{"name": "Sam", "tags": ["a", "b"]}`. Python dict/list/str/int/float/bool/None map to JSON object/array/string/number/true/null.

```bash
curl -i http://127.0.0.1:8000/health                       # -i shows status + headers
curl -X POST http://127.0.0.1:8000/notes -H "Content-Type: application/json" -d '{"text":"hi"}'
```

## 2. Hello FastAPI
```python
from fastapi import FastAPI

app = FastAPI(title="My API", version="0.1.0")

@app.get("/health")            # decorator: "GET /health runs this function"
def health():
    return {"status": "ok"}    # dict -> JSON, status 200
```
Run it (from the folder containing the file; `exercises:app` = module `exercises`, variable `app`):
```bash
../../.venv/bin/uvicorn exercises:app --reload     # --reload restarts on save
```
Open `http://127.0.0.1:8000/docs` (Swagger UI: try requests in the browser) and `/redoc`. The raw machine-readable spec is `/openapi.json`, built from your type hints. In a real job this is how you hand an integration partner a contract.

## 3. Path and query parameters
```python
@app.get("/users/{user_id}")                 # path parameter: part of the URL
def get_user(user_id: int): ...              # type hint -> converted + validated

@app.get("/search")
def search(q: str = "", limit: int = 10): ...   # not in path = query parameter (?q=x&limit=5)
```
- Has a default -> optional. No default -> required.
- Wrong type (`/users/abc`) -> FastAPI returns **422** automatically with details.
- Extra validation: `limit: int = Query(10, ge=1, le=50)`.
- Headers: `ua: str | None = Header(default=None)` (underscores become hyphens).
- Request body (JSON): a parameter typed `dict` (week 2 replaces this with Pydantic models).

## 4. Status codes and errors
```python
from fastapi import HTTPException
from fastapi.responses import JSONResponse

@app.post("/things", status_code=201)         # success code for this route
def create(): ...

raise HTTPException(status_code=404, detail="Thing not found")   # -> {"detail": "Thing not found"}
return JSONResponse(status_code=418, content={"detail": "teapot"})  # full control
```
A 204 must have an empty body: `return None` is fine with `status_code=204`.

## 5. Testing without a server
```python
from fastapi.testclient import TestClient
client = TestClient(app)
r = client.get("/hello/Sam", params={"shout": True})
assert r.status_code == 200 and r.json() == {"message": "HELLO, SAM!"}
```
No port, no network. You will test every route this way for the whole module.

## 6. Sync vs async (just so you recognise it)
`def` routes run in a threadpool; `async def` routes run on the event loop and must never block. You'll use plain `def` for now; `async def` appears when we use async clients later. Rule of thumb: if unsure, use `def`.

## Common mistakes
- Running `uvicorn` from the wrong folder: `Error loading ASGI app`. `cd` into the folder with `exercises.py` first.
- Forgetting the decorator or typo in the path: 404 for a route you "wrote".
- Route order: `/items/me` must be declared **before** `/items/{id}` or `{id}` swallows it.
- Returning a Python object FastAPI can't serialise (sets, custom classes).
- Setting the wrong status code: creating = 201, deleting = 204; 200 with `{"error": ...}` hides failures from clients.
- Using `return HTTPException(...)` instead of `raise`.
- Mutable global state (our `NOTES` dict) is fine for learning, but it vanishes on restart and is not shared across worker processes. Week 3 fixes this with a database.

## Your task
1. Read sections 1-5 and replay each snippet in a scratch file with `uvicorn`, curl and `/docs`.
2. Fill in `exercises.py` top to bottom. Run `../../.venv/bin/pytest -q` in this folder (see PROGRESS.md for the usual workflow).
3. Stretch: start the server, then create/read/delete a note with curl only. Read `/openapi.json` and find where your `limit` bounds appear.
