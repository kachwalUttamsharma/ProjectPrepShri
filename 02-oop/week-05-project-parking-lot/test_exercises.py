import dataclasses

import pytest

from exercises import *


class FakeClock:
    def __init__(self, now=0.0):
        self.now = now

    def __call__(self):
        return self.now

    def advance(self, minutes):
        self.now += minutes


RATES = {VehicleType.MOTORCYCLE: 1, VehicleType.CAR: 2, VehicleType.TRUCK: 5}


def moto(p="M1"):
    return Vehicle(p, VehicleType.MOTORCYCLE)


def car(p="C1"):
    return Vehicle(p, VehicleType.CAR)


def truck(p="T1"):
    return Vehicle(p, VehicleType.TRUCK)


def make_lot(spec=((1, SpotType.SMALL), (2, SpotType.MEDIUM), (3, SpotType.LARGE)), pricing=None):
    clock = FakeClock()
    spots = [ParkingSpot(i, t) for i, t in spec]
    return ParkingLot(spots, pricing or HourlyPricing(RATES), clock), clock


# ---- vehicle / spot
def test_vehicle_dataclass():
    v = car("X")
    assert dataclasses.is_dataclass(v)
    assert v == Vehicle("X", VehicleType.CAR)
    assert hash(v) == hash(Vehicle("X", VehicleType.CAR))
    with pytest.raises(dataclasses.FrozenInstanceError):
        v.plate = "Y"


def test_fit_rules():
    small, med, large = (ParkingSpot(i, t) for i, t in enumerate(SpotType, 1))
    assert [s.can_fit(moto()) for s in (small, med, large)] == [True, True, True]
    assert [s.can_fit(car()) for s in (small, med, large)] == [False, True, True]
    assert [s.can_fit(truck()) for s in (small, med, large)] == [False, False, True]


def test_spot_park_and_leave():
    s = ParkingSpot(7, SpotType.LARGE)
    assert s.spot_id == 7 and s.spot_type is SpotType.LARGE
    assert s.is_free and s.vehicle is None
    v = truck()
    s.park(v)
    assert not s.is_free and s.vehicle == v
    with pytest.raises(ParkingError):
        s.park(car())
    assert s.leave() == v
    assert s.is_free
    with pytest.raises(ParkingError):
        s.leave()


def test_spot_rejects_non_fitting():
    s = ParkingSpot(1, SpotType.SMALL)
    with pytest.raises(ParkingError):
        s.park(car())
    assert s.is_free


# ---- pricing
def test_pricing_is_abstract():
    with pytest.raises(TypeError):
        PricingStrategy()
    assert issubclass(HourlyPricing, PricingStrategy)
    assert issubclass(FlatPricing, PricingStrategy)


def test_hourly_pricing():
    p = HourlyPricing(RATES)
    assert p.fee(VehicleType.CAR, 0) == 2  # minimum one hour
    assert p.fee(VehicleType.CAR, 1) == 2
    assert p.fee(VehicleType.CAR, 60) == 2
    assert p.fee(VehicleType.CAR, 61) == 4
    assert p.fee(VehicleType.TRUCK, 150) == 15
    with pytest.raises(ValueError):
        HourlyPricing({VehicleType.CAR: 1}).fee(VehicleType.TRUCK, 10)


def test_flat_pricing():
    p = FlatPricing(10)
    assert p.fee(VehicleType.CAR, 500) == 10
    assert p.fee(VehicleType.MOTORCYCLE, 0) == 10


# ---- lot
def test_exceptions_hierarchy():
    for e in (LotFullError, DuplicateVehicleError, InvalidTicketError):
        assert issubclass(e, ParkingError)


def test_park_returns_ticket():
    lot, clock = make_lot()
    clock.now = 100
    t = lot.park(car("C1"))
    assert isinstance(t, Ticket)
    assert (t.ticket_id, t.plate, t.entry_time) == (1, "C1", 100)
    assert t.spot_id == 2  # smallest fitting spot for a car is MEDIUM
    assert lot.find_vehicle("C1") == 2
    assert lot.find_vehicle("nope") is None


def test_smallest_fitting_spot_and_tiebreak():
    lot, _ = make_lot([(5, SpotType.LARGE), (3, SpotType.MEDIUM), (4, SpotType.MEDIUM), (9, SpotType.SMALL)])
    assert lot.park(moto("a")).spot_id == 9
    assert lot.park(moto("b")).spot_id == 3  # small gone -> lowest id medium
    assert lot.park(car("c")).spot_id == 4
    assert lot.park(moto("d")).spot_id == 5  # only large left


def test_ticket_ids_increment():
    lot, _ = make_lot()
    ids = [lot.park(moto(f"m{i}")).ticket_id for i in range(3)]
    assert ids == [1, 2, 3]


def test_lot_full_for_that_vehicle_only():
    lot, _ = make_lot([(1, SpotType.SMALL), (2, SpotType.MEDIUM)])
    with pytest.raises(LotFullError):
        lot.park(truck())  # no large spot at all
    lot.park(car("c"))
    assert lot.available_count() == 1
    with pytest.raises(LotFullError):
        lot.park(car("c2"))
    lot.park(moto("m"))  # small spot still free
    assert lot.is_full()
    with pytest.raises(LotFullError):
        lot.park(moto("m2"))


def test_failed_park_does_not_burn_ticket_id():
    lot, _ = make_lot([(1, SpotType.SMALL)])
    with pytest.raises(LotFullError):
        lot.park(truck())
    assert lot.park(moto()).ticket_id == 1


def test_duplicate_plate():
    lot, _ = make_lot()
    lot.park(car("C1"))
    with pytest.raises(DuplicateVehicleError):
        lot.park(car("C1"))
    assert lot.available_count() == 2


def test_unpark_fee_and_free_spot():
    lot, clock = make_lot()
    t = lot.park(car("C1"))
    clock.advance(95)
    assert lot.unpark(t.ticket_id) == 4  # 2 hours x 2
    assert lot.find_vehicle("C1") is None
    assert lot.available_count() == 3
    assert lot.park(car("C1")).spot_id == 2  # re-park allowed, spot reusable


def test_unpark_invalid_and_double():
    lot, _ = make_lot()
    with pytest.raises(InvalidTicketError):
        lot.unpark(99)
    t = lot.park(moto())
    lot.unpark(t.ticket_id)
    with pytest.raises(InvalidTicketError):
        lot.unpark(t.ticket_id)


def test_new_ticket_ids_not_reused():
    lot, _ = make_lot()
    t1 = lot.park(moto("a"))
    lot.unpark(t1.ticket_id)
    assert lot.park(moto("a")).ticket_id == 2


def test_available_count_by_type():
    lot, _ = make_lot()
    assert lot.available_count() == 3
    assert lot.available_count(SpotType.LARGE) == 1
    lot.park(truck())
    assert lot.available_count(SpotType.LARGE) == 0
    assert lot.available_count() == 2
    assert lot.is_full() is False


def test_occupancy():
    lot, _ = make_lot([(1, SpotType.SMALL), (2, SpotType.SMALL), (3, SpotType.LARGE)])
    lot.park(moto("a"))
    assert lot.occupancy() == {SpotType.SMALL: (1, 2), SpotType.LARGE: (0, 1)}


def test_pluggable_pricing_strategy():
    lot, clock = make_lot(pricing=FlatPricing(7))
    t = lot.park(car())
    clock.advance(1000)
    assert lot.unpark(t.ticket_id) == 7


def test_default_clock_works():
    lot = ParkingLot([ParkingSpot(1, SpotType.SMALL)], FlatPricing(3))
    t = lot.park(moto())
    assert isinstance(t.entry_time, (int, float))
    assert lot.unpark(t.ticket_id) == 3
