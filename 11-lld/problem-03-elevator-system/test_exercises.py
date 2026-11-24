import pytest

from exercises import *


def opened(e, max_steps=200):
    """Step until idle; return the floors where doors opened, in order."""
    floors = []
    for _ in range(max_steps):
        if e.is_idle:
            return floors
        e.step()
        if e.state is ElevatorState.DOORS_OPEN:
            floors.append(e.floor)
    raise AssertionError("elevator never became idle")


def steps(e, n):
    for _ in range(n):
        e.step()


def make_ctrl(*starts, floors=21, strategy=None):
    elevators = [Elevator(i, floors, s) for i, s in enumerate(starts, 1)]
    return ElevatorController(elevators, strategy), elevators


# ---- Elevator basics
def test_initial_state():
    e = Elevator(1, 10)
    assert (e.elevator_id, e.num_floors, e.floor) == (1, 10, 0)
    assert e.direction is Direction.IDLE and e.state is ElevatorState.IDLE
    assert e.stops == [] and e.is_idle


def test_start_floor():
    assert Elevator(1, 10, 4).floor == 4


def test_invalid_construction():
    with pytest.raises(ValueError):
        Elevator(1, 1)
    with pytest.raises(InvalidFloorError):
        Elevator(1, 10, 10)
    with pytest.raises(InvalidFloorError):
        Elevator(1, 10, -1)


def test_add_stop_validates():
    e = Elevator(1, 10)
    for bad in (-1, 10, 99):
        with pytest.raises(InvalidFloorError):
            e.add_stop(bad)
    assert e.stops == []


def test_stops_sorted_deduped_and_copied():
    e = Elevator(1, 10)
    for f in (5, 2, 5, 9):
        e.add_stop(f)
    assert e.stops == [2, 5, 9]
    e.stops.append(7)
    assert e.stops == [2, 5, 9]


def test_error_hierarchy():
    assert issubclass(InvalidFloorError, ElevatorError)
    assert issubclass(UnknownElevatorError, ElevatorError)


# ---- stepping
def test_step_without_stops_stays_idle():
    e = Elevator(1, 10, 3)
    e.step()
    assert e.floor == 3 and e.state is ElevatorState.IDLE and e.direction is Direction.IDLE


def test_moves_one_floor_per_step_up():
    e = Elevator(1, 10)
    e.add_stop(3)
    e.step()
    assert (e.floor, e.state, e.direction) == (1, ElevatorState.MOVING_UP, Direction.UP)
    e.step()
    assert e.floor == 2
    e.step()
    assert e.floor == 3 and e.stops == [3]  # arrived, doors not yet open


def test_opens_doors_on_step_after_arrival():
    e = Elevator(1, 10)
    e.add_stop(2)
    steps(e, 2)
    e.step()
    assert e.state is ElevatorState.DOORS_OPEN and e.floor == 2 and e.stops == []
    assert not e.is_idle


def test_doors_close_on_next_step_and_direction_kept():
    e = Elevator(1, 10)
    e.add_stop(2)
    e.add_stop(5)
    steps(e, 3)  # at 2, doors open
    assert e.state is ElevatorState.DOORS_OPEN and e.direction is Direction.UP
    e.step()
    assert e.state is ElevatorState.IDLE and e.direction is Direction.UP
    e.step()
    assert e.floor == 3 and e.state is ElevatorState.MOVING_UP


def test_moves_down():
    e = Elevator(1, 10, 6)
    e.add_stop(4)
    e.step()
    assert (e.floor, e.state, e.direction) == (5, ElevatorState.MOVING_DOWN, Direction.DOWN)


def test_stop_at_current_floor_opens_doors():
    e = Elevator(1, 10, 4)
    e.add_stop(4)
    assert not e.is_idle
    e.step()
    assert e.state is ElevatorState.DOORS_OPEN and e.floor == 4


def test_add_stop_current_floor_while_doors_open_reopens():
    e = Elevator(1, 10, 4)
    e.add_stop(4)
    e.step()
    e.add_stop(4)
    e.step()  # closes
    assert e.state is ElevatorState.IDLE and e.stops == [4]
    e.step()  # opens again
    assert e.state is ElevatorState.DOORS_OPEN and e.stops == []


def test_full_trip_step_counts_and_idle_reset():
    e = Elevator(1, 10)
    e.add_stop(3)
    steps(e, 3)   # move
    steps(e, 1)   # open
    steps(e, 1)   # close
    assert e.state is ElevatorState.IDLE and e.direction is Direction.UP
    assert e.is_idle
    e.step()
    assert e.direction is Direction.IDLE


def test_is_idle_false_while_stops_pending():
    e = Elevator(1, 10)
    e.add_stop(1)
    assert not e.is_idle


# ---- LOOK ordering
def test_serves_stops_in_upward_sweep():
    e = Elevator(1, 12)
    for f in (5, 3, 8):
        e.add_stop(f)
    assert opened(e) == [3, 5, 8]


def test_idle_tie_prefers_lower_floor():
    e = Elevator(1, 12, 5)
    e.add_stop(8)
    e.add_stop(2)
    assert opened(e) == [2, 8]


def test_idle_goes_to_nearest_first():
    e = Elevator(1, 12, 5)
    e.add_stop(9)
    e.add_stop(4)
    assert opened(e) == [4, 9]


def test_keeps_direction_then_reverses():
    e = Elevator(1, 12)
    e.add_stop(6)
    steps(e, 3)  # at floor 3 heading up
    e.add_stop(1)
    e.add_stop(4)
    assert opened(e) == [4, 6, 1]


def test_downward_sweep_then_up():
    e = Elevator(1, 12, 10)
    e.add_stop(4)
    steps(e, 2)  # floor 8 going down
    e.add_stop(9)
    e.add_stop(2)
    e.add_stop(6)
    assert opened(e) == [6, 4, 2, 9]


def test_stop_added_on_passed_floor_waits_for_reversal():
    e = Elevator(1, 12)
    e.add_stop(5)
    steps(e, 3)  # floor 3
    e.add_stop(2)
    assert opened(e) == [5, 2]


def test_new_stop_ahead_is_served_in_passing():
    e = Elevator(1, 12)
    e.add_stop(9)
    steps(e, 2)
    e.add_stop(4)
    assert opened(e) == [4, 9]


# ---- strategies
def test_strategy_is_abstract():
    with pytest.raises(TypeError):
        SchedulingStrategy()


def test_nearest_picks_closest_idle():
    _, (a, b) = make_ctrl(2, 10)
    assert NearestElevatorStrategy().select([a, b], 8, Direction.UP) is b


def test_nearest_tie_lowest_id():
    _, (a, b) = make_ctrl(2, 8)
    assert NearestElevatorStrategy().select([a, b], 5, Direction.UP) is a


def test_nearest_prefers_idle_over_closer_opposite_mover():
    ctrl, (a, b) = make_ctrl(5, 9)
    ctrl.select_floor(1, 0)
    a.step()  # a at 4 heading DOWN
    assert a.floor == 4 and a.direction is Direction.DOWN
    assert NearestElevatorStrategy().select([a, b], 6, Direction.UP) is b


def test_nearest_picks_same_direction_approaching():
    ctrl, (a, b) = make_ctrl(0, 20)
    ctrl.select_floor(1, 9)
    a.step()  # a at 1 heading UP
    assert NearestElevatorStrategy().select([a, b], 5, Direction.UP) is a


def test_nearest_same_direction_but_already_passed_not_eligible():
    ctrl, (a, b) = make_ctrl(0, 20)
    ctrl.select_floor(1, 9)
    steps(a, 7)  # at 7 heading UP; floor 5 already passed
    assert NearestElevatorStrategy().select([a, b], 5, Direction.UP) is b


def test_nearest_falls_back_to_all_when_none_eligible():
    ctrl, (a, b) = make_ctrl(5, 8)
    ctrl.select_floor(1, 0)
    ctrl.select_floor(2, 0)
    a.step()
    b.step()  # a at 4, b at 7, both DOWN
    assert NearestElevatorStrategy().select([a, b], 6, Direction.UP) is b


def test_least_loaded_strategy():
    ctrl, (a, b) = make_ctrl(0, 10, strategy=LeastLoadedStrategy())
    ctrl.select_floor(2, 3)
    ctrl.select_floor(2, 4)
    ctrl.select_floor(1, 1)
    assert ctrl.request_pickup(10, Direction.DOWN) == 1  # 1 stop < 2 stops
    ctrl2, _ = make_ctrl(0, 10, strategy=LeastLoadedStrategy())
    assert ctrl2.request_pickup(9, Direction.UP) == 2  # tie 0/0 -> nearer


# ---- controller
def test_controller_validation():
    with pytest.raises(ValueError):
        ElevatorController([])
    with pytest.raises(ValueError):
        ElevatorController([Elevator(1, 5), Elevator(1, 5)])


def test_default_strategy_is_nearest():
    ctrl, _ = make_ctrl(0)
    assert isinstance(ctrl.strategy, NearestElevatorStrategy)


def test_request_pickup_returns_id_and_adds_stop():
    ctrl, (a, b) = make_ctrl(0, 15)
    assert ctrl.request_pickup(14, Direction.DOWN) == 2
    assert b.stops == [14] and a.stops == []


def test_request_pickup_validation():
    ctrl, (a,) = make_ctrl(0, floors=10)
    with pytest.raises(InvalidFloorError):
        ctrl.request_pickup(10, Direction.UP)
    with pytest.raises(ValueError):
        ctrl.request_pickup(3, Direction.IDLE)
    assert a.stops == []


def test_select_floor():
    ctrl, (a, b) = make_ctrl(0, 0, floors=10)
    ctrl.select_floor(2, 7)
    assert b.stops == [7] and a.stops == []
    with pytest.raises(UnknownElevatorError):
        ctrl.select_floor(9, 3)
    with pytest.raises(InvalidFloorError):
        ctrl.select_floor(1, 10)


def test_get():
    ctrl, (a,) = make_ctrl(0)
    assert ctrl.get(1) is a
    with pytest.raises(UnknownElevatorError):
        ctrl.get(5)


def test_custom_strategy_is_used():
    class Last(SchedulingStrategy):
        def select(self, elevators, floor, direction):
            return elevators[-1]

    ctrl, _ = make_ctrl(0, 1, 2, strategy=Last())
    assert ctrl.request_pickup(0, Direction.UP) == 3
    ctrl.strategy = NearestElevatorStrategy()
    assert ctrl.request_pickup(0, Direction.UP) == 1


def test_controller_step_moves_all_and_is_idle():
    ctrl, (a, b) = make_ctrl(0, 10, floors=15)
    assert ctrl.is_idle()
    ctrl.select_floor(1, 2)
    ctrl.select_floor(2, 7)
    assert not ctrl.is_idle()
    ctrl.step()
    assert (a.floor, b.floor) == (1, 9)
    for _ in range(50):
        if ctrl.is_idle():
            break
        ctrl.step()
    assert ctrl.is_idle() and (a.floor, b.floor) == (2, 7)


def test_end_to_end_two_cars():
    ctrl, (a, b) = make_ctrl(0, 20)
    assert ctrl.request_pickup(3, Direction.UP) == 1
    assert ctrl.request_pickup(18, Direction.DOWN) == 2
    ctrl.select_floor(1, 12)
    seen = {1: [], 2: []}
    for _ in range(100):
        if ctrl.is_idle():
            break
        ctrl.step()
        for e in (a, b):
            if e.state is ElevatorState.DOORS_OPEN:
                seen[e.elevator_id].append(e.floor)
    assert seen == {1: [3, 12], 2: [18]}
