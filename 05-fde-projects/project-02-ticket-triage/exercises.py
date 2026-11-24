"""Project 2: support-ticket triage service. Read lesson.md for the scenario.

Models, enums and constants are provided. Implement everything marked `...`.
`llm` is always a plain callable: llm(prompt: str) -> str. No network needed.
"""
import json
import re
from enum import Enum
from typing import Callable, Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field

LLM = Callable[[str], str]


class Category(str, Enum):
    BILLING = "billing"
    ACCOUNT = "account"
    BUG = "bug"
    FEATURE_REQUEST = "feature_request"
    OTHER = "other"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


# Lowest to highest. Use .index() to move up/down.
PRIORITY_ORDER = [Priority.LOW, Priority.MEDIUM, Priority.HIGH, Priority.URGENT]

# Rule-based fallback keywords. Dict order matters: first matching category wins.
KEYWORDS = {
    Category.BILLING: ["invoice", "refund", "charge", "charged", "billing", "payment"],
    Category.ACCOUNT: ["password", "login", "log in", "locked out", "account"],
    Category.BUG: ["error", "crash", "bug", "broken", "not working", "500"],
    Category.FEATURE_REQUEST: ["feature", "please add", "would be great", "wish"],
}
URGENT_WORDS = ["outage", "down", "security", "breach", "data loss"]
HIGH_WORDS = ["asap", "urgent", "cannot", "can't", "blocked"]
LOW_WORDS = ["no rush", "when you get a chance", "just curious"]


class TriageRequest(BaseModel):
    subject: str = Field(min_length=1)
    body: str = ""
    customer_tier: Literal["standard", "enterprise"] = "standard"


class TriageResult(BaseModel):
    category: Category
    priority: Priority
    team: str
    reason: str = ""
    source: Literal["llm", "rules"]


def contains_any(text: str, words: list[str]) -> bool:
    """True if any word appears in text as a whole word/phrase, case-insensitive.
    'down' must match 'The site is down!' but NOT 'download'.
    Hint: re.search(r"\\b" + re.escape(word) + r"\\b", text, re.IGNORECASE)
    """
    ...


def build_triage_prompt(ticket: TriageRequest) -> str:
    """Build the prompt sent to the LLM. It must contain: the subject, the body,
    the customer tier, every allowed category value, every allowed priority value,
    and an instruction to reply with ONLY a JSON object with keys
    "category", "priority", "reason".
    """
    ...


def parse_llm_triage(raw: str) -> dict:
    """Parse the LLM's raw reply into {"category": Category, "priority": Priority, "reason": str}.
    - The reply may be wrapped in prose or ```json fences: take the text from the
      first '{' to the last '}'.
    - "reason" is optional (default ""). "category"/"priority" are required and
      must be valid enum values (case-insensitive, e.g. "HIGH" is fine).
    - Raise ValueError for: no JSON object, invalid JSON, non-object JSON,
      missing key, unknown category/priority.
    Hint: Category(value.lower()) raises ValueError for unknown values.
    """
    ...


def keyword_classify(text: str) -> Category:
    """Rule-based category: walk KEYWORDS in order, return the first category with
    a matching keyword (use contains_any). No match -> Category.OTHER."""
    ...


def keyword_priority(text: str) -> Priority:
    """Rule-based priority. Check in this order: URGENT_WORDS -> URGENT,
    HIGH_WORDS -> HIGH, LOW_WORDS -> LOW, otherwise MEDIUM."""
    ...


def apply_escalation(priority: Priority, tier: str) -> Priority:
    """Enterprise customers get bumped up ONE level (capped at URGENT).
    Any other tier is returned unchanged. Hint: PRIORITY_ORDER.index."""
    ...


def route_team(category: Category, priority: Priority) -> str:
    """Pick the team that owns the ticket.
    URGENT (any category) -> "oncall".
    Otherwise: billing -> "finance-support", account -> "identity-support",
    bug -> "engineering", feature_request -> "product", other -> "general-support".
    """
    ...


def triage_ticket(ticket: TriageRequest, llm: LLM) -> TriageResult:
    """Full pipeline.
    1. prompt = build_triage_prompt(ticket); raw = llm(prompt); parsed = parse_llm_triage(raw).
    2. If the LLM call raises ANY Exception or the reply can't be parsed, fall back
       to rules on f"{subject} {body}": keyword_classify + keyword_priority,
       reason "rule-based fallback", source "rules".
    3. Either way apply_escalation with the customer tier, then route_team
       (never trust the LLM to choose the team). LLM path has source "llm".
    """
    ...


def create_app(llm: LLM) -> FastAPI:
    """App factory (so tests can inject a FakeLLM).
    - GET /health -> {"status": "ok"}
    - POST /triage: body TriageRequest, returns TriageResult (use response_model).
      An empty subject must produce 422 automatically from the Pydantic model.
    """
    ...
