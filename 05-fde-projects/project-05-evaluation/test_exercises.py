import json

import pytest

from exercises import *

TEMPLATE = "Classify the ticket as billing, technical or other.\nTicket: {input}\nAnswer with one word."

CASES = [
    {"id": "t1", "input": "I was charged twice", "expected": "billing"},
    {"id": "t2", "input": "refund my invoice", "expected": "billing"},
    {"id": "t3", "input": "app crashes on login", "expected": "technical"},
    {"id": "t4", "input": "cannot reset password", "expected": "technical"},
    {"id": "t5", "input": "where is your office", "expected": "other"},
    {"id": "t6", "input": "thanks for the help", "expected": "other"},
    {"id": "t7", "input": "server is down", "expected": "technical"},
    {"id": "t8", "input": "update my card", "expected": "billing"},
]


class FakeLLM:
    """Deterministic fake: looks up the ticket text in a table."""

    def __init__(self, table, default="other"):
        self.table = table
        self.default = default
        self.prompts = []

    def __call__(self, prompt):
        self.prompts.append(prompt)
        ticket = prompt.split("Ticket: ", 1)[1].split("\n", 1)[0]
        return self.table.get(ticket, self.default)


# v1: gets t2 and t4 wrong (6/8 correct)
V1 = FakeLLM({
    "I was charged twice": "billing",
    "refund my invoice": "other",
    "app crashes on login": "technical",
    "cannot reset password": "other",
    "server is down": "technical",
    "update my card": "billing",
})
# v2: fixes t2 and t4 but regresses t6 and t7 (also 6/8), noisy formatting
V2 = FakeLLM({
    "I was charged twice": "Billing.",
    "refund my invoice": " billing\n",
    "app crashes on login": '"Technical"',
    "cannot reset password": "technical!",
    "server is down": "other",
    "update my card": "billing",
    "thanks for the help": "technical",
})


def write_jsonl(tmp_path, rows, name="cases.jsonl"):
    p = tmp_path / name
    p.write_text("\n".join(r if isinstance(r, str) else json.dumps(r) for r in rows) + "\n")
    return p


def res(id, expected, predicted):
    return {"id": id, "input": "x", "expected": expected, "predicted": predicted}


# ---------- load_test_set ----------
def test_load_test_set(tmp_path):
    p = write_jsonl(tmp_path, [CASES[0], "", CASES[1]])
    assert load_test_set(p) == CASES[:2]
    assert load_test_set(str(p)) == CASES[:2]


def test_load_test_set_bad_json_reports_line(tmp_path):
    p = write_jsonl(tmp_path, [CASES[0], "{not json"])
    with pytest.raises(ValueError, match="line 2"):
        load_test_set(p)


def test_load_test_set_missing_key_and_non_object(tmp_path):
    p = write_jsonl(tmp_path, [CASES[0], {"id": "x", "input": "hi"}])
    with pytest.raises(ValueError, match="line 2"):
        load_test_set(p)
    p = write_jsonl(tmp_path, [CASES[0], CASES[1], "[1, 2]"], "b.jsonl")
    with pytest.raises(ValueError, match="line 3"):
        load_test_set(p)


def test_load_test_set_duplicate_ids(tmp_path):
    p = write_jsonl(tmp_path, [CASES[0], CASES[0]])
    with pytest.raises(ValueError, match="t1"):
        load_test_set(p)


# ---------- prompt + normalise ----------
def test_build_prompt_keeps_other_braces():
    t = 'Return {"label": "x"} for: {input}'
    assert build_prompt(t, "hello") == 'Return {"label": "x"} for: hello'


def test_normalize_label():
    assert normalize_label(' "Billing." ') == "billing"
    assert normalize_label("TECHNICAL!\n") == "technical"
    assert normalize_label("other") == "other"


# ---------- run_prompt ----------
def test_run_prompt_v1():
    results = run_prompt(V1, TEMPLATE, CASES)
    assert [r["id"] for r in results] == [c["id"] for c in CASES]
    assert [r["predicted"] for r in results] == [
        "billing", "other", "technical", "other", "other", "other", "technical", "billing"]
    assert set(results[0]) == {"id", "input", "expected", "predicted"}
    assert results[0]["expected"] == "billing"
    assert "Ticket: I was charged twice" in V1.prompts[0]
    assert "{input}" not in V1.prompts[0]


def test_run_prompt_normalizes_output():
    results = run_prompt(V2, TEMPLATE, CASES)
    assert [r["predicted"] for r in results] == [
        "billing", "billing", "technical", "technical", "other", "technical", "other", "billing"]


def test_run_prompt_survives_llm_errors():
    def flaky(prompt):
        if "crashes" in prompt:
            raise TimeoutError("boom")
        return "billing"

    results = run_prompt(flaky, TEMPLATE, CASES[:4])
    assert results[2]["predicted"] == ERROR_LABEL
    assert results[0]["predicted"] == "billing"
    assert len(results) == 4


# ---------- metrics ----------
def test_accuracy():
    r1 = run_prompt(V1, TEMPLATE, CASES)
    r2 = run_prompt(V2, TEMPLATE, CASES)
    assert accuracy(r1) == 6 / 8
    assert accuracy(r2) == 6 / 8
    assert accuracy([]) == 0.0


def test_confusion_matrix():
    r1 = run_prompt(V1, TEMPLATE, CASES)
    assert confusion_matrix(r1) == {
        "billing": {"billing": 2, "other": 1},
        "technical": {"technical": 2, "other": 1},
        "other": {"other": 2},
    }
    assert confusion_matrix([]) == {}


def test_precision_recall_f1():
    r1 = run_prompt(V1, TEMPLATE, CASES)
    m = precision_recall_f1(r1, "billing")
    assert m["precision"] == 1.0
    assert m["recall"] == pytest.approx(2 / 3)
    assert m["f1"] == pytest.approx(0.8)
    m = precision_recall_f1(r1, "other")
    assert m["precision"] == pytest.approx(2 / 4)
    assert m["recall"] == 1.0
    assert m["f1"] == pytest.approx(2 * 0.5 * 1 / 1.5)


def test_precision_recall_f1_zero_division():
    r = [res("a", "x", "y")]
    assert precision_recall_f1(r, "x") == {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    assert precision_recall_f1(r, "never") == {"precision": 0.0, "recall": 0.0, "f1": 0.0}
    assert precision_recall_f1([], "x") == {"precision": 0.0, "recall": 0.0, "f1": 0.0}


# ---------- failure analysis ----------
def test_worst_confusions():
    results = [
        res("1", "billing", "other"), res("2", "billing", "other"),
        res("3", "technical", "other"), res("4", "other", "technical"),
        res("5", "billing", "billing"), res("6", "a", "b"),
    ]
    assert worst_confusions(results, 2) == [(("billing", "other"), 2), (("a", "b"), 1)]
    assert len(worst_confusions(results, 10)) == 4
    assert worst_confusions([res("1", "a", "a")]) == []


# ---------- regression comparison ----------
def test_compare_runs():
    old = run_prompt(V1, TEMPLATE, CASES)
    new = run_prompt(V2, TEMPLATE, CASES)
    cmp = compare_runs(old, new)
    assert cmp == {
        "fixed": ["t2", "t4"],
        "regressed": ["t6", "t7"],
        "still_correct": ["t1", "t3", "t5", "t8"],
        "still_wrong": [],
    }


def test_compare_runs_same_set_of_ids_required():
    old = [res("a", "x", "x"), res("b", "x", "x")]
    with pytest.raises(ValueError):
        compare_runs(old, old[:1])
    with pytest.raises(ValueError):
        compare_runs(old, [res("a", "x", "x"), res("c", "x", "x")])


def test_compare_runs_matches_by_id_not_position():
    old = [res("a", "x", "y"), res("b", "x", "x")]
    new = [res("b", "x", "x"), res("a", "x", "x")]
    cmp = compare_runs(old, new)
    assert cmp["fixed"] == ["a"]
    assert cmp["still_correct"] == ["b"]


def test_verdict():
    base = {"fixed": [], "regressed": [], "still_correct": [], "still_wrong": []}
    assert verdict({**base, "fixed": ["a", "b"], "regressed": ["c"]}) == "hold"
    assert verdict({**base, "fixed": ["a", "b"], "regressed": ["c"]}, max_regressions=1) == "ship"
    assert verdict({**base, "fixed": ["a"]}) == "ship"
    assert verdict(base) == "no change"
    assert verdict({**base, "fixed": ["a"], "regressed": ["b"]}, max_regressions=1) == "no change"
    assert verdict({**base, "regressed": ["b"]}, max_regressions=2) == "no change"


def test_verdict_on_real_runs():
    cmp = compare_runs(run_prompt(V1, TEMPLATE, CASES), run_prompt(V2, TEMPLATE, CASES))
    assert verdict(cmp) == "hold"
    assert verdict(cmp, max_regressions=2) == "no change"


# ---------- report ----------
def test_format_report():
    report = format_report("v1", run_prompt(V1, TEMPLATE, CASES))
    lines = report.splitlines()
    assert "Prompt: v1" in lines
    assert "Cases: 8" in lines
    assert "Accuracy: 75.0%" in lines
    assert "Failures: 2" in lines
    assert "Most common mistakes:" in lines
    assert "- expected billing, got other (1 times)" in report


def test_format_report_top_n_and_perfect():
    results = [res("1", "a", "b"), res("2", "a", "b"), res("3", "c", "d")]
    report = format_report("p", results, top_n=1)
    assert "- expected a, got b (2 times)" in report
    assert "expected c" not in report
    perfect = format_report("p", [res("1", "a", "a")])
    assert "Accuracy: 100.0%" in perfect
    assert "Failures: 0" in perfect
    assert "Most common mistakes" not in perfect
    assert "Accuracy: 0.0%" in format_report("p", [])
