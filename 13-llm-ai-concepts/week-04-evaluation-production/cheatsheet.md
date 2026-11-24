# Week 4 Cheatsheet: Evaluation and Production

## Eval set
Real traffic first; stratify; edge + adversarial + unanswerable + past failures; held-out; versioned; no leakage into prompts/finetune. 50-100 start. Use paired comparisons and bootstrap CIs.

## Metric menu
Classify: P/R/F1, confusion matrix. RAG: recall@k, MRR, faithfulness, citation acc, abstention. Agent: success rate, steps, cost per success, forbidden actions. Ops: p50/p95/p99, cost, error rate.
Order: deterministic checks, then LLM judge, then humans for calibration.

## LLM judge pitfalls
Position, verbosity, self-preference, vague rubric, factual blind spots, nondeterminism, version drift, judge overfitting. Fix: randomize, specific rubric, references, other family, pin, calibrate with humans.

## Offline vs online
Offline: dataset, CI gate. Online: shadow, canary, A/B, implicit feedback, sampled review. Failures become tests.

## Observability
Trace spans: retrieval, rerank, LLM (prompt version, model, tokens, latency, finish reason), tools, validation. Correlation ID. Redact PII. Alert on latency, errors, cost, thumbs-down, empty retrieval.

## Latency levers
Stream, shorten prompt, cap output, parallelize, smaller model, caching, precompute, hedge. Measure percentiles. Latency = TTFT + out_tokens / tps.

## Caching
Prompt prefix cache (static first). Exact response cache. Semantic cache (threshold, tenant-scoped, false-hit risk). Tool and embedding caches.

## Limits
RPM/TPM/concurrency; 429 -> backoff + jitter + Retry-After, token bucket, priority queue, tenant fairness, fallback, quota request. Batch API for offline. Cancel streams on disconnect.

## Cost formula
(in*P_in + out*P_out)/1e6 per call; subtract cached discount; add embeddings, rerank, vector DB, infra, logging. Report per successful outcome. Levers: route, cache, trim, batch, tuned small model.
Worked (hypothetical $1/$4): 300 in + 20 out = $0.00038; x100k/day = $38/day.

## Versioning
Prompt (git), model id pinned, params, tool schemas, index/embedding versions, eval set version; flags, canary, rollback; track deprecations.

## Safety/PII
Minimize, redact before external call, no raw logs, tenant isolation, user-identity ACLs, retention/deletion across stores, DPA/BAA, region/residency, red-team. Involve customer security/legal.

## Fine-tuning
Ladder: prompt, few-shot, RAG/tools, then fine-tune. LoRA = frozen base + low-rank adapters (A*B), cheap, swappable; QLoRA = quantized base. For behavior/format/distill, not fresh facts. Needs clean labels + eval + stable task.

## Deployment privacy options (more control = more ops)
Provider API with zero-retention terms < provider inside customer cloud/VPC < self-hosted open weights / air-gapped.
