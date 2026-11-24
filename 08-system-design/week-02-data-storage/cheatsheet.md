# Week 2 Cheatsheet - Data and Storage

## Replication
| Type | Writes | Conflicts | Examples | Watch for |
|---|---|---|---|---|
| Single-leader | 1 node | none | Postgres, MySQL, Mongo, Kafka, Redis | failover data loss, split brain, lag |
| Multi-leader | 1 per region | yes | CouchDB, MySQL group repl., DynamoDB global tables | conflict resolution, LWW loss |
| Leaderless | any node | yes | Cassandra, Dynamo, Riak | stale reads, repair, clock skew |

- Sync = no loss, slow/blocks. Async = fast, can lose acked writes. Semi-sync = 1 sync + rest async.
- Lag anomalies: read-your-writes (read own from leader), monotonic reads (pin user to replica), consistent prefix (same partition).
- Failover steps: detect -> elect -> reconfigure. Dangers: lost writes, split brain, flapping from short timeouts.

## Quorum
- W + R > N => read/write sets overlap. N=3: QUORUM = 2 (W=2,R=2). Tolerates N-W write and N-R read failures.
- NOT linearizable by itself (sloppy quorum, LWW + skew, failed partial writes, concurrent writes).
- Repair: read repair, hinted handoff, anti-entropy (Merkle trees).
- Cassandra levels: ONE, QUORUM, LOCAL_QUORUM, ALL. DynamoDB: eventual (default) vs strong read.

## Partitioning
| Scheme | Good | Bad |
|---|---|---|
| Range | range scans, easy splits | hot spot on sequential keys |
| Hash | even spread | no range queries |
| Consistent hash (+vnodes) | add/remove node moves ~K/N keys | needs routing map |
| Fixed partitions (Kafka, Redis 16384 slots) | simple rebalance | count fixed up front |
- hash mod N: BAD (almost all keys move when N changes).
- Local sec. index: cheap write, scatter-gather read. Global: single-shard read, async multi-shard write.
- Hot key fixes: cache, salt key (key#0..9), replicate, aggregate writes, isolate tenants.
- Shard key checklist: dominant access pattern, high cardinality, even load, not monotonic, growth, resharding cost.
- Routing: any-node forwarding / proxy tier / smart client; map in etcd/ZooKeeper or gossip.

## SQL vs NoSQL quick pick
- Relational: joins, ad hoc, ACID, fits primary+replicas -> default start.
- KV/wide-column (DynamoDB, Cassandra): huge writes, key access, known queries, denormalize.
- Document (Mongo): aggregate-shaped, flexible schema.
- Distributed SQL (Spanner, Cockroach): SQL + ACID + horizontal/geo, pay latency/cost.
- Search: Elasticsearch. Cache: Redis. Blob: S3. OLAP: Redshift/BigQuery/ClickHouse. Time series: Timescale/Prometheus.
- Polyglot: source of truth + derived stores via CDC/outbox.

## Indexes
- B-tree: read/range friendly, in-place. LSM: write-heavy, SSTables + compaction + Bloom filters.
- Composite: leftmost prefix. Covering: index-only scan. Partial: index subset of rows.
- Over-indexing slows writes; hot index must fit in RAM; UUIDv4 PKs fragment B-trees.
- Use keyset pagination, not OFFSET. Create indexes concurrently.
- Geo: geohash, quadtree, S2, H3.

## CAP / PACELC
- CAP: during partition choose C (linearizable) or A (every live node answers). P is not optional. Per-operation.
- PACELC: if Partition -> A or C; Else -> Latency or Consistency.
- PA/EL: Cassandra, Dynamo, Riak. PC/EC: Spanner, Cockroach. CP: etcd, ZooKeeper, HBase.

## Consistency ladder (strong -> weak)
linearizable > sequential > causal > session (RYW, monotonic reads/writes) > eventual
| Need | Pick |
|---|---|
| money, inventory, unique constraint, lock | linearizable / serializable |
| chat ordering, replies | causal |
| own profile edit | read-your-writes |
| likes, feeds, counters | eventual |
| cart | eventual + merge |

## Real systems one-liners
- Dynamo/Cassandra: ring + vnodes + leaderless quorum + LSM + gossip.
- DynamoDB: PK hash + SK range, GSI/LSI, Streams, txns (limited), global tables LWW.
- Spanner: Paxos groups per split + TrueTime commit-wait = external consistency.
- Kafka: partition = unit of ordering/parallelism; leader + ISR; acks=all + min.insync.replicas.
- Redis: async single-leader; Cluster 16384 slots; can lose acked writes on failover.
- etcd/ZooKeeper: Raft/ZAB, 3 or 5 nodes, small critical metadata.
- Aurora: 6 copies / 3 AZs, 4/6 write quorum, 3/6 read (check current docs).

## Failure modes list
replication lag, split brain, lost acked writes, hot partition, resharding storm, scatter-gather tail latency, clock skew + LWW, tombstones, unbounded partitions, retry storms, index migration locks.

## Say-it-out-loud lines
- "Replication buys availability and read scale; partitioning buys write and storage scale."
- "Hashing balances keys, not load."
- "Quorum overlap is not linearizability."
- "CAP is only about partitions; PACELC covers the normal case: latency vs consistency."
- "Pick the weakest consistency that keeps the invariants."
- "Start with Postgres + replicas + cache; shard when a measured bottleneck demands it."
