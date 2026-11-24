# Week 6 Cheatsheet - Architecture and FDE

| Topic | One-liner | Use |
|---|---|---|
| Well-Architected | 6 pillars: Ops, Security, Reliability, Performance, Cost, Sustainability | Review framework |
| RTO / RPO | Time to restore / acceptable data loss | Drive DR design |
| Backup & restore | Hours RTO, cheapest | Non-critical |
| Pilot light | Core data replicated, compute off | Moderate RTO |
| Warm standby | Scaled-down full copy running | Minutes RTO |
| Active-active | Both regions live | Near-zero RTO, highest cost |
| Multi-AZ | Survive a data center loss | Default for prod |
| AWS Backup | Central backup policies, vault lock | Compliance/ransomware |
| Fargate vs Lambda vs EKS vs EC2 | Containers no-ops / events / K8s / full control | Compute choice |
| Bedrock | Managed foundation models via IAM | LLM in AWS boundary |
| Bedrock Knowledge Bases | Managed RAG ingest+retrieve | Fast RAG pilot |
| pgvector (Aurora/RDS) | Vectors in Postgres | RAG with SQL filters |
| OpenSearch | k-NN + BM25 hybrid search | Larger/hybrid RAG |
| Secrets Manager | Rotating secrets | DB creds |
| ECS task role | App permissions (Bedrock, S3) | Keyless access |
| Savings Plans / Spot / Graviton | Cost levers | FinOps |
| Cost Explorer / Budgets / CUR | Visibility | FinOps |

RAG-on-AWS blueprint: CloudFront+WAF -> ALB -> Fargate FastAPI -> (Aurora pgvector | OpenSearch) + S3 + Secrets Manager + Bedrock (VPC endpoint); async ingestion S3 -> SQS -> worker; CI/CD via OIDC -> ECR -> ECS.
Customer comms: goals -> options (2-3) -> recommendation -> numbers -> risks -> next steps.
Watch: API GW 29 s timeout for LLM calls; Bedrock quotas/throttling; NAT cost; tenant isolation in retrieval.
