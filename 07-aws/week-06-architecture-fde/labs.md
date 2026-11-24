# Week 6 Labs (OPTIONAL, paper-first)

COST WARNING: Bedrock bills per token (and requires model access in the console), Aurora/OpenSearch/Fargate/ALB/NAT all bill hourly. Do the design on paper; only deploy a tiny version briefly, if at all.

1. Paper: draw the RAG architecture from lesson.md from memory; annotate each arrow with protocol, auth, and failure mode.
2. Paper: write a one-page decision record choosing pgvector vs OpenSearch for a made-up customer.
3. Free: run the AWS Well-Architected Tool (free) against an imaginary workload; read the questions for Security and Reliability.
4. Free: estimate the architecture in the AWS Pricing Calculator and export it. Compare Fargate vs Lambda for 5 req/s steady vs 0.1 req/s.
5. Optional small spend: call Bedrock `converse` with a small model a handful of times from your laptop with a budget alarm set; delete nothing is needed but disable model access if unused.
6. Local (no AWS): FastAPI + Postgres + pgvector in docker compose to practice the retrieval query.
