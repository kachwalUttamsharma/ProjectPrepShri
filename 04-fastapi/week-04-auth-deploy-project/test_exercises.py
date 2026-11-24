import io
import json
import logging

import httpx
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from exercises import *
import exercises


@pytest.fixture(autouse=True)
def _reset_logger():
    yield
    lg = logging.getLogger("ticketapi")
    for h in list(lg.handlers):
        lg.removeHandler(h)
    lg.setLevel(logging.NOTSET)


# ---------------- 1. settings ----------------
def test_load_settings_defaults():
    s = load_settings({"API_KEYS": "a, b ,,c"})
    assert s.api_keys == frozenset({"a", "b", "c"})
    assert s.database_url == "sqlite://"
    assert s.log_level == "INFO"
    assert s.max_page_size == 100
    assert s.notify_url is None


def test_load_settings_overrides():
    s = load_settings(
        {
            "API_KEYS": "k",
            "DATABASE_URL": "sqlite:///x.db",
            "LOG_LEVEL": "debug",
            "MAX_PAGE_SIZE": "25",
            "NOTIFY_URL": "https://hooks.test/x",
        }
    )
    assert (s.database_url, s.log_level, s.max_page_size, s.notify_url) == (
        "sqlite:///x.db", "DEBUG", 25, "https://hooks.test/x")
    assert load_settings({"API_KEYS": "k", "NOTIFY_URL": ""}).notify_url is None


@pytest.mark.parametrize(
    "env",
    [
        {},
        {"API_KEYS": ""},
        {"API_KEYS": " , "},
        {"API_KEYS": "k", "LOG_LEVEL": "LOUD"},
        {"API_KEYS": "k", "MAX_PAGE_SIZE": "lots"},
        {"API_KEYS": "k", "MAX_PAGE_SIZE": "0"},
    ],
)
def test_load_settings_errors(env):
    with pytest.raises(ConfigError):
        load_settings(env)


def test_mask_secret():
    assert mask_secret("sk-abcdef1234") == "*********1234"
    assert mask_secret("12345") == "*2345"
    assert mask_secret("1234") == "****"
    assert mask_secret("ab") == "****"
    assert mask_secret("") == "****"
    assert mask_secret(None) == "****"


# ---------------- 3. API key ----------------
def keyed_client(keys):
    app = FastAPI()
    dep = make_api_key_dependency(keys)

    @app.get("/secure")
    def secure(key: str = Depends(dep)):
        return {"key": key}

    return TestClient(app)


def test_api_key_dependency():
    c = keyed_client({"k1", "k2"})
    assert c.get("/secure", headers={"X-API-Key": "k2"}).json() == {"key": "k2"}
    r = c.get("/secure")
    assert r.status_code == 401
    assert r.json() == {"detail": "Invalid or missing API key"}
    assert r.headers["www-authenticate"] == "ApiKey"
    assert c.get("/secure", headers={"X-API-Key": "nope"}).status_code == 401
    assert c.get("/secure", headers={"X-API-Key": ""}).status_code == 401
    assert c.get("/secure", headers={"X-API-Key": "k"}).status_code == 401  # prefix of a key


def test_api_key_dependency_shows_in_openapi():
    spec = keyed_client({"k"}).get("/openapi.json").json()
    schemes = spec["components"]["securitySchemes"]
    assert any(s.get("name") == "X-API-Key" for s in schemes.values())


# ---------------- 4/5. tokens ----------------
def test_token_roundtrip():
    t = create_token("s3", "alice", 60, now=1000)
    assert t.count(".") == 1
    assert decode_token("s3", t, now=1030) == "alice"
    assert decode_token("s3", t, now=1059) == "alice"


def test_token_expiry_and_tamper():
    t = create_token("s3", "alice", 60, now=1000)
    with pytest.raises(InvalidToken):
        decode_token("s3", t, now=1060)
    with pytest.raises(InvalidToken):
        decode_token("other-secret", t, now=1010)
    payload, sig = t.split(".")
    other = create_token("s3", "mallory", 60, now=1000).split(".")[0]
    with pytest.raises(InvalidToken):
        decode_token("s3", other + "." + sig, now=1010)
    for junk in ["", "abc", "a.b.c", "a.b", payload + "."]:
        with pytest.raises(InvalidToken):
            decode_token("s3", junk, now=1010)


def test_token_default_now_is_real_time():
    t = create_token("s", "bob", 30)
    assert decode_token("s", t) == "bob"
    with pytest.raises(InvalidToken):
        decode_token("s", create_token("s", "bob", -1))


def test_bearer_dependency():
    app = FastAPI()
    dep = make_bearer_dependency("s3")

    @app.get("/me")
    def me(user: str = Depends(dep)):
        return {"user": user}

    c = TestClient(app)
    good = create_token("s3", "alice", 60)
    assert c.get("/me", headers={"Authorization": f"Bearer {good}"}).json() == {"user": "alice"}
    r = c.get("/me")
    assert r.status_code == 401 and r.json() == {"detail": "Not authenticated"}
    assert r.headers["www-authenticate"] == "Bearer"
    r = c.get("/me", headers={"Authorization": "Bearer garbage"})
    assert r.status_code == 401 and r.json() == {"detail": "Invalid token"}
    expired = create_token("s3", "alice", -5)
    assert c.get("/me", headers={"Authorization": f"Bearer {expired}"}).status_code == 401
    wrong = create_token("zzz", "alice", 60)
    assert c.get("/me", headers={"Authorization": f"Bearer {wrong}"}).status_code == 401


# ---------------- 6/7/8. logging ----------------
def test_json_formatter():
    rec = logging.makeLogRecord({"name": "ticketapi", "levelname": "INFO", "levelno": 20, "msg": "hi %s", "args": ("x",)})
    out = json.loads(JsonFormatter().format(rec))
    assert out == {"level": "INFO", "logger": "ticketapi", "message": "hi x"}
    rec2 = logging.makeLogRecord({"name": "t", "levelname": "WARNING", "levelno": 30, "msg": "m", "request_id": "abc"})
    assert json.loads(JsonFormatter().format(rec2))["request_id"] == "abc"


def test_configure_logging_writes_json_and_is_idempotent():
    buf = io.StringIO()
    lg = configure_logging("INFO", stream=buf)
    lg = configure_logging("INFO", stream=buf)
    assert lg.name == "ticketapi"
    lg.debug("hidden")
    lg.info("shown", extra={"request_id": "r1"})
    try:
        1 / 0
    except ZeroDivisionError:
        lg.exception("boom")
    lines = buf.getvalue().strip().splitlines()
    assert len(lines) == 2  # one handler only, DEBUG filtered
    first, second = (json.loads(x) for x in lines)
    assert first["message"] == "shown" and first["request_id"] == "r1" and first["level"] == "INFO"
    assert second["level"] == "ERROR" and "ZeroDivisionError" in second["exception"]
    assert logging.getLogger("ticketapi").propagate is True


def test_configure_logging_level():
    assert configure_logging("WARNING", stream=io.StringIO()).level == logging.WARNING


def test_request_id_middleware(caplog):
    app = FastAPI()
    add_request_id_middleware(app)

    @app.get("/ping")
    def ping():
        return {"pong": True}

    c = TestClient(app)
    with caplog.at_level(logging.INFO, logger="ticketapi"):
        r = c.get("/ping")
        r2 = c.get("/ping", headers={"X-Request-ID": "req-123"})
        c.get("/missing")
    assert r.json() == {"pong": True}
    assert len(r.headers["x-request-id"]) >= 16
    assert r.headers["x-request-id"] != c.get("/ping").headers["x-request-id"]
    assert r2.headers["x-request-id"] == "req-123"
    msgs = [rec.getMessage() for rec in caplog.records if rec.name == "ticketapi"]
    assert "GET /ping -> 200" in msgs
    assert "GET /missing -> 404" in msgs
    assert any(getattr(rec, "request_id", None) == "req-123" for rec in caplog.records)


# ---------------- services ----------------
@pytest.fixture
def session():
    eng = make_engine("sqlite://")
    with Session(eng) as s:
        yield s


def mk(session, title="T", priority="medium", description=""):
    return create_ticket(session, TicketCreate(title=title, priority=priority, description=description))


def test_create_ticket(session):
    t = mk(session, "Printer broken", "high", "paper jam")
    assert t.id == 1 and t.status == "open" and t.priority == "high"
    assert t.description == "paper jam" and t.created_at is not None
    assert mk(session).id == 2


def test_list_tickets_filters_and_paging(session):
    mk(session, "a", "low")
    mk(session, "b", "high")
    mk(session, "c", "high")
    update_ticket(session, 2, TicketUpdate(status="closed"))
    ids = lambda **kw: [t.id for t in list_tickets(session, **kw)]
    assert ids() == [1, 2, 3]
    assert ids(priority="high") == [2, 3]
    assert ids(status="closed") == [2]
    assert ids(status="open", priority="high") == [3]
    assert ids(limit=1, offset=1) == [2]
    assert ids(offset=5) == []


def test_update_ticket_partial_and_missing(session):
    mk(session, "Old", "low", "d")
    t = update_ticket(session, 1, TicketUpdate(title="New"))
    assert (t.title, t.priority, t.description, t.status) == ("New", "low", "d", "open")
    t = update_ticket(session, 1, TicketUpdate(status="in_progress", priority="high"))
    assert (t.status, t.priority) == ("in_progress", "high")
    with pytest.raises(NotFound):
        update_ticket(session, 99, TicketUpdate(title="x"))


def test_closed_tickets_can_only_be_reopened(session):
    mk(session)
    update_ticket(session, 1, TicketUpdate(status="closed"))
    with pytest.raises(TicketClosed):
        update_ticket(session, 1, TicketUpdate(title="edit"))
    with pytest.raises(TicketClosed):
        update_ticket(session, 1, TicketUpdate())
    with pytest.raises(TicketClosed):
        update_ticket(session, 1, TicketUpdate(status="open", title="x"))
    assert update_ticket(session, 1, TicketUpdate(status="open")).status == "open"


def test_delete_ticket_removes_comments(session):
    mk(session)
    add_comment(session, 1, CommentCreate(body="hello"))
    delete_ticket(session, 1)
    assert list_tickets(session) == []
    assert session.exec(select(Comment)).all() == []
    with pytest.raises(NotFound):
        delete_ticket(session, 1)


def test_comments(session):
    mk(session)
    c1 = add_comment(session, 1, CommentCreate(body="first"))
    add_comment(session, 1, CommentCreate(body="second"))
    assert c1.id == 1 and c1.ticket_id == 1
    assert [c.body for c in list_comments(session, 1)] == ["first", "second"]
    with pytest.raises(NotFound):
        add_comment(session, 9, CommentCreate(body="x"))
    with pytest.raises(NotFound):
        list_comments(session, 9)
    update_ticket(session, 1, TicketUpdate(status="closed"))
    with pytest.raises(TicketClosed):
        add_comment(session, 1, CommentCreate(body="late"))
    assert len(list_comments(session, 1)) == 2  # reading still allowed


def test_ticket_stats(session):
    assert ticket_stats(session) == {"open": 0, "in_progress": 0, "closed": 0, "total": 0}
    mk(session); mk(session); mk(session)
    update_ticket(session, 2, TicketUpdate(status="in_progress"))
    update_ticket(session, 3, TicketUpdate(status="closed"))
    mk(session)
    assert ticket_stats(session) == {"open": 2, "in_progress": 1, "closed": 1, "total": 4}


# ---------------- notifier ----------------
def notifier(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_notify_sends_for_high_priority_only(session):
    seen = []

    def h(request):
        seen.append((str(request.url), json.loads(request.content)))
        return httpx.Response(200)

    c = notifier(h)
    hi = mk(session, "Server down", "high")
    assert notify_high_priority(c, "https://hooks.test/n", hi) is True
    assert seen == [("https://hooks.test/n", {"text": "[HIGH] #1: Server down"})]
    assert notify_high_priority(c, "https://hooks.test/n", mk(session, "meh", "low")) is False
    assert notify_high_priority(c, None, hi) is False
    assert notify_high_priority(c, "", hi) is False
    assert notify_high_priority(None, "https://hooks.test/n", hi) is False
    assert len(seen) == 1


def test_notify_never_raises(session, caplog):
    hi = mk(session, "x", "high")
    with caplog.at_level(logging.WARNING, logger="ticketapi"):
        assert notify_high_priority(notifier(lambda r: httpx.Response(500)), "https://h.test", hi) is False
        def boom(request):
            raise httpx.ConnectError("down")
        assert notify_high_priority(notifier(boom), "https://h.test", hi) is False
        def slow(request):
            raise httpx.ReadTimeout("slow")
        assert notify_high_priority(notifier(slow), "https://h.test", hi) is False
    assert len([r for r in caplog.records if r.levelno == logging.WARNING]) == 3


# ---------------- the app ----------------
KEY = {"X-API-Key": "k1"}


def make_client(notifier_client=None, **kw):
    settings = Settings(api_keys=frozenset({"k1", "k2"}), max_page_size=5, **kw)
    return TestClient(create_app(settings, notifier_client))


def post(c, title="T", **kw):
    r = c.post("/tickets", json={"title": title, **kw}, headers=KEY)
    assert r.status_code == 201, r.text
    return r.json()


def test_health_is_public():
    assert make_client().get("/health").json() == {"status": "ok"}


@pytest.mark.parametrize(
    "method,path",
    [("GET", "/tickets"), ("POST", "/tickets"), ("GET", "/tickets/1"), ("PATCH", "/tickets/1"),
     ("DELETE", "/tickets/1"), ("GET", "/tickets/1/comments"), ("POST", "/tickets/1/comments"), ("GET", "/stats")],
)
def test_routes_require_api_key(method, path):
    c = make_client()
    assert c.request(method, path, json={}).status_code == 401
    assert c.request(method, path, json={}, headers={"X-API-Key": "wrong"}).status_code == 401


def test_second_key_works():
    assert make_client().get("/tickets", headers={"X-API-Key": "k2"}).status_code == 200


def test_apps_are_isolated():
    a, b = make_client(), make_client()
    post(a)
    assert b.get("/tickets", headers=KEY).json() == []


def test_create_and_get_ticket():
    c = make_client()
    t = post(c, "Printer", description="jam", priority="high")
    assert t["id"] == 1 and t["status"] == "open" and t["priority"] == "high"
    assert set(t) == {"id", "title", "description", "priority", "status", "created_at"}
    assert c.get("/tickets/1", headers=KEY).json() == t
    r = c.get("/tickets/9", headers=KEY)
    assert r.status_code == 404 and r.json() == {"detail": "Ticket not found"}


def test_create_validation():
    c = make_client()
    for body in ({}, {"title": ""}, {"title": "x" * 121}, {"title": "ok", "priority": "urgent"}):
        assert c.post("/tickets", json=body, headers=KEY).status_code == 422, body


def test_list_filters_and_page_limits():
    c = make_client()
    for i in range(4):
        post(c, f"t{i}", priority="high" if i % 2 else "low")
    c.patch("/tickets/1", json={"status": "closed"}, headers=KEY)
    ids = lambda **p: [t["id"] for t in c.get("/tickets", params=p, headers=KEY).json()]
    assert ids() == [1, 2, 3, 4]
    assert ids(priority="high") == [2, 4]
    assert ids(status="closed") == [1]
    assert ids(limit=2, offset=2) == [3, 4]
    assert c.get("/tickets", params={"limit": 5}, headers=KEY).status_code == 200
    assert c.get("/tickets", params={"limit": 6}, headers=KEY).status_code == 422
    assert c.get("/tickets", params={"limit": 0}, headers=KEY).status_code == 422
    assert c.get("/tickets", params={"status": "weird"}, headers=KEY).status_code == 422
    assert c.get("/tickets", params={"offset": -1}, headers=KEY).status_code == 422


def test_patch_and_closed_rules():
    c = make_client()
    post(c)
    r = c.patch("/tickets/1", json={"title": "New", "status": "in_progress"}, headers=KEY)
    assert r.status_code == 200 and r.json()["title"] == "New" and r.json()["status"] == "in_progress"
    assert c.patch("/tickets/1", json={"status": "bogus"}, headers=KEY).status_code == 422
    assert c.patch("/tickets/5", json={"title": "x"}, headers=KEY).status_code == 404
    c.patch("/tickets/1", json={"status": "closed"}, headers=KEY)
    r = c.patch("/tickets/1", json={"title": "again"}, headers=KEY)
    assert r.status_code == 409 and r.json() == {"detail": "Ticket is closed"}
    assert c.patch("/tickets/1", json={"status": "open"}, headers=KEY).json()["status"] == "open"


def test_delete_ticket():
    c = make_client()
    post(c)
    c.post("/tickets/1/comments", json={"body": "hi"}, headers=KEY)
    r = c.delete("/tickets/1", headers=KEY)
    assert r.status_code == 204 and r.content == b""
    assert c.get("/tickets/1", headers=KEY).status_code == 404
    assert c.delete("/tickets/1", headers=KEY).status_code == 404


def test_comments_api():
    c = make_client()
    post(c)
    r = c.post("/tickets/1/comments", json={"body": "looking into it"}, headers=KEY)
    assert r.status_code == 201
    assert r.json()["body"] == "looking into it" and r.json()["ticket_id"] == 1 and r.json()["id"] == 1
    c.post("/tickets/1/comments", json={"body": "fixed"}, headers=KEY)
    got = c.get("/tickets/1/comments", headers=KEY).json()
    assert [x["body"] for x in got] == ["looking into it", "fixed"]
    assert c.post("/tickets/1/comments", json={"body": ""}, headers=KEY).status_code == 422
    assert c.post("/tickets/7/comments", json={"body": "x"}, headers=KEY).status_code == 404
    assert c.get("/tickets/7/comments", headers=KEY).status_code == 404
    c.patch("/tickets/1", json={"status": "closed"}, headers=KEY)
    assert c.post("/tickets/1/comments", json={"body": "late"}, headers=KEY).status_code == 409


def test_stats_endpoint():
    c = make_client()
    assert c.get("/stats", headers=KEY).json() == {"open": 0, "in_progress": 0, "closed": 0, "total": 0}
    post(c); post(c)
    c.patch("/tickets/2", json={"status": "closed"}, headers=KEY)
    assert c.get("/stats", headers=KEY).json() == {"open": 1, "in_progress": 0, "closed": 1, "total": 2}


def test_high_priority_triggers_notification_and_failures_do_not_break():
    seen = []

    def h(request):
        seen.append(json.loads(request.content))
        return httpx.Response(200)

    c = make_client(notifier(h), notify_url="https://hooks.test/n")
    post(c, "Low one", priority="low")
    assert seen == []
    post(c, "Prod down", priority="high")
    assert seen == [{"text": "[HIGH] #2: Prod down"}]

    def broken(request):
        raise httpx.ConnectError("chat is down")

    c2 = make_client(notifier(broken), notify_url="https://hooks.test/n")
    assert post(c2, "Still saved", priority="high")["id"] == 1
    assert len(c2.get("/tickets", headers=KEY).json()) == 1


def test_no_notify_url_means_no_call():
    called = []
    c = make_client(notifier(lambda r: called.append(r) or httpx.Response(200)))
    post(c, "x", priority="high")
    assert called == []


def test_build_app_from_env(monkeypatch):
    monkeypatch.setenv("API_KEYS", "envkey")
    c = TestClient(exercises.build_app_from_env())
    assert c.get("/tickets", headers={"X-API-Key": "envkey"}).status_code == 200
    assert c.get("/tickets", headers=KEY).status_code == 401
    monkeypatch.delenv("API_KEYS")
    with pytest.raises(ConfigError):
        exercises.build_app_from_env()
