import pytest

from exercises import *


class FakeLLM:
    """Returns scripted replies in order (repeats the last) and records prompts."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.prompts = []

    def __call__(self, prompt):
        self.prompts.append(prompt)
        i = min(len(self.prompts) - 1, len(self.replies) - 1)
        return self.replies[i]


SCHEMA = {"name": str, "qty": int, "urgent": bool}
GOOD = '{"name": "pallet", "qty": 3, "urgent": false}'


def test_build_prompt_basic():
    p = build_prompt(" You are terse. ", "Extract fields.", [], " ship 3 pallets ")
    assert p == "You are terse.\n\nInstructions:\nExtract fields.\n\nInput: ship 3 pallets\nOutput:"


def test_build_prompt_examples():
    p = build_prompt("S", "I", [("a", "1"), ("b", "2")], "c")
    assert p == "S\n\nInstructions:\nI\n\nExamples:\nInput: a\nOutput: 1\n\nInput: b\nOutput: 2\n\nInput: c\nOutput:"


def test_extract_json_plain_and_array():
    assert extract_json(' {"a": 1} ') == {"a": 1}
    assert extract_json("[1, 2]") == [1, 2]


def test_extract_json_fenced():
    assert extract_json('Here:\n```json\n{"a": {"b": 2}}\n```\nbye') == {"a": {"b": 2}}
    assert extract_json('```\n{"a": 1}\n```') == {"a": 1}


def test_extract_json_with_chatter():
    assert extract_json('Sure! Here you go: {"a": {"b": [1, 2]}} Hope that helps.') == {"a": {"b": [1, 2]}}


def test_extract_json_failure():
    with pytest.raises(LLMOutputError, match="JSON"):
        extract_json("I cannot help with that.")
    with pytest.raises(LLMOutputError):
        extract_json("{not json}")
    assert issubclass(LLMOutputError, ValueError)


def test_validate_fields_ok():
    assert validate_fields({"name": "x", "qty": 1, "urgent": True, "extra": 1}, SCHEMA) == []


def test_validate_fields_errors():
    errs = validate_fields({"name": 5, "urgent": "yes"}, SCHEMA)
    assert errs == [
        "field name should be str, got int",
        "missing field: qty",
        "field urgent should be bool, got str",
    ]


def test_validate_fields_bool_int_float():
    assert validate_fields({"n": True}, {"n": int}) == ["field n should be int, got bool"]
    assert validate_fields({"n": 3}, {"n": float}) == []
    assert validate_fields({"n": "a"}, {"n": (int, float)}) == ["field n should be int|float, got str"]


def test_validate_fields_not_dict():
    assert validate_fields([1], SCHEMA) == ["expected a JSON object"]


def test_get_structured_first_try():
    llm = FakeLLM([GOOD])
    assert get_structured(llm, "P", SCHEMA) == {"name": "pallet", "qty": 3, "urgent": False}
    assert llm.prompts == ["P"]


def test_get_structured_retries_on_bad_json():
    llm = FakeLLM(["nope", "```json\n" + GOOD + "\n```"])
    out = get_structured(llm, "P", SCHEMA)
    assert out["qty"] == 3
    assert len(llm.prompts) == 2
    assert llm.prompts[1].startswith("P\n\nYour previous reply was invalid: ")
    assert llm.prompts[1].endswith("\nReturn only valid JSON.")


def test_get_structured_retries_on_validation_error():
    llm = FakeLLM(['{"name": "x"}', GOOD])
    get_structured(llm, "P", SCHEMA)
    assert "missing field: qty; missing field: urgent" in llm.prompts[1]


def test_get_structured_does_not_stack_repairs():
    llm = FakeLLM(["bad", "bad", GOOD])
    get_structured(llm, "P", SCHEMA, max_retries=2)
    assert len(llm.prompts) == 3
    assert llm.prompts[2].count("Your previous reply was invalid") == 1


def test_get_structured_gives_up():
    llm = FakeLLM(["bad"])
    with pytest.raises(LLMOutputError, match="after 3 attempts"):
        get_structured(llm, "P", SCHEMA, max_retries=2)
    assert len(llm.prompts) == 3
    llm0 = FakeLLM(["bad"])
    with pytest.raises(LLMOutputError, match="after 1 attempts"):
        get_structured(llm0, "P", SCHEMA, max_retries=0)


def test_collect_stream():
    seen = []
    gen = (c for c in ["Hel", "", None, "lo", " there"])
    assert collect_stream(gen, on_chunk=seen.append) == "Hello there"
    assert seen == ["Hel", "lo", " there"]
    assert collect_stream([]) == ""
    assert collect_stream(["a", "b"]) == "ab"


def test_parse_sse_lines():
    lines = [
        ": keepalive",
        "",
        'data: {"text": "Hel"}',
        "event: ping",
        "data: not json",
        'data: {"other": 1}',
        'data: {"text": "lo"}',
        "data: [DONE]",
        'data: {"text": "ignored"}',
    ]
    assert parse_sse_lines(lines) == ["Hel", "lo"]
    assert parse_sse_lines(iter([])) == []


def test_estimate_tokens():
    assert estimate_tokens("") == 0
    assert estimate_tokens("abcd") == 1
    assert estimate_tokens("abcde") == 2
    assert estimate_tokens("a" * 400) == 100


def test_estimate_cost():
    assert estimate_cost(1_000_000, 0, 3.0, 15.0) == 3.0
    assert estimate_cost(1000, 500, 3.0, 15.0) == pytest.approx(0.0105)
    assert estimate_cost(1, 1, 3.0, 15.0) == 0.000018
    with pytest.raises(ValueError):
        estimate_cost(-1, 0, 1, 1)
    with pytest.raises(ValueError):
        estimate_cost(1, 1, 1, -1)


def test_usage_tracker():
    t = UsageTracker(3.0, 15.0)
    assert (t.calls, t.total_tokens, t.total_cost) == (0, 0, 0)
    t.record("a" * 400, "b" * 40)
    t.record("c" * 4, "d" * 4)
    assert t.calls == 2
    assert t.input_tokens == 101
    assert t.output_tokens == 11
    assert t.total_tokens == 112
    assert t.total_cost == estimate_cost(101, 11, 3.0, 15.0)


def test_usage_tracker_wrap():
    t = UsageTracker(1.0, 1.0)
    llm = FakeLLM(["abcdefgh"])
    wrapped = t.wrap(llm)
    assert wrapped("abcd") == "abcdefgh"
    assert t.calls == 1 and t.input_tokens == 1 and t.output_tokens == 2
    get_structured(t.wrap(FakeLLM(["bad", GOOD])), "P", SCHEMA)
    assert t.calls == 3


def test_end_to_end_with_tracker():
    t = UsageTracker(3.0, 15.0)
    llm = t.wrap(FakeLLM(["oops", GOOD]))
    prompt = build_prompt("S", "Extract", [], "3 pallets, rush")
    assert get_structured(llm, prompt, SCHEMA)["name"] == "pallet"
    assert t.calls == 2 and t.total_cost > 0
