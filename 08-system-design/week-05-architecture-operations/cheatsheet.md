# Week 5 Cheatsheet - Architecture and Operations

Numbers marked "check current docs" change. Long form: lesson.md.

## Monolith vs microservices
- Default: modular monolith. Split for team autonomy, independent scaling, fault isolation.
- Costs: network failures, no cross-service ACID, ops overhead. Smell: shared DB, lockstep deploys.
- Migration: strangler fig. Patterns: sidecar, BFF, anti-corruption layer.

## API design
| | REST | gRPC | GraphQL |
|---|---|---|---|
| Use | public CRUD | internal, streaming | multi-client, nested |
| Cache | easy (HTTP/CDN) | hard | hard |
| Gotcha | over-fetch | needs HTTP/2 LB | N+1, query cost |
- Codes: 400 bad, 401 unauthn, 403 forbidden, 404, 409 conflict, 429 (Retry-After), 503 overload.
- Pagination: cursor (keyset) for big/feeds, offset only for small. Opaque cursor + tiebreaker.
- Versioning: additive, tolerant reader, deprecate with Sunset. Expand then contract.
- POST not idempotent -> Idempotency-Key. Long ops -> 202 + status URL. ETag/If-Match for concurrency.

## Discovery and gateway
- Client-side (Eureka), server-side (LB, K8s Service), DNS/mesh (Envoy). Health checks, readiness vs liveness.
- Gateway: authn, rate limit, routing, TLS, aggregation. LB = distribute; gateway = north-south; mesh = east-west.

## Observability
- Metrics (alerts/trends), logs (detail), traces (path/timing). Link via trace_id (W3C traceparent, OpenTelemetry).
- RED: rate, errors, duration. USE: utilization, saturation, errors. Golden: latency, traffic, errors, saturation.
- Percentiles not averages. Fan-out: P(slow)=1-(1-p)^N (100 x p99 -> 63%).
- No high-cardinality metric labels. Structured logs, no secrets. Tail-based sampling keeps errors/slow.
- Alert on SLO burn rate, with runbooks. Liveness shallow.

## Deployment
| Strategy | Rollback | Cost | Notes |
|---|---|---|---|
| Rolling | slow | low | mixed versions |
| Blue-green | instant | 2x | DB must be compatible |
| Canary | auto | low | needs metrics |
| Shadow | n/a | 2x load | no user impact; beware side effects |
| Flags | instant | low | clean up flags |
- Graceful shutdown + connection draining. Immutable artifacts. Stage config pushes like code.

## Multi-region / DR
- RPO = data loss; RTO = downtime.
- Backup/restore (hrs) < pilot light < warm standby < active-active (~0).
- Data is the hard part: home-region partitioning, single-writer + replicas, LWW/CRDT multi-writer, Spanner-style global consensus.
- Risks: replication lag, split-brain (fence), standby under-capacity, control plane in dead region, DNS TTL.
- 3-2-1 backups; test restores; game days.

## Security
- AuthN vs AuthZ. OAuth2 = delegation, OIDC = identity, PKCE for public clients, client credentials for services.
- JWT: validate sig, exp, iss, aud; short-lived; hard to revoke; signed not encrypted.
- RBAC / ABAC / ReBAC. Check authz server-side every request (IDOR). Tenant id from token.
- TLS 1.3: ECDHE forward secrecy, 1 RTT. mTLS for service identity. Automate cert rotation.
- Envelope encryption (KMS). Secrets in manager, IAM roles, rotation. Parameterized queries. WAF + rate limits.

## LLM / RAG service
```
 gateway(authn, quotas) -> guardrails in -> cache -> retrieve(hybrid+rerank, ACL filter)
   -> prompt build (token budget) -> LLM (timeout, retry+jitter, fallback, breaker) -> guardrails out -> stream + citations
 async: logs/traces/cost; ingestion: parse->chunk->embed->upsert (idempotent, versioned, deletes propagate)
```
- Constraints: seconds latency, per-token cost (output > input price; check current docs), TPM/RPM limits, nondeterminism.
- Latency: stream, shrink prompt, route small models, parallelize, prefix cache, cap output.
- Cost: cost = in_tok*p_in + out_tok*p_out (+embed, vector DB). Route, cache, trim, batch API, per-tenant budgets.
- Cache: exact (safe), semantic (threshold, partition by tenant/ACL, invalidate on doc change), embeddings cache.
- Rate limits: per-tenant token bucket (in tokens) + global limiter for provider; 429 -> backoff+jitter, fallback, queue, priority.
- Evals: offline set in CI; retrieval (recall@k, MRR, nDCG) vs generation (faithfulness, relevance); LLM-judge calibrated; online feedback. Version prompt/model/index/embedder.
- Guardrails: PII, injection (direct + indirect via docs), ACL at retrieval, schema validation, citations/refuse, least-privilege tools, step/cost caps.
- Most RAG bugs = retrieval (chunking, stale index, missing filter).

## Say unprompted at the end
Multi-AZ, SLOs and alerts, canary + rollback, backups with tested restore, secrets/TLS/least privilege, tenant isolation, cost levers, what you would monitor.

## Cross-links
[07-aws week 5](../../07-aws/week-05-integration-ops-security), [07-aws week 6](../../07-aws/week-06-architecture-fde).
