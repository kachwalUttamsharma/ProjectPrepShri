# Week 2 Cheatsheet - Compute

| Service | One-liner | Typical use |
|---|---|---|
| EC2 | Virtual machines | Legacy apps, GPUs, full control |
| AMI | VM image template | Golden images, ASG launches |
| EBS | Persistent block disk, AZ-scoped | Boot/DB volumes |
| Instance store | Ephemeral local NVMe | Cache/scratch |
| Spot | Cheap interruptible EC2 (2-min warning) | Batch, stateless workers |
| Savings Plans / RI | 1-3 yr commitment discounts | Steady baseline |
| Lambda | Event-driven functions (15 min max) | Glue, APIs, S3/SQS processing |
| Provisioned concurrency / SnapStart | Kill cold starts | Latency-sensitive Lambda |
| ECS | AWS-native container orchestrator | Containerized services |
| EKS | Managed Kubernetes | K8s shops, portability |
| Fargate | Serverless container compute | No node management |
| ECR | Container registry | Image storage/scan |
| App Runner | Simplest container/web service hosting | Small APIs |
| Elastic Beanstalk | PaaS on EC2 | Quick web app deploy |
| ALB | L7 load balancer | HTTP routing, microservices |
| NLB | L4, static IP, extreme perf | TCP/UDP, PrivateLink |
| GWLB | Appliance insertion | Firewalls/IDS |
| Auto Scaling | Add/remove capacity by policy | Elastic web/worker tiers |
| AWS Batch | Managed batch jobs on EC2/Spot/Fargate | Large job queues |
| Lightsail | Simple VPS bundle | Small sites |

Numbers: Lambda 15 min / 10 GB mem / 6 MB sync payload / 1,000 default concurrency; ALB idle timeout 60 s; Spot 2-min notice; gp3 3,000 IOPS baseline; EKS $0.10/hr/cluster.
Rule: event-driven short -> Lambda; container service -> Fargate; K8s -> EKS; special hardware -> EC2.
