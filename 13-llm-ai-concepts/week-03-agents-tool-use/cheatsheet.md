# Week 3 Cheatsheet: Agents and Tool Use

## Function calling flow
messages + tool schemas -> model emits tool_call -> YOU validate, authorize, execute -> tool result message -> model continues -> final answer.
Model never executes. Tool descriptions are prompt text.

## Agent loop
think -> act -> observe -> repeat. Stop: final answer | max steps | token/$ budget | timeout | repeated failures | needs human.

## Workflow vs agent
Known path = workflow (chain, route, parallel, orchestrator-workers, evaluator-optimizer). Open path = agent. Start simple.

## Planning
ReAct (stepwise) vs plan-then-execute (reviewable, re-plan). Failure: loops, drift, premature done. Fix: caps, loop detection, verification step.

## Memory
Short (history, trim/summarise) | working (state object) | long-term (store + retrieval). Risks: privacy, stale, poisoning, bloat.

## MCP-style protocols
Client (agent host) <-> servers via JSON-RPC (stdio or HTTP). Tools, resources, prompts. Discovery + capability negotiation + auth. Risks: malicious/changed tool descriptions, broad scopes, token leaks, tool overload. Allowlist, pin, least privilege, approvals.

## Multi-agent
Orchestrator-worker, handoff, parallel, critic. Costs tokens/latency/debuggability. One good agent often wins.

## Reliability
Compounding: 0.95^10 about 0.6. Step cap, budgets, timeouts, backoff + jitter, idempotency keys, validate args, circuit breaker, fallback, loop detection, tracing, resumable state, scenario evals run multiple times.

## HITL
Risk-tier tools: read-only auto, reversible log, irreversible approve. Edit-and-approve UI. Pause/resume state. Thresholds to avoid fatigue. Log decisions as eval data.

## Cost
History resent each step -> growth about quadratic. Cache static prefix, trim tool output, route models, parallelize, cache deterministic tools, quotas, measure cost per successful task.

## Security
Least privilege, per-user creds, auth in tool code, allowlists, sandbox, no secrets in prompt, untrusted tool output, audit logs.

## Debug questions
Which step failed? Wrong tool, wrong args, bad result, ignored result? Loop? Budget? Show trace first.
