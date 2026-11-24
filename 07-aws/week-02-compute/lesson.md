# Week 2 - Compute: EC2, Lambda, Containers, Beanstalk, ELB, Auto Scaling

Numbers: verify "(check current docs)" before quoting.

---
## 1. EC2 (Elastic Compute Cloud)

**What:** Virtual machines (Nitro-based) in a chosen AZ. You manage OS and up.

### Instance families (letter = purpose)
| Family | Optimized for | Examples |
|---|---|---|
| T (t3/t4g) | Burstable general purpose (CPU credits) | dev, small web |
| M | General purpose balanced | app servers |
| C | Compute | batch, encoding, game servers |
| R / X / z | Memory | in-memory DBs, caches |
| I / D | Storage (NVMe local, dense HDD) | NoSQL, data warehouses |
| P / G / Inf / Trn | GPU / inference / training chips | ML training, inference |
Suffixes: `g` = Graviton (ARM, usually better price/perf), `a` = AMD, `i` = Intel, `n` = network, `d` = local NVMe disk. Example `m7g.large`.

### Pricing models
| Model | Discount | Commitment | Notes |
|---|---|---|---|
| On-Demand | 0 | none | per-second billing (Linux, 60 s min) |
| Savings Plans (Compute / EC2 Instance) | up to ~70% | 1 or 3 yr $/hr | Compute SP flexible across family/region/Fargate/Lambda |
| Reserved Instances (Standard/Convertible) | up to ~70% | 1 or 3 yr | Less flexible; mostly superseded by Savings Plans |
| Spot | up to ~90% | none | can be reclaimed with 2-minute warning; for stateless/fault-tolerant |
| Dedicated Hosts / Instances | premium | optional | licensing (BYOL), compliance |
| Capacity Reservations | none | none | guarantee capacity in an AZ |
Typical strategy: baseline on Savings Plans, spikes On-Demand, batch/stateless on Spot (diversify instance types and AZs, use capacity-optimized allocation).

### AMI
Template of root volume + launch permissions + block device mapping. Regional (copy across regions). Sources: AWS-provided, Marketplace, custom (golden AMIs via EC2 Image Builder/Packer). Launch template = AMI + type + SG + user data + IAM profile.

### Storage for EC2
| | EBS | Instance store |
|---|---|---|
| Persistence | persists independent of instance (unless DeleteOnTermination) | ephemeral: lost on stop/terminate/host failure |
| Attach | network-attached, AZ-scoped, snapshots to S3 | physically attached NVMe |
| Perf | gp3 baseline 3,000 IOPS/125 MB/s (up to 16,000 IOPS/1,000 MB/s); io2 Block Express up to 256,000 IOPS (check current docs) | very high IOPS, low latency |
| Use | boot, DBs, general | cache, scratch, buffers, replicated data |
EBS types: gp3 (default SSD), io1/io2 (provisioned IOPS, DBs), st1 (throughput HDD), sc1 (cold HDD). EBS Multi-Attach for io1/io2 in same AZ. Volume size up to 64 TiB (check docs). Snapshots incremental, region-copyable. Encryption via KMS, transparent.

### Networking and misc
- Security groups (stateful firewall), key pair/SSM Session Manager (preferred over SSH + open port 22), Elastic IP (charged when idle; public IPv4 addresses now cost money hourly), placement groups (cluster / spread / partition), ENA/EFA, user data (bootstrap, runs at first boot), IMDSv2 (require tokens).
- Stop vs terminate vs hibernate. Stopped = no compute charge, still pay EBS. Public IP changes on stop/start (not with EIP).
- Limits: On-demand vCPU service quotas per family per region (check current docs).

**When NOT EC2:** spiky/event-driven small work (Lambda), you don't want to patch OSes (Fargate/managed), simple static sites (S3+CloudFront).

---
## 2. Lambda

**What:** Run code on events without managing servers; pay per request and GB-seconds (per-ms billing).

Key limits (check current docs)
- Timeout max 15 min. Memory 128 MB - 10,240 MB (CPU scales with memory; ~1 vCPU at 1,769 MB). Ephemeral /tmp 512 MB default up to 10,240 MB.
- Payload: 6 MB sync request/response; async event up to 256 KB (increased in 2025 - check). Response streaming supports larger.
- Deployment: zip 50 MB direct upload / 250 MB unzipped incl. layers; container image up to 10 GB.
- Concurrency: account default 1,000 per region (soft limit). Scaling: each function can add up to 1,000 concurrent executions every 10 seconds.
- Env vars 4 KB. 5 layers per function.

Invocation models
- Synchronous (API Gateway, ALB, function URL, SDK RequestResponse): caller waits, handles errors/retry.
- Asynchronous (S3, SNS, EventBridge): Lambda queues; auto retries twice; use DLQ or on-failure destinations.
- Poll-based event source mapping (SQS, Kinesis, DynamoDB Streams, Kafka): Lambda polls and batches; failures retry batch; use `ReportBatchItemFailures`, bisect batch, DLQ/on-failure destination. For SQS set queue visibility timeout >= 6x function timeout.

Cold starts
```
 request -> [new env: download code, start runtime, init (imports, clients)] -> handler   (cold)
 request ->                                                    handler                   (warm)
```
Mitigation: smaller packages, lazy imports, init clients outside handler, Provisioned Concurrency (pay to keep warm), SnapStart (Java; also Python/.NET), choose ARM/faster runtimes, avoid VPC ENI concerns (now mostly fixed with Hyperplane). Cold starts typically hundreds of ms to a few seconds, worse for JVM/large packages.

Concurrency types: Unreserved (shared pool), Reserved (guarantees AND caps a function; also protects downstream like RDS), Provisioned (pre-initialized, billed).

Pricing: requests ($0.20 per 1M) + GB-seconds; free tier 1M requests + 400,000 GB-s per month. ARM ~20% cheaper. Cost cliff: long-running or steady high-traffic work is cheaper on containers/EC2.

Gotchas: Lambda to RDS needs RDS Proxy (connection storms); no persistent connections; throttling returns 429; recursion loops (S3 -> Lambda -> S3 same bucket); logs go to CloudWatch (cost); API Gateway 29 s timeout (default) shorter than Lambda 15 min; idempotency required because retries/at-least-once.

```python
import json, boto3
s3 = boto3.client("s3")             # init outside handler -> reused on warm starts

def handler(event, context):
    for rec in event["Records"]:    # SQS batch
        body = json.loads(rec["body"])
        s3.put_object(Bucket="my-bucket", Key=f"out/{body['id']}.json", Body=rec["body"])
    return {"statusCode": 200}
```

---
## 3. Containers: ECS, EKS, Fargate, ECR

```
          +-- ECS (AWS-native orchestrator) --+      +-- EKS (managed Kubernetes control plane) --+
 Compute: |  EC2 launch type | Fargate        |      |  managed node groups | Karpenter | Fargate  |
          +-----------------------------------+      +--------------------------------------------+
 Images: ECR (private registry, scan, replication, lifecycle policies)
```
- **ECS:** concepts: cluster, task definition (container spec: image, cpu/mem, ports, env/secrets, roles), task (running instance), service (keeps N tasks, integrates with ALB, rolling/blue-green deployments via CodeDeploy). Task role vs task execution role. No control-plane fee.
- **Fargate:** serverless compute for ECS/EKS: no EC2 to manage, per-vCPU/GB-second pricing, each task its own kernel/ENI (awsvpc). Max task size 16 vCPU / 120 GB (check docs); ephemeral storage 20 GB default up to 200 GB. Costs more per unit than well-packed EC2; Spot Fargate available. No privileged containers/GPUs (limited).
- **EKS:** conformant Kubernetes; control plane charged (~$0.10/hr per cluster), you manage add-ons, upgrades (version support windows), node scaling (Cluster Autoscaler/Karpenter), IAM via IRSA / EKS Pod Identity. Pick for K8s portability, ecosystem (Helm, operators), existing K8s skills.
- **ECS vs EKS:** ECS simpler, deep AWS integration, less lock-in knowledge needed; EKS portable, richer ecosystem, more operational overhead.
- **App Runner:** even simpler, deploy container/source -> HTTPS service with autoscaling. Good for small web APIs. (check current availability/roadmap.)
- **ECR:** private image registry, image scanning, immutable tags, lifecycle policies, cross-region replication, pull-through cache.
- **Lambda vs Fargate vs EC2** quick rule: event-driven + short -> Lambda; long-running service or >15 min or needs custom runtime/large memory -> Fargate; special hardware/max cost efficiency at scale/GPU -> EC2.

Gotchas: Fargate tasks in private subnets need NAT or VPC endpoints (ECR, S3, CloudWatch Logs, Secrets Manager) to pull images and log; health check grace period; ALB target type `ip` for awsvpc; task stuck PENDING (no capacity/ENI/IP exhaustion); `exec` into container via ECS Exec needs SSM perms.

---
## 4. Elastic Beanstalk
PaaS: upload code (Python, Node, Java, Docker...), Beanstalk provisions EC2 + ASG + ELB + monitoring. You keep access to resources. Deployment policies: all-at-once, rolling, rolling with additional batch, immutable, blue/green (CNAME swap), traffic-splitting. Use for quick lift-and-shift of web apps with minimal ops knowledge; avoid for new modern architectures (prefer ECS/App Runner/Lambda). Free service; pay for underlying resources.

---
## 5. Elastic Load Balancing
| Type | Layer | Features | Use |
|---|---|---|---|
| ALB | 7 (HTTP/HTTPS/gRPC/WebSocket) | path/host/header routing, redirects, auth (OIDC/Cognito), WAF, Lambda targets, sticky sessions, HTTP/2 | web apps, microservices |
| NLB | 4 (TCP/UDP/TLS) | millions of rps, ultra-low latency, static IP/Elastic IP per AZ, preserves client IP, PrivateLink endpoint service | non-HTTP, static IP needs, extreme perf |
| GWLB | 3 | transparent insertion of appliances (firewalls, IDS) via GENEVE | security appliances |
| CLB | 4/7 legacy | - | avoid |
Concepts: target groups (instance/ip/lambda/ALB targets), health checks, cross-zone load balancing (ALB on by default, no inter-AZ charge; NLB off by default, inter-AZ charges if enabled), connection draining (deregistration delay default 300 s), SNI + ACM certs for TLS termination, idle timeout 60 s default (ALB), `X-Forwarded-For` header, access logs to S3.
Pricing: hourly + LCUs (ALB) / NLCUs.
Troubleshoot: 502 = bad response from target / target closed connection; 503 = no healthy targets; 504 = target timeout (idle timeout < app time); check SG allows LB -> target, health check path/port, subnets in >=2 AZs.

---
## 6. Auto Scaling
- EC2 Auto Scaling Group: min/desired/max, launch template, multi-AZ spread, health checks (EC2 + ELB), mixed instances policy (on-demand + spot), instance refresh (rolling AMI updates), lifecycle hooks, warm pools.
- Policies: target tracking (e.g. keep CPU 50% or ALBRequestCountPerTarget - simplest and preferred), step scaling, simple scaling, scheduled, predictive scaling.
- Scale on queue depth for workers (SQS backlog per instance). Cooldown / instance warm-up avoids flapping.
- Application Auto Scaling covers ECS service tasks, DynamoDB capacity, Lambda provisioned concurrency, Aurora replicas, etc.
- Scale OUT quickly, scale IN slowly.

```
 Users -> Route 53 -> ALB (2+ AZs) -> Target group -> ASG: EC2 / ECS tasks in private subnets
                                                   |-> scale on ALBRequestCountPerTarget
                                                   -> RDS Multi-AZ (data tier)
```

## 7. Choosing compute (decision guide)
- Static content -> S3 + CloudFront.
- Event-driven glue, spiky, short -> Lambda.
- Containerized service, no cluster ops -> ECS Fargate (or App Runner for simplest).
- Need K8s -> EKS.
- Legacy/monolith/lift-and-shift/license-bound/GPU -> EC2 (+ASG, ALB).
- Batch -> AWS Batch (Spot).
Alternatives outside AWS: GCP Cloud Run/GKE, Azure Functions/AKS, Heroku, Lightsail (simple VPS in AWS).

## 8. boto3 illustrations
```python
ec2 = boto3.client("ec2")
for r in ec2.describe_instances(Filters=[{"Name":"instance-state-name","Values":["running"]}])["Reservations"]:
    for i in r["Instances"]:
        print(i["InstanceId"], i["InstanceType"], i["Placement"]["AvailabilityZone"])

lam = boto3.client("lambda")
lam.invoke(FunctionName="my-fn", InvocationType="Event", Payload=b'{"x":1}')  # async
```
