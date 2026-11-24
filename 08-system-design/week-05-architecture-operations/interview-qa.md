# Week 5 - Interview Q&A: Architecture and Operations

Cover the answer, say yours aloud (30-60 s), then compare. Numbers marked "check current docs" change.

---
**1. Monolith or microservices for a new product?**
Start with a modular monolith unless team size or divergent scaling forces otherwise. Microservices add network failure modes, distributed data, and ops overhead. Keep clean module boundaries so extraction later (strangler fig) is cheap. Split when teams block each other on deploys or components have very different scaling/availability needs.

**2. What is a "distributed monolith" and how do you avoid it?**
Services that must be deployed together, share a database, or are chatty synchronously. You get microservice costs without benefits. Avoid with bounded contexts, database per service, async events, versioned contracts, and independent deployability as a hard test.

**3. REST vs gRPC vs GraphQL?**
REST: public APIs, cacheable, simple. gRPC: internal low-latency typed contracts, streaming, Protobuf, needs HTTP/2-aware LB. GraphQL: many client shapes, avoids over/under-fetching, but needs N+1 handling (DataLoader), query depth/cost limits, and is harder to cache.

**4. Offset vs cursor pagination?**
Offset scans and discards rows (slow deep) and shifts when data changes. Cursor/keyset uses `WHERE (sort_key, id) < cursor ORDER BY ... LIMIT n`, stable and index-friendly, but no random page jump. Use opaque cursors with a unique tiebreaker.

**5. How do you version an API without breaking clients?**
Additive-only changes where possible (new optional fields), tolerant readers, explicit version (URL or header) for breaking changes, deprecation window with Sunset header and usage metrics. For Protobuf never reuse field numbers. DB and API changes go expand then contract because old and new code coexist during rollout.

**6. What does an API gateway do, and what are its risks?**
Edge concerns: TLS termination, authn, rate limiting, routing, aggregation, logging, canary routing. Risks: bottleneck/SPOF (run redundant and stateless), extra latency, business logic creeping in. Distinguish from LB (traffic distribution) and service mesh (east-west).

**7. How does service discovery work?**
Instances register (or the platform tracks them) in a registry; health checks remove bad ones; clients look up via client-side discovery (Eureka), server-side (LB, Kubernetes Service), or DNS/mesh. Registries can be stale so clients need retries and timeouts. CP stores (etcd/Consul) vs AP (Eureka) tradeoff.

**8. Metrics, logs, traces: when do you use each?**
Metrics: cheap aggregates for alerting and trends. Logs: detailed events for debugging. Traces: per-request path and timing across services to find the slow/failing hop. Link them via trace_id and exemplars. Avoid high-cardinality metric labels.

**9. What should you alert on?**
User-visible symptoms tied to SLOs (error rate, latency, availability) using burn-rate alerts, not causes like CPU. Every alert actionable with a runbook. Use RED for services, USE for resources, golden signals overall.

**10. Why percentiles instead of averages, and why does tail latency matter more with fan-out?**
Averages hide the slow tail. With fan-out to N dependencies, probability at least one is slow is 1-(1-p)^N; 100 calls at p99 means ~63% of requests hit a slow one. Mitigate with hedged requests, timeouts, fewer hops, caching.

**11. Compare rolling, blue-green, and canary.**
Rolling: gradual, cheap, mixed versions, slower rollback. Blue-green: full parallel stack, instant switch and rollback, 2x capacity, DB compatibility still needed. Canary: small traffic slice with metric-gated promotion and auto-rollback; needs good SLIs. Add feature flags to decouple deploy from release.

**12. How do you do a zero-downtime schema change?**
Expand/contract: add nullable column or new table, deploy code writing both, backfill, switch reads, then drop old after all old code is gone. Avoid long locks (online schema tools), and make each step independently reversible.

**13. Define RPO and RTO and map to DR strategies.**
RPO = tolerable data loss; RTO = tolerable downtime. Backup/restore (hours/hours, cheapest), pilot light (minutes), warm standby (seconds-minutes), active-active (near zero, most expensive and needs conflict handling). Choose by business cost of downtime; test with drills.

**14. Active-active multi-region: what is hard?**
Data. Writes in two regions need conflict resolution (LWW, CRDTs), or partition users by home region, or a globally consistent DB (Spanner, higher write latency). Also routing, replication lag, split-brain, cross-region egress cost, and the control plane living in the failed region. Active-passive is simpler if RTO of minutes is acceptable.

**15. How do you avoid split-brain during failover?**
Single authority for who is leader (consensus system like etcd/ZooKeeper), quorum-based promotion, fencing tokens or STONITH so the old leader cannot write, and avoiding automatic failover on flaky health checks without hysteresis.

**16. JWT vs session cookies?**
Sessions: server state, easy revoke, needs shared store. JWT: stateless verification, good for service-to-service and scale, but hard to revoke, so use short expiry plus refresh tokens or a denylist. Always validate signature, exp, iss, aud; reject alg none. JWT is signed, not encrypted.

**17. How do you enforce multi-tenant isolation?**
Tenant id from verified token (never client-supplied), enforced in every query/cache key (row-level security or per-tenant schema/index), per-tenant quotas, optionally per-tenant encryption keys and separate stores for high-sensitivity tenants. Test with cross-tenant access tests. In RAG, filter by ACL in the vector query itself.

**18. Where should secrets live and how should they be used?**
In a secrets manager (Vault, AWS Secrets Manager) accessed via workload identity, injected at runtime, rotated, audited, short-lived where possible. Never in git, images, or logs. Prefer IAM roles over static keys.

**19. Design the serving path for an LLM feature. What is different from a normal service?**
Slow (seconds), costly per token, rate-limited by tokens, nondeterministic. So: stream responses, per-tenant token quotas plus a global limiter for provider limits, timeouts and retries with jitter, fallback model, caching (exact and careful semantic), model routing, async queue for non-interactive work, tracing with token/cost metrics, guardrails, and evals.

**20. How do you reduce LLM latency and cost?**
Latency: stream, smaller prompts, fewer chunks, small model for easy steps, parallelize independent calls, prefix caching, cap output, fewer agent hops. Cost: route to cheaper models, cache, trim context and history, batch APIs for offline work, cap output tokens, per-tenant budgets, consider fine-tuned small models at stable high volume. Verify current pricing and features in provider docs.

**21. How do you evaluate a RAG system and detect regressions?**
Curated eval set per domain; measure retrieval (recall@k, MRR, nDCG) separately from generation (faithfulness, relevance, correctness, citation accuracy); run in CI on any prompt/model/chunking/embedding change; calibrate LLM-as-judge against human labels; online feedback and sampled review; version prompts, models, indexes. Most failures are retrieval, so debug retrieval first.

**22. What are the main security risks in RAG/agent systems?**
Prompt injection (direct and via retrieved documents), data leakage across tenants/permissions, over-privileged tools, PII in prompts/logs, and unverified outputs. Controls: ACL-filtered retrieval, treat retrieved text as untrusted, least-privilege tools with approval for destructive actions, output validation, redaction, step/cost limits, audit logs.

**23. The provider is returning 429s and timeouts. What do you do?**
Backoff with jitter honoring Retry-After, circuit breaker, fall back to alternate model/provider, queue and prioritize interactive over batch, shed load with clear 503s, ensure timeouts and bulkheads so the LLM pool cannot exhaust shared threads, and alert on provider error budget. Longer term: provisioned capacity, multi-provider.

**24. Walk me through debugging a p99 latency spike.**
Check dashboards (RED) to scope endpoint/service and start time; correlate with deploys, config, traffic, dependency health; pull slow traces to find the slow span; check saturation (CPU, pools, queues, GC) and downstream; read logs for that trace; mitigate (rollback, scale, shed load, disable feature flag); then root-cause and postmortem with action items.
