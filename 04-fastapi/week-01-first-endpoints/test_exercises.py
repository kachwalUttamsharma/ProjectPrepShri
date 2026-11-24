import pytest
from fastapi.testclient import TestClient

from exercises import *
import exercises


@pytest.fixture(autouse=True)
def _clean():
    exercises.reset_state()
    yield
    exercises.reset_state()


@pytest.fixture
def client():
    return TestClient(exercises.app)


def test_app_metadata(client):
    info = client.get("/openapi.json").json()["info"]
    assert info["title"] == "Week 1 API"
    assert info["version"] == "0.1.0"
    assert client.get("/docs").status_code == 200


def test_status_category():
    assert status_category(200) == "success"
    assert status_category(204) == "success"
    assert status_category(301) == "redirect"
    assert status_category(404) == "client error"
    assert status_category(503) == "server error"
    assert status_category(101) == "informational"
    with pytest.raises(ValueError):
        status_category(99)
    with pytest.raises(ValueError):
        status_category(600)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_hello(client):
    assert client.get("/hello/Sam").json() == {"message": "Hello, Sam!"}
    assert client.get("/hello/Sam?shout=true").json() == {"message": "HELLO, SAM!"}
    assert client.get("/hello/Sam?shout=false").json() == {"message": "Hello, Sam!"}
    assert client.get("/hello/Sam?shout=maybe").status_code == 422


def test_get_fruit(client):
    assert client.get("/fruits/0").json() == {"index": 0, "name": "apple"}
    assert client.get("/fruits/2").json()["name"] == "banana"
    r = client.get("/fruits/99")
    assert r.status_code == 404
    assert r.json() == {"detail": "Fruit not found"}
    assert client.get("/fruits/-1").status_code == 404
    assert client.get("/fruits/abc").status_code == 422


def test_add(client):
    assert client.get("/add", params={"a": 2, "b": 3}).json() == {"result": 5}
    assert client.get("/add", params={"a": -2, "b": 1}).json() == {"result": -1}
    assert client.get("/add", params={"a": 1}).status_code == 422
    assert client.get("/add", params={"a": 1, "b": "x"}).status_code == 422


def test_search_filters_and_paginates(client):
    r = client.get("/search", params={"q": "AP"}).json()
    assert r == {"query": "AP", "count": 3, "results": ["apple", "apricot", "grape"]}
    allr = client.get("/search").json()
    assert allr["count"] == len(FRUITS) and len(allr["results"]) == 9
    page = client.get("/search", params={"limit": 2, "offset": 2}).json()
    assert page["results"] == ["banana", "blueberry"]
    assert page["count"] == 9
    assert client.get("/search", params={"q": "zzz"}).json()["results"] == []


def test_search_validation(client):
    assert client.get("/search", params={"limit": 0}).status_code == 422
    assert client.get("/search", params={"limit": 51}).status_code == 422
    assert client.get("/search", params={"offset": -1}).status_code == 422


def test_notes_crud(client):
    r = client.post("/notes", json={"text": "buy milk"})
    assert r.status_code == 201
    assert r.json() == {"id": 1, "text": "buy milk"}
    r2 = client.post("/notes", json={"text": "call mom"})
    assert r2.json()["id"] == 2
    assert client.get("/notes/1").json() == {"id": 1, "text": "buy milk"}
    d = client.delete("/notes/1")
    assert d.status_code == 204
    assert d.content == b""
    assert client.get("/notes/1").status_code == 404
    assert client.get("/notes/1").json() == {"detail": "Note not found"}
    assert client.delete("/notes/1").status_code == 404


def test_notes_bad_input(client):
    for body in ({}, {"text": ""}, {"text": 5}, {"other": "x"}):
        r = client.post("/notes", json=body)
        assert r.status_code == 400, body
        assert r.json() == {"detail": "text is required"}


def test_teapot(client):
    r = client.get("/teapot")
    assert r.status_code == 418
    assert r.json() == {"detail": "I'm a teapot"}


def test_whoami(client):
    assert client.get("/whoami", headers={"User-Agent": "course/1.0"}).json() == {"user_agent": "course/1.0"}
