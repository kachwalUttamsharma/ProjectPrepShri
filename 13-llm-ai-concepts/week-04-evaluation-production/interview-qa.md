# Week 4 Interview Q&A: Evaluation and Production

Prices in worked answers are hypothetical placeholders; say "check current docs" for real numbers.

---

**1. How do you design an eval set?**
Start from real traffic or tickets, stratify by category/difficulty/language, include edge cases, adversarial and unanswerable items and every past failure. 50 to 100 to begin, hundreds later, with a held-out slice. Define labels or rubrics, version the dataset, check annotator agreement, and keep eval items out of prompts and fine-tuning data.

**2. What metrics for a classification feature? For RAG? For an agent?**
Classification: per-class precision/recall/F1, confusion matrix, schema-valid rate. RAG: retrieval recall@k/MRR plus generation faithfulness, correctness, citation accuracy, abstention. Agent: task success rate, tool-call correctness, steps, cost per success, forbidden-action rate. All: latency percentiles and cost.

**3. Pitfalls of LLM-as-judge?**
Position bias, verbosity bias, self-preference, vague rubrics, ignorance of facts, nondeterminism, judge version drift, optimizing against the judge. Mitigate with randomized order, specific rubrics, reference answers, different-family or multiple judges, pinned judge versions, and calibration against human labels with reported agreement.

**4. Offline vs online evaluation?**
Offline: fixed dataset, repeatable, run pre-release; limited by representativeness. Online: shadow, canary, A/B on real traffic with business metrics and implicit feedback; captures reality but is slower and riskier. Use both: online failures feed the offline set; offline gates deploys.

**5. How do you regression-test prompts?**
Prompts in version control, eval suite in CI on every change to prompt, model, retrieval or tools. Gate on key metrics and must-pass cases, compare per category and inspect output diffs. Pin model versions and run the suite on provider deprecation notices.

**6. Is a 2-point accuracy gain on 100 examples real?**
Probably not. Standard error is around 4 to 5 points at that size and accuracy near 80 percent. Use more samples, paired comparisons on the same items, bootstrap confidence intervals, and look at which items flipped.

**7. What do you log and trace for an LLM feature?**
Trace spans for retrieval (query, IDs, scores), each model call (prompt version, model id, params, tokens, latency, finish reason), each tool call, validation outcomes, guardrail triggers, final answer, user feedback, with a correlation ID. Redact PII, restrict access, set retention.

**8. How do you monitor quality in production?**
Operational metrics (latency, errors, cost), proxies (thumbs, retries, escalation, empty-retrieval or "not found" rate), sampled human or judge scoring of live traffic, input-drift detection, alerts and dashboards, a weekly review of failures that become eval cases.

**9. Explain prompt caching and how to benefit from it.**
The provider reuses computed state for an identical prompt prefix, lowering cost and latency for repeated prefixes. Put static content (system prompt, tool defs, documents) first and dynamic content last; avoid early timestamps/IDs; check current docs for TTL, minimum prefix length and discount.

**10. Semantic caching: when is it safe?**
For repeated, non-personalized, low-stakes FAQ-style questions, with a tuned similarity threshold, TTL and invalidation, and tenant-scoped keys. Unsafe when near-identical text means different things (order 12 vs 21), when answers are personalized, or when data changes. Evaluate false-hit rate before enabling.

**11. You are getting 429s. What do you do?**
Short-term: exponential backoff with jitter, honor Retry-After, client-side token bucket/concurrency limit, queue with priorities and per-tenant fairness, fallback model. Medium: request higher limits or provisioned throughput, reduce tokens per request, caching, move offline work to batch APIs. Capacity-plan peak tokens per minute before launch.

**12. When to use batch APIs versus streaming?**
Batch for offline, non-urgent bulk work (evals, backfills, archive classification, embeddings), usually discounted and asynchronous. Streaming for interactive UX to cut perceived latency; remember to cancel on disconnect and validate the final output.

**13. Estimate cost: 50,000 requests/day, 1,500 input and 200 output tokens, hypothetical $1/$4 per million.**
Per call: 1,500*1/1e6 + 200*4/1e6 = 0.0015 + 0.0008 = $0.0023. Per day $115; per month about $3,450. Then discuss levers: caching a static prefix, routing easy requests to a smaller model, trimming output, plus non-LLM costs (embeddings, vector DB, infra, logging, engineering).

**14. p95 latency is 12 s. How do you reduce it?**
Break down by span from traces. Typical wins: stream output; shrink prompt/retrieved context; cap output length; parallelize retrieval and tool calls; smaller model for easy steps; cache prefix/results; fix slow tools; hedge tail requests. Set an SLO by percentile and re-measure.

**15. How do you version prompts and models?**
Prompt templates in git with semantic versions, model ids pinned (no floating alias in prod), params, tool schemas, retrieval/index versions and eval dataset versions all recorded per request. Rollout via flags/canaries with rollback, and an eval report attached to each change.

**16. How do you handle PII and compliance?**
Classify data, minimize what is sent, detect and redact/pseudonymize before calling external models, avoid raw logging, encrypt, isolate tenants, enforce access via user identity, honor retention and deletion across vector store/caches/logs, get appropriate agreements (DPA/BAA), and involve the customer's security and legal teams. Check provider terms for retention, training use and region.

**17. What is LoRA and when is fine-tuning worth it?**
LoRA freezes base weights and trains small low-rank adapter matrices, cutting memory and storage and allowing swappable adapters. Worth it when prompting plateaus, volume makes a smaller tuned model cheaper, you need strict style/format, and you have hundreds to thousands of clean labeled examples and an eval to prove the gain. Not for fresh facts (use RAG). Compare against a strong prompt baseline first.

**18. Scenario: "Customer says answers got worse after your last release."**
Pull traces and the release diff (prompt, model, retrieval, tools). Re-run the regression suite on both versions; slice by category to find where it dropped. If the suite missed it, add those cases. Roll back if impact is severe, then fix forward behind a canary. Share a short root-cause note and the new safeguard.

**19. Scenario: "Security team won't let any customer data go to a third-party model."**
Ask what exactly is forbidden (PII only, or all content; region). Options: redaction/pseudonymization with a third-party model, a provider endpoint inside their cloud account/VPC with private networking and customer-managed keys, or self-hosted open-weights models. Explain capability, cost and ops tradeoffs, propose a pilot on non-sensitive data to prove value, and document the data-flow diagram for their review.

**20. Scenario: "Leadership asks: is the AI feature worth it? Cost is $X per month."**
Define the business metric (tickets deflected, handle time saved, conversion), measure a baseline, compute cost per successful outcome including infra and human review, compare against the human/process baseline, show quality and risk metrics from evals and online tests, and present sensitivity (volume, accuracy, price changes). Recommend scale/iterate/stop with evidence.

---

## Bonus probes
- "How big should the eval set be?" Big enough that differences you care about exceed noise; compute intervals.
- "How do you evaluate without ground truth?" Rubrics, pairwise preference, judge with calibration, user outcomes, expert review samples.
- "How do you test safety?" Red-team set of injections, PII bait, jailbreaks; track attack success rate across versions.
