# Week 3 Interview Q&A: Agents and Tool Use

---

**1. How does function calling work?**
You send messages plus tool definitions (name, description, JSON schema). The model returns a structured request to call a tool with arguments. Your code validates, authorizes and executes it, then returns the result as a message; the model continues, possibly calling more tools, until it answers. The model never executes anything itself.

**2. What makes a good tool definition?**
Specific name, description saying when to use and when not to, strict schema with enums and required fields, examples, small focused tools, consistent error messages. The description is prompt text; vague tools cause wrong selection.

**3. What can go wrong with tool calls?**
Hallucinated tools or arguments, wrong tool chosen, missing required info, huge outputs flooding context, repeated calls, non-idempotent side effects on retry, injected instructions in results. Mitigate with validation, error feedback, size caps, idempotency keys, approval gates.

**4. Agent vs workflow: how do you decide?**
If the steps are known, use a workflow (code controls flow, LLM at nodes): predictable, testable, cheaper. Use an agent when the path depends on intermediate results and cannot be enumerated. Start with a single prompt, add structure, add autonomy only when evals show a need.

**5. Describe the agent loop and its stop conditions.**
Model chooses action, you execute, feed back the observation, repeat. Stop on final answer, max steps, token/cost budget, timeout, repeated-failure threshold, or need for human input.

**6. Plan-and-execute vs ReAct?**
ReAct decides one step at a time: flexible, good for short tasks, can wander. Plan-and-execute drafts a plan first, executes steps, re-plans on failure: more controllable, reviewable by a human, better for long tasks, but plans can be wrong and brittle.

**7. How do you give an agent memory?**
Short-term: message history, trimmed or summarised. Working memory: a structured state object. Long-term: external store, retrieved by relevance. Watch privacy (per-user isolation, deletion), stale facts, poisoning via injected content, and context bloat.

**8. What is MCP (generic protocol view) and why does it exist?**
A standard client-server protocol so an agent host can discover and call tools, read resources, and use prompt templates from independent servers, replacing N-by-M custom integrations. Transports: local process or remote HTTP, with auth for remote. Risks: malicious or changing tool descriptions, over-broad scopes, credential leakage, too many tools. Mitigate with allowlists, version pinning, least privilege, approval prompts. Check the current spec for details.

**9. When would you use multiple agents?**
When subtasks need different tools, prompts or contexts, or can run in parallel (orchestrator-worker, handoffs, critic). Costs: more tokens, latency, harder debugging, error compounding. If one agent with good tools suffices, do that.

**10. Why do agents fail in production even when demos work?**
Compounding error (10 steps at 95 percent is about 60 percent), edge-case inputs, flaky tools, ambiguous user goals, context growth, non-determinism. Fix with narrower scope, deterministic code where possible, validation, evals on trajectories, tracing, and human fallback.

**11. How do you make retries safe?**
Retry only transient errors with exponential backoff and jitter. Make tools idempotent or pass idempotency keys so duplicates are ignored. Never blindly retry non-idempotent actions (payments, emails). Cap attempts and surface failure to the model or human.

**12. How do you prevent runaway loops and cost?**
Hard step cap, token and dollar budget per run, wall-clock timeout, repeated-call detection, truncated tool output, prompt caching for static prefixes, cheaper models for easy steps, and per-user quotas with alerts.

**13. Where should humans be in the loop?**
Before irreversible or high-impact actions, on low-confidence or policy-sensitive outputs, when required parameters are ambiguous, and for escalations. Classify tools by risk; auto-run read-only, approve irreversible. Persist state to pause and resume; capture human decisions as eval data; avoid approval fatigue with thresholds.

**14. How do you secure an agent?**
Least privilege, per-user credentials, authorization enforced in the tool code, allowlisted arguments/domains/amounts, sandboxed code execution, no secrets in prompts, treat tool results and retrieved text as untrusted, approval gates for side effects, full audit logs, red-team tests.

**15. How do you test and evaluate an agent?**
Scenario suites with inputs and expected outcomes (final state, tools called, forbidden actions), mocked or sandboxed tools, run each several times to measure success rate and variance, inspect traces for bad trajectories, track cost and steps per task, regression-test on each prompt/model/tool change. LLM judges can help for free-text, with caveats (Week 4).

**16. How do you handle very long tool outputs or conversations?**
Truncate or paginate at the tool, return only needed fields, summarise older turns, store large artifacts outside the context and pass handles, retrieve on demand, use caching for the stable prefix.

**17. What is structured output's role in agents?**
Forces machine-readable plans, decisions and tool args, enabling validation and branching in code. Use schemas for routing decisions and final results; validate semantics beyond shape.

**18. Scenario: "The agent sent the same email three times."**
Likely retries or loop on a non-idempotent tool. Check traces. Fix: idempotency key per logical action, dedupe store, approval gate on send, loop detection, and only retry on clearly failed calls (distinguish timeout-after-send from failure). Add a regression scenario and tell the customer exactly what happened and what controls now exist.

**19. Scenario: "Customer wants an agent that can do everything in their CRM autonomously."**
Narrow it. Start with read-only tools and a few high-value tasks, define success metrics, add write tools one at a time with approvals and limits (amounts, record scope), per-user permissions, audit logs, shadow mode (agent proposes, humans act) to gather accuracy data, then graduate actions to autonomous as measured error rates justify.

**20. Scenario: "Agent works in staging but is slow and expensive in prod."**
Look at traces: steps per task, tokens per step, tool latencies. Typical causes: history growth, large tool outputs, sequential calls that could be parallel, big model for easy steps, no caching, retries on timeouts. Fix with trimming/summarising, parallel tool calls, routing to smaller models, prompt caching, a workflow for the common path, and per-run budgets. Report cost per successful task before and after.

---

## Bonus probes
- "How many tools can you give an agent?" Accuracy tends to fall as the list grows; subset by task or route; test.
- "Should the LLM do auth checks?" Never; code does.
- "How do you resume a crashed run?" Persisted state and idempotent steps.
