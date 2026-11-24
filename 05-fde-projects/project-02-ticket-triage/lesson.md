# Project 2: Support-ticket triage service

Budget: ~2 hours. Plan: read + sketch the pipeline (15 min), pure functions (45 min), pipeline + API (45 min), demo rehearsal (15 min).

## The customer scenario
> "Northwind Software gets ~400 support emails a day. Two people read every one, tag it, and forward it to billing, engineering, product or the identity team. Enterprise customers complain when their tickets sit. Can an LLM do the first pass? We need something our helpdesk tool can call over HTTP by Friday."

Your job: a small FastAPI service that takes a ticket and returns category, priority and owning team. It must never be down because the LLM was down.

## Spec
- `POST /triage` body `{subject, body?, customer_tier: "standard"|"enterprise"}` returns `{category, priority, team, reason, source}`.
- `GET /health` returns `{"status": "ok"}`.
- Categories: billing, account, bug, feature_request, other. Priorities: low, medium, high, urgent.
- The LLM picks category + priority + a short reason. **Code** picks the team and applies escalation (enterprise +1 level, capped at urgent). Urgent always goes to `oncall`.
- If the LLM errors, times out, or returns garbage, fall back to keyword rules and mark `source: "rules"`.
- Empty subject -> 422 (Pydantic does this for you).

## Concepts
- **Dependency injection**: `create_app(llm)` takes any `llm(prompt) -> str`. Tests pass a `FakeLLM`; production passes a wrapper around the Anthropic SDK. This is also how you swap vendors.
- **Validate model output like user input**: the LLM is an untrusted client. Parse, check enums, reject.
- **Graceful degradation**: a dumb rules path beats a 500 error. Report which path was used.
- **Keep business rules in code**: routing and escalation are policy the customer can read, test and change. Do not bury them in a prompt.
- **App factory**: no globals, so each test builds its own app.
- Whole-word matching: `"down"` must not match `"download"`; use `\b` in regex.

## How an FDE would approach it
1. Ask for 20 real (anonymised) tickets and who they were routed to. This becomes your test set (Project 5).
2. Ship the rules baseline first. Now you have something to beat and a fallback.
3. Add the LLM for what rules can't do, keeping the output a tiny JSON schema.
4. Agree with the customer what "wrong" costs: a mis-routed feature request is cheap, a missed outage is not. That is why urgent keywords can be checked in code even when the LLM says "low" (a good stretch goal).
5. Return `reason` and `source` so humans can audit and trust it.

## Common mistakes
- Trusting `json.loads(reply)` on the raw reply (models add prose or ```json fences).
- Letting the LLM choose the team name; it will invent one.
- Catching only `ValueError`: network errors are different exceptions. Catch `Exception` at the boundary.
- Substring matching (`"down" in "download"`).
- Module-level global `llm` in the app, so tests leak into each other.
- Priority arithmetic on strings; use `PRIORITY_ORDER.index`.

## Demo tips
- Open `/docs` (FastAPI's Swagger UI) and triage live tickets from the customer's own inbox.
- Show a failure on purpose: unplug the key and show `source: "rules"` still answers.
- Show the enterprise escalation with the same ticket in both tiers.
- Say out loud: "the model suggests, our code decides."

## Optional manual step: real Claude (needs ANTHROPIC_API_KEY; not used by tests)
```python
import anthropic
from exercises import create_app

client = anthropic.Anthropic()

def claude_llm(prompt: str) -> str:
    msg = client.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text

app = create_app(claude_llm)
```
Save as `serve.py` (outside the tests) and run `.venv/bin/fastapi dev serve.py` or `.venv/bin/uvicorn serve:app`.

## Your task
Fill in `exercises.py`, then run `.venv/bin/pytest 05-fde-projects/project-02-ticket-triage -q`.
