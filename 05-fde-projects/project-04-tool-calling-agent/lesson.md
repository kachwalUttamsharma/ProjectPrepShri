# Project 4: Tool-calling agent over a CRM

Budget: ~2 hrs. Read (20 min), validation + registry (30 min), parsing + run_tool (25 min), SQL layer (25 min), agent loop (20 min).

## The customer scenario
> "Our support reps spend half their day switching between the CRM and the orders database to answer 'where is my order?' and 'is this customer on the Pro plan?'. Can the assistant just look things up itself? We are nervous about it changing data or going haywire."

Spec: the assistant may call three read-only tools (`lookup_customer`, `list_orders`, `run_query`), loop until it has an answer, and never write data or run forever.

## Concepts
- **Tool calling** = the model emits a structured request, YOUR code runs it, you feed the result back. The model never touches the database; you do.
- **Protocol used here** (the model replies with exactly one JSON object as text):
  - `{"tool": "list_orders", "args": {"customer_id": 1}}` call a tool
  - `{"final": "Ada has 1 pending order."}` finish
  - Tool results come back as a user message: `TOOL_RESULT: {"ok": true, "result": ...}`; problems as `ERROR: ...`.
- **Registry + schema**: tools declared once (name, description, parameter spec). The same declaration feeds the prompt (`describe()`), argument validation, and execution.
- **Validate model output like user input.** It is untrusted: wrong types, extra keys, made-up tool names.
- **Errors are observations, not crashes.** `run_tool` never raises; the error text goes back to the model so it can self-correct.
- **Guardrails**: allow-list per customer/role, `max_steps`, read-only SQL guard, parameterized queries, row limits.
- **Dependency injection**: `llm(messages) -> str`. Tests use a scripted FakeLLM, so no network or API key.

## How an FDE would approach it
1. Ask what actions the rep needs and which are dangerous. Ship read-only first; writes (refunds) later behind human approval.
2. Prefer a few narrow tools (`list_orders`) over one powerful one (`run_query`). Free-form SQL is a demo convenience; in production give a DB user with SELECT-only rights too (the regex guard is a second layer, not the only one).
3. Log every tool call and result (the `trace`); customers will ask "why did it say that?".
4. Build with the FakeLLM first so the loop is deterministic, then try the real model.
5. Explain tradeoffs to non-engineers: more tools = more capability but more risk and cost; each step is another paid LLM call.

## Exercises (in `exercises.py`)
1. `validate_args` 2. `ToolRegistry` 3. `parse_action` 4. `run_tool` 5. `is_read_only_sql` 6. `lookup_customer` / `list_orders` / `run_readonly_query` 7. `build_crm_registry` 8. `run_agent`

Run: `cd 05-fde-projects/project-04-tool-calling-agent && ../../.venv/bin/pytest -q`

## Optional manual step: real model
Not needed for tests. Needs `ANTHROPIC_API_KEY` in your shell.
```python
import anthropic
from exercises import *

client = anthropic.Anthropic()
reg = build_crm_registry(seed_crm_db())
SYSTEM = ("You answer support questions. Reply with ONE JSON object only: "
          '{"tool": name, "args": {...}} or {"final": answer}.\nTools:\n' + reg.describe())

def llm(messages):
    r = client.messages.create(model="claude-sonnet-5-5", max_tokens=500,
                               system=SYSTEM, messages=messages)
    return r.content[0].text

print(run_agent(llm, reg, "How many pending orders does ada@example.com have?"))
```
(Anthropic also has native tool use via the `tools=` parameter; this JSON-text protocol teaches the same loop with no SDK coupling.) Note: messages must alternate user/assistant; the loop here does.

## Common mistakes
- `isinstance(True, int)` is True, so booleans slip through integer checks.
- Building SQL with f-strings (injection). Use `?` placeholders.
- Checking only that SQL "starts with SELECT"; `SELECT 1; DROP TABLE x` passes. Reject `;` stacking.
- Letting a tool exception crash the loop instead of returning it to the model.
- No `max_steps`: a confused model loops and burns money.
- Counting a malformed reply as free; it is still a paid LLM call.
- Returning huge result sets into the prompt; always cap rows.

## Demo tips
- Show the `trace` live: "it looked up the customer, then the orders, then answered".
- Demo a refusal: ask it to delete orders and show the guard saying no. Non-engineers love this.
- Keep a canned seed DB so the demo is repeatable; mention what you would swap for their real CRM API.
