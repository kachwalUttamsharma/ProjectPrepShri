# HLD 8 - Enterprise RAG / Chat-with-Documents Platform (FDE-style)

Background: [caching, rate limiting, observability, LLM-system angle](../week-05-architecture-operations/lesson.md), [queues](../week-03-coordination-messaging/lesson.md), [sharding/indexes](../week-02-data-storage/lesson.md). AWS context: [07-aws](../../07-aws/README.md). Framework: [framework.md](framework.md).

This is the most likely prompt for a forward-deployed role: the customer has messy documents, strict security, and wants answers they can trust. Lead with *trust, permissions, evaluation*, not just "embed and search".

## 1. Clarify requirements
Functional
- Ingest documents from connectors (SharePoint, Drive, Confluence, S3, email, PDFs, wikis); keep them in sync.
- Chat Q&A with citations; follow-up questions with conversation memory; feedback (thumbs).
- Admin: sources, tenants/workspaces, usage and cost dashboards.
Non-functional / questions to ask
- Tenants: how many, how big? (e.g., 500 tenants, 1k - 10M docs each.) Multi-tenant SaaS vs single-tenant VPC/on-prem deployment?
- **Access control**: user must only get answers from documents they may read (ACLs mirrored from source).
- Latency: time to first token < ~2 s, full answer < ~10 s. Freshness: new doc searchable within minutes.
- Data residency, no training on customer data, PII handling, audit logs, SOC2/HIPAA-style needs (check customer requirements).
- Accuracy bar: must say "I don't know" rather than hallucinate? Quality targets measured by evals.
Out of scope: model training, fine-tuning (mention as later options).

## 2. Estimate (worked)
- 100 tenants x 1M docs avg 10 pages = 1B pages... too big; take 20M docs total, ~10 chunks of 500 tokens each = 200M chunks.
- Embeddings: 1024-dim float32 = 4 KB/vector -> 200M x 4 KB = 800 GB raw (+ index overhead ~1.5-2x; quantization to int8 or binary cuts 4-32x). Check chosen vector DB docs for memory vs disk index.
- Ingestion cost: 200M chunks x 500 tokens = 100B tokens to embed once; at embedding prices (check current pricing, often cents per million tokens) this is order of thousands of dollars, so incremental re-embedding by content hash matters.
- Query load: 10k users, 20 queries/user/day = 200k/day ~ 2.3/s avg, peak ~25/s. Low QPS; cost and latency per query dominate, not throughput.
- LLM cost per query: 6k input tokens (prompt + 5-8 chunks + history) + 500 output. At, say, $3/M input and $15/M output (illustrative; check current prices) = $0.018 + $0.0075 ~ $0.025/query -> ~ $5k/day at 200k queries. Prompt caching, smaller models for routing/rewrite, and answer caching are meaningful levers.

## 3. API
```
POST /v1/chat   {conversation_id?, message, filters?{source,date}, stream:true}
     -> SSE stream: tokens, then {citations:[{doc_id, title, url, chunk_id, quote}]}
POST /v1/feedback {message_id, rating, comment}
POST /v1/sources  {type:"sharepoint", credentials_ref, sync_schedule}   (admin)
GET  /v1/documents/{id}/status          indexed|failed|pending
DELETE /v1/documents/{id}                (must purge vectors, cache, derived data)
```
AuthN via OIDC/SAML SSO; the user's identity (and groups) flows through to retrieval.

## 4. Data model
- `documents(doc_id, tenant_id, source_id, source_uri, content_hash, acl_hash, version, status, updated_at)` - Postgres.
- `chunks(chunk_id, doc_id, tenant_id, ord, text, metadata{title,section,page,...}, embedding)` - vector store (pgvector, OpenSearch, Pinecone, Qdrant, etc.) plus a keyword index (BM25) for hybrid.
- `acl`: principals (user/group ids) allowed per doc, stored as metadata on each chunk (`allowed_principals`) *and* re-checked against source or a synced ACL table.
- `conversations/messages`, `eval_sets`, `traces` (prompt, retrieved chunk ids, model, tokens, latency, feedback).
- Raw files in object storage (S3) with per-tenant prefix and KMS keys.

## 5. High-level diagram
```
 INGESTION (async, idempotent)
 Connectors --> [Sync scheduler / webhooks] --> queue --> [Fetcher]
   -> raw store (S3, per-tenant KMS) -> [Parser: PDF/OCR/HTML/tables]
   -> [Chunker] -> [Embedder (batch, rate-limited)] -> [Indexer]
        |                                                  |-> Vector index (tenant-filtered)
        |-> ACL sync (users/groups) ------------------------|-> BM25 index
        `-> DLQ / failure dashboard

 QUERY (sync, streaming)
 User -> API GW (authN, rate limit, tenant quota)
      -> [Orchestrator]
          1 guard input (injection/PII/policy)
          2 rewrite query w/ history (small model)
          3 retrieve: vector + BM25, filter tenant AND ACL  (top ~50)
          4 rerank (cross-encoder) -> top 5-8
          5 build prompt (instructions, chunks w/ ids, history budget)
          6 LLM (streaming)  -> 7 guard output (grounding, PII, citation check)
          8 return answer + citations; log trace
      caches: semantic/answer cache, embedding cache, prompt cache
      observability: traces, token/cost metrics, eval sampling
```

## 6. Deep dives
**Chunking.** Structure-aware (headings, sections, tables), ~300-800 tokens with ~10-15% overlap; prepend document title/section ("contextual chunking") so chunks are self-explanatory. Keep parent doc pointer to expand context. Tables and PDFs/OCR are where quality dies - invest in parsing and test on real customer docs.
**Embeddings and vector store.** ANN indexes (HNSW: fast, memory-hungry; IVF/PQ: compact, lossy; DiskANN-type for disk). Choose by scale: pgvector fine to ~ few million vectors per tenant-sharded index; dedicated store beyond. Embedding model choice is versioned: changing models means full re-embed, so store `embedding_model` and support dual indexes during migration.
**Hybrid search + rerank.** Dense vectors miss exact terms (IDs, acronyms, error codes); BM25 misses paraphrase. Merge with reciprocal rank fusion, then rerank with a cross-encoder for precision. Metadata filters (date, source) from query understanding.
**Per-tenant isolation and ACLs (critical).**
- Tenant isolation: separate index/namespace per tenant for strict customers (blast radius, deletion, per-tenant keys), shared index with mandatory `tenant_id` filter for small tenants. Filter is enforced in a data-access layer, never trusting the LLM or client.
- Document ACLs: pre-filter during retrieval (ACL as filter in vector query) rather than post-filtering top-k (post-filter leaks counts and returns too few results). Group membership changes: sync frequently; cache with short TTL; permission changes must propagate faster than content changes. Prefer failing closed.
- Never put unauthorized text into the prompt: the LLM cannot be trusted to withhold it.
**Freshness and deletes.** Incremental sync via webhooks/delta APIs; content_hash to skip unchanged docs; deletion must cascade to chunks, caches, and backups per policy ("right to erasure").
**Caching.** Exact-match answer cache keyed by (tenant, ACL-scope, normalized query, index version); semantic cache (embedding similarity) is risky across ACL scopes - scope it by permission set and be conservative. Provider prompt caching for the stable prefix (system prompt + instructions). Embedding cache for repeated queries.
**Rate limits and quotas.** Per-user and per-tenant token buckets (see [rate limiter](02-rate-limiter.md)) counting *tokens*, not just requests; global limiter to stay under provider TPM/RPM; queue and backoff on 429; model fallback (secondary provider/smaller model) with circuit breaker. Budgets with alerts per tenant.
**Cost control.** Route simple queries to small models; trim context (rerank top-k small); cap output tokens; batch embedding at off-peak; dedupe chunks; quantize vectors; track $/query and $/tenant.
**Latency.** Stream tokens; parallelize vector + BM25; small query-rewrite model; avoid sequential LLM calls where possible; budget: retrieval ~200 ms, rerank ~150 ms, TTFT ~ 1 s.
**Evaluation (what separates senior answers).** Offline golden set per customer (question, expected answer, supporting doc). Measure retrieval (recall@k, MRR, nDCG) separately from generation (faithfulness/groundedness, answer relevance, citation accuracy), using LLM-as-judge calibrated against human labels. Run in CI on every change to chunking, prompts, models; online: feedback, sampled review, drift dashboards. Keep a regression set from past failures.
**Guardrails.** Prompt-injection from documents (indirect injection): treat retrieved text as untrusted data, delimit it, no tool execution on its say-so, least-privilege tools. PII redaction in logs; output checks for citation presence and grounding; refusal when retrieval confidence low ("I could not find this in your documents"); content policy filters; audit log of who asked what.
**Observability.** Trace per request: query, rewritten query, retrieved chunk ids + scores, rerank, prompt tokens, model, latency per stage, cost, feedback. Dashboards: no-answer rate, thumbs-down rate, p95 latency, 429 rate, ingestion lag, index freshness. Redact sensitive content per policy.
**Deployment constraints (FDE reality).** Customer may require VPC/private deployment or on-prem: models via cloud private endpoints (e.g., Bedrock/Azure OpenAI/Vertex in the customer's account, check current availability and data-handling terms) or self-hosted open-weight models (GPU capacity, quantization, vLLM-type serving). Design components behind interfaces (LLM client, vector store, object store) so they swap per environment. Secrets in KMS/Secrets Manager, egress controls, private networking, bring-your-own-key.
**Agentic extensions (mention only).** Tool use, multi-hop retrieval, query decomposition for complex questions; adds latency, cost and new failure modes.

## 7. Bottlenecks and failure modes
- Bad parsing -> bad answers (garbage in). - Stale or wrongly permissioned index (security incident). - Provider rate limits/outages. - Embedding model drift/migration. - Long ingestion backlog on initial sync (backfill throttling, per-tenant fairness). - Hallucinated citations. - Cost blowup from long histories/loops. - Noisy neighbor tenant. - Prompt injection via a poisoned document.

## 8. Tradeoffs
- Per-tenant index (isolation, ops overhead) vs shared (cheap, filter bug = leak).
- Larger chunks (context) vs smaller (precision). - Reranker (quality, +latency/cost). - Long context stuffing vs retrieval (cost, "lost in the middle"). - Semantic cache (savings) vs correctness/ACL risk. - Managed LLM API (fast start) vs self-hosted (control, ops). - Fine-tuning vs RAG (RAG for knowledge, fine-tune for style/format).

## 9. What to say out loud
"Before architecture, I want the trust model: who can see which documents, and what accuracy bar the customer needs. I will split ingestion (async, idempotent, incremental) from query (streaming). Permissions are enforced at retrieval time as a filter, so unauthorized text never reaches the model. Quality comes from hybrid retrieval and reranking and is measured with a golden set, separating retrieval metrics from generation metrics. I will control cost with caching, routing, and token-based quotas, and keep the LLM and vector store behind interfaces because the customer's deployment constraints may differ."

## 10. Follow-ups
- A user complains the bot missed a doc they know exists. How do you debug? (trace: ACL filter? chunking? recall@k? rewrite?)
- How do you roll out a new embedding model with zero downtime? (dual index, shadow eval, cutover, delete)
- How do you prove no cross-tenant leakage? (enforced data layer, tests with canary docs, audit, pen test)
- How would you handle 10x tenants? (shard vector store by tenant, queue fairness, per-tenant budgets)
- When would you not use RAG? (small corpus -> long context; structured data -> text-to-SQL; need exact calc -> tools)
- How do you present uncertainty to the end user? (citations, confidence threshold, "not found" path)
