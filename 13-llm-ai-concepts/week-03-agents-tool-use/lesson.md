# Week 3: Agents and Tool Use

Goal: explain how tool calling works, build and bound an agent loop, and talk about reliability, safety and cost like someone who has shipped one. Hands-on companion: `05-fde-projects/project-04-tool-calling-agent`.

---

## 1. Function calling (tool use)

The model cannot act on the world. Tool calling lets it request an action; your code performs it.

```
 you -> model:  messages + tool definitions (name, description, JSON schema)
 model -> you:  "call get_order(order_id='A123')"     (a structured request, NOT executed by the model)
 you:           validate args, check permission, run the function
 you -> model:  tool result as a message
 model -> you:  final natural-language answer (or another tool call)
```

Key facts:
- The tool description and schema are prompt text; the model picks tools from them. Clear names, precise descriptions, enums and examples matter more than most people expect.
- The model can hallucinate tools, arguments, or IDs. Validate everything against the schema and against business rules. Return errors as tool results so the model can self-correct.
- Models can emit multiple tool calls in one turn (parallel calls); handle them concurrently when independent.
- Tool results are untrusted input (prompt-injection vector).
- Forcing a tool (`tool_choice`) or forbidding tools is a provider option (check current docs for exact parameter names).

Runnable skeleton with a fake model, no API key:

```python
import json

TOOLS = {
    "get_order": lambda order_id: {"order_id": order_id, "status": "shipped", "eta_days": 2},
    "add": lambda a, b: a + b,
}

def fake_model(messages):
    """Stands in for an LLM: asks for a tool first, then answers from the result."""
    last = messages[-1]
    if last["role"] == "user":
        return {"type": "tool_call", "name": "get_order", "args": {"order_id": "A123"}}
    result = json.loads(last["content"])
    return {"type": "final", "text": f"Order {result['order_id']} is {result['status']}, arriving in {result['eta_days']} days."}

def run(user_text, max_steps=5):
    messages = [{"role": "user", "content": user_text}]
    for step in range(max_steps):                     # hard cap
        out = fake_model(messages)
        if out["type"] == "final":
            return out["text"]
        fn = TOOLS.get(out["name"])
        if fn is None:                                 # hallucinated tool
            result = {"error": f"unknown tool {out['name']}"}
        else:
            try:
                result = fn(**out["args"])
            except Exception as e:                     # feed errors back, do not crash
                result = {"error": str(e)}
        messages.append({"role": "tool", "content": json.dumps(result)})
    return "Stopped: step limit reached."

print(run("Where is my order A123?"))
```

## 2. The agent loop

An agent is an LLM in a loop with tools, deciding the next step from observations.

```
        +---------------------------------------------+
        |                                             v
 goal -> [LLM: think / choose action] -> action? --yes--> [execute tool] -> observation
                                            |                                   |
                                            no (final answer)                   |
                                            v                                   |
                                         return  <----- stop conditions <-------+
        stop conditions: final answer | max steps | token/cost budget | timeout | error threshold | human needed
```

ReAct pattern: reason, act, observe, repeat. Modern APIs implement this via tool-calling messages instead of text parsing.

Workflow vs agent: a workflow has a fixed control flow written in code with LLM calls at nodes (predictable, testable); an agent lets the model choose the flow (flexible, riskier). Default to the simplest thing that works: single call, then chain/workflow, then agent only when the path is genuinely open-ended. Interviewers like hearing "I would not use an agent here".

Workflow shapes: prompt chaining, routing, parallelization (fan-out/fan-in), orchestrator-workers, evaluator-optimizer loop.

## 3. Planning

- Implicit: the model decides step by step (ReAct). Good for short tasks.
- Explicit plan-then-execute: produce a plan (list of steps), execute each, re-plan on failure. Better for long tasks, easier to show to a human for approval, and cheaper to monitor.
- Reasoning models plan internally with thinking tokens; still bound them with budgets.
- Failure modes: looping on the same failing call, drifting from the goal, over-planning, premature "done", skipping verification. Mitigate with step caps, loop detection (same tool + same args N times), checklists, and a final verification step.

## 4. Memory

```
 Short-term : the message history in the context window (trim, summarise when long)
 Working    : scratchpad/state object for the current task (plan, found facts, IDs)
 Long-term  : external store (DB / vector store) of user preferences, past cases, facts; retrieved on demand
```
Techniques: sliding window, summarize old turns, extract key facts into a structured state, retrieve memories by similarity (RAG on memory). Risks: stale or wrong memories, privacy (per-user isolation, deletion rights), memory poisoning (injected instructions persisted), context bloat. Tool results can be huge: truncate, summarise, or store off-context and pass a handle.

## 5. Tool protocols and MCP-style integration (generic)

Problem: N apps times M tools means N*M custom integrations. A standard protocol (the Model Context Protocol pattern) defines how a client (the agent host) discovers and calls tools exposed by servers.

```
 Agent host (LLM app) <--- JSON-RPC over stdio / HTTP --->  Tool server(s)
   - list tools (name, description, input schema)               - expose tools, resources (read-only data), prompts
   - call tool with args, get result                            - own auth to the underlying system
   - consent / approval UI
```
Concepts: tools (actions), resources (data the model can read), prompts (templates), capability negotiation, transport (local process vs remote HTTP), auth (OAuth for remote servers). Benefits: reuse, separation of concerns, discoverability. Risks: untrusted or malicious servers (tool description injection, "rug pull" changes to tool definitions), over-broad permissions, token leakage, too many tools bloating the prompt (selection accuracy drops past a few dozen). Mitigate: allowlist servers, pin versions, least-privilege scopes per user, approval for risky tools, tool-count discipline (route/subset tools per task). Check the current protocol spec for details; do not quote version specifics from memory.

## 6. Multi-agent patterns

- Orchestrator-worker (supervisor): a planner delegates subtasks to specialists and merges results. Most common.
- Pipeline/handoff: agent A passes to agent B (e.g., triage to billing agent).
- Parallel workers: fan-out for independent research, then synthesize.
- Debate/critic: one agent proposes, another critiques.
Tradeoffs: more tokens and latency, harder debugging, error compounding, context handoff losses. Use when subtasks need different tools/prompts/contexts, or when parallelism pays. Often one agent with good tools beats several agents. Give each agent a narrow tool set and its own context, communicate through structured messages.

## 7. Reliability engineering

Failure rates compound: ten steps at 95 percent each is about 60 percent end to end. So design for it.

Checklist:
- Step cap, token/cost budget, wall-clock timeout per run and per tool call.
- Retries with exponential backoff and jitter for transient errors (timeouts, 429, 5xx); not for validation errors; make tools idempotent or use idempotency keys so retries do not double-charge.
- Schema validation of tool arguments; return helpful errors to the model; cap self-correction attempts.
- Circuit breaker on failing downstream systems; fallback model or graceful degradation.
- Loop detection and repeat-call suppression.
- Deterministic code for what code can do (math, dates, ID lookups, permissions).
- Guardrails: input checks (PII, injection heuristics), output checks (schema, policy, URL stripping), allowlists of tools/domains/amounts, sandbox for code execution (no network, resource limits).
- Observability: trace each step (prompt, tool call, args, result, latency, tokens). Without traces you cannot debug an agent.
- State persistence and resumability for long runs; idempotent steps.
- Testing: scenario evals with expected tool sequences and final outcomes; mock tools; adversarial cases; run multiple times because of non-determinism (pass@k or success rate).

```python
import random, time

def call_with_retry(fn, attempts=4, base=0.2):
    for i in range(attempts):
        try:
            return fn()
        except TimeoutError:
            if i == attempts - 1:
                raise
            time.sleep(base * (2 ** i) + random.random() * base)   # exponential backoff + jitter

calls = {"n": 0}
def flaky():
    calls["n"] += 1
    if calls["n"] < 3:
        raise TimeoutError
    return "ok"

print(call_with_retry(flaky), calls)
```

## 8. Human-in-the-loop (HITL)

Where to put humans: approval before irreversible or costly actions (send email, refund, delete, deploy), review of low-confidence outputs, clarification questions when required parameters are missing, escalation path with full context, and feedback capture.

Design: classify tools as read-only / reversible / irreversible; auto-run the first, ask for approval on the last. Present a clear proposed action with arguments and reasoning, allow edit-and-approve. Persist state so the run can pause and resume (approval may take hours). Avoid approval fatigue: batch, set sensible thresholds (e.g. refunds below X auto-approve), audit logs. Log human decisions as labeled data for evals.

## 9. Cost and latency control

- Budget per run (tokens, tool calls, dollars) with hard stops; per-user and per-tenant quotas.
- Each loop iteration re-sends the whole history: cost grows roughly quadratically with steps unless you trim, summarise or use prompt caching. Put stable content (system prompt, tool definitions) first so caching works.
- Use cheaper models for routing/simple steps, stronger ones for planning/hard steps.
- Limit tool output size; paginate; return only needed fields.
- Parallelize independent tool calls; stream partial results to the user.
- Cache deterministic tool results.
- Prefer workflows to agents when the path is known.
- Track cost per successful task, not per call.

Worked example (illustrative, use placeholder prices P_in, P_out per million tokens): an agent with a 3,000-token fixed prefix and 800 new tokens per step over 8 steps resends about 3,000 + 800*k tokens at step k. Total input about 8*3,000 + 800*(0+1+...+7) = 24,000 + 22,400 = 46,400 tokens, plus output. Caching the prefix and trimming tool output can cut this sharply. Cost = 46,400/1e6 * P_in + out_tokens/1e6 * P_out. Look up current prices.

## 10. Security for agents
- Least privilege and per-user credentials; the agent acts with the user's rights, never more.
- Indirect injection through tool results and retrieved content; do not let untrusted content trigger high-impact tools without approval.
- Validate arguments server-side as if the caller were hostile (authorization in the tool, not the prompt).
- Secrets never in prompts; tools hold credentials.
- Audit log of every action.
- Sandboxed code execution.

## 11. How interviewers probe
- "Walk through how function calling works." (Model emits request; you execute; result returned.)
- "How do you stop an agent from looping or burning money?" (Caps, budgets, loop detection, timeouts.)
- "The agent called the refund tool twice." (Idempotency keys, approval, retries on non-idempotent actions.)
- "Agent or workflow?" (Open-ended path vs known path.)
- "How do you test an agent?" (Scenario evals, tool mocks, trace inspection, repeated runs.)
- "Tell me about MCP." (Standard client-server tool protocol; discovery; security risks.)
- "Memory design?" (Short/working/long-term; privacy; poisoning.)
- "When multi-agent?" (Different contexts/tools, parallelism; otherwise single agent.)

## Self-check
1. Write the agent loop with caps from memory.
2. List five stop conditions.
3. Explain why retries need idempotency.
4. Name three ways a tool server can be an attack vector.
5. Compute the cost growth for an N-step loop with and without caching.
