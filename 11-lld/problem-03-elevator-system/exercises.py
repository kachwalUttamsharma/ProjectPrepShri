"""LLD problem 03: elevator system. Read lesson.md for the full spec.

Enums, exceptions and the strategy ABC are provided. Implement everything
marked `...`. The simulation is discrete: nothing moves except inside `step()`.
"""
from abc import ABC, abstractmethod
from enum import Enum


class Direction(Enum):
    UP = "up"
    DOWN = "down"
    IDLE = "idle"


class ElevatorState(Enum):
    IDLE = "idle"
    MOVING_UP = "moving_up"
    MOVING_DOWN = "moving_down"
    DOORS_OPEN = "doors_open"


class ElevatorError(Exception):
    """Base class for all elevator errors."""


class InvalidFloorError(ElevatorError):
    """Floor is outside 0 .. num_floors-1."""


class UnknownElevatorError(ElevatorError):
    """No elevator with that id in the controller."""


class Elevator:
    """Elevator(elevator_id, num_floors, start_floor=0).

    Floors are 0 .. num_floors-1. num_floors < 2 -> ValueError; bad start_floor
    -> InvalidFloorError.

    Public attributes: elevator_id, num_floors, floor (current floor),
    direction (Direction, starts IDLE), state (ElevatorState, starts IDLE).

    Properties:
      stops    -> sorted list of pending stop floors (no duplicates), a copy.
      is_idle  -> True iff there are no pending stops and doors are not open.

    add_stop(floor): register a stop. InvalidFloorError if out of range.
        Adding an existing stop is a no-op. Adding the current floor is allowed
        (doors will open on the next step()).

    step(): advance the simulation by exactly ONE action, checked in this order:
      1. state is DOORS_OPEN -> close the doors: state = IDLE. `direction` is
         left unchanged. Done.
      2. current floor is in stops -> remove it, state = DOORS_OPEN. Done.
      3. no stops -> direction = IDLE, state = IDLE. Done.
      4. otherwise choose a direction (LOOK rule below), move ONE floor that
         way, and set state = MOVING_UP / MOVING_DOWN, direction = UP / DOWN.

    LOOK rule (step 4; no stop equals the current floor here):
      - direction UP: keep going UP if any stop is above, else turn DOWN.
      - direction DOWN: keep going DOWN if any stop is below, else turn UP.
      - direction IDLE: go toward the nearest stop (smallest |stop - floor|);
        on a tie prefer the LOWER stop floor.
    The elevator therefore serves every stop in its current direction of travel
    before reversing, never zig-zagging.
    """

    def __init__(self, elevator_id, num_floors, start_floor=0):
        ...

    @property
    def stops(self):
        ...

    @property
    def is_idle(self):
        ...

    def add_stop(self, floor):
        ...

    def step(self):
        ...


class SchedulingStrategy(ABC):
    """Abstract: select(elevators, floor, direction) -> Elevator.

    `elevators` is a non-empty list ordered by elevator_id; `direction` is
    Direction.UP or Direction.DOWN (the button pressed). Must not mutate them.
    """

    @abstractmethod
    def select(self, elevators, floor, direction):
        ...


class NearestElevatorStrategy(SchedulingStrategy):
    """Pick the best elevator for a hall call.

    An elevator is ELIGIBLE if either
      - it has no pending stops (`not e.stops`), or
      - it is already travelling in the requested `direction` and has not yet
        passed `floor`: direction == UP and e.floor <= floor, or
        direction == DOWN and e.floor >= floor.
    Among eligible elevators choose the minimum (abs(e.floor - floor),
    e.elevator_id). If none is eligible, apply the same minimum over ALL
    elevators.
    """

    def select(self, elevators, floor, direction):
        ...


class LeastLoadedStrategy(SchedulingStrategy):
    """Choose the minimum of (len(e.stops), abs(e.floor - floor), e.elevator_id)
    over all elevators. Ignores direction."""

    def select(self, elevators, floor, direction):
        ...


class ElevatorController:
    """ElevatorController(elevators, strategy=None).

    `elevators`: non-empty list of Elevator with unique ids, else ValueError.
    `strategy` defaults to NearestElevatorStrategy(); it is a public,
    reassignable attribute named `strategy`.

    request_pickup(floor, direction) -> elevator_id
        Hall call. direction must be Direction.UP or DOWN (IDLE -> ValueError).
        Invalid floor -> InvalidFloorError (raised before any state changes).
        Ask the strategy for an elevator (list ordered by elevator_id), add
        `floor` as a stop on it, return its id.

    select_floor(elevator_id, floor) -> None
        Cabin button. Unknown id -> UnknownElevatorError; bad floor ->
        InvalidFloorError. Adds a stop on that elevator.

    get(elevator_id) -> Elevator (UnknownElevatorError if missing).
    step() -> None: call step() on every elevator, in elevator_id order.
    is_idle() -> bool: True iff every elevator is_idle.
    """

    def __init__(self, elevators, strategy=None):
        ...

    def get(self, elevator_id):
        ...

    def request_pickup(self, floor, direction):
        ...

    def select_floor(self, elevator_id, floor):
        ...

    def step(self):
        ...

    def is_idle(self):
        ...
