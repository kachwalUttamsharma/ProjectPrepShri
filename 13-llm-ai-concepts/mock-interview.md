# FDE-flavored Mock Interview (6 scenarios)

How to use: 15 to 20 minutes per scenario, out loud, with a timer. Start by asking clarifying questions (the interviewer rewards it), state assumptions, structure the answer, bring up security and cost unprompted, and end with how you would measure success. Then score yourself against the rubric. Pass bar: at least 3 of 4 on every dimension for each scenario, or know exactly which dimension to retry.

Scoring dimensions (0 to 4 each): Discovery (clarifying questions, requirements), Technical design (correct, justified, tradeoffs), Risk and quality (evals, security, failure modes), Communication and ownership (customer-ready, concrete next steps).

---

## Scenario 1: Support copilot for a mid-size SaaS customer
Prompt: "A customer with 40,000 help-center articles and 2,000 tickets per day wants an AI assistant that drafts replies for agents. Design it and tell me what you would ship in four weeks."

Rubric - strong answers:
- Discovery: who are users (agents), what is "good" (acceptance rate, handle time), languages, tone, systems (helpdesk, KB), data sensitivity, volume, latency expectations.
- Design: RAG over KB plus similar past tickets; hybrid search, reranking, citations; draft-for-agent (human in loop) rather than auto-send; ticket classification/routing as separate cheap-model step; prompt template with tone and policy; structured output.
- Quality: golden set from real tickets with agent-approved replies; metrics for retrieval recall and faithfulness; abstain when not found; shadow mode first; feedback capture (accept/edit/reject).
- Risk: PII redaction, tenant isolation, injection via ticket text, no auto commitments (refunds), logging policy.
- Phasing: week 1 ingestion and baseline, week 2 evals and iteration, week 3 pilot with a few agents, week 4 metrics review and rollout plan. Cost estimate with token math and a note to check current prices.
- Red flags: jumping to fine-tuning, no eval plan, auto-sending replies on day one.

## Scenario 2: "The demo was great, production answers are wrong"
Prompt: "Two weeks after launch the customer's VP says the RAG bot gives wrong answers about pricing and policies. You join a call in 30 minutes. What do you do?"

Rubric:
- Immediate: gather examples with traces; do not defend; acknowledge impact; ask for 5 concrete failures.
- Diagnosis: use the RAG debug tree (corpus, retrieval, ranking, generation, citation); check for stale/multiple document versions, parsing of pricing tables, exact-term queries needing BM25, missing abstention; check whether the model or index changed.
- Mitigation: short-term guardrails (route pricing questions to a verified source or human, show document dates), rollback if recent change, fix top root cause.
- Prevent: add failures to regression set, monitoring, owner for content freshness, weekly quality review.
- Communication: simple root-cause statement, timeline, what changes, how you will measure; avoid promising zero errors.
- Red flags: blaming the user/model, "just switch to a bigger model" without evidence.

## Scenario 3: Agent with write access to a CRM
Prompt: "A sales-ops team wants an agent that updates CRM records, drafts emails, and creates tasks from call notes. They want it fully autonomous. How do you proceed?"

Rubric:
- Discovery: what actions, which objects, error tolerance, who is accountable, current manual process and volume.
- Design: tool inventory classified by risk (read, reversible write, irreversible); per-user permissions; schema-validated arguments; idempotency keys; approval UI for risky actions; plan visible to the user; step and cost budgets; audit log.
- Rollout: shadow mode (agent proposes, humans act), measure agreement, graduate low-risk actions to auto with thresholds, keep a kill switch.
- Security: prompt injection from call notes/emails, least privilege, no secrets in prompt, data residency.
- Testing: scenario evals including adversarial notes, repeated runs, trajectory checks, cost per task.
- Red flags: giving the agent admin credentials, relying on the prompt for authorization, no rollback path.

## Scenario 4: Cost and latency blow-up
Prompt: "Your feature costs about 5x the estimate and p95 latency is 14 seconds. The customer is threatening to cancel. Walk me through the next two weeks."

Rubric:
- Measure first: traces by span, tokens per request distribution, cache hit rate, retries, which queries are expensive, volume vs forecast.
- Hypotheses: prompt bloat or too many chunks, history resend, large model for easy tasks, no prompt caching, sequential calls, retries on timeouts, runaway outputs.
- Actions in priority order: cap output and context, route easy cases to a smaller model with an eval gate, prompt caching with static-prefix layout, parallelize, stream, response caching for FAQ, batch API for offline parts, per-tenant quotas.
- Show math: cost per request before/after with placeholder prices, then verify with real prices; cost per successful outcome.
- Quality guard: re-run eval suite on each change; report quality, cost and latency together.
- Customer handling: weekly numbers, a target SLO, and an honest tradeoff table.
- Red flags: optimizing blind, cutting quality without measurement.

## Scenario 5: Regulated customer and data privacy
Prompt: "A healthcare/finance customer wants an assistant over internal documents containing sensitive data. Their security team says no data can leave their cloud account. Propose an approach."

Rubric:
- Discovery: data classes, regulations (HIPAA/GDPR-style; involve their legal/compliance), regions, retention, who can see what, audit needs, existing identity provider.
- Options: provider endpoint inside their cloud account/VPC with private networking and customer-managed keys vs self-hosted open-weights model; compare capability, cost, ops, latency; propose pilot.
- Architecture: ingestion within their boundary, per-user ACL filtering at retrieval, redaction where needed, encrypted stores, no raw logging or tightly controlled logs, deletion across vector store/caches/backups, tenant isolation, audit trails.
- Risks: injection, leakage via caches or embeddings, model memorization, over-broad access, shadow IT.
- Deliverables: data-flow diagram, threat model, DPIA-style checklist inputs, runbook.
- Red flags: giving legal advice as fact, ignoring ACLs, sending PII to a third party without agreement.

## Scenario 6: "Is the new model/prompt actually better?"
Prompt: "Your teammate says the new prompt plus a newer model improves quality. The customer wants to switch tomorrow. How do you decide?"

Rubric:
- Define quality: task metrics, rubric, cost, latency, safety.
- Eval design: golden set (stratified, real, includes failures and unanswerables), paired comparison on same items, deterministic checks plus calibrated LLM judge plus human spot checks, confidence intervals, per-category slices, check regressions on must-pass cases.
- Pitfalls: judge biases, test-set leakage or overfit to the eval, noisy small sample, cherry-picked examples, changing two things at once (separate prompt vs model effects).
- Rollout: shadow or canary with online metrics, monitoring, rollback plan, pinned versions.
- Decision: written summary with numbers, risks, and recommendation; do not switch "tomorrow" without at least a quick eval and canary, but offer the fastest safe path.
- Red flags: "looks better to me", no baseline, ignoring cost/latency.

---

## Debrief checklist after each scenario
- Did I ask about users, success metric, data, constraints before designing?
- Did I mention evals, security/privacy and cost without being asked?
- Did I give a phased plan with a first deliverable?
- Did I name failure modes and how I would detect them?
- Could the customer repeat my summary to their boss?
