import hashlib
import hmac
import json

import httpx
import pytest
import sqlalchemy
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from exercises import *
import exercises


# ---------------- fixtures ----------------
@pytest.fixture(autouse=True)
def _clean():
    exercises.reset_state()
    yield
    exercises.reset_state()
    exercises.app.dependency_overrides.clear()


@pytest.fixture
def db_engine():
    return exercises.make_engine("sqlite://")


@pytest.fixture
def client(db_engine):
    def override():
        with Session(db_engine) as s:
            yield s

    exercises.app.dependency_overrides[exercises.get_session] = override
    return TestClient(exercises.app)


def add(client, name="Ada", email="ada@acme.com", company="Acme"):
    r = client.post("/contacts", json={"name": name, "email": email, "company": company})
    assert r.status_code == 201, r.text
    return r.json()


# ---------------- A. database ----------------
def test_contact_model_and_engine(db_engine):
    assert {"id", "name", "email", "company"} <= set(Contact.model_fields)
    assert "contact" in sqlalchemy.inspect(db_engine).get_table_names()
    with Session(db_engine) as s:
        s.add(Contact(name="A", email="a@x.co"))
        s.commit()
        got = s.get(Contact, 1)
        assert got.name == "A" and got.company is None
        s.add(Contact(name="B", email="a@x.co"))
        with pytest.raises(IntegrityError):
            s.commit()


def test_make_engine_in_memory_is_shared_across_connections():
    eng = make_engine()
    with Session(eng) as s:
        s.add(Contact(name="A", email="a@x.co"))
        s.commit()
    with Session(eng) as s2:  # a second session must still see the table and row
        assert s2.get(Contact, 1).email == "a@x.co"


def test_make_engine_file_persists(tmp_path):
    url = f"sqlite:///{tmp_path}/t.db"
    eng = make_engine(url)
    with Session(eng) as s:
        s.add(Contact(name="A", email="a@x.co"))
        s.commit()
    eng.dispose()
    eng2 = make_engine(url)
    with Session(eng2) as s:
        assert s.get(Contact, 1).name == "A"


def test_get_session_yields_session(monkeypatch, db_engine):
    monkeypatch.setattr(exercises, "engine", db_engine)
    gen = exercises.get_session()
    s = next(gen)
    assert isinstance(s, Session)
    assert s.bind is db_engine
    with pytest.raises(StopIteration):
        next(gen)


def test_create_contact(client):
    r = client.post("/contacts", json={"name": "Ada", "email": "ADA@Acme.com"})
    assert r.status_code == 201
    assert r.json() == {"id": 1, "name": "Ada", "email": "ada@acme.com", "company": None}
    assert add(client, "Bob", "bob@acme.com")["id"] == 2


def test_create_contact_duplicate_and_validation(client):
    add(client)
    r = client.post("/contacts", json={"name": "X", "email": "ADA@acme.com"})
    assert r.status_code == 409
    assert r.json() == {"detail": "Email already exists"}
    assert client.post("/contacts", json={"name": "X"}).status_code == 422
    # session still usable after the failed insert
    assert add(client, "Bob", "bob@acme.com")["id"] == 2


def test_get_contact(client):
    add(client)
    assert client.get("/contacts/1").json()["email"] == "ada@acme.com"
    r = client.get("/contacts/5")
    assert r.status_code == 404 and r.json() == {"detail": "Contact not found"}


def test_list_contacts_filter_and_paging(client):
    for i in range(5):
        add(client, f"N{i}", f"n{i}@x.co", company="A" if i % 2 == 0 else "B")
    allc = client.get("/contacts").json()
    assert [c["id"] for c in allc] == [1, 2, 3, 4, 5]
    assert [c["id"] for c in client.get("/contacts", params={"company": "A"}).json()] == [1, 3, 5]
    assert [c["id"] for c in client.get("/contacts", params={"limit": 2, "offset": 1}).json()] == [2, 3]
    assert client.get("/contacts", params={"company": "Z"}).json() == []
    assert client.get("/contacts", params={"limit": 0}).status_code == 422
    assert client.get("/contacts", params={"limit": 101}).status_code == 422


def test_update_contact(client):
    add(client)
    add(client, "Bob", "bob@acme.com")
    r = client.patch("/contacts/1", json={"company": "NewCo"})
    assert r.status_code == 200
    assert r.json() == {"id": 1, "name": "Ada", "email": "ada@acme.com", "company": "NewCo"}
    assert client.patch("/contacts/1", json={"email": "NEW@acme.com"}).json()["email"] == "new@acme.com"
    assert client.patch("/contacts/1", json={"company": None}).json()["company"] is None
    assert client.patch("/contacts/1", json={"email": "bob@acme.com"}).status_code == 409
    assert client.patch("/contacts/9", json={"name": "x"}).status_code == 404
    assert client.get("/contacts/1").json()["email"] == "new@acme.com"


def test_delete_contact(client):
    add(client)
    r = client.delete("/contacts/1")
    assert r.status_code == 204 and r.content == b""
    assert client.get("/contacts/1").status_code == 404
    r = client.delete("/contacts/1")
    assert r.status_code == 404 and r.json() == {"detail": "Contact not found"}


# ---------------- B. outbound HTTP ----------------
def mock_client(handler, **kw):
    return httpx.Client(base_url="https://up.test", transport=httpx.MockTransport(handler), **kw)


def scripted(*steps):
    """Handler that plays steps in order: an int status, a (status, json) tuple, or an exception."""
    calls = []

    def handler(request):
        step = steps[min(len(calls), len(steps) - 1)]
        calls.append(request)
        if isinstance(step, Exception):
            raise step
        if isinstance(step, tuple):
            return httpx.Response(step[0], json=step[1])
        return httpx.Response(step, json={"n": len(calls)})

    return handler, calls


def test_make_client_config():
    seen = []

    def h(request):
        seen.append(request)
        return httpx.Response(200, json={"ok": True})

    c = make_client("https://api.test", "tok123", timeout=2.5, transport=httpx.MockTransport(h))
    assert c.timeout == httpx.Timeout(2.5)
    assert c.base_url.host == "api.test"
    assert c.get("/things").json() == {"ok": True}
    assert seen[0].url == "https://api.test/things"
    assert seen[0].headers["authorization"] == "Bearer tok123"
    assert seen[0].headers["accept"] == "application/json"


def test_fetch_json_success_first_try():
    h, calls = scripted((200, {"a": 1}))
    sleeps = []
    assert fetch_json(mock_client(h), "/x", sleep=sleeps.append) == {"a": 1}
    assert len(calls) == 1 and sleeps == []


def test_fetch_json_retries_5xx_then_succeeds_with_backoff():
    h, calls = scripted(503, 500, (200, {"ok": 1}))
    sleeps = []
    out = fetch_json(mock_client(h), "/x", retries=3, backoff=0.5, sleep=sleeps.append)
    assert out == {"ok": 1}
    assert len(calls) == 3
    assert sleeps == [0.5, 1.0]


def test_fetch_json_gives_up_after_retries():
    h, calls = scripted(500)
    sleeps = []
    with pytest.raises(UpstreamError) as e:
        fetch_json(mock_client(h), "/x", retries=2, backoff=1, sleep=sleeps.append)
    assert e.value.status_code == 500
    assert len(calls) == 3
    assert sleeps == [1, 2]


def test_fetch_json_no_retry_on_4xx():
    h, calls = scripted(404)
    sleeps = []
    with pytest.raises(UpstreamError) as e:
        fetch_json(mock_client(h), "/x", sleep=sleeps.append)
    assert e.value.status_code == 404
    assert len(calls) == 1 and sleeps == []


def test_fetch_json_retries_429():
    h, calls = scripted(429, (200, {"ok": 1}))
    assert fetch_json(mock_client(h), "/x", sleep=lambda s: None) == {"ok": 1}
    assert len(calls) == 2


def test_fetch_json_retries_network_errors_and_timeouts():
    h, calls = scripted(httpx.ConnectError("boom"), httpx.ReadTimeout("slow"), (200, {"ok": 1}))
    assert fetch_json(mock_client(h), "/x", sleep=lambda s: None) == {"ok": 1}
    assert len(calls) == 3
    h2, calls2 = scripted(httpx.ReadTimeout("slow"))
    with pytest.raises(UpstreamError) as e:
        fetch_json(mock_client(h2), "/x", retries=1, sleep=lambda s: None)
    assert e.value.status_code is None
    assert len(calls2) == 2


def test_fetch_json_zero_retries_and_bad_json():
    h, calls = scripted(500)
    with pytest.raises(UpstreamError):
        fetch_json(mock_client(h), "/x", retries=0, sleep=lambda s: None)
    assert len(calls) == 1

    def bad(request):
        return httpx.Response(200, content=b"<html>not json</html>")

    with pytest.raises(UpstreamError):
        fetch_json(mock_client(bad), "/x", sleep=lambda s: None)


def enrichment_client(client, handler):
    exercises.app.dependency_overrides[exercises.get_http_client] = lambda: mock_client(handler)
    return client


def test_enrichment_happy_path(client):
    add(client, email="ada@acme.com")
    seen = []

    def h(request):
        seen.append(str(request.url))
        return httpx.Response(200, json={"domain": "acme.com", "employees": 120})

    enrichment_client(client, h)
    r = client.get("/contacts/1/enrichment")
    assert r.status_code == 200
    assert r.json() == {
        "contact": {"id": 1, "name": "Ada", "email": "ada@acme.com", "company": "Acme"},
        "company": {"domain": "acme.com", "employees": 120},
    }
    assert seen == ["https://up.test/companies/acme.com"]


def test_enrichment_upstream_404_gives_null_company(client):
    add(client)
    enrichment_client(client, lambda req: httpx.Response(404, json={"error": "nope"}))
    r = client.get("/contacts/1/enrichment")
    assert r.status_code == 200 and r.json()["company"] is None


def test_enrichment_upstream_failure_is_502_after_retries(client):
    add(client)
    h, calls = scripted(503)
    enrichment_client(client, h)
    r = client.get("/contacts/1/enrichment")
    assert r.status_code == 502
    assert r.json() == {"detail": "Enrichment service unavailable"}
    assert len(calls) == 3  # 1 try + 2 retries


def test_enrichment_missing_contact(client):
    h, calls = scripted(200)
    enrichment_client(client, h)
    r = client.get("/contacts/42/enrichment")
    assert r.status_code == 404 and calls == []


# ---------------- C. webhooks ----------------
def sign(body: bytes, secret=exercises.WEBHOOK_SECRET):
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_verify_signature():
    body = b'{"id":"e1"}'
    good = sign(body, "s3cret")
    assert verify_signature("s3cret", body, good) is True
    assert verify_signature("other", body, good) is False
    assert verify_signature("s3cret", body + b" ", good) is False
    assert verify_signature("s3cret", body, good.removeprefix("sha256=")) is False
    assert verify_signature("s3cret", body, "") is False
    assert verify_signature("s3cret", body, "sha256=zzzz") is False


def post_event(client, event, signature="auto"):
    body = json.dumps(event).encode() if not isinstance(event, bytes) else event
    headers = {"Content-Type": "application/json"}
    if signature == "auto":
        headers["X-Signature"] = sign(body)
    elif signature is not None:
        headers["X-Signature"] = signature
    return client.post("/webhooks/payments", content=body, headers=headers)


def test_webhook_accepts_valid_event(client):
    ev = {"id": "evt_1", "type": "payment.succeeded", "amount": 500}
    r = post_event(client, ev)
    assert r.status_code == 202
    assert r.json() == {"status": "accepted"}
    assert exercises.EVENT_LOG == [ev]
    assert "evt_1" in exercises.PROCESSED_EVENTS


def test_webhook_rejects_bad_signature(client):
    ev = {"id": "evt_1", "type": "x"}
    assert post_event(client, ev, signature=None).status_code == 401
    r = post_event(client, ev, signature="sha256=deadbeef")
    assert r.status_code == 401 and r.json() == {"detail": "Invalid signature"}
    assert exercises.EVENT_LOG == []


def test_webhook_is_idempotent(client):
    ev = {"id": "evt_9", "type": "payment.succeeded"}
    assert post_event(client, ev).status_code == 202
    r = post_event(client, ev)
    assert r.status_code == 200
    assert r.json() == {"status": "duplicate"}
    assert len(exercises.EVENT_LOG) == 1


def test_webhook_bad_payloads(client):
    r = post_event(client, b"{not json")
    assert r.status_code == 400 and r.json() == {"detail": "Invalid JSON"}
    for ev in ({"id": "x"}, {"type": "x"}, {"id": 5, "type": "x"}, [1, 2]):
        r = post_event(client, ev)
        assert r.status_code == 400 and r.json() == {"detail": "Malformed event"}, ev
    assert exercises.EVENT_LOG == []


# ---------------- D. messy data ----------------
@pytest.mark.parametrize(
    "raw,expected",
    [
        ("(415) 555-0134", "+14155550134"),
        ("1-415-555-0134", "+14155550134"),
        ("415.555.0134", "+14155550134"),
        ("+1 415 555 0134", "+14155550134"),
        ("555-0134", None),
        ("", None),
        (None, None),
        ("+44 20 7946 0958", None),
        ("call me", None),
        ("2-415-555-0134", None),
    ],
)
def test_clean_phone(raw, expected):
    assert clean_phone(raw) == expected


CSV = """Full Name, E-mail ,Phone Number,Company Name
  Ada   Lovelace ,ADA@Example.com,(415) 555-0134,Analytical Engines
Bob,bob@example,1-415-555-0199,
,carl@example.com,,Acme
Dee,dee@example.com,555-0134,Acme
Ada Again,ada@example.com,,Other
,,,
Eve,eve@example.com
"""


def test_clean_contacts_csv():
    good, bad = clean_contacts_csv(CSV)
    assert good == [
        {"name": "Ada Lovelace", "email": "ada@example.com", "phone": "+14155550134", "company": "Analytical Engines"},
        {"name": "Dee", "email": "dee@example.com", "phone": None, "company": "Acme"},
        {"name": "Eve", "email": "eve@example.com", "phone": None, "company": None},
    ]
    assert bad == [
        {"line": 3, "reason": "invalid email"},
        {"line": 4, "reason": "missing name"},
        {"line": 6, "reason": "duplicate email"},
    ]


def test_clean_contacts_csv_bom_and_other_aliases():
    text = "\ufeffname,Email-Address,organization\nZed,Z@Y.io,Zed Inc\n"
    good, bad = clean_contacts_csv(text)
    assert bad == []
    assert good == [{"name": "Zed", "email": "z@y.io", "phone": None, "company": "Zed Inc"}]


def test_clean_contacts_csv_empty_inputs():
    assert clean_contacts_csv("") == ([], [])
    assert clean_contacts_csv("name,email\n") == ([], [])


DOC = {"a": {"b": [{"c": 1}, {"c": 2}]}, "n": None, "list": [10, 20]}


def test_get_path():
    assert get_path(DOC, "a.b.1.c") == 2
    assert get_path(DOC, "list.0") == 10
    assert get_path(DOC, "a.x.y", "dflt") == "dflt"
    assert get_path(DOC, "a.b.5.c", 0) == 0
    assert get_path(DOC, "a.b.first", "d") == "d"
    assert get_path(DOC, "n.deeper", "d") == "d"
    assert get_path(DOC, "n") is None
    assert get_path(DOC, "") is DOC
    assert get_path(None, "a") is None
    assert get_path("text", "a", "d") == "d"
