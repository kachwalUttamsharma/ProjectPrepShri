# Project 1: LLM basics (prompts, structured output, streaming, cost)

Budget: ~2 hours. Tests need **no network and no API key**.

## Customer scenario
Northwind Logistics gets ~2,000 messy shipping emails a day ("pls send 3 pallets asap!!! to dock 4"). Ops staff retype them into their system. They ask: *"Can the AI read these and give us clean records?"* Your job this week is the foundation every later project uses: talk to a model in a way that is **testable, structured, retryable, and costed**.

## The one design rule: inject the model
Every function takes `llm`, a plain callable `llm(prompt: str) -> str`. In production it wraps the Anthropic SDK; in tests it is a `FakeLLM` returning scripted replies. Benefits: no API key in CI, deterministic tests, and you can swap vendors, add logging, caching or cost tracking by wrapping the callable (see `UsageTracker.wrap`).

## Concepts
- **Prompt building**: system role, instructions, few-shot examples, then the input. Keep layout in one function so you can version and test it.
- **Structured output**: models return text, not objects. Ask for JSON, then *never trust it*: extract (fences, chatter), parse, validate fields and types.
- **Retry with feedback**: on bad output, re-ask with the specific error. Cap attempts (cost and latency!). Rebuild from the original prompt rather than stacking repair messages.
- **Streaming**: responses arrive as chunks (or SSE `data:` lines). Show text as it arrives; users perceive streaming as much faster. Handle empty chunks and `[DONE]`.
- **Tokens and cost**: cost = tokens x price. `len/4` is a good-enough budget estimate. Customers always ask "what will this cost per month?" Have a number.

## Exercises (`exercises.py`)
`build_prompt`, `extract_json`, `validate_fields`, `get_structured`, `collect_stream`, `parse_sse_lines`, `estimate_tokens`, `estimate_cost`, `UsageTracker`. Run: `.venv/bin/pytest 05-fde-projects/project-01-llm-basics -q`.

## How an FDE would approach it
1. Get 10-20 *real* emails from the customer on day one. Their mess is not your mess.
2. Define the output schema with the customer's ops lead (which fields, which are required, what "unknown" means).
3. Start with the simplest prompt; look at failures; add examples for the failures.
4. Add validation and a retry cap before the demo, not after the first crash.
5. Compute rough cost per email x volume and say it out loud: "about $X per month".

## Optional manual step: the real model
Not part of the tests. Needs `ANTHROPIC_API_KEY` in your environment.
```python
import anthropic
from exercises import build_prompt, get_structured

client = anthropic.Anthropic()

def llm(prompt: str) -> str:
    msg = client.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text

prompt = build_prompt("You extract shipping data.", "Reply with JSON only: name, qty, urgent.",
                      [], "pls send 3 pallets asap")
print(get_structured(llm, prompt, {"name": str, "qty": int, "urgent": bool}))

# streaming
with client.messages.stream(model="claude-sonnet-5-5", max_tokens=300,
                            messages=[{"role": "user", "content": "Say hi"}]) as s:
    from exercises import collect_stream
    print(collect_stream(s.text_stream, on_chunk=lambda c: print(c, end="", flush=True)))
```

## Common mistakes
- `json.loads` directly on model output (fences and chatter break it).
- Accepting `True` as an int, or a string "3" as a number.
- Unbounded retries: a bad prompt then burns money in a loop.
- Appending repair messages every retry so the prompt grows each time.
- Forgetting output tokens cost ~5x input tokens.
- Calling the real API in unit tests.

## Demo tips
- Show a messy email in, clean JSON out, side by side.
- Deliberately show one failure and the retry fixing it: customers trust systems that visibly handle errors.
- Stream the response in the demo; it feels instant.
- End with the cost slide: per email, per day, per month.
