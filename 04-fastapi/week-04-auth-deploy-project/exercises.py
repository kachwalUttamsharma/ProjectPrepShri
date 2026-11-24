"""Week 4 exercises: config, auth, logging, then the Ticket API project.

Part 1 (ex 1-8): small, testable building blocks -- settings from env vars, masking
secrets, API-key and bearer-token auth, JSON logging, request-id middleware.
Part 2 (ex 9-14): the project. Service functions (plain Python + a Session), an
outbound notifier, and `create_app(...)` which wires everything into a FastAPI app.
Read lesson.md for the full spec and the stage review checklist.

Replace each `...` with your code. Tests are offline: in-memory SQLite, httpx.MockTransport.
Run the real thing:
    API_KEYS=dev-key-1 ../../.venv/bin/uvicorn --factory exercises:build_app_from_env --reload
"""
import base64
import hashlib
import hmac
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Collection, Literal, Mapping

import httpx
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request, Security
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func
from sqlalchemy.pool import StaticPool
from sqlmodel import Field, Session, SQLModel, create_engine, select

LOGGER_NAME = "ticketapi"


# ======================= Part 1: building blocks ========================

# Exercise 1 -------------------------------------------------------------
class ConfigError(Exception):
    """Provided. Raised when the environment is misconfigured."""


@dataclass(frozen=True)
class Settings:
    """Provided."""

    api_keys: frozenset[str]
    database_url: str = "sqlite://"
    log_level: str = "INFO"
    max_page_size: int = 100
    notify_url: str | None = None


def load_settings(env: Mapping[str, str]) -> Settings:
    """Build Settings from environment variables (pass os.environ, or a dict in tests).
    - API_KEYS: required, comma-separated, whitespace around each key stripped, empty
      entries ignored. No keys at all -> ConfigError("API_KEYS is required").
    - DATABASE_URL: default "sqlite://"
    - LOG_LEVEL: default "INFO"; upper-cased; must be DEBUG/INFO/WARNING/ERROR else ConfigError
    - MAX_PAGE_SIZE: default 100; must be an integer >= 1 else ConfigError
    - NOTIFY_URL: optional; empty or missing -> None
    Fail fast at startup with a clear message instead of crashing on the first request.
    """
    ...


# Exercise 2 -------------------------------------------------------------
def mask_secret(value: str | None) -> str:
    """Safe-to-log version of a secret: keep the last 4 characters, replace the rest
    with '*' (same length). Values of 4 chars or fewer, empty or None -> "****".
    mask_secret("sk-abcdef1234") == "*********1234"
    """
    ...


# Exercise 3 -------------------------------------------------------------
def make_api_key_dependency(valid_keys: Collection[str]):
    """Return a FastAPI dependency function `require_api_key` that reads the X-API-Key
    header and returns the key when valid.
    Missing or unknown key -> HTTPException(401, "Invalid or missing API key",
    headers={"WWW-Authenticate": "ApiKey"}).
    Compare with hmac.compare_digest against every valid key (no early `in` shortcut).
    Hint: inside, define
        def require_api_key(api_key: str | None = Security(APIKeyHeader(name="X-API-Key", auto_error=False))): ...
    and return it. (Security() also puts the scheme into /docs so you get an Authorize button.)
    """
    ...


# Exercise 4 -------------------------------------------------------------
class InvalidToken(Exception):
    """Provided. Bad, tampered, or expired token."""


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def create_token(secret: str, subject: str, ttl_seconds: int, now: float | None = None) -> str:
    """A tiny signed token (the idea behind JWT, minus the standards).
    payload = json {"sub": subject, "exp": int(now + ttl_seconds)}   (now defaults to time.time())
    token   = _b64(payload_json_bytes) + "." + hex(HMAC-SHA256(secret, the _b64 part))
    In real systems use a library (PyJWT) or your identity provider; never invent crypto.
    """
    ...


def decode_token(secret: str, token: str, now: float | None = None) -> str:
    """Return the subject, or raise InvalidToken if: malformed (not exactly two
    dot-separated parts, bad base64/JSON), signature mismatch (compare_digest!),
    or expired (now >= exp). Check the signature BEFORE trusting the payload.
    """
    ...


# Exercise 5 -------------------------------------------------------------
def make_bearer_dependency(secret: str):
    """Return a dependency `current_user` that returns the token's subject.
    - No Authorization header -> 401 "Not authenticated"
    - Header present but decode_token fails -> 401 "Invalid token"
    Both with headers={"WWW-Authenticate": "Bearer"}.
    Hint: def current_user(creds: HTTPAuthorizationCredentials | None = Security(HTTPBearer(auto_error=False))):
    creds.credentials is the token text.
    """
    ...


# Exercise 6 -------------------------------------------------------------
class JsonFormatter(logging.Formatter):
    """One JSON object per log line (what log aggregators like Splunk/Datadog want).
    format(record) -> json string with keys "level" (levelname), "logger" (name),
    "message" (record.getMessage()); plus "request_id" if the record has that attribute
    (set via logger.info(..., extra={"request_id": ...})); plus "exception" (formatted
    traceback text) if record.exc_info is set.
    """

    def format(self, record: logging.LogRecord) -> str:
        ...


# Exercise 7 -------------------------------------------------------------
def configure_logging(level: str = "INFO", stream=None) -> logging.Logger:
    """Configure and return logging.getLogger(LOGGER_NAME): set its level, remove any
    handlers it already has (so calling twice doesn't duplicate lines), add one
    logging.StreamHandler(stream) using JsonFormatter. Leave propagate as True.
    """
    ...


# Exercise 8 -------------------------------------------------------------
def add_request_id_middleware(app: FastAPI) -> None:
    """Register an HTTP middleware on `app` that:
    - takes the request id from the incoming X-Request-ID header or makes uuid.uuid4().hex
    - calls the route, then sets X-Request-ID on the response
    - logs one INFO line to logging.getLogger(LOGGER_NAME) like "GET /tickets -> 200",
      with extra={"request_id": rid}
    Hint: @app.middleware("http") async def mw(request, call_next): response = await call_next(request)
    """
    ...


# ======================= Part 2: Ticket API project =====================

def utcnow() -> datetime:
    return datetime.now(timezone.utc)  # SQLModel's datetime column wants timezone-aware values


class Ticket(SQLModel, table=True):
    """Provided."""

    id: int | None = Field(default=None, primary_key=True)
    title: str
    description: str = ""
    priority: str = "medium"
    status: str = "open"
    created_at: datetime = Field(default_factory=utcnow)


class Comment(SQLModel, table=True):
    """Provided."""

    id: int | None = Field(default=None, primary_key=True)
    ticket_id: int = Field(foreign_key="ticket.id", index=True)
    body: str
    created_at: datetime = Field(default_factory=utcnow)


Priority = Literal["low", "medium", "high"]
Status = Literal["open", "in_progress", "closed"]


class TicketCreate(SQLModel):
    title: str = Field(min_length=1, max_length=120)
    description: str = ""
    priority: Priority = "medium"


class TicketUpdate(SQLModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    priority: Priority | None = None
    status: Status | None = None


class TicketRead(SQLModel):
    id: int
    title: str
    description: str
    priority: str
    status: str
    created_at: datetime


class CommentCreate(SQLModel):
    body: str = Field(min_length=1, max_length=1000)


class CommentRead(SQLModel):
    id: int
    ticket_id: int
    body: str
    created_at: datetime


class NotFound(Exception):
    """Provided. A ticket doesn't exist."""


class TicketClosed(Exception):
    """Provided. The ticket is closed and the operation isn't allowed."""


def make_engine(url: str = "sqlite://"):
    """Provided (same as week 3)."""
    kwargs = {"connect_args": {"check_same_thread": False}}
    if url in ("sqlite://", "sqlite:///:memory:"):
        kwargs["poolclass"] = StaticPool
    engine = create_engine(url, **kwargs)
    SQLModel.metadata.create_all(engine)
    return engine


# Exercise 9 -------------------------------------------------------------
def create_ticket(session: Session, data: TicketCreate) -> Ticket:
    """Insert a Ticket (status "open"), commit, refresh, return it."""
    ...


def list_tickets(
    session: Session,
    *,
    status: str | None = None,
    priority: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[Ticket]:
    """Tickets ordered by id ascending; filter by status/priority when given; then offset/limit."""
    ...


# Exercise 10 ------------------------------------------------------------
def update_ticket(session: Session, ticket_id: int, changes: TicketUpdate) -> Ticket:
    """Partial update (exclude_unset!). NotFound if missing.
    Rule: a closed ticket can only be reopened, i.e. the only accepted change is exactly
    {"status": "open"}; anything else (including an empty change) raises TicketClosed.
    """
    ...


def delete_ticket(session: Session, ticket_id: int) -> None:
    """Delete the ticket AND its comments (foreign key!). NotFound if missing."""
    ...


# Exercise 11 ------------------------------------------------------------
def add_comment(session: Session, ticket_id: int, data: CommentCreate) -> Comment:
    """NotFound if the ticket is missing; TicketClosed if it is closed; else add + return the comment."""
    ...


def list_comments(session: Session, ticket_id: int) -> list[Comment]:
    """NotFound if the ticket is missing; comments ordered by id."""
    ...


# Exercise 12 ------------------------------------------------------------
def ticket_stats(session: Session) -> dict[str, int]:
    """{"open": n, "in_progress": n, "closed": n, "total": n} -- every key always present (0 if none).
    Hint: select(Ticket.status, func.count()).group_by(Ticket.status), or just count in Python first.
    """
    ...


# Exercise 13 ------------------------------------------------------------
def notify_high_priority(client: httpx.Client | None, url: str | None, ticket: Ticket) -> bool:
    """Tell a chat/webhook endpoint about urgent tickets. Returns True if a notification was delivered.
    - client is None, url empty/None, or ticket.priority != "high": return False, make NO request.
    - POST json {"text": "[HIGH] #<id>: <title>"} to url; 2xx -> True.
    - Non-2xx response or any httpx.HTTPError: log a WARNING on the LOGGER_NAME logger and return False.
    It must NEVER raise: a broken chat integration must not break ticket creation.
    """
    ...


# Exercise 14 ------------------------------------------------------------
def create_app(settings: Settings, notifier_client: httpx.Client | None = None) -> FastAPI:
    """App factory: build a fresh app + database from settings (tests make many apps).
    Complete the TODOs. Behaviour spec:
      GET  /health                      public -> {"status": "ok"}
      every other route requires a valid X-API-Key (401 otherwise)
      POST /tickets          201 TicketRead; if priority is high call notify_high_priority(notifier_client, settings.notify_url, ticket)
      GET  /tickets          ?status= &priority= &limit= &offset=0 ; limit defaults to min(20, max_page_size);
                             limit < 1 or > settings.max_page_size -> 422
      GET  /tickets/{id}     TicketRead
      PATCH /tickets/{id}    TicketRead
      DELETE /tickets/{id}   204
      POST /tickets/{id}/comments   201 CommentRead
      GET  /tickets/{id}/comments   list[CommentRead]
      GET  /stats            ticket_stats
      NotFound -> 404 {"detail": "Ticket not found"};  TicketClosed -> 409 {"detail": "Ticket is closed"}
    """
    app = FastAPI(title="Ticket API", version="1.0.0")
    engine = make_engine(settings.database_url)

    def get_session():
        with Session(engine) as session:
            yield session

    # TODO (a): configure logging from settings.log_level and add the request-id middleware.

    # TODO (b): protect the routes. Build require_key = make_api_key_dependency(settings.api_keys)
    # and give the router dependencies=[Depends(require_key)] so every route on it is checked.
    protected = APIRouter()

    # TODO (c): translate domain errors into HTTP responses.
    @app.exception_handler(NotFound)
    async def not_found_handler(request: Request, exc: NotFound):
        ...

    @app.exception_handler(TicketClosed)
    async def ticket_closed_handler(request: Request, exc: TicketClosed):
        ...

    @app.get("/health")
    def health():
        return {"status": "ok"}

    # TODO (d): routes. Keep them thin: parse input -> call a service function -> return.
    @protected.post("/tickets", status_code=201, response_model=TicketRead)
    def post_ticket(data: TicketCreate, session: Session = Depends(get_session)):
        ...

    @protected.get("/tickets", response_model=list[TicketRead])
    def get_tickets(
        status: Status | None = None,
        priority: Priority | None = None,
        limit: int | None = None,
        offset: int = Query(0, ge=0),
        session: Session = Depends(get_session),
    ):
        # limit defaults to min(20, settings.max_page_size); an explicit limit must be
        # 1..settings.max_page_size: raise HTTPException(422, ...) otherwise
        ...

    @protected.get("/tickets/{ticket_id}", response_model=TicketRead)
    def get_ticket(ticket_id: int, session: Session = Depends(get_session)):
        # no service function for a single read: session.get(Ticket, id) or raise NotFound
        ...

    @protected.patch("/tickets/{ticket_id}", response_model=TicketRead)
    def patch_ticket(ticket_id: int, changes: TicketUpdate, session: Session = Depends(get_session)):
        ...

    @protected.delete("/tickets/{ticket_id}", status_code=204)
    def remove_ticket(ticket_id: int, session: Session = Depends(get_session)):
        ...

    @protected.post("/tickets/{ticket_id}/comments", status_code=201, response_model=CommentRead)
    def post_comment(ticket_id: int, data: CommentCreate, session: Session = Depends(get_session)):
        ...

    @protected.get("/tickets/{ticket_id}/comments", response_model=list[CommentRead])
    def get_comments(ticket_id: int, session: Session = Depends(get_session)):
        ...

    @protected.get("/stats")
    def stats(session: Session = Depends(get_session)):
        ...

    app.include_router(protected)
    return app


def build_app_from_env() -> FastAPI:
    """Provided: entry point for uvicorn --factory and Docker."""
    return create_app(load_settings(os.environ))
