# Week 3 - Storage and Databases

---
## 1. S3 (Simple Storage Service)

**What:** Regional object store (key -> object + metadata) in buckets. Designed for 99.999999999% (11 9s) durability; objects stored across >=3 AZs (except One Zone classes).

### Key facts / limits (check current docs)
- Object size 0 B - 5 TB. Single PUT max 5 GB; use multipart upload (recommended > 100 MB; parts 5 MB - 5 GB, up to 10,000 parts).
- Bucket names globally unique; ~10,000 buckets per account default (raisable). Unlimited objects.
- Request rates: at least 3,500 PUT/COPY/POST/DELETE and 5,500 GET/HEAD per second PER PREFIX; scale by spreading across prefixes. (No need for random prefixes anymore.)
- **Consistency:** strong read-after-write and list consistency for all operations (since Dec 2020).
- Flat namespace; "folders" are key prefixes.

### Storage classes
| Class | Use | Retrieval | Min duration |
|---|---|---|---|
| Standard | hot data | ms | none |
| Intelligent-Tiering | unknown/changing access; auto-tiers, small monitoring fee | ms (opt. archive tiers) | none |
| Standard-IA | infrequent, rapid access | ms, retrieval fee | 30 d |
| One Zone-IA | re-creatable infrequent data, single AZ | ms | 30 d |
| Glacier Instant Retrieval | archive, rare access, ms | ms | 90 d |
| Glacier Flexible Retrieval | archive, minutes-hours | 1 min-12 h | 90 d |
| Glacier Deep Archive | cheapest, compliance | 12-48 h | 180 d |
| Express One Zone | single-digit ms, high-perf, directory buckets (ML, analytics) | ms | none |
Min object-size charges apply for IA classes (128 KB).

### Features
- **Versioning:** keeps all versions; deletes create delete markers; protects from overwrite/delete; once enabled can only be suspended. Combine with MFA Delete / Object Lock.
- **Lifecycle rules:** transition (Standard -> IA -> Glacier) and expiration, incl. noncurrent versions, abort incomplete multipart uploads (important cost leak).
- **Replication:** CRR (cross-region) / SRR (same-region), requires versioning, async, not retroactive (use Batch Replication for existing objects).
- **Object Lock** (WORM; governance vs compliance mode, legal hold).
- **Security layers:** IAM policies, bucket policies, Block Public Access (on by default for new buckets), ACLs disabled by default (Object Ownership = bucket owner enforced), encryption at rest always on (SSE-S3 default; SSE-KMS; SSE-C; DSSE-KMS), TLS in transit (enforce with `aws:SecureTransport`), VPC gateway endpoint + `aws:SourceVpce` condition, Access Points, Access Analyzer, Macie (PII discovery), CloudTrail data events.
- **Presigned URLs:** time-limited URL signed with the signer's credentials granting GET/PUT of one object without AWS creds. Expiry up to 7 days with IAM user keys (shorter if signed with temporary role creds - bounded by the session). Pattern: client uploads directly to S3 -> API never proxies big files.
- **Events:** S3 -> EventBridge/SNS/SQS/Lambda on object create.
- **Static website hosting** (use CloudFront + OAC for HTTPS).
- **S3 Select/Athena/Glue** for querying data in place; **Transfer Acceleration** (edge-upload), **Multi-Region Access Points**, **Batch Operations**, **Storage Lens**.
- Pricing: GB-month by class + requests + retrieval + data transfer out (+ cross-region replication). Requests on tiny objects can dominate cost.
- Gotchas: public bucket leaks (Block Public Access), `ListBucket` vs `GetObject` ARNs, delete markers hide versions but still cost, small-files problem for analytics, 503 SlowDown when hot prefix, KMS request-rate throttling (use S3 Bucket Keys), versioned bucket + lifecycle must expire noncurrent versions.
- Alternatives: EFS/EBS (not objects), GCS/Azure Blob, MinIO (self-hosted), R2/B2 (cheaper egress).

```python
s3 = boto3.client("s3")
url = s3.generate_presigned_url("put_object",
        Params={"Bucket": "my-bucket", "Key": "uploads/a.pdf", "ContentType": "application/pdf"},
        ExpiresIn=900)
# client: requests.put(url, data=..., headers={"Content-Type": "application/pdf"})
```

---
## 2. EBS / EFS / FSx (summary)
| | Type | Scope | Use |
|---|---|---|---|
| EBS | block | single AZ, 1 instance (Multi-Attach io1/io2 aside) | boot/DB disks |
| EFS | NFS (Linux) file, elastic, POSIX | multi-AZ regional, thousands of clients; Standard/IA/Archive tiers; Bursting vs Elastic/Provisioned throughput | shared content, CMS, ML datasets, Lambda/Fargate shared storage |
| FSx for Windows | SMB, AD integrated | Single/Multi-AZ | Windows file shares |
| FSx for Lustre | HPC parallel FS, S3-linked | | ML training, HPC |
| FSx for NetApp ONTAP | NFS/SMB/iSCSI, snapshots, multiprotocol | | lift-and-shift NetApp |
| FSx for OpenZFS | NFS, low-latency | | Linux migrations |
Also: Storage Gateway (hybrid), DataSync (bulk transfer), Transfer Family (SFTP to S3), Snow family (offline), AWS Backup (centralized backup).
EFS pricing is per GB-month, more than S3 (roughly 10x+ Standard S3) and several times EBS; EBS billed on provisioned size, EFS on used.

---
## 3. Relational: RDS and Aurora

**RDS:** managed MySQL, MariaDB, PostgreSQL, Oracle, SQL Server (and Db2). AWS handles provisioning, patching, backups (automated 1-35 days + PITR; manual snapshots), failover. No OS/SSH access (RDS Custom exists for Oracle/SQL Server). Storage autoscaling; storage max 64 TiB (check docs). Encryption at rest via KMS (must choose at creation; to encrypt existing: snapshot -> copy encrypted -> restore).

### Multi-AZ vs Read Replicas (classic interview question)
| | Multi-AZ | Read replica |
|---|---|---|
| Purpose | HA / failover | Read scaling (and DR/cross-region) |
| Replication | Synchronous | Asynchronous (lag) |
| Readable? | Standby not readable (Multi-AZ instance); the Multi-AZ DB *cluster* option has 2 readable standbys | Yes, own endpoint |
| Failover | Automatic, DNS endpoint flips (~60-120 s) | Manual promotion (becomes standalone) |
| Region | Same region, different AZ | Same or cross-region (up to 15 for MySQL/Postgres/MariaDB, check docs) |
| Backups | taken from standby | independent |

**Aurora:** MySQL/PostgreSQL-compatible, cloud-native. Storage separated from compute: 6 copies across 3 AZs, auto-grows in 10 GB chunks up to 128 TiB, continuous backup to S3. Up to 15 low-lag read replicas sharing the same storage; failover typically < 30 s. Cluster endpoint (writer), reader endpoint (load-balanced), custom endpoints. Aurora Serverless v2 (scales in ACUs, fine-grained, can scale down to 0 ACUs in newer versions - check docs). Aurora Global Database (cross-region <1 s replication lag typical, RPO ~1 s, fast promote). Backtrack (MySQL), parallel query, zero-ETL to Redshift, Data API, pgvector extension for embeddings (Aurora PostgreSQL), I/O-Optimized vs Standard pricing.
Aurora vs RDS: Aurora costs more per instance (but I/O-Optimized helps) yet gives faster failover, more replicas, bigger storage; RDS cheaper for small/simple.

RDS Proxy: connection pooling, faster failover, IAM auth - needed for Lambda.
Gotchas: connection limits depend on instance memory; parameter groups need reboot for static params; Multi-AZ does not give read scaling; replica lag; major version upgrades have downtime/planning; stopped RDS instances auto-start after 7 days; snapshots persist and cost.

When not RDS: key-value at huge scale (DynamoDB), analytics (Redshift/Athena), graph (Neptune), documents (DocumentDB).

---
## 4. DynamoDB

**What:** Serverless, fully managed key-value/document NoSQL; single-digit ms latency at any scale; multi-AZ by default.

- **Keys:** Partition key (hash) alone, or partition + sort key (range). Item max 400 KB. Design access patterns first, then keys; avoid hot partitions (choose high-cardinality PK; write sharding).
- **Per-partition limits (check docs):** ~3,000 RCU and 1,000 WCU per partition (adaptive capacity helps).
- **Capacity:** 1 RCU = one strongly consistent read of up to 4 KB/s (eventually consistent = half; transactional = 2x). 1 WCU = one write up to 1 KB/s (transactional = 2x).
- **Modes:** Provisioned (+ auto scaling; cheaper at predictable load, reserved capacity) vs On-Demand (pay per request, instant scaling, good for unknown/spiky; more expensive at steady high load). Can switch modes (limited frequency). Table classes: Standard vs Standard-IA.
- **Indexes:** LSI: same PK, different SK; must be created at table creation; max 5; shares table capacity; limits 10 GB per partition key value (item collection). GSI: different PK/SK; anytime; default max 20; own capacity; eventually consistent only; can be projected attributes.
- **Query vs Scan:** Query uses key (efficient); Scan reads everything (avoid). Filter expressions don't reduce RCU consumed.
- **Features:** TTL (free deletes), Streams (24 h change log -> Lambda), PITR (35 days) + on-demand backups, Global Tables (multi-region active-active, last-writer-wins), transactions (up to 100 items / 4 MB), conditional writes (optimistic locking), DAX (in-memory cache, microsecond reads), PartiQL, export to S3, batch ops (25 writes/100 reads per call), encryption always on (KMS).
- **Pricing:** per request (on-demand) or per provisioned capacity-hour, storage GB-month, plus options (streams, backups, global tables replicated writes).
- **Use:** sessions, carts, IoT, leaderboards, metadata, high-scale known access patterns. **Not:** ad-hoc queries/joins/aggregations, complex relational/analytics, items > 400 KB (store in S3, pointer in DDB).
- Gotchas: throttling (ProvisionedThroughputExceeded) from hot keys; scan cost; GSI backpressure throttles base table writes; single-table design learning curve; no cross-item joins.

```python
tbl = boto3.resource("dynamodb").Table("Orders")
tbl.put_item(Item={"pk": "USER#42", "sk": "ORDER#2026-01-01#9", "total": 30},
             ConditionExpression="attribute_not_exists(pk)")
tbl.query(KeyConditionExpression=Key("pk").eq("USER#42") & Key("sk").begins_with("ORDER#"))
```

---
## 5. ElastiCache / MemoryDB
- ElastiCache engines: Redis OSS / Valkey (data structures, persistence, replication, Multi-AZ failover, cluster mode sharding, pub/sub, Lua) vs Memcached (simple, multithreaded, no persistence/replication). Also serverless option.
- Patterns: cache-aside (lazy load; app checks cache, falls back to DB, writes to cache with TTL), write-through, TTL + eviction (LRU). Use for session store, rate limiting, leaderboards, DB offload.
- MemoryDB: Redis-compatible durable primary DB (multi-AZ transaction log). DAX only for DynamoDB.
- Gotchas: cache invalidation, thundering herd, must be in VPC (no public access), data must be tolerant of loss unless MemoryDB.

---
## 6. Redshift (and analytics neighbors)
- Redshift: columnar MPP data warehouse (OLAP); provisioned (RA3 nodes with managed storage) or Serverless; Spectrum queries S3; concurrency scaling; materialized views; zero-ETL from Aurora/DynamoDB. Not for OLTP, high-frequency single-row writes.
- Athena: serverless SQL on S3 (pay ~$5/TB scanned); use Parquet + partitioning to cut cost. Glue: ETL + Data Catalog. Lake Formation: governance. EMR: Spark/Hadoop. OpenSearch: search/log analytics/vector search.
- Other DBs: DocumentDB (Mongo-compatible), Neptune (graph), Keyspaces (Cassandra), Timestream (time series), QLDB (ledger; being retired - check), RDS Custom.

## 7. Choosing a database
```
 Relational, transactions, joins? --> RDS / Aurora (Aurora for HA + scale; Postgres w/ pgvector for RAG)
 Key-value/document, massive scale, known access patterns, serverless? --> DynamoDB
 Sub-ms cache / sessions / rate limit? --> ElastiCache (Redis/Valkey)
 Analytics / BI on TBs-PBs? --> Redshift (warehouse) or Athena on S3 (ad hoc)
 Search / logs / vectors? --> OpenSearch
 Graph --> Neptune ; Wide column --> Keyspaces ; Time series --> Timestream
 Files/blobs --> S3 (objects), EFS (shared POSIX), EBS (block)
```

## 8. Architecture example: image upload service
```
 Client -> API (Fargate) : POST /upload -> returns presigned PUT URL (S3)
 Client -> S3 (direct upload) -> S3 event -> SQS -> Lambda (thumbnail) -> S3 /thumbs
                                        \-> DynamoDB (metadata: user, key, status)
 Reads: CloudFront (OAC) -> S3
 Lifecycle: originals -> Standard-IA after 30d -> Glacier after 180d
```
