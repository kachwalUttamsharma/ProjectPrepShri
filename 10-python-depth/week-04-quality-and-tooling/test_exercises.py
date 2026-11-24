import io
import logging
from unittest.mock import Mock

import pytest

from exercises import *


# ---------- 1. exception hierarchy ----------
def test_exception_hierarchy():
    assert issubclass(NotFoundError, AppError)
    assert issubclass(ValidationFailed, AppError)
    assert issubclass(AppError, Exception)


def test_exception_codes_and_messages():
    assert AppError("boom").code == 500
    assert AppError("boom", code=503).code == 503
    e = NotFoundError("missing")
    assert e.code == 404 and e.message == "missing" and str(e) == "missing"
    v = ValidationFailed("bad")
    assert v.code == 422 and v.message == "bad"


# ---------- 2. parse_age (parametrize) ----------
@pytest.mark.parametrize("text,expected", [("0", 0), ("42", 42), (" 150 ", 150)])
def test_parse_age_ok(text, expected):
    assert parse_age(text) == expected


@pytest.mark.parametrize("text", ["abc", "", "-1", "151", None, "3.5"])
def test_parse_age_invalid(text):
    with pytest.raises(ValidationFailed):
        parse_age(text)


def test_parse_age_chains_cause():
    with pytest.raises(ValidationFailed) as info:
        parse_age("abc")
    assert isinstance(info.value.__cause__, ValueError)


# ---------- 3. retry ----------
def make_flaky(fail_times, exc=ValueError):
    state = {"calls": 0}

    def f():
        state["calls"] += 1
        if state["calls"] <= fail_times:
            raise exc("fail")
        return "ok"

    f.state = state
    return f


def test_retry_succeeds_after_failures():
    f = make_flaky(2)
    assert retry(f, attempts=3) == "ok"
    assert f.state["calls"] == 3


def test_retry_gives_up_and_reraises_last():
    f = make_flaky(5)
    with pytest.raises(ValueError):
        retry(f, attempts=3)
    assert f.state["calls"] == 3


def test_retry_only_catches_listed_exceptions():
    f = make_flaky(1, exc=KeyError)
    with pytest.raises(KeyError):
        retry(f, attempts=3, exceptions=(ValueError,))
    assert f.state["calls"] == 1


def test_retry_no_failure_single_call():
    f = make_flaky(0)
    assert retry(f) == "ok"
    assert f.state["calls"] == 1


def test_retry_rejects_bad_attempts():
    with pytest.raises(ValueError):
        retry(lambda: 1, attempts=0)


# ---------- 4. get_logger ----------
def test_get_logger_format_and_level():
    stream = io.StringIO()
    log = get_logger("w4.format", stream)
    log.info("hi")
    log.debug("hidden")
    assert stream.getvalue() == "INFO:hi\n"


def test_get_logger_no_duplicate_handlers_and_no_propagation():
    stream = io.StringIO()
    a = get_logger("w4.dupe", stream)
    b = get_logger("w4.dupe", stream)
    assert a is b
    assert len(a.handlers) == 1
    assert a.propagate is False
    a.warning("once")
    assert stream.getvalue() == "WARNING:once\n"


# ---------- 5. process_orders (caplog) ----------
def test_process_orders_total_and_logs(caplog):
    logger = logging.getLogger("w4.orders")
    orders = [
        {"id": 1, "amount": 10},
        {"id": 2, "amount": -5},
        {"id": 3, "amount": 7},
    ]
    with caplog.at_level(logging.INFO, logger="w4.orders"):
        total = process_orders(orders, logger)
    assert total == 17
    assert caplog.messages == [
        "processed order 1",
        "skipping order 2: negative amount",
        "processed order 3",
    ]
    levels = [r.levelno for r in caplog.records]
    assert levels == [logging.INFO, logging.WARNING, logging.INFO]


def test_process_orders_empty(caplog):
    with caplog.at_level(logging.INFO, logger="w4.orders"):
        assert process_orders([], logging.getLogger("w4.orders")) == 0
    assert caplog.records == []


# ---------- 6. fetch_username (Mock) ----------
def make_client(status, payload=None):
    resp = Mock()
    resp.status_code = status
    resp.json.return_value = payload
    client = Mock()
    client.get.return_value = resp
    return client


def test_fetch_username_ok():
    client = make_client(200, {"name": "Ada"})
    assert fetch_username(7, client) == "Ada"
    client.get.assert_called_once_with("/users/7")


def test_fetch_username_not_found():
    client = make_client(404)
    with pytest.raises(NotFoundError) as info:
        fetch_username(9, client)
    assert info.value.code == 404


def test_fetch_username_upstream_error():
    client = make_client(500)
    with pytest.raises(AppError) as info:
        fetch_username(1, client)
    assert not isinstance(info.value, NotFoundError)
    assert info.value.code == 502


# ---------- 7. get_config (monkeypatch) ----------
def test_get_config_defaults(monkeypatch):
    for k in ("APP_DEBUG", "APP_PORT", "APP_NAME"):
        monkeypatch.delenv(k, raising=False)
    assert get_config() == {"debug": False, "port": 8000, "name": "app"}


def test_get_config_from_env(monkeypatch):
    monkeypatch.setenv("APP_DEBUG", "true")
    monkeypatch.setenv("APP_PORT", "9001")
    monkeypatch.setenv("APP_NAME", "svc")
    assert get_config() == {"debug": True, "port": 9001, "name": "svc"}


@pytest.mark.parametrize("raw,expected", [("1", True), ("TRUE", True), ("0", False), ("no", False)])
def test_get_config_debug_values(monkeypatch, raw, expected):
    monkeypatch.setenv("APP_DEBUG", raw)
    assert get_config()["debug"] is expected


# ---------- 8. count_words_in_file (tmp_path) ----------
def test_count_words_in_file(tmp_path):
    p = tmp_path / "notes.txt"
    p.write_text("The cat and the Dog\nand THE bird\n")
    assert count_words_in_file(p) == {
        "the": 3, "cat": 1, "and": 2, "dog": 1, "bird": 1,
    }


def test_count_words_in_empty_file(tmp_path):
    p = tmp_path / "empty.txt"
    p.write_text("")
    assert count_words_in_file(str(p)) == {}


# ---------- 9. best_time (fake timer, deterministic) ----------
def test_best_time_uses_min_of_repeats():
    # Timer is read twice per repeat: (start, end). Runs take 1, 2, 1 -> /number
    ticks = iter([0, 1, 10, 12, 20, 21])
    calls = []
    result = best_time(lambda: calls.append(1), number=2, repeat=3, timer=lambda: next(ticks))
    assert result == pytest.approx(0.5)
    assert len(calls) == 6  # number * repeat


def test_best_time_picks_fastest_even_if_not_first():
    ticks = iter([0, 8, 8, 10])
    assert best_time(lambda: None, number=1, repeat=2, timer=lambda: next(ticks)) == pytest.approx(2)


# ---------- 10. profile_calls ----------
def test_profile_calls_counts_calls():
    def helper():
        return 1

    def work():
        for _ in range(5):
            helper()

    calls = profile_calls(work)
    assert calls["helper"] == 5
    assert calls["work"] == 1


def test_profile_calls_propagates_errors():
    def boom():
        raise RuntimeError("x")

    with pytest.raises(RuntimeError):
        profile_calls(boom)
