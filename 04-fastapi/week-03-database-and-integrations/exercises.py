"""Week 3 exercises: SQLModel + dependency injection, outbound HTTP, webhooks, messy data.

Sections:  A) database + CRUD (ex 1-6)   B) calling other APIs with httpx (ex 7-9)
           C) receiving webhooks (ex 10-11)   D) cleaning messy input (ex 12-14)
Replace each `...` with your code. Everything is tested offline (in-memory SQLite,
httpx.MockTransport) -- no network, no real server needed.
"""
import csv
import hashlib
import hmac
import io
import json
import time

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.pool import StaticPool
from sqlmodel import Field, Session, SQLModel, create_engine, select

app = FastAPI(title="Week 3 API")


# ======================= A. Database ====================================

# Exercise 1 -------------------------------------------------------------
class Contact(SQLModel, table=True):
    """The `contact` table. `id` is given. TODO add:
        name: str
        email: str          -- unique, indexed (Field(unique=True, index=True))
        company: str | None -- optional, default None
    """

    id: int | None = Field(default=None, primary_key=True)


# Plain (non-table) schemas, provided. Tables hold data; these describe the API.
class ContactCreate(SQLModel):
    name: str
    email: str
    company: str | None = None


class ContactUpdate(SQLModel):
    name: str | None = None
    email: str | None = None
    company: str | None = None


class ContactRead(SQLModel):
    id: int
    name: str
    email: str
    company: str | None = None


# Exercise 2 -------------------------------------------------------------
def make_engine(url: str = "sqlite://"):
    """Create an engine, create all tables, return the engine.
    - In-memory SQLite ("sqlite://" or "sqlite:///:memory:"): every new connection would
      get a *separate empty database*, so use connect_args={"check_same_thread": False}
      and poolclass=StaticPool (one shared connection).
    - Any other sqlite URL (a file): just connect_args={"check_same_thread": False}.
    Then SQLModel.metadata.create_all(engine).
    """
    ...


engine = make_engine()  # in-memory by default; week 4 reads DATABASE_URL from the environment


# Exercise 3 -------------------------------------------------------------
def get_session():
    """FastAPI dependency: yield one Session (bound to the module-level `engine`)
    per request and close it afterwards. Hint: `with Session(engine) as session: yield session`.
    Look up `engine` when called (not at definition time) so tests can swap it.
    """
    ...


# Exercise 4 -------------------------------------------------------------
@app.post("/contacts", status_code=201, response_model=ContactRead)
def create_contact(data: ContactCreate, session: Session = Depends(get_session)):
    """TODO: store a Contact (email lowercased). If the email already exists the
    database raises IntegrityError on commit: call session.rollback() and respond
    409 with detail "Email already exists". Refresh and return the contact.
    """
    ...


# Exercise 5 -------------------------------------------------------------
@app.get("/contacts/{contact_id}", response_model=ContactRead)
def get_contact(contact_id: int, session: Session = Depends(get_session)):
    """TODO: session.get(Contact, contact_id) or 404 with detail "Contact not found"."""
    ...


@app.get("/contacts", response_model=list[ContactRead])
def list_contacts(
    company: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
):
    """TODO: contacts ordered by id. If `company` is given keep only exact matches.
    Apply offset/limit. Hint: select(Contact).where(...).order_by(...).offset(..).limit(..)
    then session.exec(statement).all().
    """
    ...


# Exercise 6 -------------------------------------------------------------
@app.patch("/contacts/{contact_id}", response_model=ContactRead)
def update_contact(contact_id: int, changes: ContactUpdate, session: Session = Depends(get_session)):
    """TODO: partial update using changes.model_dump(exclude_unset=True) (lowercase an
    email if present). 404 "Contact not found" if missing; 409 "Email already exists"
    on IntegrityError (rollback first). Hint: contact.sqlmodel_update(data).
    """
    ...


@app.delete("/contacts/{contact_id}", status_code=204)
def delete_contact(contact_id: int, session: Session = Depends(get_session)):
    """TODO: delete the contact (404 "Contact not found" if missing). Return None."""
    ...


# ======================= B. Outbound HTTP ===============================

class UpstreamError(Exception):
    """Provided. Raised when a call to another service ultimately fails.
    status_code is the last HTTP status, or None for network errors/timeouts.
    """

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


# Exercise 7 -------------------------------------------------------------
def make_client(base_url: str, token: str, timeout: float = 5.0, transport=None) -> httpx.Client:
    """Build an httpx.Client for a partner API:
    - base_url=base_url, transport=transport (tests pass httpx.MockTransport; None = real)
    - timeout=httpx.Timeout(timeout)   <- ALWAYS set one; httpx defaults to 5s but be explicit
    - default headers: Authorization: Bearer <token>, Accept: application/json
    """
    ...


# Exercise 8 -------------------------------------------------------------
def fetch_json(client: httpx.Client, url: str, *, retries: int = 3, backoff: float = 0.5, sleep=time.sleep):
    """GET url and return the parsed JSON, retrying transient failures.

    - Total attempts = 1 + retries.
    - Retry on: network errors / timeouts (httpx.TransportError), HTTP 429, HTTP >= 500.
    - Do NOT retry other 4xx: raise UpstreamError(msg, status_code) immediately.
    - Between attempts call sleep(backoff * 2 ** retry_index) -> backoff, 2*backoff, 4*backoff...
      (no sleep after the last attempt). `sleep` is injectable so tests don't wait.
    - When attempts run out raise UpstreamError (status_code = last HTTP status, or None).
    - 2xx whose body isn't valid JSON -> UpstreamError (no retry).
    """
    ...


def get_http_client():
    """Provided dependency: one client per request to the enrichment service."""
    client = make_client("https://enrich.example.com", "demo-token")
    try:
        yield client
    finally:
        client.close()


# Exercise 9 -------------------------------------------------------------
@app.get("/contacts/{contact_id}/enrichment")
def enrich_contact(
    contact_id: int,
    session: Session = Depends(get_session),
    client: httpx.Client = Depends(get_http_client),
):
    """TODO: look up the contact (404 "Contact not found"), take the email's domain
    (part after '@') and call fetch_json(client, f"/companies/{domain}", retries=2, backoff=0).
    Return {"contact": <ContactRead as dict>, "company": <upstream JSON>}.
    - Upstream 404 (UpstreamError.status_code == 404): still 200, "company": None.
    - Any other UpstreamError: 502 with detail "Enrichment service unavailable".
    """
    ...


# ======================= C. Webhooks ====================================

WEBHOOK_SECRET = "whsec_test_secret"
PROCESSED_EVENTS: set[str] = set()
EVENT_LOG: list[dict] = []


def reset_state():
    """Provided: tests call this between tests. Do not change."""
    PROCESSED_EVENTS.clear()
    EVENT_LOG.clear()


# Exercise 10 ------------------------------------------------------------
def verify_signature(secret: str, body: bytes, signature: str) -> bool:
    """The sender signs the RAW body: signature header = "sha256=" + hex(HMAC-SHA256(secret, body)).
    Return True only if `signature` starts with "sha256=" and the hex matches.
    Use hmac.compare_digest (constant-time) -- never ==. Never raise; bad input -> False.
    """
    ...


# Exercise 11 ------------------------------------------------------------
@app.post("/webhooks/payments", status_code=202)
async def payments_webhook(request: Request, x_signature: str | None = Header(default=None)):
    """TODO, in this order:
    1. raw = await request.body(); if the X-Signature header is missing or
       verify_signature(WEBHOOK_SECRET, raw, x_signature) is False -> 401, detail "Invalid signature".
    2. Parse raw as JSON (json.loads). Invalid JSON -> 400 "Invalid JSON".
       Must be an object with string "id" and "type", else 400 "Malformed event".
    3. If the event id is already in PROCESSED_EVENTS (senders retry!) return
       JSONResponse({"status": "duplicate"}, status_code=200) and do nothing else.
    4. Otherwise add the id to PROCESSED_EVENTS, append the event dict to EVENT_LOG,
       and return {"status": "accepted"} (202 comes from the decorator).
    Real handlers do the slow work later (queue/background task) and answer fast.
    """
    ...


# ======================= D. Messy data ==================================

# Exercise 12 ------------------------------------------------------------
def clean_phone(raw) -> str | None:
    """Normalise a US phone number to E.164, or None if it can't be.
    Keep digits only. 10 digits -> "+1" + digits. 11 digits starting with 1 -> "+" + digits.
    Anything else (including None, "", too short, other countries) -> None.
    '(415) 555-0134' -> '+14155550134'; '1-415-555-0134' -> '+14155550134'; '555-0134' -> None
    """
    ...


# Exercise 13 ------------------------------------------------------------
HEADER_ALIASES = {
    "full_name": "name",
    "e_mail": "email",
    "email_address": "email",
    "phone_number": "phone",
    "company_name": "company",
    "organization": "company",
}


def clean_contacts_csv(text: str) -> tuple[list[dict], list[dict]]:
    """Turn a customer's messy CSV export into (good_rows, rejected_rows).

    Headers: strip, lowercase, replace spaces/hyphens with '_', then map through
    HEADER_ALIASES ("Full Name", " E-mail " -> name, email). A leading BOM ("\\ufeff") must not break the first header.
    Rows (use csv.DictReader over io.StringIO; the first data row is line 2):
    - all values blank -> skip silently
    - strip every value (missing cells count as "")
    - name: collapse inner whitespace ("Ada   Lovelace" -> "Ada Lovelace"); empty -> rejected "missing name"
    - email: lowercase; must have exactly one '@' and a '.' after it, else rejected "invalid email"
    - email already seen in an earlier good row -> rejected "duplicate email" (first one wins)
    - good row = {"name", "email", "phone": clean_phone(...), "company": value or None}
    - rejected row = {"line": <line number>, "reason": <one of the strings above>}
    Check name first, then email, then duplicate.
    """
    ...


# Exercise 14 ------------------------------------------------------------
def get_path(data, path: str, default=None):
    """Safely read a nested value from parsed JSON: get_path(d, "a.b.0.c").
    Each dotted part is a dict key, or (for lists) an integer index. Anything
    missing/out-of-range/wrong type along the way -> default. Never raises.
    Empty path returns data itself.
    """
    ...
