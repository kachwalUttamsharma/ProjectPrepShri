# Project 6 (capstone): From messy data to a deployed demo

Budget: ~2 hrs/week, so plan 2 sessions. Session 1: scoping + data cleaning + extraction (functions 1-5). Session 2: API, Docker, README, demo script, risks (functions 6-11), then rehearse the demo out loud.

## The customer request (verbatim, as it arrives)
> Hi, we're a mid-size logistics company. Our finance team drowns in supplier invoices: PDFs, emails, and a spreadsheet export from our old system that nobody trusts. We heard AI can "just read them". Can you show us something next week? Ideally it plugs into our ERP and has a dashboard, and handles everything automatically. Not sure how accurate it needs to be.

Your job is not to build all of that. Your job is to turn it into a demo that is small, honest, and impressive in 5 minutes.

## Scoping a vague request (`scope_request`)
Listen for three things: the real pain (finance re-keying invoices), the wish list (ERP, dashboard, "everything"), and the missing facts (volume, accuracy bar, sample data, who approves).

| Customer says | You translate to |
|---|---|
| "plugs into our ERP" | Out of scope for the demo; ask for a sandbox or a sample export |
| "dashboard" | Out of scope; FastAPI `/docs` or one simple page is enough |
| "handles everything automatically" | One workflow, human review for low confidence |
| "not sure how accurate" | Propose a metric, e.g. 90% field accuracy on 20 samples |

Always ask: can we get 20+ real anonymised samples? Who judges success?

## Spec
Build a service that takes messy invoice data and returns clean structured data.
- Batch path: messy CSV export -> `parse_messy_csv` -> `clean_records` -> clean rows + an explicit rejected list (never silently drop data).
- LLM path: `POST /extract {"text": "..."}` -> `extract_with_fallback` -> `{"data", "needs_review", "error", "attempts"}`.
- `GET /health` for the container health check.
- Ship it with a Dockerfile, README, a 5-minute demo script, and a risk checklist.

## Concepts
- **Injected `llm: Callable[[str], str]`**: the tests use a `FakeLLM`; production plugs in Anthropic. Same code, no network in tests.
- **Validate everything the LLM returns**; retry once with the error in the prompt; then fall back to `needs_review=True` instead of crashing or guessing.
- **Money as integer cents** with `Decimal`, never floats. Dates to ISO; state your assumption (`03/04/2024` is DD/MM here) to the customer.
- **Docker layer caching**: copy `requirements.txt` and install before copying code.
- **Honest limits**: a demo that shows its failure handling builds more trust than one that looks perfect.

## How an FDE would approach it
1. Day 0: reply with a 5-line scope (in / out / questions) before writing code. `scope_request` is a toy version of that habit.
2. Get real samples first; the messiest 3 files tell you more than the spec does.
3. Make the ugly path work end to end (CSV in, JSON out), then add the LLM where rules run out.
4. Measure: even 20 hand-labelled examples (see Project 5) beat "it looks good".
5. Package: Dockerfile + README so someone else can run it in 2 minutes.
6. Rehearse the demo with a timer; prepare the failure case on purpose.

## Optional manual step: real Anthropic (not used by tests)
```python
import anthropic
client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment

def llm(prompt: str) -> str:
    msg = client.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text

app = create_app(llm)   # then: uvicorn main:app --reload
```
Never commit the key. Set it with `export ANTHROPIC_API_KEY=...` or pass `-e ANTHROPIC_API_KEY` to `docker run`.

## Dockerfile walkthrough (`generate_dockerfile`)
```
FROM python:3.14-slim                      # small base image
WORKDIR /app
COPY requirements.txt .                    # changes rarely -> cached layer
RUN pip install --no-cache-dir -r requirements.txt
COPY . .                                   # changes often -> last
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```
`--host 0.0.0.0` is required or the container is unreachable from outside. Run: `docker build -t invoice-demo .` then `docker run -p 8000:8000 -e ANTHROPIC_API_KEY invoice-demo`. (Docker is a manual step; tests only check the generated text.)

## README template (`render_readme`)
Name, one-line summary, Setup (numbered), Endpoints (table), Known limitations. The limitations section is not optional: it is what a customer's engineer reads first.

## 5-minute demo script (`demo_script`)
| Time | Step |
|---|---|
| 0:00-0:45 | Their problem in their words |
| 0:45-1:30 | The messy input (show the ugliest file) |
| 1:30-3:30 | Live run: CSV clean-up, then `/extract` on a PDF text |
| 3:30-4:15 | Failure case: bad LLM output -> `needs_review`, human in the loop |
| 4:15-5:00 | Limits, next steps, what you need from them |

## Risks and limits checklist (`risk_checklist`)
Eval set exists - fallback for invalid output - human review - PII decision - cost per request estimated - timeouts/retries - secrets in env vars. Say the unmet ones out loud to the customer.

## Common mistakes
- Promising ERP integration or "100% accuracy" in the first call.
- Silently dropping bad rows; report them.
- Floats for money; ambiguous dates left unstated.
- Trusting LLM JSON without validating; no timeout on the LLM call.
- Demoing only the happy path; improvising the demo instead of rehearsing it.
- Dockerfile that copies code before installing dependencies (slow rebuilds).

## Demo tips
- Pre-load inputs; do not type live. Keep a recorded fallback in case wifi dies.
- Use the customer's own (anonymised) data and vocabulary.
- Show a failure on purpose, then show how it is contained.
- Explain tradeoffs to non-engineers in terms of cost, risk and review time, not tokens.
- End with a concrete ask: samples, a sandbox, and a success metric.

## Your task
Fill in `exercises.py`, run `.venv/bin/pytest -q` inside this folder. Then write a real `main.py`, README and Dockerfile with your functions and do a timed rehearsal.
