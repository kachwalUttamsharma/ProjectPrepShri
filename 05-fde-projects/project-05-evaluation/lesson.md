# Project 5: Evaluating an LLM feature (is v2 actually better?)

Budget: ~2 hours. No network, no API key needed for the tests.

## Customer scenario
> "Our support team uses your ticket classifier. Last week someone tweaked the prompt and 'it feels worse.' Another person says the new one is great. Can you tell us, with numbers, which prompt we should ship?"

The customer has 12 labelled tickets in a spreadsheet exported as JSONL. Your job is to build a tiny evaluation harness: run each prompt version over the same test set, score it, find out *what* fails, and compare the versions.

## Spec (what you build in `exercises.py`)
- Test set: a JSONL file, one object per line: `{"id": "t1", "input": "...", "expected": "billing"}`.
- A *prompt template* is a string containing `{input}`.
- `llm` is any callable `llm(prompt: str) -> str`. Tests inject a deterministic fake.
- A *result* is a dict: `{"id", "input", "expected", "predicted"}`.
- Metrics: accuracy, per-class precision / recall / F1, confusion matrix.
- Failure analysis: list failures, rank the most common (expected -> predicted) mistakes.
- Regression comparison: which cases were fixed, which regressed, and a ship / hold verdict.
- A plain-English report a non-engineer can read.

## Concepts
- **Accuracy**: share of cases correct. Misleading when classes are imbalanced (95% "other" -> a model that always says "other" scores 95%).
- **Precision of class X**: of the tickets we *called* X, how many really were X? (Cost of false alarms.)
- **Recall of class X**: of the tickets that *are* X, how many did we find? (Cost of misses.)
- **F1**: harmonic mean of precision and recall.
- **Confusion matrix**: rows = truth, columns = prediction. Shows *which* classes get mixed up.
- **Regression**: a case v1 got right that v2 gets wrong. Averages hide these; always list them.
- A test set is a contract with the customer: it must come from *their* real data.

## How an FDE would approach it
1. Get 30-100 real, labelled examples from the customer before touching the prompt. Ask who labels them and whether labelers agree.
2. Freeze the test set. Never tune the prompt on the same cases you report on (keep a separate dev set).
3. Run every prompt version through the same harness, on the same cases, with temperature 0.
4. Lead with the business meaning: "v2 fixes 3 billing tickets but breaks 2 urgent outage tickets. Missing an outage costs more than misrouting a billing question, so I recommend holding v2."
5. Pick the metric by cost of error: missing urgent tickets -> optimise recall on "urgent"; flooding agents with false alarms -> precision.
6. Show 2-3 concrete failing examples, not only numbers. Non-engineers trust examples.
7. State the limits: "12 cases is a smoke test, not proof. One case is 8 points of accuracy."

## Optional manual step: real Anthropic SDK
Not run by tests. Needs `ANTHROPIC_API_KEY` in your environment.
```python
import anthropic
client = anthropic.Anthropic()

def real_llm(prompt: str) -> str:
    msg = client.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=20,
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text

from exercises import *
cases = load_test_set("my_cases.jsonl")
results = run_prompt(real_llm, "Classify into billing/technical/other: {input}\nAnswer with one word.", cases)
print(format_report("v1", results))
```

## Common mistakes
- Comparing accuracy on different test sets or different sample sizes.
- Not normalising model output (`"Billing."` vs `"billing"`) and then blaming the model.
- Dividing by zero when a class never appears (precision/recall must return 0.0).
- Reporting only the average; hiding regressions.
- Tuning on the test set (overfitting) and then presenting the score as if it were unseen.
- One LLM error crashing the whole run: record it as a failed case instead.
- Declaring a winner from a 1-case difference.

## Demo tips
- Show the confusion matrix as a small table, then say one sentence about it.
- Have a "regressions" slide: the first thing a skeptical customer asks is "what got worse?"
- Keep the run reproducible: one command, same output every time.
- Be upfront about the sample size before they ask.

## Your task
Fill in `exercises.py`, then run `.venv/bin/pytest 05-fde-projects/project-05-evaluation` (from the repo root) or `pytest -q` from this folder.
