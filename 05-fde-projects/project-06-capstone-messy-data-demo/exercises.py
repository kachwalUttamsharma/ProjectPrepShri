"""Project 6 (capstone): messy data -> deployed demo. Read lesson.md first.

Everything LLM-related takes an injected `llm` callable: llm(prompt: str) -> str.
Tests use a FakeLLM; no network and no API key are needed.
"""
import csv
import io
import json
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from fastapi import FastAPI
from pydantic import BaseModel, Field

DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%b %d, %Y", "%B %d, %Y", "%d %b %Y", "%Y/%m/%d"]

CURRENCY_MARKERS = {"$": "USD", "USD": "USD", "€": "EUR", "EUR": "EUR", "£": "GBP", "GBP": "GBP"}

# (key, message shown when the key is missing/False in the project dict)
RISK_CHECKS = [
    ("has_eval_set", "No evaluation set: you cannot say how accurate the demo is."),
    ("fallback_for_bad_llm_output", "No fallback when the LLM returns invalid output."),
    ("human_in_loop", "No human review step for low-confidence results."),
    ("pii_handled", "PII/sensitive data handling is not decided."),
    ("cost_estimated", "Per-request cost and volume have not been estimated."),
    ("timeouts_set", "No timeouts/retries on LLM or customer-system calls."),
    ("secrets_in_env", "Secrets are not loaded from environment variables."),
]


# ---------------------------------------------------------------- 1. messy CSV
def parse_messy_csv(text):
    """Parse CSV text into a list of dicts with tidy keys and values.

    - Header names: strip, lowercase, spaces -> underscores ("Invoice ID" -> "invoice_id").
    - Values: stripped strings; missing values become "".
    - Rows that are completely blank (all values "") are skipped.
    Hint: csv.DictReader(io.StringIO(text)). Beware of `None` for short rows.
    """
    ...


# ---------------------------------------------------------------- 2. dates
def normalize_date(s):
    """Return an ISO date string 'YYYY-MM-DD', or None if unparseable/empty.

    Try the formats in DATE_FORMATS in order. NOTE: "03/04/2024" is DD/MM/YYYY
    (3 April) - state this assumption to the customer! Strip whitespace first.
    Hint: datetime.strptime(...).date().isoformat(), catch ValueError.
    """
    ...


# ---------------------------------------------------------------- 3. money
def parse_amount(s):
    """Parse messy money text into (cents: int, currency: str | None), or None.

    "$1,200.50" -> (120050, "USD");  "99 EUR" -> (9900, "EUR");  "12.345" -> (1235, None)
    - Currency comes from markers in CURRENCY_MARKERS ($, USD, EUR, ...); none -> None.
    - Remove markers, commas and spaces, then parse with Decimal (never float for money).
    - Round half up to whole cents. Empty or unparseable text -> None.
    Hint: Decimal.quantize / (d * 100).to_integral_value(ROUND_HALF_UP).
    """
    ...


# ---------------------------------------------------------------- 4. cleaning
def clean_records(rows):
    """Normalise parsed rows. Return (clean, rejected).

    Each input row has keys invoice_id, customer, email, date, amount (as strings).
    Each clean row is a dict with:
      invoice_id   - stripped, uppercased
      customer     - whitespace collapsed, Title Case ("  acme   corp " -> "Acme Corp")
      email        - lowercased ("" if missing)
      date         - normalize_date(...) (may be None)
      amount_cents - int or None (from parse_amount)
      currency     - str or None (from parse_amount)
    Reject (do not drop silently!) rows into `rejected` as
    {"row": original_row, "reason": "missing invoice_id"} or
    {"row": original_row, "reason": "duplicate invoice_id"} (first occurrence wins).
    Preserve input order. Never mutate the input rows.
    """
    ...


# ---------------------------------------------------------------- 5. LLM extraction
def build_extraction_prompt(text):
    """Return a prompt asking the model to extract invoice fields as JSON.

    It must: contain the document `text` verbatim, mention the keys "vendor",
    "total" and "date" (YYYY-MM-DD), and tell the model to reply with JSON only.
    """
    ...


def validate_invoice(data):
    """Return a list of error strings (empty list = valid).

    Rules: data must be a dict; "vendor" non-empty str; "total" an int/float
    (not bool) and >= 0; "date" a real date in YYYY-MM-DD form.
    Each error must mention the offending key name (e.g. "total must be a number").
    Missing keys are errors too.
    """
    ...


def extract_with_fallback(text, llm, max_retries=1):
    """Ask the LLM to extract fields; retry on bad output; never raise.

    Make up to 1 + max_retries calls to llm(prompt). For each reply: strip
    ```json fences, json.loads, then validate_invoice. On the first valid reply
    return {"data": parsed, "needs_review": False, "error": None, "attempts": n}.
    On a retry, append the previous error text to the prompt so the model can fix it.
    If every attempt fails return
    {"data": None, "needs_review": True, "error": "<last error>", "attempts": n}.
    """
    ...


# ---------------------------------------------------------------- 6. API
class ExtractRequest(BaseModel):
    text: str = Field(min_length=1)


def create_app(llm):
    """Build a FastAPI app around the injected `llm`.

    GET  /health  -> {"status": "ok"}
    POST /extract -> body {"text": "..."} (empty text -> 422 via ExtractRequest);
                     returns extract_with_fallback(text, llm) as JSON, status 200
                     even when needs_review is True (the caller decides what to do).
    Hint: define the app inside this function so each test gets its own FakeLLM.
    """
    ...


# ---------------------------------------------------------------- 7. scoping
def scope_request(text):
    """Turn a vague customer request into {"in_scope", "out_of_scope", "questions"} (lists of str).

    Lowercase the text and split into words (re.findall(r"[a-z0-9%]+|%", ...) or similar).
    Apply these rules in order, appending each message at most once:
    1. any word in {invoice, invoices, pdf, pdfs, csv, spreadsheet, spreadsheets, email, emails, extract}
       -> in_scope: "Extract structured fields from messy input (one document type)"
    2. any word starting with summar / classif / triage
       -> in_scope: "LLM summarisation or classification for one workflow"
    3. any word in {dashboard, portal, frontend}
       -> out_of_scope: "Custom dashboard or portal (demo uses API docs or one simple page)"
    4. any word in {salesforce, sap, erp, crm, workday, sync} or starting with "integrat"
       -> out_of_scope: "Production integration with customer systems (demo uses exported samples)"
       -> questions:    "Which system of record, and can we get a sandbox or sample export?"
    5. any word in {everything, fully, automate, automatic, automatically} or the phrase "end-to-end"/"all of our"
       -> out_of_scope: "Full end-to-end automation (keep a human in the loop)"
       -> questions:    "Which single workflow should the demo cover first?"
    6. no word in {accuracy, target, metric, metrics} and no "%" in text
       -> questions: "How will we measure success (e.g. a field accuracy target)?"
    7. no word "sample"/"samples"
       -> questions: "Can we get 20+ real, anonymised sample documents?"
    """
    ...


# ---------------------------------------------------------------- 8. Dockerfile
def generate_dockerfile(python_version, app_module, port):
    """Return Dockerfile text (ending with a newline) for a FastAPI app.

    Lines, in this order:
      FROM python:<python_version>-slim
      WORKDIR /app
      COPY requirements.txt .
      RUN pip install --no-cache-dir -r requirements.txt
      COPY . .
      EXPOSE <port>
      CMD ["uvicorn", "<app_module>", "--host", "0.0.0.0", "--port", "<port>"]
    Copying requirements.txt BEFORE the code keeps the dependency layer cached.
    Raise ValueError if app_module has no ":" (expected "main:app") or port is
    not an int in 1..65535.
    """
    ...


# ---------------------------------------------------------------- 9. README
def render_readme(project):
    """Render a README.md string from a dict.

    project keys: name (str), summary (str) - both required (ValueError if missing/empty);
    setup (list[str]), endpoints (list[(method, path, description)]), limitations (list[str]) - optional.
    Layout (blank line between blocks):
      # <name>
      <summary>
      ## Setup            -> numbered list "1. step"   (or "_None_")
      ## Endpoints        -> table: header "| Method | Path | Description |", separator "|---|---|---|", rows "| POST | /extract | ... |"  (or "_None_")
      ## Known limitations -> bullet list "- item"       (or "_None_")
    Always include all three sections. Result ends with a single newline.
    """
    ...


# ---------------------------------------------------------------- 10. demo script
def demo_script(steps):
    """Build a timed demo plan. steps = list of (title, minutes) with minutes > 0.

    The minutes must add up to exactly 5 (use a tolerance of 1e-9), else ValueError;
    a non-positive duration or empty list is also a ValueError.
    Return a list of strings "MM:SS-MM:SS title" with cumulative times:
      [("Problem", 1), ("Live demo", 2.5), ("Limits", 1.5)] ->
      ["00:00-01:00 Problem", "01:00-03:30 Live demo", "03:30-05:00 Limits"]
    Hint: work in whole seconds: round(minutes * 60); divmod(seconds, 60).
    """
    ...


# ---------------------------------------------------------------- 11. risks
def risk_checklist(project):
    """Return the messages from RISK_CHECKS whose key is missing or falsy in `project`.

    Keep the order of RISK_CHECKS. Example: {} -> all messages; a project with every
    key True -> []. Hint: a list comprehension over RISK_CHECKS.
    """
    ...
