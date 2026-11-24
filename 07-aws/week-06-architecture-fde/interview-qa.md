# Week 6 Interview Q&A - Architecture and FDE

**1. Name the six Well-Architected pillars.**
Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization, Sustainability.

**2. Define RTO and RPO.**
RTO: how long until service is restored. RPO: how much data (measured in time) you can afford to lose. They drive the DR strategy and its cost.

**3. List the four DR strategies in order of cost/speed.**
Backup & restore (hours), pilot light (core replicated, scaled-up on failover), warm standby (scaled-down full copy), multi-site active-active (near-zero RTO/RPO). Cost and complexity increase as RTO/RPO shrink.

**4. How would you design for 99.99% availability?**
Multi-AZ at every tier, no single points of failure, health checks and auto-healing, stateless services, Multi-AZ managed data stores, graceful degradation, safe deploys (blue/green/canary), tested failover; consider multi-region if the SLA includes regional failure. Compose dependency SLAs (multiply availabilities).

**5. Difference between high availability and disaster recovery?**
HA keeps service running through component/AZ failures with automatic recovery, minimal downtime. DR restores service after a major event (region loss, corruption), usually with defined RTO/RPO and sometimes manual steps.

**6. How do you protect against ransomware/accidental deletion?**
Versioning + MFA delete/Object Lock, AWS Backup with vault lock in a separate account, cross-region copy, least-privilege, SCPs, tested restores.

**7. Serverless vs containers: how do you choose?**
Serverless (Lambda) for event-driven, bursty, short work and low ops; containers (Fargate) for long-running services, streaming, larger runtimes, steady traffic, portability. EKS when K8s tooling/portability is required; EC2 for special hardware or max cost efficiency at scale.

**8. Scenario: Deploy a FastAPI + RAG app on AWS. Walk me through it.**
CloudFront+WAF -> ALB -> ECS Fargate (FastAPI) in private subnets across 2+ AZs; auth via Cognito/OIDC JWT; Aurora Postgres with pgvector (or OpenSearch) for vectors + metadata; S3 for documents with presigned uploads; async ingestion via S3 event -> SQS -> worker (parse, chunk, embed with Bedrock, upsert); Bedrock for LLM through VPC endpoint with task role; Secrets Manager for DB creds; CloudWatch/X-Ray; CI/CD via GitHub OIDC -> ECR -> ECS; IaC in Terraform/CDK.

**9. pgvector vs OpenSearch for vectors?**
pgvector: simple, one datastore, SQL filtering/joins, transactional, good to tens of millions vectors with HNSW, cheaper at pilot scale. OpenSearch: horizontal scale, hybrid BM25 + k-NN, advanced filtering, more ops/cost. Choose by scale, hybrid-search need, and existing stack.

**10. Why Bedrock rather than calling an external LLM API directly?**
IAM auth (no API keys), data stays within AWS and isn't used to train models by default, PrivateLink/VPC endpoints, CloudTrail audit, Guardrails, multi-model access and consolidated billing. Tradeoffs: model/feature lag, regional quotas, sometimes higher price.

**11. How do you handle LLM latency and long responses behind AWS infra?**
Stream tokens (SSE/WebSocket), avoid API Gateway's default 29 s limit (use ALB/Fargate or Lambda response streaming), raise ALB idle timeout, set client timeouts, async job pattern (202 + polling) for very long tasks.

**12. How do you handle Bedrock throttling?**
Retry with exponential backoff and jitter, request quota increases, cross-region inference profiles, queue requests (SQS) to smooth, cache results, fallback to a smaller/alternate model, provisioned throughput for steady high volume.

**13. How do you keep customer data isolated in a multi-tenant RAG app?**
Tenant ID on every chunk and mandatory filter enforced in the data layer (Postgres RLS or separate indexes/collections), per-tenant encryption keys if required, per-tenant rate limits, never rely on prompt instructions for isolation, audit retrieval logs.

**14. Where do secrets go in this architecture?**
Secrets Manager for DB credentials (rotation) and third-party keys; SSM for config; inject via ECS task definition secrets; Bedrock access by IAM role not keys; no secrets in images or git.

**15. Estimate what drives cost in a RAG app.**
LLM tokens (largest, scale with context size x requests), embeddings, vector store (OpenSearch minimums or Aurora instance), Fargate tasks, NAT/data transfer, logging. Levers: smaller models, smaller context/top-k, caching, prompt caching, batch embedding, endpoints instead of NAT.

**16. How would you explain Multi-AZ vs Multi-Region to a non-technical customer?**
Multi-AZ: like having two buildings in the same city; survives one building outage with no noticeable downtime. Multi-Region: a second city; survives a city-wide disaster but costs significantly more and is more complex. Ask what an hour of downtime costs them to decide.

**17. Customer wants Kubernetes for a small pilot. What do you say?**
Ask why (skills, portability, platform standards). If no hard need, recommend ECS Fargate or App Runner for the pilot for lower ops, with containerized code that can move to EKS later. If they have a K8s platform team, honor it.

**18. Customer says "AWS is too expensive". What do you do?**
Get a cost breakdown (Cost Explorer/CUR by tag), find top 5 line items, apply right-sizing, commitments, storage tiering, remove idle, endpoints vs NAT, architecture changes; show savings estimates and effort.

**19. Troubleshooting: app works in dev but times out in prod ECS service behind ALB.**
Check target health and health check path/port, SGs (ALB->task), task logs, NAT/endpoints for outbound dependencies, ALB idle timeout vs response time, DB connection limits, quotas (Bedrock throttling), recent deploy diffs, secrets/env differences.

**20. Troubleshooting: RAG answers are poor/hallucinating. AWS-side and design-side checks?**
Review chunking/size/overlap, embedding model consistency (index and query must match), retrieval quality (top-k, hybrid search, reranking, metadata filters), stale index, context truncation, prompt, guardrails; add evaluation sets and log retrieved chunks.

**21. How do you do zero-downtime deployment of the API?**
ECS rolling with min healthy 100% and ALB health checks, or CodeDeploy blue/green with test listener and automatic rollback on alarms; backward-compatible DB migrations (expand/contract).

**22. How do you structure environments and accounts?**
Separate AWS accounts per environment under Organizations, SSO access, shared network/logging accounts, SCP guardrails, IaC modules parameterized per env, promotion through CI/CD.

**23. What observability would you put on an LLM app?**
Request IDs, structured logs, latency per stage (retrieval vs LLM), token counts and cost per request/tenant, throttle/error rates, quality metrics (user feedback, eval scores), traces (X-Ray/OTel), alarms on error rate/p95/cost anomalies.

**24. What do you check in a security review of this architecture?**
Network exposure (public vs private), IAM least privilege (Bedrock model ARNs, S3 prefixes), encryption (KMS), secrets handling, prompt injection and data exfiltration paths, tenant isolation, logging/PII retention, WAF/rate limiting, supply chain (image scanning), CloudTrail/GuardDuty.

**25. When is Lambda the wrong choice here?**
Long streaming responses with sustained traffic, heavy dependencies (large ML libs near size limits), steady high QPS (cost), strict p99 latency without provisioned concurrency, persistent DB connections.
