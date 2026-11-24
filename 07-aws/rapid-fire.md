# Top 50 Rapid-Fire AWS Q&A (one or two lines each)

Check "current docs" for any number you plan to quote.

1. Region vs AZ? Region = geographic area; AZ = isolated data center group in it (HA unit).
2. Global services? IAM, Route 53, CloudFront, Organizations (control planes are global).
3. Shared responsibility? AWS: security OF the cloud; you: security IN the cloud.
4. IAM eval order? Default deny; explicit deny wins; need an allow; SCP/boundary must also allow.
5. Role vs user? Role = temporary credentials, assumable; user = long-lived identity.
6. STS AssumeRole duration? 15 min - 12 h, default 1 h; role chaining max 1 h.
7. SCP? Org guardrail that limits (never grants); not applied to management account.
8. EC2 pricing models? On-Demand, Savings Plans/RI, Spot, Dedicated, Capacity Reservation.
9. Spot warning? 2 minutes.
10. EBS vs instance store? Persistent network block vs ephemeral local NVMe.
11. Lambda max timeout/memory? 15 min / 10,240 MB.
12. Lambda cold start fix? Provisioned Concurrency, SnapStart, smaller packages, init outside handler.
13. Reserved vs provisioned concurrency? Reserved = guarantee + cap (free); provisioned = pre-warmed (paid).
14. ECS vs EKS? AWS-native simple vs managed Kubernetes (+$0.10/hr/cluster).
15. Fargate? Serverless compute for containers; no nodes to manage.
16. ALB vs NLB? L7 HTTP routing vs L4 TCP/UDP, static IPs, extreme perf.
17. ALB 502/503/504? Bad target response / no healthy targets / target timeout.
18. ASG best policy? Target tracking.
19. S3 consistency? Strong read-after-write and list.
20. S3 durability? 11 nines (multi-AZ classes).
21. S3 max object / single PUT? 5 TB / 5 GB (use multipart).
22. S3 Glacier Deep Archive retrieval? ~12-48 hours; 180-day minimum.
23. Presigned URL? Time-limited signed URL granting one operation without creds.
24. S3 public leak prevention? Block Public Access, bucket owner enforced, Access Analyzer.
25. EBS vs EFS vs S3? Block (1 AZ) vs shared NFS (multi-AZ) vs object (regional).
26. RDS Multi-AZ vs read replica? Sync HA failover vs async read scaling.
27. Aurora storage? 6 copies across 3 AZs, up to 128 TiB, up to 15 replicas.
28. RDS Proxy purpose? Connection pooling, faster failover (needed for Lambda).
29. DynamoDB item max? 400 KB.
30. 1 RCU / 1 WCU? 4 KB strongly consistent read/s; 1 KB write/s.
31. GSI vs LSI? GSI any time, different PK, default 20; LSI at creation, same PK, max 5.
32. DynamoDB on-demand vs provisioned? Spiky/unknown vs steady/predictable.
33. DAX? In-memory cache for DynamoDB (microseconds).
34. Redis vs Memcached? Rich + persistent + replication vs simple multithreaded cache.
35. Redshift vs Athena? Warehouse (provisioned/serverless) vs serverless SQL on S3.
36. SG vs NACL? Stateful allow-only (ENI) vs stateless allow/deny (subnet).
37. NAT Gateway vs IGW? Outbound-only for private vs two-way for public; NAT costs per GB.
38. Gateway vs interface endpoint? S3/DynamoDB only, free vs PrivateLink ENI for many services, paid.
39. Peering vs TGW? 1:1 non-transitive vs hub-and-spoke transitive.
40. VPN vs Direct Connect? Encrypted internet, quick vs dedicated private link, consistent, weeks.
41. Route 53 policies? Simple, weighted, latency, failover, geolocation, geoproximity, multivalue, IP-based.
42. CloudFront private S3? Origin Access Control + bucket policy; ACM cert in us-east-1.
43. SQS standard vs FIFO? Unlimited/at-least-once/unordered vs ordered/dedup/lower throughput.
44. SQS visibility timeout? Hide time after receive (default 30 s, max 12 h); must exceed processing time.
45. SNS vs SQS vs EventBridge vs Kinesis? Push fan-out / queue / routed event bus / replayable stream.
46. Step Functions Standard vs Express? Up to 1 yr exactly-once vs 5 min high-volume at-least-once.
47. CloudWatch vs CloudTrail vs Config? Metrics/logs vs API audit vs resource state/compliance.
48. KMS envelope encryption? Data key encrypts data; CMK encrypts the data key; direct encrypt only 4 KB.
49. Secrets Manager vs Parameter Store? Rotation + $0.40/secret vs free config store.
50. RTO/RPO and DR tiers? Time to recover/data loss tolerated; backup-restore, pilot light, warm standby, active-active.

Bonus - FDE one-liners
- API Gateway default 29 s limit: stream LLM responses via ALB/Fargate or Lambda response streaming.
- Vector store default for a pilot: Aurora Postgres + pgvector; OpenSearch for hybrid/scale.
- Keyless Bedrock access: ECS task role with `bedrock:InvokeModel` on specific model ARNs.
- First cost suspects: NAT data, cross-AZ, CloudWatch logs, idle LBs, LLM tokens.
