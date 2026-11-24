from datetime import date

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

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


def make(client, **kw):
    body = {"name": "Mug", "price": 9.5, "quantity": 3, "tags": ["kitchen"]}
    body.update(kw)
    r = client.post("/products", json=body)
    assert r.status_code == 201, r.text
    return r.json()


# ---- models ----
def test_product_create_valid_and_defaults():
    p = ProductCreate(name="Mug", price=2.5)
    assert p.name == "Mug" and p.price == 2.5
    assert p.quantity == 0
    assert p.tags == []
    p.tags.append("x")
    assert ProductCreate(name="a", price=1).tags == []


@pytest.mark.parametrize(
    "kw",
    [
        {"name": "", "price": 1},
        {"name": "x" * 51, "price": 1},
        {"name": "ok", "price": 0},
        {"name": "ok", "price": -3},
        {"name": "ok", "price": 1, "quantity": -1},
        {"name": "ok", "price": "abc"},
        {"price": 1},
    ],
)
def test_product_create_rejects_bad_input(kw):
    with pytest.raises(ValidationError):
        ProductCreate(**kw)


def test_product_read_and_update():
    r = ProductRead(id=3, name="Mug", price=1.0)
    assert r.id == 3 and r.quantity == 0
    with pytest.raises(ValidationError):
        ProductRead(name="Mug", price=1.0)
    u = ProductUpdate()
    assert u.model_dump(exclude_unset=True) == {}
    assert ProductUpdate(price=5).model_dump(exclude_unset=True) == {"price": 5}
    with pytest.raises(ValidationError):
        ProductUpdate(price=0)
    with pytest.raises(ValidationError):
        ProductUpdate(quantity=-1)


def test_customer_normalises():
    c = Customer(name="  Sam  ", email="  Sam@Example.COM ", age=30)
    assert c.name == "Sam"
    assert c.email == "sam@example.com"
    assert Customer(name="A", email="a@b.co").age is None


@pytest.mark.parametrize(
    "kw",
    [
        {"name": "   ", "email": "a@b.co"},
        {"name": "A", "email": "nope"},
        {"name": "A", "email": "a@b"},
        {"name": "A", "email": "a@@b.co"},
        {"name": "A", "email": "a@b.co", "age": 121},
        {"name": "A", "email": "a@b.co", "age": -1},
    ],
)
def test_customer_rejects(kw):
    with pytest.raises(ValidationError):
        Customer(**kw)


def test_date_range():
    r = DateRange(start="2024-01-01", end="2024-01-31")
    assert r.start == date(2024, 1, 1)
    assert r.days == 31
    assert DateRange(start=date(2024, 5, 5), end=date(2024, 5, 5)).days == 1
    with pytest.raises(ValidationError) as e:
        DateRange(start="2024-02-02", end="2024-02-01")
    assert "end" in str(e.value).lower()
    with pytest.raises(ValidationError):
        DateRange(start="not-a-date", end="2024-02-01")


def test_user_models():
    u = UserIn(email=" Bob@Example.com ", password="longenough")
    assert u.email == "bob@example.com"
    with pytest.raises(ValidationError):
        UserIn(email="bob@example.com", password="short")
    with pytest.raises(ValidationError):
        UserIn(email="bob", password="longenough")
    assert set(UserOut.model_fields) == {"id", "email"}
    assert UserOut(id=1, email="a@b.co").model_dump() == {"id": 1, "email": "a@b.co"}


# ---- routes ----
def test_create_product(client):
    r = client.post("/products", json={"name": "Mug", "price": 9.5})
    assert r.status_code == 201
    assert r.json() == {"id": 1, "name": "Mug", "price": 9.5, "quantity": 0, "tags": []}
    assert make(client, name="Cup")["id"] == 2


def test_create_product_validation_error_shape(client):
    r = client.post("/products", json={"name": "Mug", "price": -1})
    assert r.status_code == 422
    assert "price" in r.json()["detail"][0]["loc"]
    assert client.post("/products", json={"name": "Mug"}).status_code == 422


def test_get_product(client):
    make(client)
    assert client.get("/products/1").json()["name"] == "Mug"
    r = client.get("/products/9")
    assert r.status_code == 404
    assert r.json() == {"detail": "Product not found"}


def test_list_products_filters(client):
    make(client, name="A", price=5, tags=["x"])
    make(client, name="B", price=15, tags=["x", "y"])
    make(client, name="C", price=25, tags=["y"])
    names = lambda r: [p["name"] for p in r.json()]
    assert names(client.get("/products")) == ["A", "B", "C"]
    assert names(client.get("/products", params={"min_price": 10})) == ["B", "C"]
    assert names(client.get("/products", params={"max_price": 15})) == ["A", "B"]
    assert names(client.get("/products", params={"tag": "y"})) == ["B", "C"]
    assert names(client.get("/products", params={"tag": "y", "min_price": 20})) == ["C"]
    assert names(client.get("/products", params={"min_price": 15, "max_price": 15})) == ["B"]
    assert client.get("/products", params={"min_price": "abc"}).status_code == 422


def test_patch_product(client):
    make(client, price=10, quantity=4)
    r = client.patch("/products/1", json={"price": 12})
    assert r.status_code == 200
    body = r.json()
    assert body["price"] == 12 and body["quantity"] == 4 and body["name"] == "Mug"
    assert client.patch("/products/1", json={"tags": []}).json()["tags"] == []
    assert client.patch("/products/1", json={}).json()["price"] == 12
    assert client.patch("/products/1", json={"price": 0}).status_code == 422
    assert client.patch("/products/7", json={"price": 1}).status_code == 404
    assert client.get("/products/1").json()["price"] == 12


def test_create_user_hides_password(client):
    r = client.post("/users", json={"email": "Bob@Example.com", "password": "supersecret"})
    assert r.status_code == 201
    assert r.json() == {"id": 1, "email": "bob@example.com"}
    assert "password" not in r.text and "supersecret" not in r.text
    assert "password_hash" not in r.text
    stored = exercises.USERS[1]
    assert stored["password_hash"] != "supersecret" and len(stored["password_hash"]) == 64


def test_create_user_conflict_and_validation(client):
    client.post("/users", json={"email": "a@b.co", "password": "longenough"})
    r = client.post("/users", json={"email": "A@B.co", "password": "otherpass1"})
    assert r.status_code == 409
    assert r.json() == {"detail": "Email already registered"}
    assert client.post("/users", json={"email": "a@c.co", "password": "x"}).status_code == 422


def test_purchase_ok_and_out_of_stock(client):
    make(client, quantity=3)
    r = client.post("/products/1/purchase", params={"qty": 2})
    assert r.status_code == 200
    assert r.json() == {"id": 1, "quantity": 1}
    assert client.post("/products/1/purchase").json() == {"id": 1, "quantity": 0}
    r = client.post("/products/1/purchase", params={"qty": 5})
    assert r.status_code == 409
    assert r.json() == {"error": "out_of_stock", "product_id": 1, "requested": 5, "available": 0}
    assert exercises.PRODUCTS[1]["quantity"] == 0


def test_purchase_errors(client):
    assert client.post("/products/1/purchase").status_code == 404
    make(client)
    assert client.post("/products/1/purchase", params={"qty": 0}).status_code == 422
