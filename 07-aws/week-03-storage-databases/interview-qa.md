# Week 3 Interview Q&A - Storage and Databases

**1. What is S3's consistency model?**
Strong read-after-write consistency for PUTs of new and overwritten objects, deletes, and strongly consistent LISTs (since Dec 2020). No more eventual-consistency caveats.

**2. List S3 storage classes and when to use them.**
Standard (hot), Intelligent-Tiering (unknown pattern), Standard-IA / One Zone-IA (infrequent, 30-day min), Glacier Instant/Flexible/Deep Archive (archive; 90/90/180-day min; ms / minutes-hours / 12-48 h), Express One Zone (low-latency single AZ). Use lifecycle rules to move data.

**3. How would you reduce an S3 bill?**
Lifecycle transitions and expirations, Intelligent-Tiering, delete noncurrent versions and incomplete multipart uploads, compress/aggregate small objects, avoid cross-region transfer (use CloudFront/VPC endpoints), Storage Lens to find waste, S3 Bucket Keys for KMS requests.

**4. Versioning: how does delete work?**
A plain DELETE adds a delete marker; prior versions remain (and cost money). Deleting a specific versionId permanently removes it. Versioning cannot be turned off, only suspended.

**5. What is a presigned URL and what are the security considerations?**
URL carrying a signature that grants temporary access to a specific operation on one object using the signer's permissions. Anyone with the URL can use it until expiry; keep expiry short, restrict key/content-type, make sure the signing identity has least privilege, URL is bound to signer credential validity (role creds expire sooner).

**6. Scenario: users upload 2 GB videos from browsers. Design?**
Backend issues presigned multipart-upload URLs (or POST policy); browser uploads directly to S3 (multipart for resumability, Transfer Acceleration if global); S3 event triggers processing (MediaConvert/Lambda/SQS). Avoids API Gateway's 10 MB and Lambda's 6 MB limits and proxying bandwidth.

**7. How do you secure an S3 bucket?**
Block Public Access (account + bucket), bucket policy with least privilege and `aws:SecureTransport`, bucket owner enforced (no ACLs), SSE-KMS where needed, VPC endpoint with policy, Access Analyzer, CloudTrail data events, versioning + Object Lock for ransomware, Macie for sensitive data, access logging.

**8. SSE-S3 vs SSE-KMS vs SSE-C?**
SSE-S3: S3-managed keys, default, free. SSE-KMS: KMS keys with key policy control and CloudTrail audit, request cost and throttling quotas. SSE-C: you supply key on every request, AWS doesn't store it.

**9. S3 vs EBS vs EFS?**
S3: object, HTTP API, unlimited, regional, cheapest. EBS: block, single AZ, attach to one instance, low latency. EFS: shared POSIX file system across many instances/AZs, elastic, pricier.

**10. RDS Multi-AZ vs Read Replica?**
Multi-AZ: synchronous standby in another AZ for automatic failover/HA (not for reads in the classic mode). Read replica: asynchronous copy for read scaling, can be cross-region, promotable manually; may lag.

**11. Scenario: Reporting queries slow the production RDS. Options?**
Add a read replica and point reports there; or cache results (ElastiCache), or offload to Redshift/Athena via zero-ETL/export; add indexes; Aurora reader endpoint. Remember replica lag.

**12. Aurora vs RDS?**
Aurora: distributed storage (6 copies / 3 AZs), auto-grow to 128 TiB, up to 15 replicas, faster failover (typically <30 s), Global Database, Serverless v2; higher price/vendor-specific. RDS: standard engines on EBS, simpler/cheaper for modest workloads, supports Oracle/SQL Server.

**13. How do you do DR for a database across regions?**
Aurora Global Database (RPO ~seconds, RTO ~minute), RDS cross-region read replica + promote, or cross-region snapshot copy (backup/restore, slower). DynamoDB Global Tables for active-active.

**14. How does RDS failover work and how long does it take?**
On AZ/instance failure, RDS flips the DNS CNAME to the standby, typically 60-120 s (Aurora faster). Apps must reconnect and respect DNS TTL; use RDS Proxy to shorten disruption.

**15. DynamoDB partition key vs sort key; how to choose a key?**
PK determines distribution (hash); SK orders items within a PK and enables range queries. Choose a high-cardinality PK that evenly spreads traffic and supports your main access pattern; model with composite keys, GSIs for alternates.

**16. GSI vs LSI?**
LSI: same PK, alternate SK, created only at table creation, max 5, strongly consistent reads possible, shares capacity, 10 GB item collection cap. GSI: different PK/SK, any time, default 20 per table, separate capacity, eventually consistent only.

**17. Provisioned vs on-demand capacity?**
Provisioned: set RCU/WCU (+auto scaling), cheapest for steady predictable load, can reserve. On-demand: pay per request, handles unknown/spiky traffic and new tables, higher unit price. Switch based on observed traffic.

**18. How many RCUs for 100 strongly consistent reads/s of 6 KB items?**
Each read rounds up to 8 KB = 2 RCU; 100 x 2 = 200 RCU. Eventually consistent: 100. Transactional: 400.

**19. Troubleshooting: DynamoDB ProvisionedThroughputExceeded despite low overall usage.**
Hot partition/key; adaptive capacity helps but not infinite. Fix key design (sharding suffix), spread writes, cache hot reads with DAX, check GSI throttling back-pressuring the table, use on-demand, add retries with exponential backoff and jitter (SDK does by default).

**20. When would you NOT use DynamoDB?**
Ad hoc queries, joins, complex transactions across many entities, analytics/aggregations, unknown access patterns, items >400 KB. Choose Aurora/Postgres, or S3+Athena, or OpenSearch.

**21. What are DynamoDB Streams used for?**
24-hour ordered change log per item; trigger Lambda for materialized views, cross-system sync, audit; Global Tables use it internally. Alternative: Kinesis Data Streams for DynamoDB for longer retention.

**22. Redis vs Memcached in ElastiCache?**
Redis/Valkey: rich data structures, persistence, replication, Multi-AZ failover, cluster mode, pub/sub. Memcached: simple key-value, multithreaded, no persistence or replication. Default to Redis/Valkey.

**23. Explain cache-aside and its pitfalls.**
App reads cache first; on miss reads DB and populates cache with TTL. Pitfalls: stale data, stampede on expiry (use jitter/locks), cache cold start, inconsistent invalidation on writes.

**24. Redshift vs Athena vs RDS for analytics?**
Redshift: managed warehouse for heavy, repeated BI workloads with high concurrency and data loaded in columnar storage. Athena: serverless ad hoc SQL on S3, pay per TB scanned, best with Parquet. RDS: OLTP, not scaled for large analytical scans.

**25. Scenario: choose a database for a chat app storing messages, 50k writes/s, lookup by conversation.**
DynamoDB (PK conversationId, SK timestamp/messageId), on-demand or provisioned with autoscaling, TTL for retention, Streams for fan-out. Alternative Keyspaces/Cassandra. Not RDS due to write scale and simple access pattern.

**26. How do you encrypt an unencrypted RDS instance?**
Cannot toggle in place: take snapshot, copy with encryption (KMS key), restore to a new instance, cut over (or use DMS/replica for low downtime).

**27. Cost angle: unexpected RDS/Aurora charges?**
Idle instances, oversized instances, Multi-AZ in dev, Aurora I/O charges (consider I/O-Optimized), orphaned snapshots, long backup retention, cross-region replicas/transfer, provisioned IOPS storage. Use Compute Optimizer, Savings Plans/RIs for steady use, stop/schedule dev DBs (auto-restart after 7 days).
