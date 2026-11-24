# Week 2: Pydantic, validation, response models, errors

Goal: stop accepting raw dicts. Define the *shape* of your data once; FastAPI validates input, filters output, and documents it. As an FDE, this is how you survive messy customer payloads. Budget ~7-8 hours.

## 1. Pydantic models
```python
from pydantic import BaseModel, Field

class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    price: float = Field(gt=0)
    quantity: int = Field(default=0, ge=0)
    tags: list[str] = Field(default_factory=list)   # never `= []` style sharing worries; this is explicit
```
```python
p = ProductCreate(name="Mug", price="9.5")   # "9.5" is coerced to 9.5 (lax mode)
p.price            # 9.5
p.model_dump()     # plain dict
p.model_dump_json()
ProductCreate.model_validate({"name": "Mug", "price": 1})   # from a dict
ProductCreate(name="", price=1)   # raises pydantic.ValidationError
```
- Field constraints: `gt, ge, lt, le` (numbers), `min_length, max_length, pattern` (strings/lists).
- Optional: `age: int | None = None`.
- Coercion: `"5"` -> `5`, `"2024-01-31"` -> `date`. Surprising at first, great for messy input. Strict mode exists when you don't want it.
- Inheritance reuses fields: `class ProductRead(ProductCreate): id: int`.
- Nested models and lists of models work as you'd hope.

## 2. Custom validators
```python
from pydantic import field_validator, model_validator

class Customer(BaseModel):
    email: str
    @field_validator("email")
    @classmethod
    def clean_email(cls, v: str) -> str:      # runs after type check; return the cleaned value
        v = v.strip().lower()
        if "@" not in v:
            raise ValueError("not an email")   # becomes a validation error
        return v

class DateRange(BaseModel):
    start: date
    end: date
    @model_validator(mode="after")           # sees the whole model: cross-field rules
    def check_order(self):
        if self.end < self.start:
            raise ValueError("end before start")
        return self
```
`mode="before"` validators see the raw input (useful to normalise junk before type checking).

## 3. Models in FastAPI
```python
@app.post("/products", status_code=201, response_model=ProductRead)
def create(product: ProductCreate):      # body parsed + validated; invalid -> 422 automatically
    ...
```
- **Request model**: a parameter typed with a `BaseModel` is read from the JSON body.
- **`response_model`**: FastAPI validates and *filters* what you return. If you return a dict with `password_hash`, a `UserOut` without that field strips it. This is your security net against leaking fields.
- **Separate models per purpose**: `XCreate` (input), `XUpdate` (all optional), `XRead` (output). One model for everything leads to leaked fields and impossible PATCHes.
- The 422 body looks like `{"detail": [{"loc": ["body", "price"], "msg": "...", "type": "..."}]}`: great to show customers exactly what to fix.

## 4. Partial updates (PATCH)
```python
changes.model_dump(exclude_unset=True)    # only the fields the client actually sent
```
Without `exclude_unset` every omitted field would overwrite data with `None`.

## 5. Errors
```python
raise HTTPException(status_code=404, detail="Product not found")      # -> {"detail": "..."}
```
For your own domain errors, raise a custom exception in business logic and translate it once:
```python
class OutOfStock(Exception): ...

@app.exception_handler(OutOfStock)
async def handle(request, exc):
    return JSONResponse(status_code=409, content={"error": "out_of_stock"})
```
Business code stays free of HTTP details; the API layer owns status codes.

Pick codes deliberately: 400 malformed/semantic problem you detect yourself, 404 missing, 409 conflicts with current state (duplicate, out of stock), 422 schema validation (automatic).

## 6. Query parameter validation
`qty: int = Query(1, ge=1)`, `tag: str | None = None` (optional filter). Same constraint vocabulary as `Field`.

## Common mistakes
- Using the same model for input and output (leaks passwords/internal ids, or forces clients to send `id`).
- `PATCH` that writes `None` over unsent fields (forgot `exclude_unset`).
- Mutable default `tags: list = []` in plain Python classes. In Pydantic it's copied, but `default_factory=list` is the clear habit.
- Forgetting `@classmethod` under `@field_validator`.
- Validators that don't `return` the value (field becomes `None`).
- Raising `HTTPException` deep in business logic (hard to reuse/test). Prefer domain exceptions + handlers.
- Treating coercion as bug-free: `"true"`, `"1"`, `1` all become `True` for a `bool`; check what your customers actually send.
- Storing passwords unhashed. (We use sha256 only to keep the exercise stdlib; real systems use argon2/bcrypt.)

## Your task
1. Experiment in a REPL: build models, feed them bad data, read `ValidationError.errors()`.
2. Fill in `exercises.py`: models first (tests run without HTTP), then routes. Run `../../.venv/bin/pytest -q`.
3. Stretch: run uvicorn, send an invalid body from `/docs`, and read the 422 response. Then add a `Literal["small","large"]` field to `ProductCreate` and see how `/docs` changes.
