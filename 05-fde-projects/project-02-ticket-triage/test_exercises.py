import json

import pytest
from fastapi.testclient import TestClient

from exercises import *


class FakeLLM:
    """Deterministic stand-in for a real model. Records prompts it received."""

    def __init__(self, reply="", raises=None):
        self.reply = reply
        self.raises = raises
        self.prompts = []

    def __call__(self, prompt):
        self.prompts.append(prompt)
        if self.raises:
            raise self.raises
        return self.reply


def good_reply(category="bug", priority="medium", reason="because"):
    return json.dumps({"category": category, "priority": priority, "reason": reason})


def test_contains_any_whole_words():
    assert contains_any("The site is DOWN!", ["down"]) is True
    assert contains_any("please download it", ["down"]) is False
    assert contains_any("I can't log in", ["log in"]) is True
    assert contains_any("hello", []) is False


def test_build_triage_prompt():
    t = TriageRequest(subject="Refund please", body="Charged twice", customer_tier="enterprise")
    p = build_triage_prompt(t)
    for s in ["Refund please", "Charged twice", "enterprise", "JSON", "reason"]:
        assert s in p
    for c in Category:
        assert c.value in p
    for pr in Priority:
        assert pr.value in p


def test_parse_llm_triage_plain_and_fenced():
    d = parse_llm_triage(good_reply("billing", "high", "double charge"))
    assert d == {"category": Category.BILLING, "priority": Priority.HIGH, "reason": "double charge"}
    fenced = "Sure!\n```json\n" + good_reply("account", "LOW") + "\n```\nHope it helps"
    d = parse_llm_triage(fenced)
    assert d["category"] is Category.ACCOUNT and d["priority"] is Priority.LOW
    assert parse_llm_triage('{"category": "bug", "priority": "low"}')["reason"] == ""


@pytest.mark.parametrize("raw", [
    "no json here",
    "{not valid json}",
    "[1, 2]",
    '{"priority": "low"}',
    '{"category": "bug"}',
    '{"category": "weather", "priority": "low"}',
    '{"category": "bug", "priority": "critical"}',
    "",
])
def test_parse_llm_triage_rejects_bad(raw):
    with pytest.raises(ValueError):
        parse_llm_triage(raw)


def test_keyword_classify():
    assert keyword_classify("I was charged twice on my invoice") is Category.BILLING
    assert keyword_classify("Locked out, forgot password") is Category.ACCOUNT
    assert keyword_classify("App crash with error 500") is Category.BUG
    assert keyword_classify("Please add dark mode") is Category.FEATURE_REQUEST
    assert keyword_classify("hello there") is Category.OTHER
    assert keyword_classify("REFUND ME") is Category.BILLING


def test_keyword_priority():
    assert keyword_priority("total outage in prod") is Priority.URGENT
    assert keyword_priority("We cannot export, asap") is Priority.HIGH
    assert keyword_priority("no rush, just a thought") is Priority.LOW
    assert keyword_priority("something is off") is Priority.MEDIUM
    assert keyword_priority("outage but also asap") is Priority.URGENT
    assert keyword_priority("my download is slow") is Priority.MEDIUM


def test_apply_escalation():
    assert apply_escalation(Priority.LOW, "enterprise") is Priority.MEDIUM
    assert apply_escalation(Priority.HIGH, "enterprise") is Priority.URGENT
    assert apply_escalation(Priority.URGENT, "enterprise") is Priority.URGENT
    assert apply_escalation(Priority.LOW, "standard") is Priority.LOW
    assert apply_escalation(Priority.HIGH, "free") is Priority.HIGH


def test_route_team():
    assert route_team(Category.BILLING, Priority.LOW) == "finance-support"
    assert route_team(Category.ACCOUNT, Priority.HIGH) == "identity-support"
    assert route_team(Category.BUG, Priority.MEDIUM) == "engineering"
    assert route_team(Category.FEATURE_REQUEST, Priority.LOW) == "product"
    assert route_team(Category.OTHER, Priority.LOW) == "general-support"
    for c in Category:
        assert route_team(c, Priority.URGENT) == "oncall"


def test_triage_ticket_llm_path():
    llm = FakeLLM(good_reply("billing", "medium", "double charge"))
    r = triage_ticket(TriageRequest(subject="Charged twice", body="help"), llm)
    assert r == TriageResult(category=Category.BILLING, priority=Priority.MEDIUM,
                             team="finance-support", reason="double charge", source="llm")
    assert len(llm.prompts) == 1 and "Charged twice" in llm.prompts[0]


def test_triage_ticket_escalates_enterprise_and_routes():
    llm = FakeLLM(good_reply("bug", "high"))
    r = triage_ticket(TriageRequest(subject="x", customer_tier="enterprise"), llm)
    assert r.priority is Priority.URGENT and r.team == "oncall" and r.source == "llm"


def test_triage_ticket_ignores_llm_team():
    llm = FakeLLM(json.dumps({"category": "bug", "priority": "low", "team": "marketing"}))
    r = triage_ticket(TriageRequest(subject="x"), llm)
    assert r.team == "engineering"


@pytest.mark.parametrize("llm", [
    FakeLLM("I am not sure, sorry"),
    FakeLLM('{"category": "nonsense", "priority": "low"}'),
    FakeLLM(raises=TimeoutError("llm timed out")),
    FakeLLM(raises=RuntimeError("boom")),
])
def test_triage_ticket_falls_back_to_rules(llm):
    r = triage_ticket(TriageRequest(subject="Invoice wrong", body="we cannot pay"), llm)
    assert r.source == "rules"
    assert r.category is Category.BILLING
    assert r.priority is Priority.HIGH
    assert r.team == "finance-support"
    assert r.reason == "rule-based fallback"


def test_fallback_still_escalates():
    r = triage_ticket(TriageRequest(subject="no rush: wish", customer_tier="enterprise"), FakeLLM("bad"))
    assert r.source == "rules" and r.category is Category.FEATURE_REQUEST
    assert r.priority is Priority.MEDIUM  # low bumped one level


def test_api_health_and_triage():
    llm = FakeLLM(good_reply("account", "high", "locked"))
    client = TestClient(create_app(llm))
    assert client.get("/health").json() == {"status": "ok"}
    resp = client.post("/triage", json={"subject": "Locked out", "body": "pls", "customer_tier": "standard"})
    assert resp.status_code == 200
    assert resp.json() == {"category": "account", "priority": "high", "team": "identity-support",
                           "reason": "locked", "source": "llm"}


def test_api_validation_and_fallback():
    client = TestClient(create_app(FakeLLM(raises=ConnectionError("down"))))
    assert client.post("/triage", json={"subject": ""}).status_code == 422
    assert client.post("/triage", json={"body": "x"}).status_code == 422
    assert client.post("/triage", json={"subject": "s", "customer_tier": "vip"}).status_code == 422
    r = client.post("/triage", json={"subject": "Site outage"})
    assert r.status_code == 200
    assert r.json()["priority"] == "urgent" and r.json()["team"] == "oncall" and r.json()["source"] == "rules"


def test_apps_are_independent():
    a = TestClient(create_app(FakeLLM(good_reply("bug", "low"))))
    b = TestClient(create_app(FakeLLM(good_reply("billing", "low"))))
    assert a.post("/triage", json={"subject": "s"}).json()["category"] == "bug"
    assert b.post("/triage", json={"subject": "s"}).json()["category"] == "billing"
