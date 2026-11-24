# Week 5 Labs (OPTIONAL)

COST WARNING: SQS, SNS, EventBridge, Lambda, Step Functions Standard, CloudWatch basics and CloudTrail event history have free tiers. Secrets Manager ($0.40/secret/month, 30-day trial), KMS customer keys ($1/month prorated), WAF, Kinesis shards (hourly), API Gateway beyond free tier and CloudWatch log ingestion cost money.

1. SQS: create standard queue + DLQ (maxReceiveCount 3); send a message; receive without deleting 3 times; watch it land in the DLQ.
2. SNS -> 2 SQS fan-out with a filter policy.
3. EventBridge: rule on a custom event pattern -> SQS; put events with `aws events put-events`. Add a Scheduler schedule.
4. Step Functions: build a 3-state workflow (Pass, Choice, Fail with retry) in Workflow Studio; run it.
5. CloudTrail: browse Event history, find your own CreateQueue call.
6. KMS (optional): create a CMK, encrypt a small file via CLI, schedule key deletion (7 days) afterward.
7. CDK/CloudFormation: deploy a stack with one S3 bucket, run drift detection, destroy the stack.

Cleanup: delete queues/topics/rules/state machines, schedule KMS key deletion, delete secrets (7+ day recovery window; use force delete if you want it now), delete stacks, delete log groups.
