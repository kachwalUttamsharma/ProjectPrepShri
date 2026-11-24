"""Week 5 project: parking lot system. Read lesson.md for the full spec.

Enums and exception classes are provided. Implement everything marked `...`.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, IntEnum
import math
import time


class VehicleType(Enum):
    MOTORCYCLE = "motorcycle"
    CAR = "car"
    TRUCK = "truck"


class SpotType(IntEnum):
    SMALL = 1
    MEDIUM = 2
    LARGE = 3


class ParkingError(Exception):
    """Base class for all parking errors."""


class LotFullError(ParkingError):
    """No free spot fits the vehicle."""


class DuplicateVehicleError(ParkingError):
    """The plate is already parked in the lot."""


class InvalidTicketError(ParkingError):
    """Unknown or already-used ticket."""


# Which spot types each vehicle may use. Fill this in (see lesson.md).
FITS = {}


@dataclass(frozen=True)
class Vehicle:
    """Fields: plate: str, vehicle_type: VehicleType."""


class ParkingSpot:
    """ParkingSpot(spot_id, spot_type). Attributes: spot_id, spot_type, vehicle (None).

    is_free (property), can_fit(vehicle) -> bool (type fits; ignores occupancy),
    park(vehicle) -> None (ParkingError if occupied or doesn't fit),
    leave() -> the vehicle (ParkingError if empty).
    """

    def __init__(self, spot_id, spot_type):
        ...

    @property
    def is_free(self):
        ...

    def can_fit(self, vehicle):
        ...

    def park(self, vehicle):
        ...

    def leave(self):
        ...


@dataclass(frozen=True)
class Ticket:
    """Fields: ticket_id: int, plate: str, spot_id: int, entry_time: float."""


class PricingStrategy(ABC):
    """Abstract: fee(vehicle_type, minutes) -> int."""

    @abstractmethod
    def fee(self, vehicle_type, minutes):
        ...


class HourlyPricing(PricingStrategy):
    """HourlyPricing(rates: dict[VehicleType, int]).
    fee = rate * max(1, ceil(minutes / 60)); unknown vehicle type -> ValueError.
    """

    def __init__(self, rates):
        ...

    def fee(self, vehicle_type, minutes):
        ...


class FlatPricing(PricingStrategy):
    """FlatPricing(amount): fee is always `amount`."""

    def __init__(self, amount):
        ...

    def fee(self, vehicle_type, minutes):
        ...


class ParkingLot:
    """ParkingLot(spots, pricing, clock=None). See lesson.md for every rule."""

    def __init__(self, spots, pricing, clock=None):
        ...

    def park(self, vehicle):
        """Return a Ticket. DuplicateVehicleError / LotFullError as per spec."""
        ...

    def unpark(self, ticket_id):
        """Free the spot and return the fee (int). InvalidTicketError if unknown/used."""
        ...

    def available_count(self, spot_type=None):
        ...

    def is_full(self):
        ...

    def find_vehicle(self, plate):
        """Return the spot_id holding this plate, or None."""
        ...

    def occupancy(self):
        """{SpotType: (occupied, total)} for each spot type present."""
        ...
