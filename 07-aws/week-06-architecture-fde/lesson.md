# Week 6 - Architecture and the Forward-Deployed-Engineer Angle

---
## 1. Well-Architected Framework (6 pillars)
| Pillar | Core question | Typical practices |
|---|---|---|
| Operational Excellence | Can we run and evolve it? | IaC, CI/CD, runbooks, observability, game days, small reversible changes |
| Security | Is data and access protected? | Least privilege, identity foundation, encryption, traceability, automate response, defense in depth |
| Reliability | Does it recover and scale? | Multi-AZ, health checks, retries with backoff, quotas, backups, test recovery, loose coupling |
| Performance Efficiency | Right resources for the job? | Right-size, serverless where fit, caching, CDN, measure and experiment |
| Cost Optimization | Are we paying only for value? | Right-size, pricing models, tagging, turn off idle, data transfer awareness, FinOps |
| Sustainability | Minimizing environmental impact | Graviton, utilization, managed services, region choice, less data |
Tools: Well-Architected Tool (reviews), lenses (Serverless, SaaS, ML, GenAI), Trusted Advisor, Compute Optimizer.
Interview framing: "I trade pillars off explicitly: e.g. Multi-Region improves Reliability but hurts Cost and Operational complexity."

---
## 2. HA and DR
- **RTO** = max acceptable time to restore service. **RPO** = max acceptable data loss window (time).
- **HA** (within region, minutes/no downtime): Multi-AZ everything stateful and stateless; **DR** (region loss).

| Strategy | RTO | RPO | Cost | How |
|---|---|---|---|---|
| Backup & Restore | hours | hours | $ | Backups/snapshots copied cross-region (AWS Backup), rebuild with IaC |
| Pilot Light | tens of min - hours | minutes | $$ | Data replicated (Aurora Global/cross-region replica), minimal core running; scale up on failover |
| Warm Standby | minutes | seconds-minutes | $$$ | Scaled-down full copy running; scale up + switch DNS |
| Multi-site Active-Active | near zero | near zero/seconds | $$$$ | Both regions serve traffic (DynamoDB Global Tables, Aurora Global write-forwarding, Route 53 latency/GA) |
Practices: define RTO/RPO per workload with the business; automate failover and test it (game days); remember data-plane vs control-plane dependencies (use data-plane actions, pre-provision) ; keep configs/AMIs/secrets replicated; Route 53 ARC.
Single-region HA reference: ALB across 3 AZs -> ASG/ECS across 3 AZs -> Aurora Multi-AZ + ElastiCache replica -> S3 (11 9s) ; static assets via CloudFront.
Common failure answers: AZ failure = handled by Multi-AZ; region failure = DR plan; human error/ransomware = backups, versioning, Object Lock, separate backup account; bad deploy = blue/green + rollback.

---
## 3. Cost optimization toolbox
1. Visibility: tags + cost allocation tags, Cost Explorer, Budgets, CUR, Anomaly Detection.
2. Right-size: Compute Optimizer, Graviton, gp3 over gp2, delete idle (EBS, EIP, ELB, NAT).
3. Commit: Savings Plans (compute), RIs (RDS/ElastiCache/Redshift/OpenSearch reserved), Spot for fault-tolerant.
4. Architecture: serverless for spiky, scale to zero, caching/CDN, S3 lifecycle/Intelligent-Tiering, VPC endpoints, compress, avoid cross-AZ/region chatter.
5. LLM-specific: choose smaller model per task, prompt caching, batch inference (discount), limit max tokens, cache responses, provisioned throughput only at sustained volume.
Top surprise bills: NAT Gateway data, cross-AZ transfer, CloudWatch logs ingestion, idle load balancers, orphaned snapshots, public IPv4, Provisioned IOPS, Bedrock/LLM token usage with no limits, DynamoDB on-demand scans.

---
## 4. Serverless vs containers vs VMs
| | Lambda (serverless) | ECS Fargate | EKS | EC2 |
|---|---|---|---|---|
| Ops burden | lowest | low | high | highest |
| Scale to zero | yes | no (min 1 task; or scale to 0 via app autoscaling manually) | no | no |
| Max run time | 15 min | unlimited | unlimited | unlimited |
| Cost at steady high load | high | medium | lower | lowest |
| Startup | cold start ms-s | task start 10s of seconds | pod seconds | minutes |
| Portability | low | medium | high | high |
| Best for | events, glue, bursty APIs | web services, workers | K8s platform teams | special needs/optimization |
Rule of thumb: start serverless/managed; move to containers when you hit limits (duration, cold start, runtime, cost at sustained throughput); choose EKS only with a reason.

---
## 5. FDE-style walkthrough: FastAPI + LLM/RAG app on AWS

### Requirements (clarify first)
Users? latency target? data sensitivity (PII, region residency)? documents volume/updating cadence? model choice (Bedrock vs external API)? budget? auth (SSO)? availability target?

### Reference architecture
```
                      Route 53 -> CloudFront (+WAF) -> ALB (public subnets, ACM TLS)
                                                          |
   Cognito/OIDC (JWT) ----------------------------> ECS Fargate service "api" (FastAPI + uvicorn)
                                                    private subnets, 2+ AZs, autoscale on ALB req/target + CPU
                                                          |
        +----------------------+-----------------+--------+-----------------+
        |                      |                 |                          |
   RDS/Aurora Postgres     S3 (docs, uploads)  Secrets Manager        Amazon Bedrock (via VPC interface endpoint)
   (+pgvector index)       presigned URLs       (DB creds, 3rd-party)  - embeddings (Titan/Cohere)  - LLM (Claude etc.)
        |                                                              - Guardrails (optional)
   OR OpenSearch (Serverless/managed) for vector + hybrid BM25 search

 Ingestion path (async): S3 upload -> EventBridge/S3 event -> SQS -> ECS worker/Lambda:
     parse -> chunk -> embed (Bedrock) -> upsert into pgvector/OpenSearch ; status in DB ; DLQ on failure
 Observability: CloudWatch Logs/metrics/alarms, X-Ray/OTel traces, token/cost metrics per tenant ; CloudTrail, Config
 CI/CD: GitHub Actions (OIDC role) -> ECR -> ECS rolling/blue-green ; IaC: Terraform/CDK
```

### Key design decisions and tradeoffs
- **Compute:** ECS Fargate vs Lambda. Fargate chosen because LLM calls/streaming can exceed API Gateway's 29 s, FastAPI is a long-running ASGI app, no cold start, easy containers. Lambda + function URL streaming viable for low traffic/cost. EKS overkill unless the customer is K8s-standard.
- **Streaming:** use SSE/WebSocket via ALB (idle timeout raise from 60 s e.g. to 120-300 s). CloudFront must allow streaming (don't buffer).
- **Vector store options:**
  | Option | Pros | Cons |
  |---|---|---|
  | Aurora/RDS Postgres + pgvector | One DB for relational + vectors, SQL filters/joins, transactional, simple ops, cheap at small-medium scale (HNSW/IVFFlat indexes) | Scale limits at very large (100M+ vectors), tuning index memory, limited hybrid search |
  | OpenSearch (managed/Serverless) | k-NN + BM25 hybrid, scale-out, rich filtering | More cost (OpenSearch Serverless has minimum OCU cost - check docs), more ops |
  | Bedrock Knowledge Bases | Managed ingest/chunk/embed/retrieve (backed by OpenSearch Serverless, Aurora pgvector, S3 Vectors, etc. - check current list) | Less control over chunking/ranking, vendor coupling |
  | S3 Vectors / others | Very low-cost storage for large, infrequent-query corpora (check GA status/limits) | Latency/features differ |
  Default pitch: pgvector on Aurora for most FDE pilots (fewer moving parts); OpenSearch when hybrid search or scale demands.
- **Bedrock vs direct API:** Bedrock keeps data in AWS account boundary, IAM auth (no API keys), VPC endpoints/PrivateLink, no training on customer data by default, CloudTrail logging, Guardrails, multiple models behind one API, regional availability and quotas (tokens/min, requests/min; cross-region inference profiles for capacity). Direct Anthropic/OpenAI API: newest models/features first, sometimes cheaper/more features; needs egress via NAT and key management. Say which fits customer compliance.
- **Secrets:** DB creds in Secrets Manager with rotation; injected via task definition `secrets`; Bedrock needs no key (task role with `bedrock:InvokeModel*` on specific model ARNs).
- **Data/security:** private subnets for tasks and DB; SG chain; S3 Block Public Access + SSE-KMS; encrypt RDS; per-tenant isolation (row-level security / tenant_id filter on vector queries - enforce in the DB layer, not just prompts); PII redaction/Guardrails; audit logs of prompts/responses with retention policy; WAF; rate limiting per user/tenant.
- **Reliability:** Multi-AZ Aurora, 2+ Fargate tasks across AZs, health checks `/healthz`, timeouts and retries with backoff + jitter on Bedrock (`ThrottlingException`), circuit breaker, fallback model, async ingestion with DLQ, idempotent upserts.
- **Cost levers:** Smaller model (Haiku-class) for routing/classification, bigger model for synthesis; limit top-k and context size; prompt caching; cache frequent answers (ElastiCache); batch embeddings; cheaper embeddings model; scale Fargate off-hours (dev); NAT avoidance via endpoints.
- **Evaluation/ops:** log retrieval hits, groundedness evals, golden question set, regression tests per prompt/model change; feature flag model IDs; version prompts.
- **Environments:** separate accounts (dev/stage/prod), Terraform/CDK modules, per-env Bedrock quotas.

### FastAPI snippet (illustrative; no account needed to read)
```python
import json, boto3
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
app = FastAPI()
brt = boto3.client("bedrock-runtime")          # creds come from ECS task role

@app.post("/ask")
def ask(q: str):
    # 1) embed query 2) SELECT ... ORDER BY embedding <=> :qvec LIMIT 5 (pgvector) 3) call LLM
    resp = brt.converse(modelId="<model-id-or-inference-profile>",
        messages=[{"role": "user", "content": [{"text": q}]}],
        inferenceConfig={"maxTokens": 512})
    return {"answer": resp["output"]["message"]["content"][0]["text"]}
```
(Use `converse_stream` for token streaming; check the Bedrock docs for current model IDs.)

---
## 6. Explaining tradeoffs to a customer (FDE communication skills)
1. **Start with their goal and constraints**, not services: users, SLA, data sensitivity, budget, team skills, timeline.
2. **Offer 2-3 options with a recommendation**: "Option A (fastest, managed), B (cheaper at scale), C (most control). I recommend A for the pilot because..., revisit at X load."
3. **Quantify**: rough monthly cost ranges, latency numbers, RTO/RPO, team-weeks of effort. State assumptions and what would change the answer.
4. **Use their language**: "if us-east-1 loses an AZ, you lose nothing; if the whole region fails, you're down ~4 hrs unless you pay roughly +60% for warm standby".
5. **Name the risks and reversibility**: two-way-door decisions (move fast) vs one-way (data model, region, account structure).
6. **Pilot -> production path**: what we'd harden (auth, observability, quotas, DR, evals, cost guardrails).
7. **Be honest about unknowns**: "check quotas with Bedrock; model availability varies by region."
8. Leave a diagram + a one-page decision record (ADR).
Anti-patterns: jargon dumps, over-engineering for a pilot (EKS + multi-region on day 1), ignoring their existing stack/skills, unquantified claims.

---
## 7. Anti-pattern spotting list (review exercise)
Public S3 buckets; DB in public subnet; one big NAT with cross-AZ traffic; access keys in env vars; no DLQ; synchronous chains; single AZ; unbounded Lambda concurrency onto RDS; no budget alarms; hardcoded model keys; secrets in git; no log retention; manual console changes; no tagging.
