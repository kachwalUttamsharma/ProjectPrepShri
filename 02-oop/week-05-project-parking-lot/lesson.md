# Week 5: Project - Parking lot system

A classic low-level-design (LLD) interview problem. This week you design and build it yourself from the spec, using everything from weeks 1-4. Budget: ~7-8 hours. Suggested split: read spec + sketch classes on paper (1h), spots/vehicles (1.5h), pricing (1h), lot (2.5h), review + polish + checklist (2h).

## How to approach an LLD interview question
1. **Clarify requirements** (what vehicles? pricing? one entrance?). State assumptions.
2. **Identify nouns -> classes** (Vehicle, ParkingSpot, Ticket, ParkingLot), **verbs -> methods** (park, unpark, fee).
3. **Decide relationships**: lot HAS spots (composition); pricing is a pluggable Strategy; errors are a small exception hierarchy.
4. **Code the happy path first**, then edge cases (full lot, double parking, bad ticket).
5. **Talk through extensions** (multiple floors, EV spots, reservations, concurrency/locking) and how your design absorbs them.

## Spec

### Enums (provided in `exercises.py`)
- `VehicleType`: MOTORCYCLE, CAR, TRUCK
- `SpotType` (IntEnum): SMALL=1, MEDIUM=2, LARGE=3

### Fit rules
| Vehicle | Fits in |
|---|---|
| MOTORCYCLE | SMALL, MEDIUM, LARGE |
| CAR | MEDIUM, LARGE |
| TRUCK | LARGE |

### Classes
- `Vehicle` - frozen dataclass: `plate: str`, `vehicle_type: VehicleType`.
- `ParkingSpot(spot_id, spot_type)` - `vehicle` (None when free), `is_free` property, `can_fit(vehicle)`, `park(vehicle)`, `leave()`.
  - `park` raises `ParkingError` if occupied or the vehicle doesn't fit. `leave` returns the vehicle; raises `ParkingError` if already empty.
- `Ticket` - frozen dataclass: `ticket_id: int`, `plate: str`, `spot_id: int`, `entry_time: float`.
- `PricingStrategy` - ABC with abstract `fee(vehicle_type, minutes) -> int`.
  - `HourlyPricing(rates)`: `rates` maps VehicleType to price per hour. Fee = rate x hours, rounded **up** to whole hours, minimum 1 hour. Missing vehicle type -> `ValueError`.
  - `FlatPricing(amount)`: always `amount`.
- `ParkingLot(spots, pricing, clock=None)`
  - `clock` is a zero-argument callable returning the current time **in minutes** (inject a fake in tests). Default: real time.
  - `park(vehicle) -> Ticket`: choose the **smallest fitting free spot** (lowest `SpotType`, ties by lowest `spot_id`). Ticket ids are 1, 2, 3... and never reused. A failed park must not consume an id.
  - `unpark(ticket_id) -> int fee`: frees the spot, invalidates the ticket.
  - `available_count(spot_type=None) -> int`: free spots (of that type, or all).
  - `is_full() -> bool`: no free spots at all.
  - `find_vehicle(plate) -> spot_id | None`.
  - `occupancy() -> dict[SpotType, tuple[int, int]]`: `(occupied, total)` for each spot type that exists.
- Exceptions (provided): `ParkingError` (base), `LotFullError`, `DuplicateVehicleError`, `InvalidTicketError`.
  - `park` raises `DuplicateVehicleError` if the plate is already parked, `LotFullError` if no free spot fits that vehicle. `unpark` raises `InvalidTicketError` for unknown/used tickets.

### Out of scope (talk about them, don't build)
Multiple floors, reservations, thread safety, persistence.

## Design hints
- Don't repeat the fit table in `if/elif` chains; use a dict `{VehicleType: set of SpotType}`.
- `ParkingLot` should depend on the `PricingStrategy` abstraction (injected), not on `HourlyPricing`.
- Keep a dict `ticket_id -> Ticket` and `plate -> ticket_id` for O(1) lookups. Choosing a spot may be O(n) at first; note how you'd make it O(log n) with a heap per spot type.
- Validate at the edges, keep internal methods simple.

## Common mistakes
- Spot selection that takes the first fit instead of the smallest fit (motorcycles filling truck spots).
- Incrementing the ticket counter before a failed `park`.
- Forgetting to remove the plate/ticket entries on `unpark` (then re-parking raises Duplicate).
- Using `time.time()` directly inside the lot (untestable). Inject the clock.
- `math.ceil(minutes / 60)` for 0 minutes gives 0: enforce the minimum of 1 hour.
- Returning floats for money where the spec says int.

## Your task
Fill in `exercises.py`, then run
`.venv/bin/pytest 02-oop/week-05-project-parking-lot -v`

## Stage 2 review checklist
Before showing me the code, tick every box honestly. Then be ready to explain each item out loud (that's the interview).

**Week 1-2 fundamentals**
- [ ] I can explain `self`, `__init__`, class vs instance attributes without notes.
- [ ] No mutable default arguments; no accidental shared mutable class attributes.
- [ ] Attributes that shouldn't be touched use `_name`; validated state uses `@property` where useful.
- [ ] I know when to define `__repr__`, `__eq__` + `__hash__` together and why.
- [ ] I can explain `@classmethod` vs `@staticmethod` vs instance method.

**Week 3 inheritance**
- [ ] I used an ABC (`PricingStrategy`) and can say why it can't be instantiated.
- [ ] I can draw the MRO of a diamond and say what `super()` really does.
- [ ] I can justify every inheritance relationship as truly "is-a" (and name where I chose composition).

**Week 4 design**
- [ ] The lot HAS spots and a pricing strategy (composition); pricing is injected (DIP).
- [ ] Adding a new pricing scheme or vehicle type needs no edits to `ParkingLot` logic (OCP) - and I can say what edits it would need.
- [ ] Errors use a small custom exception hierarchy; callers can catch `ParkingError` or a specific subclass.
- [ ] I can name SOLID's five letters with one example each from this project.
- [ ] I can state why I did or did not use a Singleton for the lot.

**Quality**
- [ ] All tests pass; I also added 3+ tests of my own (e.g. re-park after unpark, ties between equal spots).
- [ ] Each method does one thing; no method is longer than ~20 lines.
- [ ] Names are clear; docstrings explain *why*, not *what*.
- [ ] I can state time complexity of `park`, `unpark`, `find_vehicle`, and how to improve `park`.
- [ ] Extension talk ready: multiple floors, EV charging spots, reservations, thread safety (locks), persistence.

**Mock-interview drill (do once, out loud, 35 minutes)**: re-solve "design an elevator system" or "design a library system" on paper using the 5 steps above. Send me the class sketch.
