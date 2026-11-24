# Week 3 Cheatsheet - Storage and Databases

| Service | One-liner | Typical use |
|---|---|---|
| S3 | Regional object store, 11 9s, strong consistency | Files, data lake, backups, static assets |
| S3 Glacier classes | Archive tiers (90/90/180 d min) | Compliance/archives |
| S3 Intelligent-Tiering | Auto-tier by access | Unknown access patterns |
| Presigned URL | Temporary signed access to one object | Direct browser upload/download |
| EBS | Block disk, one AZ | EC2 boot/DB |
| EFS | Shared NFS, multi-AZ | Shared Linux file storage |
| FSx | Managed Windows/Lustre/ONTAP/OpenZFS | Windows shares, HPC |
| Storage Gateway / DataSync / Snow | Hybrid / bulk transfer / offline | Migration |
| RDS | Managed relational (MySQL/PG/MariaDB/Oracle/SQLServer) | Standard OLTP |
| Aurora | Cloud-native MySQL/PG, 6-copy storage, 15 replicas | HA, scale, global, pgvector |
| RDS Proxy | Connection pooler | Lambda -> RDS |
| DynamoDB | Serverless key-value/document, ms latency | Sessions, carts, high-scale lookups |
| DAX | DynamoDB in-memory cache | Microsecond reads |
| ElastiCache (Redis/Valkey, Memcached) | In-memory cache | Caching, sessions, rate limits |
| MemoryDB | Durable Redis-compatible DB | Primary in-memory store |
| Redshift | Columnar data warehouse | BI/analytics |
| Athena | Serverless SQL on S3 | Ad hoc lake queries |
| OpenSearch | Search/log/vector | Search, RAG retrieval |
| DocumentDB / Neptune / Keyspaces / Timestream | Mongo / graph / Cassandra / time series | Specialty |

Numbers: S3 object 5 TB max, 5 GB single PUT, 3,500 write / 5,500 read rps per prefix; DDB item 400 KB, 1 RCU = 4 KB strong read, 1 WCU = 1 KB write, LSI max 5 (creation-time), GSI default 20; Aurora 6 copies/3 AZs, 128 TiB, 15 replicas; RDS backups 1-35 d; RDS Multi-AZ failover ~1-2 min.
Multi-AZ = HA (sync). Read replica = scale reads (async).
