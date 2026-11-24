"""Week 1 exercises: first FastAPI endpoints.

Replace each `...` with your code. Routes are marked `# TODO`. The decorators
are given; you write the function bodies (and, where the docstring says so,
adjust the decorator).

Run it by hand to see the docs:
    cd 04-fastapi/week-01-first-endpoints
    ../../.venv/bin/uvicorn exercises:app --reload
then open http://127.0.0.1:8000/docs
"""
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import JSONResponse

# Exercise 1 (TODO): give the app title="Week 1 API" and version="0.1.0".
# Hint: FastAPI(title=..., version=...). These show up in /docs and /openapi.json.
app = FastAPI()

FRUITS = ["apple", "apricot", "banana", "blueberry", "cherry", "cranberry", "date", "fig", "grape"]
NOTES: dict[int, dict] = {}


def reset_state():
    """Provided: tests call this between tests. Do not change."""
    NOTES.clear()


# Exercise 2 -------------------------------------------------------------
def status_category(code):
    """Return the class of an HTTP status code as a string.
    100-199 'informational', 200-299 'success', 300-399 'redirect',
    400-499 'client error', 500-599 'server error'. Anything else: ValueError.
    Hint: code // 100 gives the first digit.
    """
    ...


# Exercise 3 -------------------------------------------------------------
@app.get("/health")
def health():
    """TODO: return {"status": "ok"}. (FastAPI turns the dict into JSON.)"""
    ...


# Exercise 4 -------------------------------------------------------------
@app.get("/hello/{name}")
def hello(name: str, shout: bool = False):
    """TODO: return {"message": "Hello, Sam!"} for name='Sam'.
    If the query parameter ?shout=true is given, the message is uppercased:
    {"message": "HELLO, SAM!"}. Hint: path param = in the route string;
    query param = any other function argument. bool accepts true/false/1/0.
    """
    ...


# Exercise 5 -------------------------------------------------------------
@app.get("/fruits/{index}")
def get_fruit(index: int):
    """TODO: return {"index": index, "name": FRUITS[index]}.
    If index is out of range (negative or too big) respond 404 with
    detail "Fruit not found". Hint: raise HTTPException(status_code=404, detail=...).
    A non-integer index (/fruits/abc) is rejected automatically with 422.
    """
    ...


# Exercise 6 -------------------------------------------------------------
@app.get("/add")
def add(a: int, b: int):
    """TODO: return {"result": a + b} for /add?a=2&b=3.
    Missing or non-integer a/b must give 422 -- you get that for free from the type hints.
    """
    ...


# Exercise 7 -------------------------------------------------------------
@app.get("/search")
def search(q: str = "", limit: int = 10, offset: int = 0):
    """TODO: search FRUITS for names containing q (case-insensitive substring;
    empty q matches all). Return
        {"query": q, "count": <total matches>, "results": <the page>}
    where the page is matches[offset : offset + limit].
    Also change `limit` to be validated: 1 <= limit <= 50 (422 otherwise), and
    offset >= 0. Hint: limit: int = Query(10, ge=1, le=50)
    """
    ...


# Exercise 8 -------------------------------------------------------------
@app.post("/notes")  # TODO: this must answer 201 Created. Hint: status_code=201
def create_note(body: dict):
    """TODO: body looks like {"text": "buy milk"}. If "text" is missing or is not
    a non-empty string, respond 400 with detail "text is required".
    Otherwise store it in NOTES with id = max(existing ids, default=0) + 1 and
    return {"id": id, "text": text}.
    """
    ...


@app.get("/notes/{note_id}")
def get_note(note_id: int):
    """TODO: return {"id": ..., "text": ...} or 404 (detail "Note not found")."""
    ...


@app.delete("/notes/{note_id}")  # TODO: successful delete answers 204 (no body).
def delete_note(note_id: int):
    """TODO: remove the note. 404 (detail "Note not found") if it does not exist.
    A 204 response must have an empty body, so return None.
    """
    ...


# Exercise 9 -------------------------------------------------------------
@app.get("/teapot")
def teapot():
    """TODO: respond with status 418 and JSON body {"detail": "I'm a teapot"}.
    Hint: return JSONResponse(status_code=..., content=...)
    """
    ...


# Exercise 10 ------------------------------------------------------------
@app.get("/whoami")
def whoami(user_agent: str | None = Header(default=None)):
    """TODO: return {"user_agent": <value of the User-Agent request header>}.
    FastAPI converts the argument name user_agent to the header User-Agent.
    """
    ...
