# Week 2 - Data and Storage: Replication, Sharding, SQL vs NoSQL, Consistency

Time budget: ~3 hrs. Read lesson (1.5h), Q&A aloud (1h), cheatsheet (0.5h).
Numbers marked "(check current docs)" change over time; verify before quoting in an interview.
AWS tie-in: see ../../07-aws/week-03-storage-databases (RDS/Aurora, DynamoDB, ElastiCache) for the managed versions of everything here.

Why this week matters: in almost every system design interview the hard part is the data layer. Compute is easy to scale because it is stateless (week 1). State is not. Everything in this lesson is a answer to two forces:
1. One machine cannot hold or serve all the data (so: partition it).
2. One machine can die (so: copy it).
Copying creates the consistency problem. Partitioning creates the routing, hot-spot, and cross-partition-query problems. The rest is detail.

---
## 1. Replication: keeping copies of data

Reasons to replicate: (a) availability - survive node/AZ loss, (b) read scalability - spread reads, (c) latency - put copies near users. Replication does NOT help write throughput in single-leader designs (every replica applies every write).

### 1.1 Single-leader (leader-follower, primary-replica)

```
            writes
   client ---------> +--------+   replication log (WAL / binlog / oplog)
                     | LEADER |------------------+-----------------+
                     +--------+                  |                 |
                         ^                       v                 v
   client ---reads-------+--------------->  +----------+      +----------+
        (or from followers)                 | FOLLOWER |      | FOLLOWER |
                                            +----------+      +----------+
```
- All writes go to the leader; it appends to a log; followers apply the log in order.
- Examples: PostgreSQL streaming replication, MySQL, MongoDB replica sets, Redis replication, Kafka partition leaders, Aurora (shared storage variant; check current docs).
- Sync vs async:
  - Synchronous: leader waits for follower ack. No data loss if leader dies, but a slow/dead follower blocks writes. Writes are as slow as the slowest sync follower.
  - Asynchronous: leader acks immediately. Fast, but if leader dies before the log ships, acknowledged writes are LOST on failover. Replication lag appears.
  - Semi-sync: 1 sync follower, rest async (so there are always >= 2 copies). Common compromise (MySQL semi-sync, Postgres synchronous_commit with one named standby).
- Replication log formats: statement-based (non-deterministic functions break it), WAL shipping (physical, tied to storage engine version), logical/row-based (portable, used by CDC like Debezium).

Failover (the dangerous part):
1. Detect leader dead (timeouts - too short = false positives and flapping, too long = long outage).
2. Elect new leader (usually the most up-to-date follower).
3. Reconfigure clients/followers to the new leader.
Failure modes:
- Lost writes: new leader missing the last async writes. When the old leader comes back it has conflicting writes; typically discarded (GitHub famously had an incident where a lagging MySQL follower was promoted and reused auto-increment IDs that were already in Redis - lesson: discarding writes is dangerous when other systems saw them).
- Split brain: two nodes both believe they are leader and both accept writes. Mitigation: consensus-based election (Raft/etcd, ZooKeeper), fencing tokens / STONITH (week 4).
- Replication lag anomalies (next section).

Replication lag anomalies (what users actually see with async followers):
```
 Read-your-writes violation:
   user posts comment -> leader        user refreshes -> follower (lagging)  -> comment "gone"

 Monotonic reads violation (time goes backwards):
   read 1 -> fresh follower A sees comment
   read 2 -> stale follower B        -> comment disappears

 Consistent prefix violation:
   Q: "How far in the future can you see?"  A: "About 10 seconds"
   observer sees the answer before the question (different partitions replicate at different speeds)
```
Fixes:
- Read-your-writes: read your own recent writes from the leader (e.g., "for 1 minute after a write, read user's profile from leader"), or track a last-write timestamp/LSN and only use followers that have caught up, or sticky routing to one replica.
- Monotonic reads: pin each user to one replica (hash user id).
- Consistent prefix: write causally related data to the same partition.

### 1.2 Multi-leader (multi-master)

```
   Region US                         Region EU
  +----------+   async replication  +----------+
  | LEADER A |<-------------------->| LEADER B |
  +----------+                      +----------+
     |  |                              |  |
   followers                         followers
```
When: multi-datacenter (local writes in each region, tolerate inter-DC link failure), offline-capable clients (each device is a "leader": calendar apps, Notes), collaborative editing.
Cost: WRITE CONFLICTS. Two leaders accept concurrent writes to the same key; neither knew about the other.
Conflict handling:
- Avoid: route all writes for a given record to the same leader (home region per user). Easiest and most common.
- Last-write-wins (LWW) by timestamp: simple, silently loses data, depends on clocks (week 4).
- Merge: keep both ("siblings") and let app/user resolve (Dynamo shopping cart, Riak), or use CRDTs / operational transform (Google Docs, Figma-like) - week 4.
- Custom resolution logic on write or on read.
Other hazards: auto-increment keys collide, triggers/constraints/unique indexes are hard across leaders. Topology matters (circular/star/all-to-all; all-to-all can have causality issues where an update arrives before the insert it depends on).
Examples: MySQL Group Replication multi-primary, Postgres BDR, CouchDB, Cassandra-across-DCs behaves leaderless but with multi-DC settings, DynamoDB global tables (multi-region, last-writer-wins; check current docs), Spanner avoids this by using Paxos groups plus TrueTime for one globally consistent order.

### 1.3 Leaderless (Dynamo style)

```
   client writes to N replicas directly (or via a coordinator)
         +--> replica 1  (ack)
 client -+--> replica 2  (ack)     W=2 acks => success
         +--> replica 3  (down / slow)

   client reads from R replicas, takes the newest version
```
- Any replica accepts writes. No failover event at all: a dead node simply does not ack.
- Used by Amazon Dynamo paper, Cassandra, Riak, ScyllaDB (DynamoDB the service is NOT leaderless under the hood; it borrows the ideas but uses leader-based partitions - check current docs).
- Staleness repair mechanisms:
  - Read repair: reader sees a stale replica in the R responses and writes the new value back.
  - Anti-entropy: background process compares replicas (Merkle trees) and syncs differences.
  - Hinted handoff: if the target replica is down, another node stores a "hint" and forwards it when the target returns (part of "sloppy quorum").
- Versioning: LWW timestamps (Cassandra default), or version vectors (Riak) to detect concurrency.

### 1.4 Quorums (applies to leaderless; also used inside Raft/Paxos groups)

N replicas, write acked by W, read consults R. If **W + R > N**, the read set and write set must overlap in at least one node, so a read sees the latest write (in the absence of other problems).

```
 N=3, W=2, R=2:       write set {1,2}      read set {2,3}    overlap = node 2  -> sees latest
 N=3, W=1, R=1:       write {1}            read {3}          no overlap -> may be stale (fast, eventually consistent)
 N=3, W=3, R=1:       reads fast, writes block if ANY node down
 N=3, W=1, R=3:       writes fast, reads fail if ANY node down
```
- Tolerates N-W node failures for writes and N-R for reads. N=3,W=2,R=2 tolerates 1 failure either way. Typical production default: N=3, QUORUM = floor(N/2)+1.
- Cassandra consistency levels: ONE, QUORUM, LOCAL_QUORUM (quorum inside local DC, avoids cross-region latency), ALL. DynamoDB offers eventually consistent reads (default, half the read cost) vs strongly consistent reads (check current docs for cost).
- Quorum is NOT linearizability. Edge cases that still give stale reads even with W+R>N:
  - Sloppy quorums / hinted handoff (write went to nodes outside the "home" N, so R may not overlap).
  - Concurrent writes resolved by LWW with clock skew (a "later" write gets an earlier timestamp and is dropped).
  - A write that succeeded on fewer than W nodes returns an error but is NOT rolled back; readers may or may not see it.
  - A node restored from a stale replica, breaking the W count.
  - Read concurrent with a write in flight (some replicas new, some old).
  For true linearizability you need consensus (Raft/Paxos) or read-modify-write via compare-and-set / lightweight transactions (Cassandra LWT = Paxos).

### 1.5 Comparison

| | Single-leader | Multi-leader | Leaderless |
|---|---|---|---|
| Write path | One node | One per region | Any node |
| Conflicts | None (single order) | Yes, must resolve | Yes, must resolve |
| Failover | Needed, risky | Per-leader | Not needed |
| Consistency | Easy to reason about; strong possible | Eventual | Tunable via quorum |
| Best for | OLTP, most apps | Multi-region writes, offline | High availability, write-heavy, multi-DC |
| Examples | Postgres, MySQL, Mongo, Kafka | Group repl., CouchDB | Cassandra, Dynamo, Riak |

How interviewers probe: "What happens when the leader dies and a follower was 2 seconds behind?" "How do you give a user read-your-writes?" "Multi-region active-active: how do you handle the same row edited in two regions?" "Does W+R>N guarantee linearizability?" (No.)

---
## 2. Partitioning (sharding)

Replication copies the same data; partitioning splits DIFFERENT data across nodes so each holds a subset. Used when data or write throughput exceeds one machine. Almost always combined: each partition is itself replicated.

```
   keys A..Z  --partition-->  P1: A-H [leader n1, followers n2,n3]
                              P2: I-Q [leader n2, followers n3,n1]
                              P3: R-Z [leader n3, followers n1,n2]
```
Goals: spread data AND load evenly; avoid hot spots; make rebalancing cheap; make routing simple.
Terminology differs: shard (MongoDB, MySQL/Vitess), partition (Kafka, Cassandra, DynamoDB), region (HBase), tablet (Bigtable/Spanner), vnode (Cassandra/Riak).

### 2.1 Range partitioning
- Each partition owns a contiguous key range (A-H, I-Q, ...). Keys stay sorted within a partition.
- Pro: efficient range scans (`WHERE ts BETWEEN`), ordered iteration, easy to split a range.
- Con: hot spots when access follows the key order. Classic: time-series key (timestamp prefix) sends ALL current writes to the newest partition.
  Fix: prefix with another dimension, e.g., `(sensor_id, timestamp)` so writes spread across sensors but each sensor's range scan is still local.
- Used by: HBase, Bigtable, Spanner, CockroachDB, TiKV, MongoDB range sharding, DynamoDB sort key within a partition key.
- Splitting: partition grows past threshold -> split in two, move one half. Often automatic.

### 2.2 Hash partitioning
- partition = hash(key) mod N or hash falls into a range of the hash space. Spreads keys uniformly.
- Pro: even distribution, removes ordering hot spots.
- Con: range queries are destroyed (adjacent keys land everywhere) -> scatter-gather over all partitions. Cassandra compromise: compound key (partition key hashed, clustering columns sorted within the partition). DynamoDB: partition key hashed, sort key ordered within it.
- NAIVE `hash(key) mod N` is a trap: when N changes (add a node), almost every key remaps (about (N-1)/N of keys), causing a mass data migration. Hence consistent hashing or fixed partition counts.

### 2.3 Consistent hashing

```
            hash ring (0 ... 2^32-1, wraps)
                 nodeA
            .--*--------.
          /               \
       *                   * nodeB
   key k1 .                |
         \   key k2 .      |
          *                * nodeC
            '-----*-----'
   Rule: a key belongs to the first node clockwise from its hash.
```
- Add a node: it takes over only the arc between it and its predecessor -> only about K/N keys move (K keys, N nodes). Remove a node: its keys go to the next node clockwise.
- Problem with plain version: uneven arcs, and when a node dies ALL its load goes to one neighbor (cascading overload).
- Virtual nodes (vnodes): each physical node owns many (e.g., 100-256) small points on the ring. Load spreads evenly; a dead node's load is shared by many; powerful machines get more vnodes. Cassandra (num_tokens, check current docs for default), Riak, Dynamo.
- Replication on the ring: store a key on the next N distinct physical nodes clockwise (the "preference list").
- Alternatives: rendezvous (highest random weight) hashing, jump consistent hash (Google; needs sequential bucket numbering), fixed number of partitions (Kafka, Elasticsearch, Couchbase's 1024 vBuckets, Redis Cluster's 16384 hash slots) where partitions are assigned to nodes and only whole partitions move.
- Redis Cluster: slot = CRC16(key) mod 16384; each master owns a slot set; resharding moves slots; clients follow MOVED/ASK redirects. Hash tags `{user1}` force related keys into one slot.

### 2.4 Rebalancing strategies
| Strategy | How | Pros/cons |
|---|---|---|
| Fixed partitions | Create many more partitions than nodes (e.g., 1000 for 10 nodes); move whole partitions | Simple, cheap; partition count must be chosen up front, too big = overhead, too small = unsplittable |
| Dynamic splitting | Split a partition when it exceeds size; merge when small | Adapts to data; starts with one partition (pre-split to avoid initial hot spot) |
| Proportional to nodes | Fixed number of partitions per node (Cassandra) | Partition size stays steady as cluster grows |
Automatic rebalancing is convenient but dangerous: moving huge data while the cluster is already overloaded (which may be why a node looked "dead") can cause cascading failure. Many systems keep a human in the loop for approval.

### 2.5 Routing (how does a client find the partition?)
1. Any node: client contacts any node, it forwards (Cassandra gossip, Redis MOVED).
2. Routing tier / proxy: a partition-aware load balancer (mongos, Vitess vtgate, Twemproxy).
3. Partition-aware client: client has the map.
The map is kept in a coordination service (ZooKeeper, etcd) or spread by gossip (week 4).

### 2.6 Secondary indexes on partitioned data
- Local (document-partitioned) index: each partition indexes only its own documents. Write touches one partition; read by secondary attribute must scatter-gather to ALL partitions (tail latency amplification). Used by MongoDB, Cassandra, Elasticsearch.
- Global (term-partitioned) index: index itself is partitioned by the indexed term. Reads hit one partition; a write touches several partitions and is usually async (so indexes can lag). DynamoDB GSI (eventually consistent, check current docs), Spanner global indexes (transactional but costlier).
- Interview line: "Local = fast writes, slow reads; global = fast reads, slow/complex writes."

### 2.7 Hot keys and skew
Hashing spreads keys, not LOAD. A celebrity user, viral post, or a single tenant creates a hot partition.
Mitigations:
- Key salting / splitting: append a random suffix (key#0..key#9) for writes, read all 10 and merge. Costs read amplification; track which keys are hot (app-level knowledge).
- Cache in front: hot reads absorbed by Redis/CDN; local in-process cache with short TTL for the hottest keys.
- Replicate the hot key's data to more nodes (read hot partitions from several replicas).
- Request coalescing, write batching/aggregation (counters: buffer increments in memory and flush).
- Isolation: dedicate partitions to big tenants.
- DynamoDB: adaptive capacity and split-for-heat reduce but do not remove per-partition limits (check current docs: per-partition throughput limits of roughly 3000 RCU / 1000 WCU historically).
Failure mode: one hot shard causes timeouts, retries pile up (retry storm), the shard is overloaded further; cluster-wide capacity looks fine but one node is pinned at 100%.

### 2.8 Cross-partition operations
- Joins and transactions spanning shards are expensive: scatter-gather, 2PC, or sagas (week 4).
- Design rule: choose the partition key so the MOST COMMON access pattern is single-partition. E.g., chat: partition by conversation_id; e-commerce: by user_id (orders per user) or tenant_id (multi-tenant SaaS).
- Choosing the key is the single most-probed topic: state access patterns, cardinality (many distinct values), uniformity, and write/read skew.

---
## 3. SQL vs NoSQL: how to choose

Do not answer "NoSQL scales better". Answer from access patterns, consistency needs, and operational scale.

| Dimension | Relational (Postgres, MySQL, Aurora) | Key-value / wide-column (DynamoDB, Cassandra, Bigtable) | Document (MongoDB, Firestore) | Distributed SQL (Spanner, CockroachDB, TiDB, Aurora DSQL?) |
|---|---|---|---|---|
| Data model | Normalized tables, joins | Key -> value / rows by partition+sort key | Nested JSON docs | Relational |
| Queries | Ad hoc, joins, aggregates | Known access patterns only | Rich per-document queries | Ad hoc SQL |
| Transactions | Full ACID (single node) | Limited (item-level; DynamoDB has multi-item transactions with limits) | Multi-doc transactions exist, costlier | ACID across shards |
| Scale writes | Vertical; manual sharding | Horizontal, near-linear | Horizontal via sharding | Horizontal, automatic |
| Consistency | Strong | Tunable (eventual default in many) | Tunable | Strong (external consistency in Spanner) |
| Schema | Rigid, migrations | Flexible | Flexible | Rigid |
| Price of scale | Complexity of sharding | Design queries up front; denormalize | Moderate | Higher latency on writes (consensus + cross-region), cost |

Use relational when: relationships and ad hoc queries matter, strong consistency/transactions (payments, inventory, bookings), data fits a primary + replicas (a well-tuned Postgres handles surprising volume: single instance often tens of thousands of simple QPS; terabytes of data - check current docs/benchmarks).
Use wide-column / KV when: huge write throughput, simple access by key, predictable single-digit-ms latency at any scale, known queries (user activity feeds, IoT, session stores, messaging history).
Use document when: aggregates read/written as a unit, schema varies, rapid iteration.
Use distributed SQL when: you need SQL + transactions AND horizontal scale/geo-distribution, and can pay latency/cost.
Other stores to name: search (Elasticsearch/OpenSearch) for full-text; graph (Neo4j) for deep relationship traversal; time-series (Timescale, InfluxDB, Prometheus); columnar/OLAP (Redshift, BigQuery, ClickHouse); object store (S3) for blobs; in-memory (Redis) for cache/leaderboards/locks.

Pragmatic framing (works well in interviews): "Start with Postgres. Add read replicas and caching. Shard or move a specific hot table to a NoSQL store when a measured bottleneck demands it. I would pick DynamoDB/Cassandra up front only when write volume or availability requirements clearly exceed what a single-leader RDBMS gives."

Polyglot persistence: system of record (RDBMS) + derived stores (search index, cache, analytics) kept in sync via CDC / events (week 3: outbox). The derived stores are rebuildable; the source of truth is single.

Denormalization: in NoSQL you model tables per query ("single-table design" in DynamoDB). Trade: fast reads, but updates must touch many copies; consistency between copies is YOUR problem.

Case: DynamoDB data modelling example
```
 PK = USER#123          SK = PROFILE
 PK = USER#123          SK = ORDER#2026-11-01#9001
 PK = USER#123          SK = ORDER#2026-11-14#9042
 Query(PK=USER#123, SK begins_with ORDER#) -> a user's orders sorted by date in ONE partition, single request.
 GSI on (status, created_at) for "all PENDING orders" (watch for hot GSI partition if status has low cardinality).
```

---
## 4. Indexes at scale

Recap: an index trades write cost + storage for faster reads.

Storage engine families:
```
 B-tree (Postgres, MySQL InnoDB, most RDBMS)         LSM-tree (Cassandra, RocksDB, LevelDB, HBase, Bigtable)
  - update-in-place pages (typically 4-16 KB)         - writes go to memtable + WAL, flushed as immutable sorted SSTables
  - good read latency, range scans                    - background compaction merges SSTables
  - write amplification from page splits/WAL          - very high write throughput (sequential IO)
  - predictable reads                                 - reads may check several SSTables -> Bloom filters avoid useless disk reads
                                                      - compaction can spike IO/latency; space amplification
```
Rule of thumb: B-tree for read-heavy/OLTP general purpose; LSM for write-heavy, append-heavy, huge ingest.

Index types you should name:
- Primary vs secondary; clustered (data stored in index order, InnoDB) vs non-clustered/heap (Postgres).
- Composite index: order matters; leftmost-prefix rule. `(user_id, created_at)` serves `WHERE user_id=?` and `WHERE user_id=? ORDER BY created_at`, not `WHERE created_at=?` alone.
- Covering index: contains all columns the query needs -> index-only scan, no table lookup.
- Partial index (index only rows matching a predicate, e.g., `WHERE status='PENDING'`), unique, hash, GIN (full-text/JSON/array), GiST (geo), BRIN (huge ordered tables, tiny index).
- Geospatial: geohash, quadtree, S2 (Google), H3 (Uber) - relevant to ride-hailing (week 6).
- Inverted index (search engines): term -> posting list of doc ids.
- Bloom filters (week 4): per-SSTable "definitely not here" check.

Scale problems:
- Index size must fit in RAM for good performance; if the hot index exceeds memory, latency cliff.
- Write amplification: every extra index slows every INSERT/UPDATE. Over-indexing is a real production issue. Drop unused indexes (check pg_stat_user_indexes).
- Low-cardinality columns (boolean, status) make poor B-tree indexes alone; combine in composite/partial.
- Random keys (UUIDv4) as clustered primary key cause page splits and cache-unfriendly inserts; time-ordered IDs (UUIDv7, ULID, Snowflake) keep inserts append-like but beware hot-range on distributed range-partitioned stores.
- Online index creation (`CREATE INDEX CONCURRENTLY`) on huge tables; avoid long locks.
- Pagination: OFFSET N scans and discards N rows (slow deep pages); use keyset/cursor pagination (`WHERE (created_at, id) < (?, ?) ORDER BY ... LIMIT 20`) - ties into week 5 API design.
- Distributed secondary indexes: see 2.6.
- Search/analytics workloads: do not run on the OLTP primary; ship to Elasticsearch/ClickHouse/warehouse via CDC.
- Use EXPLAIN (ANALYZE) to verify; stale statistics lead to bad plans.

Interviewer probe: "Query is slow on a 500M-row table. Walk me through." Answer: EXPLAIN -> missing/wrong index -> composite order -> covering -> partition the table (by time) -> archive old data -> read replica -> cache -> denormalize/precompute -> shard.

---
## 5. CAP and PACELC

### 5.1 CAP (Brewer; formalized by Gilbert & Lynch)
In the presence of a network **P**artition, a distributed data store must choose between **C**onsistency (linearizability: every read sees the latest write, as if one copy) and **A**vailability (every non-failing node answers every request).

```
   Partition: link between node A and node B is cut
     Client1 --> A  write x=2 ...     Client2 --> B  read x
   CP choice: B refuses (error/timeout) or A refuses write  -> consistent, not available
   AP choice: B answers with old x=1, A accepts x=2         -> available, inconsistent (must reconcile later)
```
Correct understanding (commonly botched):
- It is NOT "pick any two of three". Partitions are not optional in a distributed system; the real choice is C vs A DURING a partition. When there is no partition you can have both.
- "C" in CAP means linearizability, not the "C" of ACID (which is about invariants/integrity).
- "A" in CAP means every request to a non-failed node gets a non-error response - a strong definition; most real systems are "mostly available".
- It is a per-operation property, not a per-database label. Cassandra can act CP-ish with QUORUM, DynamoDB offers both read modes, Spanner is CP but with very high availability engineering (Google's argument: partitions are rare because of private network, so "effectively CA" in practice).
- Typical classification (approximate, depends on configuration): CP - etcd, ZooKeeper, Consul, HBase, Spanner, MongoDB (default majority concerns), Redis Cluster (loses writes on partition; not strongly consistent anyway). AP - Cassandra, DynamoDB (default), Riak, CouchDB.
- Single-node RDBMS: CAP not applicable (no network between replicas). Single-leader with async replicas: effectively sacrifices C on replica reads, and may lose data on failover.

### 5.2 PACELC (Abadi)
"If there is a Partition, choose Availability or Consistency; Else (normal operation), choose Latency or Consistency."
Why: even without partitions, replicating synchronously (for consistency) costs latency (round trips to other replicas/regions).

| System | P: A or C | E: L or C | Notation |
|---|---|---|---|
| Cassandra, Dynamo, Riak | A | L | PA/EL |
| MongoDB (default settings; check current docs) | A or C depending on write concern | L | commonly PA/EC listed in papers, depends on config |
| Spanner, CockroachDB, FaunaDB | C | C | PC/EC |
| PNUTS (Yahoo) | C | L | PC/EL |
| DynamoDB | A (eventual reads) / tunable | L (default) / C (strong read) | PA/EL default |
Interview line: "CAP is only about the failure case. PACELC reminds me that the more common trade-off is latency vs consistency, which is why I'd read from a local replica for a feed but go to the leader for a balance check."

---
## 6. Consistency models (from strongest to weakest)

```
 Strict / linearizable  (strong)       one global real-time order; reads return latest committed write
        |
 Sequential                            one global order consistent with each client's program order; not real-time
        |
 Causal                                causally related ops seen in order; concurrent ops may differ per observer
        |
 Session guarantees (read-your-writes, monotonic reads, monotonic writes, writes-follow-reads)
        |
 Eventual                              if writes stop, replicas converge eventually; no ordering guarantee meanwhile
```
Definitions to give crisply:
- **Strong / linearizable**: system behaves as if there is a single copy and operations occur atomically at some point between invocation and response. Needed for: locks/leader election, unique constraints (username), bank balance, inventory with no oversell. Cost: coordination (consensus, leader reads) -> latency, reduced availability under partition.
- **Sequential**: same order seen by everyone, but may lag real time.
- **Causal**: if B depends on A (reply to a message), everyone sees A before B. Concurrent writes may be seen in different orders. Achievable without sacrificing availability (a "strongest AP" model). Implemented via version vectors / dependency tracking (COPS, MongoDB causal sessions, check docs).
- **Read-your-writes (read-after-write)**: you see your own updates. Session guarantee.
- **Monotonic reads**: once you see a value, you never see an older one.
- **Eventual**: replicas converge; the weakest useful guarantee. Often paired with conflict resolution (LWW, CRDTs). "Eventual" says nothing about HOW long; in practice ms to seconds, but under failure much longer.
- **Bounded staleness** (Cosmos DB): reads lag by at most K versions or T seconds. Good product-friendly model.

ACID "C" and isolation levels (separate axis - single-node transaction isolation):
- Read committed (no dirty reads), snapshot isolation / repeatable read (consistent snapshot; write skew possible), serializable (as if one at a time; SSI, 2PL, or actual serial execution). Anomalies: dirty read, non-repeatable read, phantom, lost update, write skew.
- Do not confuse isolation (concurrent transactions on one DB) with distributed consistency (replicas agree).
- Spanner "external consistency": strict serializability using TrueTime commit-wait (week 4).

Choosing consistency per use case:
| Use case | Needs | Why |
|---|---|---|
| Account balance, payment ledger, inventory decrement, unique username | Strong (linearizable / serializable) | invariant violations cost money |
| Social feed, like counts, view counters, recommendations | Eventual | stale is harmless |
| User's own profile edit, own post | Read-your-writes | UX: "my change vanished" |
| Chat message order within a conversation | Causal / per-conversation ordering | replies before questions look broken |
| Shopping cart | Eventual with merge (Dynamo) | availability beats perfect accuracy; reconcile at checkout |
| Config / leader / lock | Linearizable (etcd) | correctness of coordination |

Practical patterns for getting "enough" consistency cheaply:
- Route reads that must be fresh to the leader; everything else to replicas.
- Version numbers / ETags / compare-and-set (optimistic concurrency) to avoid lost updates.
- Idempotency keys (week 3) so retries do not double apply.
- Single-writer per entity (partition by entity id; actor-like) turns a distributed problem into a local one.

---
## 7. Real-world systems cheat tour

- **Amazon Dynamo (2007 paper)** / **Cassandra**: consistent hashing + vnodes, leaderless, quorum (N,R,W), sloppy quorum + hinted handoff, read repair, Merkle-tree anti-entropy, gossip membership, vector clocks (Dynamo) vs LWW timestamps (Cassandra). LSM storage. Strengths: write availability, multi-DC. Weakness: no joins, tombstone/compaction ops pain, LWT slow, hot partitions, wide partitions >100MB (guidance; check docs) hurt.
- **DynamoDB (managed service)**: partition key hash + sort key; automatic splitting; on-demand vs provisioned capacity; GSI/LSI; Streams (CDC); transactions (limited); global tables (multi-region, LWW). Great fit when access patterns are known. See ../../07-aws/week-03-storage-databases.
- **Spanner**: range-partitioned "splits", each a Paxos group (leader + replicas across zones/regions); TrueTime (GPS + atomic clocks, bounded uncertainty epsilon of a few ms) to assign commit timestamps and "commit-wait" for external consistency; SQL; 2PC across Paxos groups for multi-split txns. Cost: write latency includes cross-zone/region consensus.
- **Kafka**: topic partitions with single-leader replication; ISR (in-sync replica set); `acks=all` + `min.insync.replicas=2` for durability; consumer reads from the log by offset (details in week 3). Illustrates leader-based replication + partition by key for ordering.
- **Redis**: single-leader async replication; Sentinel for failover or Cluster for 16384-slot sharding; async means acknowledged writes can be lost on failover; WAIT command can force replica acks but is not a full guarantee. Use as cache or ephemeral store, not primary of record, unless you accept the risk.
- **Postgres/MySQL**: single-leader, async or sync replicas; sharding via Vitess (YouTube/Slack), Citus, or app-level; Aurora separates compute/storage with 6 copies across 3 AZs and a 4/6 write quorum, 3/6 read quorum (check current docs).
- **etcd/ZooKeeper/Consul**: Raft/ZAB consensus clusters (3 or 5 nodes) for small, critical, strongly consistent metadata. Not for bulk data.
- **MongoDB**: replica set per shard (single-leader, Raft-like election), config servers hold chunk map, mongos routes; hashed or ranged shard keys; shard key choice is effectively permanent (resharding exists in recent versions; check current docs).

---
## 8. Common failure modes (memorize a few)

1. **Replication lag spike**: stale reads, features broken (read-your-writes). Cause: long transaction on follower, heavy write burst, network. Mitigation: monitor lag, route to leader, backpressure.
2. **Split brain** after failover: two leaders; mitigated by quorum-based election and fencing.
3. **Lost acknowledged writes**: async replication + leader crash. Mitigate: sync/semi-sync, acks=all, accept RPO.
4. **Hot partition / hot key**: celebrity, time-series key, low-cardinality GSI. Mitigate: salting, caching, better key.
5. **Resharding storm**: adding nodes triggers data movement that overloads the cluster. Mitigate: throttle, off-peak, vnodes, pre-split.
6. **Scatter-gather tail latency**: p99 of N shards combined (if each has 1% slow, with 100 shards ~63% of requests hit a slow one). Mitigate: hedged requests, fewer shards per query, global indexes.
7. **Thundering herd after node restart**: cold caches, replica catch-up. Mitigate: staged rejoin, warmup.
8. **Clock skew + LWW**: silently dropped writes. Mitigate: logical/hybrid clocks, version vectors, avoid LWW for important data.
9. **Cascading failure from retries** (week 3): retry storms on a degraded shard.
10. **Tombstones** (LSM deletes): mass deletes in Cassandra create tombstones that slow reads; TTL design matters.
11. **Unbounded partitions**: a partition key with ever-growing data (e.g., `PK=tenant`) -> giant partition; bucket by time.
12. **Schema/index migration lock** on a huge table: use online migration tools (gh-ost, pt-osc, CONCURRENTLY).

---
## 9. How interviewers probe this topic

- "Which database and why?" -> They want access patterns, read/write ratio, consistency needs, scale numbers (QPS, GB), NOT brand names. Always quantify (week 1 estimation): 50K writes/s with 1KB rows = 50MB/s, ~4TB/day -> outgrows a single node -> partition.
- "How do you shard? What is the shard key?" -> propose key, justify cardinality + access pattern, name the downside (cross-shard queries), name hot-key mitigation, explain rebalancing (consistent hashing/fixed partitions).
- "What happens when a node fails?" -> replication factor, failover/quorum, data loss window (RPO), recovery time (RTO), who detects.
- "Is that strongly consistent?" -> define the model; do not say "yes" for quorum reads without caveats.
- "Explain CAP" -> include P is a given, C=linearizability, per-operation, then PACELC.
- "What if two users edit the same record in different regions?" -> single home region, LWW pitfalls, CRDTs/merge.
- "How would you scale reads? writes?" -> reads: replicas, cache, CDN; writes: partitioning, batching, async/queue (week 3), LSM store.
- Senior signal: say what you would NOT do (do not shard prematurely, do not use quorum as a lock, do not use LWW for money), and mention operational pain (resharding, backups, schema change).
- FDE angle: customers have messy existing data stores; talk about CDC to migrate without downtime, dual writes risks, validating consistency after migration (shadow reads, checksums).

---
## 10. Self-check (answer without notes)
1. Draw single-leader with async followers and name 3 lag anomalies and their fixes.
2. Why does hash mod N fail when N changes? How does consistent hashing with vnodes fix it?
3. N=5, W=3, R=3: what failures are tolerated; is it linearizable? Why not necessarily?
4. Local vs global secondary index trade-offs.
5. One sentence each: CAP, PACELC, linearizable, causal, read-your-writes.
6. Pick consistency models for: bank transfer, tweet likes, chat, shopping cart, leader lock.
7. Design the shard key for: chat history, orders, time-series metrics, multi-tenant SaaS.
