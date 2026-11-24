# Final Mock Interview Sheet (about 75 minutes, self-run or with a partner)

Rules: speak out loud, timebox, say tradeoffs, ask clarifying questions, never claim a number you are unsure of ("check current docs").

## Part A - Warm-up fundamentals (10 min, 1 min each)
1. Region vs AZ vs edge. 2. Explain shared responsibility with an RDS example. 3. IAM role vs user. 4. How does policy evaluation work? 5. S3 consistency and durability. 6. Multi-AZ vs read replica. 7. SG vs NACL. 8. SQS Standard vs FIFO. 9. ALB vs NLB. 10. CloudWatch vs CloudTrail vs Config.

## Part B - Deep dives (20 min, pick 4, 5 min each)
- Lambda: limits, cold starts, concurrency, connecting to RDS.
- DynamoDB: key design for "orders by customer, latest first"; GSI vs LSI; hot partition.
- VPC: draw a 3-tier VPC; explain how a private instance reaches S3 and the internet; cost traps.
- Security: how to give a CI pipeline and an app least-privilege access; KMS envelope encryption.
- Messaging: choose among SQS, SNS, EventBridge, Kinesis for three given needs.

## Part C - Troubleshooting (10 min)
1. 504s from ALB intermittently. 2. Lambda timing out only in VPC. 3. S3 AccessDenied with SSE-KMS. 4. DynamoDB throttling at low average load. 5. ECS task stuck in PENDING / cannot pull image. 6. RDS connections exhausted after Lambda scale-up.

## Part D - System design (25 min)
Prompt: "A customer wants an internal Q&A assistant over 200k PDFs and a Postgres CRM, with SSO, audit logs, and 500 daily users. Design it on AWS, explain what you would pilot first, and what could go wrong." Use the week-06 lesson. Cover: requirements questions, architecture diagram, data ingestion, vector store choice, auth and ACL-aware retrieval, Bedrock quotas, failure modes, cost estimate drivers, security review, rollout plan.

## Part E - FDE behavioral/communication (10 min)
- Explain Multi-AZ vs Multi-Region to a VP in 60 seconds.
- A customer insists on a design you think is over-engineered. What do you do?
- The pilot is live and the AWS bill is 3x the estimate. Walk through your response.
- Tell me about a time you debugged something under ambiguity (prepare a story).

## Scoring rubric (rate 1-4 each)
Correctness of facts | Tradeoff awareness | Structure and clarity | Security and cost mentioned unprompted | Operational thinking (monitoring, failure, rollback) | Customer communication.
Target: average >= 3. Re-study sections where you scored 1-2, and re-record the answer.
