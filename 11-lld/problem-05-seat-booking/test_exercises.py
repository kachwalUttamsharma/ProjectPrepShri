import dataclasses
import threading

import pytest

from exercises import *


class FakeClock:
    def __init__(self, now=0.0):
        self.now = now

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


SEATS = ["A1", "A2", "A3", "B1", "B2"]


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def svc(clock):
    s = BookingService(clock, hold_ttl=100)
    s.add_show("show1", SEATS)
    return s


# ---- exceptions / data types
def test_exception_hierarchy():
    for exc in (UnknownShowError, UnknownSeatError, SeatUnavailableError,
                HoldExpiredError, InvalidHoldError):
        assert issubclass(exc, BookingError)
    assert issubclass(BookingError, Exception)


def test_seat_status_members():
    assert {s.name for s in SeatStatus} == {"AVAILABLE", "HELD", "BOOKED"}


def test_hold_and_booking_are_frozen_dataclasses(svc):
    h = svc.hold_seats("show1", ["A2", "A1"], "u1")
    assert dataclasses.is_dataclass(h)
    with pytest.raises(dataclasses.FrozenInstanceError):
        h.user_id = "x"
    b = svc.confirm(h.hold_id)
    assert dataclasses.is_dataclass(b)
    with pytest.raises(dataclasses.FrozenInstanceError):
        b.user_id = "x"


# ---- setup validation
def test_ttl_must_be_positive(clock):
    with pytest.raises(ValueError):
        BookingService(clock, hold_ttl=0)


def test_add_show_validation(svc):
    with pytest.raises(ValueError):
        svc.add_show("show1", ["Z1"])  # duplicate show
    with pytest.raises(ValueError):
        svc.add_show("s2", [])
    with pytest.raises(ValueError):
        svc.add_show("s2", ["A", "A"])


def test_unknown_show_and_seat(svc):
    with pytest.raises(UnknownShowError):
        svc.hold_seats("nope", ["A1"], "u")
    with pytest.raises(UnknownShowError):
        svc.available_seats("nope")
    with pytest.raises(UnknownSeatError):
        svc.hold_seats("show1", ["Z9"], "u")
    with pytest.raises(UnknownSeatError):
        svc.seat_status("show1", "Z9")


def test_hold_argument_validation(svc):
    with pytest.raises(ValueError):
        svc.hold_seats("show1", [], "u")
    with pytest.raises(ValueError):
        svc.hold_seats("show1", ["A1", "A1"], "u")


# ---- holding
def test_initial_state_all_available(svc):
    assert svc.available_seats("show1") == sorted(SEATS)
    assert all(svc.seat_status("show1", s) is SeatStatus.AVAILABLE for s in SEATS)


def test_hold_returns_hold_with_sorted_seats_and_expiry(svc, clock):
    clock.now = 10
    h = svc.hold_seats("show1", ["B1", "A1"], "alice")
    assert h.show_id == "show1" and h.user_id == "alice"
    assert h.seat_ids == ("A1", "B1")
    assert h.expires_at == 110
    assert svc.seat_status("show1", "A1") is SeatStatus.HELD
    assert svc.seat_status("show1", "B1") is SeatStatus.HELD
    assert svc.available_seats("show1") == ["A2", "A3", "B2"]


def test_hold_ids_are_unique_and_increasing(svc):
    a = svc.hold_seats("show1", ["A1"], "u")
    b = svc.hold_seats("show1", ["A2"], "u")
    assert a.hold_id == 1 and b.hold_id == 2


def test_held_seat_cannot_be_held_again(svc):
    svc.hold_seats("show1", ["A1"], "alice")
    with pytest.raises(SeatUnavailableError):
        svc.hold_seats("show1", ["A1"], "bob")
    with pytest.raises(SeatUnavailableError):
        svc.hold_seats("show1", ["A1"], "alice")


def test_hold_is_all_or_nothing(svc):
    svc.hold_seats("show1", ["A2"], "alice")
    with pytest.raises(SeatUnavailableError):
        svc.hold_seats("show1", ["A1", "A2", "A3"], "bob")
    assert svc.seat_status("show1", "A1") is SeatStatus.AVAILABLE
    assert svc.seat_status("show1", "A3") is SeatStatus.AVAILABLE


def test_failed_hold_does_not_consume_id(svc):
    svc.hold_seats("show1", ["A1"], "u")
    with pytest.raises(SeatUnavailableError):
        svc.hold_seats("show1", ["A1"], "v")
    assert svc.hold_seats("show1", ["A2"], "v").hold_id == 2


def test_shows_are_independent(svc):
    svc.add_show("show2", ["A1"])
    svc.hold_seats("show1", ["A1"], "u")
    svc.hold_seats("show2", ["A1"], "v")
    assert svc.seat_status("show2", "A1") is SeatStatus.HELD


# ---- expiry (lazy)
def test_hold_expires_at_exact_ttl(svc, clock):
    svc.hold_seats("show1", ["A1"], "alice")
    clock.advance(99)
    assert svc.seat_status("show1", "A1") is SeatStatus.HELD
    clock.advance(1)
    assert svc.seat_status("show1", "A1") is SeatStatus.AVAILABLE
    assert "A1" in svc.available_seats("show1")


def test_expired_seat_can_be_held_by_someone_else(svc, clock):
    svc.hold_seats("show1", ["A1"], "alice")
    clock.advance(100)
    h = svc.hold_seats("show1", ["A1"], "bob")
    assert h.user_id == "bob"
    assert svc.seat_status("show1", "A1") is SeatStatus.HELD


# ---- confirm
def test_confirm_books_seats(svc):
    h = svc.hold_seats("show1", ["A1", "A2"], "alice")
    b = svc.confirm(h.hold_id)
    assert b.booking_id == 1
    assert b.show_id == "show1" and b.user_id == "alice"
    assert b.seat_ids == ("A1", "A2")
    assert svc.seat_status("show1", "A1") is SeatStatus.BOOKED
    assert svc.available_seats("show1") == ["A3", "B1", "B2"]


def test_booked_seats_never_expire(svc, clock):
    h = svc.hold_seats("show1", ["A1"], "alice")
    svc.confirm(h.hold_id)
    clock.advance(10_000)
    assert svc.seat_status("show1", "A1") is SeatStatus.BOOKED
    with pytest.raises(SeatUnavailableError):
        svc.hold_seats("show1", ["A1"], "bob")


def test_confirm_expired_hold_raises_and_frees_seats(svc, clock):
    h = svc.hold_seats("show1", ["A1"], "alice")
    clock.advance(100)
    with pytest.raises(HoldExpiredError):
        svc.confirm(h.hold_id)
    assert svc.seat_status("show1", "A1") is SeatStatus.AVAILABLE


def test_confirm_stale_hold_after_seat_taken_by_other(svc, clock):
    old = svc.hold_seats("show1", ["A1"], "alice")
    clock.advance(100)
    new = svc.hold_seats("show1", ["A1"], "bob")
    with pytest.raises(HoldExpiredError):
        svc.confirm(old.hold_id)
    # bob's hold must be untouched
    assert svc.seat_status("show1", "A1") is SeatStatus.HELD
    assert svc.confirm(new.hold_id).user_id == "bob"


def test_confirm_unknown_or_reused_hold(svc):
    with pytest.raises(InvalidHoldError):
        svc.confirm(999)
    h = svc.hold_seats("show1", ["A1"], "u")
    svc.confirm(h.hold_id)
    with pytest.raises(InvalidHoldError):
        svc.confirm(h.hold_id)


def test_booking_ids_increase_across_shows(svc):
    svc.add_show("show2", ["X1"])
    b1 = svc.confirm(svc.hold_seats("show1", ["A1"], "u").hold_id)
    b2 = svc.confirm(svc.hold_seats("show2", ["X1"], "u").hold_id)
    assert (b1.booking_id, b2.booking_id) == (1, 2)


def test_bookings_for_user(svc):
    svc.confirm(svc.hold_seats("show1", ["A1"], "alice").hold_id)
    svc.confirm(svc.hold_seats("show1", ["A2"], "bob").hold_id)
    svc.confirm(svc.hold_seats("show1", ["A3"], "alice").hold_id)
    assert [b.seat_ids for b in svc.bookings_for("alice")] == [("A1",), ("A3",)]
    assert svc.bookings_for("nobody") == []


# ---- release
def test_release_frees_seats(svc):
    h = svc.hold_seats("show1", ["A1", "A2"], "alice")
    svc.release(h.hold_id)
    assert svc.available_seats("show1") == sorted(SEATS)
    with pytest.raises(InvalidHoldError):
        svc.confirm(h.hold_id)


def test_release_twice_or_unknown(svc):
    h = svc.hold_seats("show1", ["A1"], "u")
    svc.release(h.hold_id)
    with pytest.raises(InvalidHoldError):
        svc.release(h.hold_id)
    with pytest.raises(InvalidHoldError):
        svc.release(12345)


def test_release_after_confirm_is_invalid_and_keeps_booking(svc):
    h = svc.hold_seats("show1", ["A1"], "u")
    svc.confirm(h.hold_id)
    with pytest.raises(InvalidHoldError):
        svc.release(h.hold_id)
    assert svc.seat_status("show1", "A1") is SeatStatus.BOOKED


def test_release_expired_hold_does_not_free_new_holders_seat(svc, clock):
    old = svc.hold_seats("show1", ["A1"], "alice")
    clock.advance(100)
    svc.hold_seats("show1", ["A1"], "bob")
    svc.release(old.hold_id)  # must not raise, must not free bob's seat
    assert svc.seat_status("show1", "A1") is SeatStatus.HELD


# ---- concurrency (deterministic: Barrier, no sleeps)
def _run_threads(n, fn):
    barrier = threading.Barrier(n)
    results = [None] * n

    def worker(i):
        barrier.wait()
        try:
            results[i] = ("ok", fn(i))
        except Exception as e:  # noqa: BLE001
            results[i] = ("err", e)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)
    assert all(r is not None for r in results)
    return results


def test_concurrent_hold_same_seat_exactly_one_wins(svc):
    for _ in range(20):
        svc.add_show(f"s{_}", ["A1"])
    for i in range(20):
        res = _run_threads(16, lambda k, i=i: svc.hold_seats(f"s{i}", ["A1"], f"u{k}"))
        winners = [r for r in res if r[0] == "ok"]
        losers = [r for r in res if r[0] == "err"]
        assert len(winners) == 1
        assert all(isinstance(e, SeatUnavailableError) for _, e in losers)


def test_concurrent_overlapping_holds_never_double_book(svc):
    svc.add_show("big", [f"S{i}" for i in range(6)])
    sets = [["S0", "S1", "S2"], ["S2", "S3", "S4"], ["S4", "S5", "S0"], ["S1", "S3", "S5"]]
    res = _run_threads(4, lambda k: svc.hold_seats("big", sets[k], f"u{k}"))
    held = [seat for r in res if r[0] == "ok" for seat in r[1].seat_ids]
    assert len(held) == len(set(held))  # no seat in two holds
    for r in res:
        if r[0] == "err":
            assert isinstance(r[1], SeatUnavailableError)
    # state agrees with holds: every held seat reports HELD, others AVAILABLE
    for i in range(6):
        expected = SeatStatus.HELD if f"S{i}" in held else SeatStatus.AVAILABLE
        assert svc.seat_status("big", f"S{i}") is expected


def test_concurrent_confirm_same_hold_exactly_one_booking(svc):
    h = svc.hold_seats("show1", ["A1"], "alice")
    res = _run_threads(12, lambda k: svc.confirm(h.hold_id))
    assert sum(1 for r in res if r[0] == "ok") == 1
    assert all(isinstance(r[1], InvalidHoldError) for r in res if r[0] == "err")
    assert len(svc.bookings_for("alice")) == 1


def test_concurrent_disjoint_holds_all_succeed(svc):
    svc.add_show("many", [f"S{i}" for i in range(32)])
    res = _run_threads(32, lambda k: svc.hold_seats("many", [f"S{k}"], f"u{k}"))
    assert all(r[0] == "ok" for r in res)
    ids = [r[1].hold_id for r in res]
    assert len(set(ids)) == 32
    assert svc.available_seats("many") == []
