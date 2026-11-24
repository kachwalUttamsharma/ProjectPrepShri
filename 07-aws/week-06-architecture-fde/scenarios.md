# Week 6 - 10 System-Design Scenarios with Model Answers

Method for each: clarify requirements -> estimate scale -> draw boxes -> pick services with reasons -> address failure, security, cost -> state tradeoffs.

---
## 1. Highly available web app (3-tier) for a growing startup
Req: 50k users, 99.9%, budget-conscious.
```
Route 53 -> CloudFront -> ALB (3 AZ) -> ECS Fargate (autoscale) -> Aurora Postgres Multi-AZ (+1 reader) ; ElastiCache for sessions ; S3 for assets
```
Why: managed everything; Fargate avoids patching; Aurora fast failover. Scaling on ALBRequestCountPerTarget. Cost: Savings Plan on Fargate/Aurora RI after stabilizing; single NAT per AZ or endpoints. Tradeoff: single-region; DR via cross-region snapshots (RTO hours) until the SLA demands more.

## 2. File upload and processing pipeline (images/videos)
Browser -> API returns presigned multipart URLs -> S3 (raw) -> S3 event -> SQS -> Lambda/Fargate workers (or MediaConvert) -> S3 (processed) -> DynamoDB status -> notify via SNS/WebSocket. DLQ on SQS; lifecycle to IA/Glacier; CloudFront for delivery. Why SQS: absorbs spikes, retries. Idempotent processing keyed by object version.

## 3. Real-time analytics on clickstream (1M events/min)
Producers -> Kinesis Data Streams (on-demand or ~N shards: 1M/min ~ 17k rec/s ~ 17+ shards at 1k rec/s each, size by bytes too) -> Flink (aggregations) -> DynamoDB/OpenSearch for dashboards; Firehose -> S3 Parquet -> Athena/Redshift for history. Partition key high-cardinality to avoid hot shards. Tradeoff: Kinesis (managed, AWS-native) vs MSK (Kafka ecosystem).

## 4. Multi-region active-active API with sub-second failover
Route 53 latency/health checks or Global Accelerator in front of regional ALB -> ECS; data in DynamoDB Global Tables (last-writer-wins; design for conflicts) or Aurora Global (single writer, write-forwarding). Replicate secrets (Secrets Manager replication), ECR images, KMS multi-region keys. Test failover regularly. Tradeoff: cost ~2x+, consistency model complexity, data residency.

## 5. Secure data lake for analytics
S3 raw/curated zones (separate buckets/accounts), Glue crawlers/ETL, Glue Data Catalog + Lake Formation for column/row-level permissions, Athena/Redshift Spectrum for queries, KMS CMKs, Macie for PII, CloudTrail data events, VPC endpoints, Parquet + partitioning for cost. Ingest via Firehose/DMS/AppFlow. Tradeoff: Redshift (performance, concurrency) vs Athena (pay per scan, no infra).

## 6. Serverless REST API with auth and a relational backend
HTTP API + Cognito JWT authorizer -> Lambda -> RDS Proxy -> Aurora Serverless v2 (or DynamoDB if access patterns are simple). WAF, throttling, reserved concurrency to protect DB, X-Ray. Cold starts mitigated with provisioned concurrency on hot endpoints. Tradeoff: at steady high QPS move to Fargate for cost.

## 7. Migrate an on-prem monolith with a SQL Server DB
Phase: assess (Migration Hub / Application Discovery), rehost (MGN) to EC2 for speed, DMS + SCT to RDS SQL Server (or Aurora Postgres if modernizing), Direct Connect + VPN backup, cutover with DMS CDC, then incrementally strangle to containers. Six Rs: rehost, replatform, refactor, repurchase, retire, retain. Risks: licensing (BYOL/Dedicated Hosts), latency to remaining on-prem deps, rollback plan.

## 8. Event-driven order processing (microservices)
API -> Order service writes DynamoDB (transactional outbox via Streams) -> EventBridge "OrderCreated" -> rules to SQS queues for payment, inventory, email; Step Functions for saga with compensation; DLQs and alarms; idempotency keys; schema registry. Tradeoff: eventual consistency, debugging distributed flows (use correlation IDs + tracing).

## 9. Cost-optimize a $50k/month AWS bill
Steps: tag + Cost Explorer by service/account; likely top items EC2/RDS/NAT/data transfer/CloudWatch/S3. Actions: Compute Optimizer right-sizing, Graviton, Savings Plans + RDS RIs for steady, Spot for stateless/batch, schedule non-prod off nights, S3 lifecycle + Intelligent-Tiering, VPC endpoints, log retention/sampling, delete orphaned EBS/snapshots/idle LBs, CloudFront for egress. Governance: budgets, anomaly detection, monthly FinOps review. Quantify expected savings (typically 20-40%) and effort; do low-risk first.

## 10. Enterprise RAG assistant with data residency + SSO
Region fixed to customer's allowed region (check Bedrock model availability; use in-region inference profile, not cross-region, if residency strict). SSO via IAM Identity Center/OIDC (Okta) -> ALB OIDC auth or Cognito federation -> Fargate FastAPI. Documents in S3 (SSE-KMS CMK), ingestion workers, pgvector on Aurora with row-level security per department, Bedrock Guardrails for PII, PrivateLink only (no internet egress), CloudTrail + prompt/response logging with retention and redaction, per-user ACL checks at retrieval time. Eval harness and feedback loop. Tradeoffs: strict isolation vs cost; in-region model choice may be narrower; managed Knowledge Bases (faster) vs custom pipeline (control over ACL-aware retrieval).
