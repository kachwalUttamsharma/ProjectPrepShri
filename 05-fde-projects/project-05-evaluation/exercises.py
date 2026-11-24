"""Project 5: evaluating an LLM feature. Read lesson.md for the spec.

Replace each `...` with your code. No network or API key is needed:
`llm` is always an injected callable `llm(prompt: str) -> str`.

A "result" is a dict: {"id", "input", "expected", "predicted"}.
"""
import json
from collections import Counter

ERROR_LABEL = "error"  # predicted value recorded when the llm raises


def load_test_set(path):
    """Load a JSONL test set and return a list of dicts.

    Each non-blank line must be a JSON object with keys "id", "input", "expected".
    - Skip blank lines.
    - Invalid JSON, a non-object, or a missing key -> ValueError whose message
      contains the 1-based line number, e.g. "line 3: ...".
    - Duplicate ids -> ValueError mentioning the duplicate id.
    Hint: enumerate(f, start=1); json.JSONDecodeError is a ValueError subclass.
    """
    ...


def build_prompt(template, case_input):
    """Return the template with the literal text "{input}" replaced by case_input.

    Hint: use str.replace, NOT str.format -- templates may contain other braces
    such as JSON examples like {"label": "billing"}.
    """
    ...


def normalize_label(text):
    """Normalise raw model output into a label: strip whitespace and trailing
    punctuation ('.', '!', quotes), lowercase.  ' "Billing." ' -> 'billing'.
    Hint: str.strip() accepts a string of characters to remove.
    """
    ...


def run_prompt(llm, template, cases):
    """Run `llm` over every case and return a list of result dicts (same order).

    prompt = build_prompt(template, case["input"]); predicted = normalize_label(llm(prompt)).
    If llm raises any Exception, predicted = ERROR_LABEL (do not crash the run).
    Result keys: id, input, expected, predicted.
    """
    ...


def accuracy(results):
    """Fraction (0.0-1.0) of results where predicted == expected. Empty -> 0.0."""
    ...


def confusion_matrix(results):
    """Return a nested dict matrix[expected][predicted] -> count.

    Only include pairs that occur (plain dicts, not defaultdicts, so tests can
    compare with ==). Hint: Counter over (expected, predicted), then nest.
    """
    ...


def precision_recall_f1(results, label):
    """Return {"precision": p, "recall": r, "f1": f} for one class `label`.

    precision = TP / (TP + FP)  (FP: predicted label, expected something else)
    recall    = TP / (TP + FN)  (FN: expected label, predicted something else)
    f1        = 2pr / (p + r)
    Any zero denominator -> that value is 0.0.
    """
    ...


def worst_confusions(results, n=3):
    """Return the n most common mistakes as [((expected, predicted), count), ...].

    Only count failures. Sort by count descending, ties by the (expected, predicted)
    pair ascending. Hint: Counter, then sorted with key=lambda kv: (-kv[1], kv[0]).
    """
    ...


def compare_runs(old, new):
    """Compare two result lists over the SAME cases (matched by id).

    Return {"fixed": [...ids], "regressed": [...ids],
            "still_correct": [...ids], "still_wrong": [...ids]}
    - fixed: wrong in old, correct in new.  regressed: correct in old, wrong in new.
    - ids are listed in the order of `old`.
    - If the two runs do not contain exactly the same set of ids -> ValueError.
    """
    ...


def verdict(comparison, max_regressions=0):
    """Decide what to tell the customer about the NEW prompt. Return one of:
    - "hold": regressions > max_regressions  (checked first, even if many fixes)
    - "ship": otherwise, and fixed > regressed
    - "no change": otherwise (nothing meaningfully better)
    """
    ...


def format_report(name, results, top_n=2):
    """Return a plain-English multi-line report (str) for non-engineers.

    Required lines (exact text, tests check them):
      "Prompt: {name}"
      "Cases: {total}"
      "Accuracy: {pct}%"            pct = accuracy*100 rounded to 1 decimal, e.g. 75.0
      "Failures: {k}"
    Then, if there are failures, a line "Most common mistakes:" followed by up to
    top_n lines like "- expected billing, got other (2 times)" (use worst_confusions;
    "1 times" is fine).  Free to add more.  Empty results -> "Accuracy: 0.0%".
    """
    ...
