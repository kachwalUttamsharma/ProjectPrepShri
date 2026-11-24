import json

import pytest
from fastapi.testclient import TestClient

from exercises import *

CSV = """Invoice ID , Customer,Email,Date,Amount
inv-001,  acme   corp ,Billing@ACME.com,03/04/2024,"$1,200.50"

INV-002,globex,,"Mar 5, 2024",99 EUR
inv-001,Acme Corp,billing@acme.com,2024-04-03,$5
,Nobody,n@x.com,2024-01-01,$1
INV-003,initech,a@b.com,not a date,lots
"""

GOOD = {"vendor": "Acme", "total": 120.5, "date": "2024-04-03"}


class FakeLLM:
    """Replays queued replies; records prompts."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.prompts = []

    def __call__(self, prompt):
        self.prompts.append(prompt)
        return self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]


def test_parse_messy_csv():
    rows = parse_messy_csv(CSV)
    assert len(rows) == 5  # blank line skipped
    assert rows[0]["invoice_id"] == "inv-001"
    assert rows[0]["customer"] == "acme   corp"
    assert rows[0]["amount"] == "$1,200.50"
    assert rows[1]["email"] == ""
    assert set(rows[0]) == {"invoice_id", "customer", "email", "date", "amount"}


def test_normalize_date():
    assert normalize_date("2024-04-03") == "2024-04-03"
    assert normalize_date("03/04/2024") == "2024-04-03"
    assert normalize_date(" Mar 5, 2024 ") == "2024-03-05"
    assert normalize_date("March 5, 2024") == "2024-03-05"
    assert normalize_date("5 Mar 2024") == "2024-03-05"
    assert normalize_date("garbage") is None
    assert normalize_date("") is None
    assert normalize_date("31/02/2024") is None


def test_parse_amount():
    assert parse_amount("$1,200.50") == (120050, "USD")
    assert parse_amount("99 EUR") == (9900, "EUR")
    assert parse_amount("£10") == (1000, "GBP")
    assert parse_amount("12.345") == (1235, None)
    assert parse_amount("0.1") == (10, None)
    assert parse_amount("") is None
    assert parse_amount("lots") is None


def test_clean_records():
    rows = parse_messy_csv(CSV)
    snapshot = [dict(r) for r in rows]
    clean, rejected = clean_records(rows)
    assert rows == snapshot  # input untouched
    assert [c["invoice_id"] for c in clean] == ["INV-001", "INV-002", "INV-003"]
    assert clean[0] == {
        "invoice_id": "INV-001", "customer": "Acme Corp", "email": "billing@acme.com",
        "date": "2024-04-03", "amount_cents": 120050, "currency": "USD",
    }
    assert clean[1]["date"] == "2024-03-05" and clean[1]["email"] == ""
    assert clean[2]["date"] is None and clean[2]["amount_cents"] is None
    assert [r["reason"] for r in rejected] == ["duplicate invoice_id", "missing invoice_id"]
    assert rejected[0]["row"]["amount"] == "$5"


def test_build_extraction_prompt():
    p = build_extraction_prompt("INVOICE from Acme total 5")
    assert "INVOICE from Acme total 5" in p
    for word in ("vendor", "total", "date", "JSON"):
        assert word in p


def test_validate_invoice():
    assert validate_invoice(GOOD) == []
    assert validate_invoice({"vendor": "A", "total": 0, "date": "2024-01-31"}) == []
    assert validate_invoice([1]) != []
    errs = " ".join(validate_invoice({"vendor": "", "total": "5", "date": "2024-13-01"}))
    assert "vendor" in errs and "total" in errs and "date" in errs
    assert any("total" in e for e in validate_invoice({"vendor": "A", "total": True, "date": "2024-01-01"}))
    assert any("total" in e for e in validate_invoice({"vendor": "A", "total": -1, "date": "2024-01-01"}))
    assert len(validate_invoice({})) == 3


def test_extract_happy_path_with_fences():
    llm = FakeLLM("```json\n" + json.dumps(GOOD) + "\n```")
    r = extract_with_fallback("doc", llm)
    assert r == {"data": GOOD, "needs_review": False, "error": None, "attempts": 1}
    assert len(llm.prompts) == 1


def test_extract_retries_then_succeeds():
    llm = FakeLLM("not json", json.dumps(GOOD))
    r = extract_with_fallback("doc", llm)
    assert r["data"] == GOOD and r["attempts"] == 2 and not r["needs_review"]
    assert "rejected" in llm.prompts[1] and llm.prompts[1] != llm.prompts[0]


def test_extract_falls_back():
    llm = FakeLLM("nope", json.dumps({"vendor": "A"}))
    r = extract_with_fallback("doc", llm)
    assert r["data"] is None and r["needs_review"] is True and r["attempts"] == 2
    assert "total" in r["error"]
    llm2 = FakeLLM("nope")
    r2 = extract_with_fallback("doc", llm2, max_retries=0)
    assert r2["attempts"] == 1 and len(llm2.prompts) == 1 and r2["needs_review"]
    assert extract_with_fallback("doc", FakeLLM("[1,2]"), max_retries=0)["needs_review"]


def test_api():
    client = TestClient(create_app(FakeLLM(json.dumps(GOOD))))
    assert client.get("/health").json() == {"status": "ok"}
    r = client.post("/extract", json={"text": "some invoice"})
    assert r.status_code == 200
    assert r.json()["data"] == GOOD and r.json()["needs_review"] is False
    assert client.post("/extract", json={"text": ""}).status_code == 422
    assert client.post("/extract", json={}).status_code == 422


def test_api_needs_review_is_200():
    client = TestClient(create_app(FakeLLM("garbage")))
    r = client.post("/extract", json={"text": "x"})
    assert r.status_code == 200
    assert r.json()["needs_review"] is True and r.json()["data"] is None


def test_scope_request_vague():
    r = scope_request("We want to automate everything in our invoices and integrate with SAP, plus a dashboard")
    assert "Extract structured fields from messy input (one document type)" in r["in_scope"]
    assert any("dashboard" in x.lower() for x in r["out_of_scope"])
    assert any("Production integration" in x for x in r["out_of_scope"])
    assert any("end-to-end" in x for x in r["out_of_scope"])
    assert any("system of record" in q for q in r["questions"])
    assert any("single workflow" in q for q in r["questions"])
    assert any("measure success" in q for q in r["questions"])
    assert any("sample" in q for q in r["questions"])
    assert len(set(r["questions"])) == len(r["questions"])


def test_scope_request_well_specified():
    r = scope_request("Classify support emails; we have 200 samples and need 90% accuracy")
    assert r["in_scope"] == [
        "Extract structured fields from messy input (one document type)",
        "LLM summarisation or classification for one workflow",
    ]
    assert r["out_of_scope"] == []
    assert r["questions"] == []


def test_scope_request_empty():
    r = scope_request("")
    assert r["in_scope"] == [] and r["out_of_scope"] == []
    assert len(r["questions"]) == 2


def test_generate_dockerfile():
    d = generate_dockerfile("3.14", "main:app", 8000)
    lines = d.splitlines()
    assert lines[0] == "FROM python:3.14-slim"
    assert d.endswith("\n")
    assert lines.index("COPY requirements.txt .") < lines.index("COPY . .")
    assert "EXPOSE 8000" in lines
    assert lines[-1] == 'CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]'
    with pytest.raises(ValueError):
        generate_dockerfile("3.14", "main", 8000)
    with pytest.raises(ValueError):
        generate_dockerfile("3.14", "main:app", 0)
    with pytest.raises(ValueError):
        generate_dockerfile("3.14", "main:app", 70000)


def test_render_readme():
    md = render_readme({
        "name": "Invoice Demo", "summary": "Extracts fields.",
        "setup": ["pip install -r requirements.txt", "uvicorn main:app"],
        "endpoints": [("POST", "/extract", "Extract fields")],
        "limitations": ["English only"],
    })
    assert md.startswith("# Invoice Demo\n\nExtracts fields.\n\n## Setup\n1. pip install")
    assert "2. uvicorn main:app" in md
    assert "| Method | Path | Description |\n|---|---|---|\n| POST | /extract | Extract fields |" in md
    assert "## Known limitations\n- English only\n" in md
    assert md.endswith("\n") and not md.endswith("\n\n")


def test_render_readme_empty_sections_and_errors():
    md = render_readme({"name": "X", "summary": "Y"})
    assert md.count("_None_") == 3
    for bad in ({"name": "X"}, {"summary": "Y"}, {"name": " ", "summary": "Y"}):
        with pytest.raises(ValueError):
            render_readme(bad)


def test_demo_script():
    out = demo_script([("Problem", 1), ("Live demo", 2.5), ("Limits", 1.5)])
    assert out == ["00:00-01:00 Problem", "01:00-03:30 Live demo", "03:30-05:00 Limits"]


def test_demo_script_validation():
    with pytest.raises(ValueError):
        demo_script([("a", 2), ("b", 2)])
    with pytest.raises(ValueError):
        demo_script([])
    with pytest.raises(ValueError):
        demo_script([("a", 6), ("b", -1)])


def test_risk_checklist():
    assert risk_checklist({}) == [m for _, m in RISK_CHECKS]
    full = {k: True for k, _ in RISK_CHECKS}
    assert risk_checklist(full) == []
    partial = dict(full, has_eval_set=False, timeouts_set=False)
    assert risk_checklist(partial) == [
        dict(RISK_CHECKS)["has_eval_set"], dict(RISK_CHECKS)["timeouts_set"]
    ]
