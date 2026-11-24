"""Week 2 exercises: Pydantic models, validation, response_model, errors.

Replace each `...` with your code. Part A: models. Part B: routes that use them.
Run by hand:  ../../.venv/bin/uvicorn exercises:app --reload   then open /docs
"""
import hashlib
from datetime import date

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator, model_validator

app = FastAPI(title="Week 2 API")

PRODUCTS: dict[int, dict] = {}
USERS: dict[int, dict] = {}


def reset_state():
    """Provided: tests call this between tests. Do not change."""
    PRODUCTS.clear()
    USERS.clear()


# ======================= Part A: models =================================

# Exercise 1 -------------------------------------------------------------
class ProductCreate(BaseModel):
    """TODO: fields
        name: str, 1..50 characters
        price: float, strictly greater than 0
        quantity: int, >= 0, default 0
        tags: list[str], default empty list
    Hint: Field(min_length=1, max_length=50), Field(gt=0), Field(default=0, ge=0),
    Field(default_factory=list).
    """


# Exercise 2 -------------------------------------------------------------
class ProductRead(ProductCreate):
    """TODO: same as ProductCreate plus `id: int`. (Inheritance keeps it DRY.)"""


class ProductUpdate(BaseModel):
    """TODO: for PATCH. Every field optional with default None:
    name (1..50), price (> 0), quantity (>= 0), tags (list[str]).
    Hint: `name: str | None = Field(default=None, min_length=1, max_length=50)`
    """


# Exercise 3 -------------------------------------------------------------
class Customer(BaseModel):
    """TODO: fields
        name: str  -- stripped of surrounding whitespace; must not be empty after stripping
        email: str -- stripped and lowercased; must contain exactly one '@' and the part
                      after '@' must contain a '.'  (else ValueError)
        age: int | None = None -- if given must be 0..120
    Hint: @field_validator("email") with @classmethod. Use mode="before" if you
    need to see the raw value; here the default ("after") works since it's already a str.
    Raising ValueError inside a validator becomes a validation error.
    """


# Exercise 4 -------------------------------------------------------------
class DateRange(BaseModel):
    """TODO: fields start: date, end: date.
    - end must not be before start (ValueError otherwise). Hint: @model_validator(mode="after")
      which receives/returns self.
    - add a property `days` -> inclusive number of days: (end - start).days + 1
    Pydantic parses "2024-01-31" strings into date objects for you.
    """


# Exercise 5 -------------------------------------------------------------
class UserIn(BaseModel):
    """TODO: email: str (stripped + lowercased, must contain '@'), password: str (min 8 chars)."""


class UserOut(BaseModel):
    """TODO: id: int, email: str. NO password -- this is what clients may see."""


# ======================= Part B: routes ==================================

# Exercise 6 -------------------------------------------------------------
@app.post("/products", status_code=201, response_model=ProductRead)
def create_product(product: ProductCreate):
    """TODO: store the product in PRODUCTS under id = max(ids, default=0) + 1 and
    return it with its id. Store plain dicts: {"id": id, **product.model_dump()}.
    """
    ...


# Exercise 7 -------------------------------------------------------------
@app.get("/products/{product_id}", response_model=ProductRead)
def get_product(product_id: int):
    """TODO: return the product or raise HTTPException(404, "Product not found")."""
    ...


@app.get("/products", response_model=list[ProductRead])
def list_products(
    min_price: float | None = None,
    max_price: float | None = None,
    tag: str | None = None,
):
    """TODO: return products ordered by id, keeping only those that match every
    filter that was given: price >= min_price, price <= max_price, tag in product tags.
    """
    ...


# Exercise 8 -------------------------------------------------------------
@app.patch("/products/{product_id}", response_model=ProductRead)
def update_product(product_id: int, changes: ProductUpdate):
    """TODO: partial update. Only fields the client actually sent change.
    Hint: changes.model_dump(exclude_unset=True) -- a field set to None explicitly
    is "set", a field not sent is not. 404 if product missing. Return the updated product.
    """
    ...


# Exercise 9 -------------------------------------------------------------
@app.post("/users", status_code=201, response_model=UserOut)
def create_user(user: UserIn):
    """TODO: emails are unique (already lowercased by UserIn). If one exists raise
    HTTPException(409, "Email already registered"). Otherwise store in USERS with
    id = max+1 as {"id", "email", "password_hash"} where password_hash is
    hashlib.sha256(password.encode()).hexdigest() (real apps use argon2/bcrypt!).
    Return the stored dict -- response_model=UserOut must strip password_hash.
    """
    ...


# Exercise 10 ------------------------------------------------------------
class OutOfStock(Exception):
    """Provided. Raised when a purchase asks for more than we have."""

    def __init__(self, product_id: int, requested: int, available: int):
        self.product_id = product_id
        self.requested = requested
        self.available = available


@app.exception_handler(OutOfStock)
async def out_of_stock_handler(request, exc: OutOfStock):
    """TODO: respond 409 with JSON
        {"error": "out_of_stock", "product_id": ..., "requested": ..., "available": ...}
    Hint: return JSONResponse(status_code=409, content={...}) (import it from fastapi.responses).
    """
    ...


@app.post("/products/{product_id}/purchase")
def purchase(product_id: int, qty: int = Query(1, ge=1)):
    """TODO: 404 if the product is missing. If qty > quantity in stock,
    `raise OutOfStock(product_id, qty, available)` (the handler above formats it).
    Otherwise decrease the stock and return {"id": product_id, "quantity": remaining}.
    """
    ...
