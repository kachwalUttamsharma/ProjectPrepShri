# Week 5 Cheatsheet - Integration, Ops, Security

| Service | One-liner | Typical use |
|---|---|---|
| SQS Standard / FIFO | Pull queue; at-least-once unordered / ordered exactly-once | Buffering, work queues |
| DLQ | Holds messages that failed maxReceiveCount | Poison message handling |
| SNS | Pub/sub push fan-out | Alerts, fan-out to SQS |
| EventBridge | Event bus w/ rules, schedules, pipes | Event-driven routing, cron |
| Kinesis Data Streams | Ordered replayable stream (shards) | Clickstream, real-time analytics |
| Firehose | Managed delivery to S3/Redshift/OpenSearch | Log/event loading |
| MSK | Managed Kafka | Kafka compatibility |
| Step Functions | State-machine orchestration (Standard 1 yr / Express 5 min) | Sagas, ETL, LLM pipelines |
| API Gateway (REST/HTTP/WebSocket) | Managed API front door | Serverless APIs, auth, throttling |
| AppSync | Managed GraphQL | GraphQL backends |
| CloudWatch | Metrics, logs, alarms, dashboards | Monitoring |
| X-Ray / OpenTelemetry | Distributed tracing | Latency analysis |
| CloudTrail | API audit log | Who did what |
| Config | Resource state history + compliance rules | Compliance/drift |
| CloudFormation | AWS-native IaC with stacks | Repeatable infra |
| CDK | IaC in real languages -> CFN | Dev-friendly IaC |
| Terraform | Multi-cloud IaC with state | Multi-cloud/standard IaC |
| KMS | Managed encryption keys, envelope encryption | Encrypt S3/EBS/RDS/secrets |
| Secrets Manager | Secrets + rotation | DB creds/API keys |
| SSM Parameter Store | Config/params (free std tier) | Config values |
| Cognito | User pools (JWT auth) + identity pools (AWS creds) | App sign-in |
| WAF | L7 web firewall | SQLi/XSS/rate limit |
| Shield | DDoS (Standard free, Advanced paid) | DDoS protection |
| GuardDuty / Security Hub / Inspector / Macie | Threat detect / aggregate / vuln scan / PII | Security posture |

Numbers: SQS msg 256 KB (check 1 MiB update), retention up to 14 d, visibility default 30 s max 12 h, long poll 20 s, FIFO 300/s (3,000 batched); KDS shard 1 MB/s in, 2 MB/s out, retention 24 h-365 d; API GW 29 s default timeout, 10 MB payload; KMS direct encrypt 4 KB; Secrets $0.40/mo; Step Functions Std 1 yr/Express 5 min; CloudTrail event history 90 d.
