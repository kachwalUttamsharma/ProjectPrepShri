"""Problem 05: BookMyShow-style seat booking. Read lesson.md for the full spec.

Enums, exceptions and data classes are provided. Implement BookingService.
"""
from dataclasses import dataclass
from enum import Enum


class SeatStatus(Enum):
    AVAILABLE = "available"
    HELD = "held"
    BOOKED = "booked"


class BookingError(Exception):
    """Base class for all booking errors."""


class UnknownShowError(BookingError):
    """show_id was never added."""


class UnknownSeatError(BookingError):
    """seat_id does not exist in that show."""


class SeatUnavailableError(BookingError):
    """At least one requested seat is HELD (unexpired) or BOOKED."""


class HoldExpiredError(BookingError):
    """confirm() on a hold whose TTL has elapsed."""


class InvalidHoldError(BookingError):
    """Unknown hold id, or the hold was already confirmed / released."""


@dataclass(frozen=True)
class Hold:
    """Fields: hold_id: int, show_id: str, seat_ids: tuple (sorted), user_id: str,
    expires_at: float (clock() at hold time + ttl)."""


@dataclass(frozen=True)
class Booking:
    """Fields: booking_id: int, show_id: str, seat_ids: tuple (sorted), user_id: str."""


class BookingService:
    """BookingService(clock, hold_ttl=300).

    `clock` is a zero-argument callable returning the current time in seconds
    (a fake in tests). hold_ttl <= 0 -> ValueError.

    Seat state is derived, never stored as a timer: a seat is HELD only while
    clock() < hold.expires_at. At clock() >= expires_at it is AVAILABLE again
    (lazy expiry, no background thread).

    Thread safety: every public method must be safe to call from many threads.
    Use one lock per show (not one global lock) so shows do not block each other.
    """

    def __init__(self, clock, hold_ttl=300):
        ...

    def add_show(self, show_id, seat_ids):
        """Register a show. seat_ids: iterable of str. ValueError if empty,
        has duplicates, or show_id already exists. All seats start AVAILABLE."""
        ...

    def seat_status(self, show_id, seat_id):
        """-> SeatStatus. UnknownShowError / UnknownSeatError as appropriate."""
        ...

    def available_seats(self, show_id):
        """-> sorted list of seat ids that are AVAILABLE right now."""
        ...

    def hold_seats(self, show_id, seat_ids, user_id):
        """Atomically hold ALL seats or none. -> Hold.

        Validation order: UnknownShowError, then ValueError (empty / duplicate
        seat_ids), then UnknownSeatError, then SeatUnavailableError (any seat
        HELD-unexpired or BOOKED; also if the same user already holds it).
        A failed call changes nothing and does not consume a hold id.
        Hold ids are 1, 2, 3, ... global across shows. Hold.seat_ids is sorted.
        """
        ...

    def confirm(self, hold_id):
        """Turn a hold into a permanent Booking. -> Booking.

        InvalidHoldError: unknown id, or hold already confirmed/released.
        HoldExpiredError: clock() >= expires_at (seats it still owns become
        AVAILABLE). Booking ids are 1, 2, 3, ... global across shows.
        Exactly one of many concurrent confirm() calls on one hold succeeds;
        the rest raise InvalidHoldError.
        """
        ...

    def release(self, hold_id):
        """Give seats back early. InvalidHoldError if unknown / confirmed /
        already released. Releasing an EXPIRED hold is allowed (no error) but
        must only free seats this hold still owns - never a seat that another
        user has since re-held.
        """
        ...

    def bookings_for(self, user_id):
        """-> list of Booking for that user, oldest first ([] if none)."""
        ...
