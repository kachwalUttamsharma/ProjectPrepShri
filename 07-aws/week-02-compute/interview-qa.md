# Week 2 Interview Q&A - Compute

**1. Name the EC2 pricing models and when to use each.**
On-Demand (unpredictable, short), Savings Plans/Reserved (steady baseline, 1-3 yr commit, up to ~70% off), Spot (up to ~90% off, interruptible, stateless/batch), Dedicated Hosts (licensing/compliance), Capacity Reservations (guaranteed capacity).

**2. Savings Plans vs Reserved Instances?**
Both are commitments. Savings Plans commit to $/hour spend and are flexible (Compute SP spans instance family, region, OS, and also Fargate/Lambda); RIs commit to specific instance attributes (Convertible adds some flexibility) and can be sold on the RI marketplace (Standard). Default recommendation: Savings Plans.

**3. How do Spot interruptions work and how do you design for them?**
AWS can reclaim with a 2-minute notice (via instance metadata/EventBridge). Design stateless/checkpointed workloads, diversify across instance types/AZs, use capacity-optimized allocation, mixed-instances ASG with an On-Demand base, handle SIGTERM/drain.

**4. EBS vs instance store?**
EBS: network-attached, persistent, snapshot-able, AZ-scoped, resizable. Instance store: local NVMe, very fast, ephemeral (lost on stop/terminate/hardware failure); use for cache/scratch/replicated data.

**5. gp3 vs io2?**
gp3 baseline 3,000 IOPS/125 MB/s independent of size, tunable up to 16,000 IOPS; cheaper default. io2 (Block Express) for latency-sensitive, high durability, very high IOPS DBs (up to 256k IOPS, check docs).

**6. What is an AMI and how do you manage them at scale?**
Machine image (root snapshot + metadata). Regional; copy for multi-region. Build golden AMIs via Image Builder/Packer, tag/version, share with accounts, and roll out with ASG instance refresh via launch templates. Alternative: containers.

**7. What happens when you stop vs terminate an EC2 instance?**
Stop: instance off, EBS retained and billed, instance-store data lost, public IP released (unless EIP). Terminate: instance deleted, root volume deleted by default. Hibernate saves RAM to EBS.

**8. How do you securely access EC2 without opening SSH?**
SSM Session Manager (IAM-based, audited, no inbound ports/bastion), EC2 Instance Connect, or bastion as fallback.

**9. What is IMDSv2 and why enforce it?**
Session-token-based instance metadata service. Prevents SSRF-style credential theft common against IMDSv1. Enforce with `HttpTokens=required`.

**10. Lambda key limits?**
15 min timeout, 128-10,240 MB memory, 10 GB /tmp max, 6 MB sync payload, 250 MB unzipped package or 10 GB container image, 1,000 default regional concurrency (soft). Check current docs for exact numbers.

**11. What is a cold start and how to reduce it?**
Latency of creating a new execution environment and running init code. Reduce with smaller packages, lazy imports, init outside handler, Provisioned Concurrency, SnapStart (Java/Python/.NET), ARM, avoiding heavy frameworks.

**12. Reserved vs provisioned concurrency?**
Reserved: carves out and caps concurrency for a function (free); protects other functions and downstream systems. Provisioned: pre-warmed environments (billed) to eliminate cold starts. They can be combined.

**13. Scenario: Lambda consuming SQS floods a small RDS with connections. Fix?**
RDS Proxy for pooling; set reserved concurrency (or SQS event-source max concurrency) to cap parallelism; batch writes; scale DB or use Aurora Serverless/DynamoDB if appropriate.

**14. Sync vs async Lambda invocation error behavior?**
Sync: error returned to caller, no automatic retry (caller retries). Async: Lambda retries up to 2 times, then sends to DLQ/on-failure destination. Stream/queue sources retry per source semantics (SQS visibility timeout; Kinesis retries until success or expiry unless configured).

**15. Troubleshooting: Lambda timing out when calling an external API from a VPC.**
Function in private subnet without NAT/egress: needs NAT gateway or VPC endpoint (for AWS services). Also check SG/NACL egress, DNS, and timeout settings.

**16. Lambda vs Fargate vs EC2: how do you pick?**
Lambda: event-driven, short, spiky, scale to zero. Fargate: long-running containers, no server mgmt, steady traffic, >15 min. EC2: need GPUs/special hardware/OS control, or highest cost efficiency at sustained scale using RIs/Spot.

**17. ECS vs EKS?**
ECS: simpler AWS-native, no control-plane fee, less to learn. EKS: managed Kubernetes, portable, rich ecosystem, more ops overhead and $0.10/hr per cluster. Choose EKS if the org already standardizes on Kubernetes or needs its tooling.

**18. ECS task role vs task execution role?**
Execution role is used by the ECS agent to pull images from ECR, write logs, and fetch secrets. Task role is assumed by your application code to call AWS APIs (S3, DynamoDB, Bedrock).

**19. What is Fargate and its tradeoffs?**
Serverless container compute: no nodes to patch/scale, per-second billing, isolation per task. Tradeoffs: higher unit price than packed EC2, fewer knobs (no privileged mode/GPUs/daemon sets), cold start of tasks (tens of seconds), image pull needs network path (NAT/endpoints).

**20. ALB vs NLB?**
ALB L7: path/host routing, auth, WAF, HTTP features. NLB L4: TCP/UDP/TLS, ultra-high throughput/low latency, static/Elastic IPs, preserves source IP, PrivateLink backends. Use NLB for non-HTTP protocols or when customers need to allowlist fixed IPs.

**21. Troubleshooting: ALB returns 502/503/504.**
502: target sent malformed response/closed connection (app crash, keep-alive mismatch - app idle timeout should exceed ALB's 60 s). 503: no healthy/registered targets or capacity. 504: target didn't respond before idle timeout. Check health checks, SGs, target logs, access logs.

**22. How does cross-zone load balancing affect cost?**
ALB: on by default, no inter-AZ data charge for LB-to-target. NLB: off by default; enabling incurs cross-AZ data charges. Without it traffic is split by AZ and can be imbalanced.

**23. Which ASG scaling policy would you choose and why?**
Target tracking for most cases (e.g. ALBRequestCountPerTarget or CPU 50%), scheduled for known peaks, predictive for cyclical load, step scaling for custom thresholds. Workers: scale on SQS backlog per instance.

**24. How do you do zero-downtime deploys on ECS/EC2?**
Rolling update with ALB health checks and connection draining, or blue/green (CodeDeploy for ECS, Beanstalk CNAME swap), or canary traffic shifting. Keep min healthy percent >= 100 for rolling in ECS.

**25. When would you choose Elastic Beanstalk?**
Small team wanting PaaS-like deployment of a standard web app on AWS, with escape hatch to underlying resources. For new builds, ECS/Fargate, App Runner or Lambda are usually preferred.

**26. Cost angle: how would you cut a large always-on EC2 bill?**
Right-size using Compute Optimizer, move to Graviton, Savings Plans for baseline, Spot for fault-tolerant, scale in off-hours, consolidate/containerize, delete idle volumes/EIPs/LBs, review data-transfer.

**27. Security angle: hardening an EC2 web tier.**
Private subnets behind ALB, SG chaining (ALB SG -> app SG), IMDSv2, SSM instead of SSH, least-privilege instance role, encrypted EBS, patching (SSM Patch Manager) or immutable AMIs, WAF on ALB, Inspector scanning.
