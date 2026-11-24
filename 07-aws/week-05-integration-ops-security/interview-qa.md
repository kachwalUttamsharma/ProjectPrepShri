# Week 5 Interview Q&A - Integration, Ops, Security

**1. SQS Standard vs FIFO?**
Standard: near-unlimited throughput, at-least-once, best-effort ordering. FIFO: ordered per message group, exactly-once processing via dedup (5 min), lower throughput (300/s, 3,000 with batching; high-throughput mode higher). Choose FIFO only when order/dup-free matters.

**2. Explain visibility timeout.**
After a consumer receives a message it is hidden for the visibility timeout (default 30 s, max 12 h). If not deleted in time it becomes visible again and is redelivered. Set it above processing time; extend dynamically for long tasks.

**3. What is a DLQ and how do you use it?**
A queue receiving messages that exceed maxReceiveCount. Use it to isolate poison messages, alarm on its depth, inspect and redrive after fixing. Retention should exceed source queue's.

**4. SQS vs SNS vs EventBridge vs Kinesis?**
SQS: buffer/work queue (pull, one consumer group). SNS: pub/sub push fan-out. EventBridge: event bus with content-based routing, SaaS/AWS events, schedules. Kinesis: ordered replayable stream for high-volume real-time data with multiple consumers.

**5. Scenario: one event must trigger email, billing, and analytics independently.**
SNS topic with SQS queue per consumer (fan-out), or EventBridge bus with three rules. Each consumer gets its own queue + DLQ so failures are isolated.

**6. How does Kinesis scale and what are shard limits?**
Per shard: 1 MB/s or 1,000 records/s write, 2 MB/s read (shared; enhanced fan-out gives dedicated per consumer). Scale by splitting/merging shards or on-demand mode. Ordering per partition key; hot key = hot shard.

**7. Kinesis Data Streams vs Firehose?**
KDS: you build consumers, retention up to 365 days, replay, ms-second latency. Firehose: managed delivery to S3/Redshift/OpenSearch/Splunk with buffering (near-real-time), no replay, no consumer code.

**8. Exactly-once in AWS messaging?**
Truly end-to-end exactly-once doesn't exist; use at-least-once delivery + idempotent consumers (idempotency keys, conditional writes in DynamoDB), or SQS FIFO dedup within the 5-min window.

**9. When would you use Step Functions over Lambda chaining?**
Multi-step workflows needing retries, branching, parallelism, waits, human approvals, visual audit trail, and state persistence. Avoid Lambda calling Lambda synchronously (cost, coupling, timeouts).

**10. Step Functions Standard vs Express?**
Standard: up to 1 year, exactly-once, priced per transition, full history. Express: up to 5 min, at-least-once, high volume (100k+/s), priced per request/duration. Use Express for high-volume short work.

**11. API Gateway REST vs HTTP API?**
REST: richer features (usage plans, API keys, caching, validation, WAF, private endpoints), higher price. HTTP: cheaper, lower latency, JWT/OIDC authorizers, fewer features. Pick HTTP unless you need REST-only features.

**12. Why might API Gateway not be right for an LLM chat endpoint?**
29-second default integration timeout (check current limit) and 10 MB payload; streaming responses are awkward. Use ALB -> ECS/Lambda with streaming (SSE/WebSocket), Lambda response streaming via function URL, or API Gateway WebSocket.

**13. How do you authenticate users on an API?**
Cognito user pool JWT authorizer (or any OIDC IdP) on HTTP API; IAM/SigV4 for service-to-service; Lambda authorizer for custom schemes; mTLS for B2B. API keys are for metering, not authentication.

**14. Cognito user pools vs identity pools?**
User pool authenticates users and returns JWTs. Identity pool exchanges identity tokens for temporary AWS credentials to call AWS services directly.

**15. CloudWatch vs CloudTrail vs Config?**
CloudWatch: metrics, logs, alarms (how is it performing). CloudTrail: API call audit (who did what). Config: resource configuration history/compliance (what does it look like, is it compliant).

**16. Troubleshooting: no memory metrics for EC2 in CloudWatch.**
Default metrics don't include memory/disk; install CloudWatch Agent (with IAM role) to publish them.

**17. Troubleshooting: someone deleted a security group rule; how to find who/when?**
CloudTrail event history/trail (RevokeSecurityGroupIngress) for who and when; AWS Config timeline for before/after state; add Config rule + EventBridge alert for the future.

**18. CloudFormation vs CDK vs Terraform?**
CFN: AWS-native declarative, stack rollback, drift, StackSets. CDK: code (Python/TS) generating CFN with high-level constructs. Terraform: multi-cloud HCL with state files, big ecosystem. Choose based on team skills, multi-cloud needs, and org standards.

**19. What is CloudFormation drift and how do you handle it?**
Difference between actual resources and template caused by manual changes. Detect with drift detection, fix by reverting manually or updating template/import; prevent via SCP/IAM restrictions and IaC-only pipelines.

**20. Explain envelope encryption.**
KMS generates a data key; plaintext key encrypts data locally, KMS-encrypted copy is stored with the ciphertext; decrypting requires KMS Decrypt on the encrypted data key. Avoids sending big data to KMS (4 KB limit) and enables per-object keys.

**21. AWS managed vs customer managed KMS keys?**
AWS managed: created per service, free, fixed policy, auto-rotation yearly, no control. Customer managed: $1/month, custom key policy, grants, rotation config, cross-account sharing, disable/schedule deletion. Use CMK when you need control/audit/cross-account.

**22. Troubleshooting: S3 GetObject returns AccessDenied on SSE-KMS object though S3 permission is granted.**
Caller also needs `kms:Decrypt` (and key policy allowing it or IAM + key policy delegation). Cross-account: key policy must allow the other account.

**23. Secrets Manager vs Parameter Store?**
Secrets Manager: rotation, replication, larger size, $0.40/secret/month. Parameter Store: free standard tier for config, no native rotation. Use SM for DB credentials/API keys needing rotation; SSM for config values.

**24. How do you deliver secrets to a Fargate container safely?**
Reference Secrets Manager/SSM ARN in task definition `secrets`; execution role gets `secretsmanager:GetSecretValue` (+ KMS decrypt); injected as env at start. For rotation without restart, fetch at runtime with the task role and cache.

**25. WAF vs Shield vs security groups?**
SG: L3/L4 instance firewall. WAF: L7 HTTP inspection (SQLi, XSS, rate limiting, bots). Shield: DDoS protection (Standard free, L3/L4; Advanced adds L7 response, cost protection, DRT).

**26. How would you protect an API from abuse/DDoS?**
CloudFront + WAF rate-based rules and managed rule groups, Shield, API Gateway throttling/usage plans, auth required, caching, autoscaling with limits, budget alarms.

**27. Cost angle: CloudWatch bill is high.**
Logs ingestion is typical: reduce debug logging, sample, set retention, filter before ingest, use metric filters instead of custom metrics at high cardinality, avoid high-res metrics and too many custom dimensions, move long-term logs to S3 via Firehose.

**28. SQS + Lambda: messages processed twice. Why?**
At-least-once delivery, visibility timeout shorter than function time/retries, partial batch failure re-driving whole batch (use ReportBatchItemFailures). Make handler idempotent.

**29. Scenario: Process 10M events/day from IoT with replay and multiple consumers.**
IoT Core -> Kinesis Data Streams (or MSK) -> Lambda/Flink consumers + Firehose to S3 for lake; DynamoDB for latest state. SQS can't replay or fan out to independent consumers.

**30. Security angle: what do you log/monitor for a new account baseline?**
Org CloudTrail to a locked-down S3 bucket, Config recorder, GuardDuty and Security Hub enabled org-wide, Access Analyzer, root-use alarm, budget alerts, S3 Block Public Access, KMS key rotation, and alarms via EventBridge to SNS/Slack.
