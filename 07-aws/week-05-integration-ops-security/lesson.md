# Week 5 - Integration, Ops and Security

---
## 1. Messaging and integration

### SQS (Simple Queue Service)
Fully managed pull-based queue; decouples producers/consumers; absorbs bursts.
| | Standard | FIFO |
|---|---|---|
| Throughput | Nearly unlimited | 300 msg/s per API action (3,000 with batching); high-throughput mode much higher (check docs) |
| Delivery | At-least-once (duplicates possible) | Exactly-once processing (5-min dedup window) |
| Ordering | Best-effort | Strict per MessageGroupId |
| Name | any | must end in `.fifo` |
- Message size up to 256 KB (extended to 1 MiB in 2025; check docs; larger -> S3 pointer / Extended Client). Retention 60 s - 14 days (default 4 days). **Visibility timeout** default 30 s (max 12 h): message hidden while a consumer works; if not deleted, it reappears. **Long polling** (WaitTimeSeconds up to 20) reduces cost/empty receives. Delay queues up to 15 min. Batch up to 10 messages.
- **DLQ:** after `maxReceiveCount` failed receives message moves to a dead-letter queue (same type); set alarm on DLQ depth; redrive back after fix.
- Pricing: per request (64 KB chunks), first 1M/month free.
- Use: work queues, buffering before DB, decoupling microservices, Lambda triggers. Not: pub/sub fan-out (SNS), replay/streaming ordering at scale (Kinesis/Kafka), complex routing (EventBridge).
- Gotchas: consumers must be idempotent; visibility timeout < processing time causes duplicates; FIFO hot message group limits throughput; Lambda visibility timeout >= 6x function timeout.

### SNS (Simple Notification Service)
Pub/sub topics; push to SQS, Lambda, HTTP(S), email, SMS, mobile push, Firehose. Message filtering policies per subscription. **Fan-out pattern:** SNS topic -> multiple SQS queues. FIFO topics (with SQS FIFO). Delivery retries + DLQ per subscription. No persistence/replay (unless via Firehose/archive for FIFO). Pricing per publish + deliveries.

### EventBridge
Serverless event bus: routes events from AWS services, SaaS partners, and your apps to targets via rules with content-based pattern matching. Features: schema registry, archive & replay, Scheduler (cron/rate one-off schedules at scale), Pipes (source -> filter/enrich -> target, point-to-point), cross-account/region buses, API destinations (call HTTP APIs with auth, rate limiting). Latency ~sub-second (not for ultra-low latency). Prefer EventBridge for event-driven architectures with routing; SNS for simple high-throughput fan-out; SQS for buffering.

### Kinesis family
- **Kinesis Data Streams (KDS):** ordered, replayable stream partitioned by shard/partition key. Per shard: write 1 MB/s or 1,000 records/s; read 2 MB/s shared (or enhanced fan-out 2 MB/s per consumer). Retention 24 h (default) to 365 days. Modes: provisioned vs on-demand. Record max 1 MB. Consumers: Lambda, KCL apps. Use for real-time analytics, log/clickstream ingestion, multiple consumers reading same data, replay.
- **Firehose:** managed delivery to S3, Redshift, OpenSearch, Splunk, HTTP; buffering (near real-time, seconds-minutes), optional Lambda transform, Parquet conversion. No replay/consumer management.
- Managed Service for Apache Flink: stream processing. MSK: managed Kafka (alternative if team uses Kafka).
- SQS vs Kinesis: SQS = message is consumed and deleted, per-message ack, no ordering at scale, many competing consumers; Kinesis = retained log, ordered per shard, multiple independent consumers, replay.

### Step Functions
Serverless workflow orchestration (state machines in Amazon States Language / visual Workflow Studio). States: Task, Choice, Parallel, Map (inline/distributed), Wait, Pass, Succeed/Fail. Built-in retry/catch, 200+ service integrations (optimized SDK integrations), callback pattern (`.waitForTaskToken`).
| | Standard | Express |
|---|---|---|
| Duration | up to 1 year | up to 5 min |
| Semantics | exactly-once workflow execution | at-least-once (async) / at-most-once (sync) |
| Pricing | per state transition | per request + duration/memory |
| Use | long-running, human approval, audit | high-volume event processing, short APIs |
Use for: multi-step ETL, order processing sagas, ML/LLM pipelines, replacing Lambda-calls-Lambda chains. Not: simple one-step logic or ultra-low latency. Payload limit 256 KB per state (pass S3 pointers). History limit 25,000 events per Standard execution.
Alternatives: Airflow (MWAA), Temporal, SWF (legacy).

### API Gateway
| | REST API | HTTP API | WebSocket |
|---|---|---|---|
| Features | API keys, usage plans, request validation, caching, WAF, per-method throttling, private APIs, canary | cheaper (~70% less), lower latency, JWT authorizers, OIDC, simpler | two-way persistent connections |
- Timeout: 29 s default integration timeout (REST can be raised for regional APIs with quota request; check docs); payload 10 MB. Default account throttle 10,000 rps, burst 5,000 (check docs).
- Auth: IAM (SigV4), Cognito authorizer, Lambda authorizer (custom), JWT (HTTP API), API keys (NOT security, only metering), mTLS.
- Alternatives: ALB (cheaper at high volume, path routing to Lambda/containers), AppSync (GraphQL), Lambda function URLs. Edge-optimized vs regional vs private endpoints.
- Gotchas: CORS config, 29 s limit for long LLM calls (use streaming via response streaming or WebSockets/ALB/SSE through ALB instead), costs at high rps, stage variables, throttling 429s.

---
## 2. Observability and governance

### CloudWatch
- **Metrics:** namespace/dimensions; EC2 basic 5-min vs detailed 1-min; custom metrics (standard 1-min, high-res down to 1 s); retention rolls up (1s data 3h, 1 min 15 d, 5 min 63 d, 1 h 455 d).
- **Alarms:** metric/composite/anomaly detection; actions to SNS, Auto Scaling, EC2.
- **Logs:** log groups/streams, retention policy (default never expire - set it), Logs Insights query language, metric filters, subscription filters, Embedded Metric Format; pricing per GB ingested + stored (ingestion is the big cost).
- Dashboards, Synthetics (canaries), RUM, Container Insights, Lambda Insights, Application Signals, X-Ray (distributed tracing; or OpenTelemetry/ADOT), CloudWatch Agent for memory/disk (not in default EC2 metrics).
- Gotcha: EC2 memory and disk metrics are NOT default; log retention forever; alarm "INSUFFICIENT_DATA".

### CloudTrail
Records API calls (who/what/when/where). Management events on by default; 90-day Event history free; create a **trail** to S3 (and CloudWatch Logs) for long-term, multi-region/org trail; data events (S3 object-level, Lambda invoke, DynamoDB) and Insights events cost extra; log file validation; CloudTrail Lake for SQL queries. Use for audit, forensics, "who deleted this?". Not for performance monitoring.

### AWS Config
Records resource configuration history and evaluates compliance with rules (managed/custom), conformance packs, auto-remediation via SSM. Question it answers: "what did this security group look like last week, and is it compliant?" CloudTrail = who did API; Config = what state/compliance; CloudWatch = metrics/logs.

### Others
GuardDuty (threat detection from CloudTrail/VPC flow/DNS logs), Security Hub (aggregated findings), Inspector (vuln scanning), Macie (S3 PII), Detective, Trusted Advisor, Systems Manager (Session Manager, Parameter Store, Patch Manager, Run Command), Health Dashboard.

### Infrastructure as Code
- **CloudFormation:** AWS-native declarative JSON/YAML; stacks, change sets (preview), drift detection, StackSets (multi-account/region), rollback on failure, nested stacks, custom resources, DeletionPolicy/UpdateReplacePolicy (avoid data loss). Free; pay for resources. Stack limit 500 resources (check docs).
- **CDK:** define infra in Python/TypeScript/Java etc.; synthesizes to CloudFormation; high-level constructs (L1/L2/L3); `cdk bootstrap`, `cdk diff`, `cdk deploy`. Good for developer-heavy teams.
- **Terraform (HashiCorp/OpenTofu):** multi-cloud HCL, state file (remote backend S3 + DynamoDB/lock), plan/apply, huge provider ecosystem; you manage state. Choose when multi-cloud or org standard. SAM: serverless shorthand over CloudFormation.
- Pulumi alternative. Console "click-ops" = drift risk.
```python
# CDK (Python) illustrative
from aws_cdk import Stack, aws_s3 as s3, RemovalPolicy
class Demo(Stack):
    def __init__(self, scope, id, **kw):
        super().__init__(scope, id, **kw)
        s3.Bucket(self, "Data", versioned=True, encryption=s3.BucketEncryption.S3_MANAGED,
                  block_public_access=s3.BlockPublicAccess.BLOCK_ALL, removal_policy=RemovalPolicy.RETAIN)
```

---
## 3. Security services

### KMS (Key Management Service)
- Managed keys in HSMs (FIPS 140-3 validated; check docs). Key types: AWS owned (invisible), AWS managed (`aws/s3`, free, auto-rotated yearly), customer managed (CMK; $1/key/month + API requests; you control key policy, rotation (automatic annual by default, configurable), disable/delete with 7-30 day waiting period). Symmetric (AES-256-GCM) vs asymmetric (RSA/ECC, sign/verify); HMAC keys; multi-region keys; imported key material.
- **Envelope encryption:** KMS `Encrypt` only handles up to 4 KB directly. For data, call `GenerateDataKey` -> get plaintext data key + encrypted data key; encrypt data locally with plaintext key, discard it, store encrypted key alongside data; to decrypt call KMS `Decrypt` on the encrypted data key.
```
 GenerateDataKey -> [plaintext DEK, encrypted DEK(by CMK)]
 encrypt(data, plaintext DEK) -> ciphertext ; store ciphertext + encrypted DEK ; wipe plaintext DEK
```
- Access = key policy (primary; required) + IAM policy (only if key policy allows) + grants. Cross-account use requires both key policy and IAM in caller. Quotas: request rate limits per region (shared; check docs) - S3 Bucket Keys reduce calls. Encryption context for extra AAD and audit.
- Keys are regional; deleting a key makes data unrecoverable.

### Secrets Manager vs SSM Parameter Store
| | Secrets Manager | Parameter Store |
|---|---|---|
| Cost | ~$0.40/secret/month + API calls | Standard free; Advanced (paid) |
| Rotation | built-in (Lambda) for RDS etc. | none built in |
| Size | 64 KB | 4 KB standard / 8 KB advanced |
| Cross-region replication | yes | no |
| Use | DB creds, API keys needing rotation | config, feature flags, non-rotating secrets |
Access via IAM; encrypt with KMS; inject into ECS tasks (`secrets` -> env var) or Lambda via extension/SDK caching. Never put secrets in code, env var plaintext in IaC, or container images.

### Cognito
- **User Pools:** user directory + auth (sign-up/in, MFA, social/SAML/OIDC federation, hosted UI), issues JWTs (ID, access, refresh). Use to authenticate app users to API Gateway/ALB.
- **Identity Pools (federated identities):** exchange tokens (from user pool/Google/etc.) for temporary AWS credentials (STS) to access S3/DynamoDB directly from client.
- Alternatives: Auth0/Okta/Clerk, Keycloak. Gotcha: user pool attribute schemas immutable-ish; migration lock-in.

### WAF and Shield
- **WAF:** L7 web ACL on CloudFront, ALB, API Gateway REST, AppSync, Cognito, App Runner; rules: managed rule groups (OWASP-like, bot control), rate-based rules, IP sets, geo match, regex, custom; count vs block modes; logs to S3/CloudWatch/Firehose; priced per ACL + rule + request.
- **Shield Standard:** free automatic L3/L4 DDoS protection for all. **Shield Advanced:** ~$3,000/month (1-yr commitment, check docs), L7 DDoS protections with WAF, DRT support, cost protection for scaling charges.
- Also: Network Firewall, Firewall Manager, Security Groups, GuardDuty.

---
## 4. Architecture example: order pipeline
```
 Client -> API Gateway (HTTP API, Cognito JWT) -> Lambda "create order" -> DynamoDB
                                                   \-> EventBridge "OrderCreated"
 EventBridge rules -> SQS(payment) -> worker (DLQ)      -> SNS -> email
                  \-> Step Functions (fulfilment saga: reserve stock -> charge -> ship, retries/catch)
 Observability: CloudWatch logs/metrics/alarms, X-Ray; Audit: CloudTrail -> S3 (org trail) ; Compliance: Config
 Secrets: Secrets Manager (payment API key) ; Encryption: KMS CMK on DDB/SQS/S3
```

## 5. boto3 illustrations
```python
sqs = boto3.client("sqs")
sqs.send_message(QueueUrl=url, MessageBody="{}", MessageGroupId="cust-1", MessageDeduplicationId="evt-123")  # FIFO
msgs = sqs.receive_message(QueueUrl=url, MaxNumberOfMessages=10, WaitTimeSeconds=20).get("Messages", [])
for m in msgs:
    ...  # process idempotently
    sqs.delete_message(QueueUrl=url, ReceiptHandle=m["ReceiptHandle"])

sm = boto3.client("secretsmanager")
pw = sm.get_secret_value(SecretId="prod/db")["SecretString"]
```
