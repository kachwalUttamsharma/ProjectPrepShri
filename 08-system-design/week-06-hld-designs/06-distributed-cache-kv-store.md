# HLD 6 - Distributed Cache / Key-Value Store

Background: [caching](../week-01-fundamentals/lesson.md), [replication, sharding, consistent hashing, quorum](../week-02-data-storage/lesson.md), [gossip, failure detection, Raft](../week-04-distributed-algorithms/lesson.md). Framework: [framework.md](framework.md).

First ask: **cache (Redis/Memcached-like, memory, lossy OK) or durable KV store (Dynamo/Cassandra-like)?** Clarify; this design covers a Dynamo-style sharded replicated store with a cache mode noted where it differs.

## 1. Requirements
Functional: `get(key)`, `put(key, value, ttl?)`, `delete(key)`; values up to ~1 MB (typically < 10 KB); optional CAS/increment.
Non-functional: low latency (p99 < 10 ms), high availability (tolerate node and AZ loss), horizontal scale, tunable consistency, automatic rebalancing. Cache mode: eviction (LRU/LFU), TTL, loss acceptable.

## 2. Estimate
- 10 TB of data, avg value 2 KB -> 5 B keys. With RF=3 -> 30 TB raw. At ~1 TB usable/node (SSD) -> ~30 nodes; memory-only at 128 GB/node -> ~240 nodes (hence caches hold hot subsets).
- 1M ops/s, 90% reads, one node handles ~50-100k simple ops/s (hardware dependent) -> need >= 20 nodes for throughput anyway; plan ~40 for headroom (target 50% utilization).
- Network: 1M ops/s x 2 KB = 2 GB/s ~ 16 Gbps aggregate across the cluster, fine spread over nodes.

## 3. API
```
GET    /kv/{key}               -> 200 {value, version} | 404
PUT    /kv/{key}  {value, ttl, if_version?}  -> 200 {version} | 409
DELETE /kv/{key}
```
Client library does routing (smart client) or any node can coordinate (Dynamo/Cassandra). Binary protocol in practice.

## 4. Data model
`key -> (value bytes, version/vector clock or timestamp, ttl, tombstone flag)`.
Storage engine per node: in-memory hash table (cache) or LSM tree (memtable + WAL + SSTables + compaction; write-optimized, as in Cassandra/RocksDB) vs B-tree (read-optimized).

## 5. Architecture
```
 Client lib / coordinator
      | hash(key)
      v
   Consistent-hash ring with virtual nodes (e.g. 256 vnodes/node)
   key K -> first N=3 distinct physical nodes clockwise (preference list)

        [Node A]----[Node B]----[Node C] ...   gossip (membership, health)
          | WAL + memtable -> SSTables (LSM)
          | hinted handoff, read repair, anti-entropy (Merkle trees)

 Write: coordinator -> N replicas in parallel; ack after W succeed
 Read : coordinator -> R replicas; return newest; repair stale ones
 Quorum: R + W > N  (N=3,W=2,R=2) gives overlap
```

## 6. Deep dives
**Partitioning.** Consistent hashing with virtual nodes: adding/removing a node moves ~1/N of keys; vnodes smooth load and let heterogeneous hardware take proportional shares. Alternative: fixed number of hash slots (Redis Cluster uses 16384) mapped to nodes - simpler rebalancing by moving slots.
**Replication and consistency.** Leaderless quorum (Dynamo/Cassandra): tunable N/R/W. Leader-per-shard with Raft/Paxos (etcd, Spanner, CockroachDB): linearizable but a leader election pause on failure. Choose by requirement (AP vs CP; see CAP/PACELC in week 2).
**Conflicts.** Concurrent writes to the same key on different replicas: last-write-wins by timestamp (simple, can lose writes, clock skew) vs vector clocks returning siblings to the client (Dynamo) vs CRDTs for counters/sets.
**Failure handling.** Failure detection via gossip + phi-accrual. Sloppy quorum + hinted handoff: write to a stand-in node and hand back later. Read repair fixes stale replicas on read; Merkle-tree anti-entropy fixes cold data in background. Permanent loss: re-replicate from surviving replicas (streaming).
**Hot keys.** One key can saturate a shard. Mitigations: client-side/near cache, replicate hot key to more nodes, key splitting (`key#0..k` for counters), request coalescing.
**Cache mode specifics.** Eviction (LRU approximate sampling as Redis, LFU, TinyLFU admission), TTL with lazy + active expiry, memory fragmentation. Patterns: cache-aside, stampede protection (single flight, locks, probabilistic early refresh, jittered TTL). Warm-up after restart. Persistence optional (snapshot/AOF) - state your durability stance.
**Rebalancing.** Join: new node bootstraps ranges via streaming while old owners still serve; throttle to protect foreground traffic. Avoid moving everything at once; one node at a time.
**Durability.** WAL fsync policy (every write vs every second) is a latency/durability tradeoff. Multi-AZ replica placement (rack/AZ aware) so a preference list never sits in one AZ.
**Multi-region.** Async cross-region replication (LWW or CRDT) vs synchronous consensus (Spanner-style, higher write latency); check current vendor docs for global-table semantics.

## 7. Bottlenecks and failure modes
- Hot shard/key; large values blocking the event loop; compaction storms causing latency spikes; GC pauses (JVM) mimic failures -> false suspicion; split brain under partition (quorum prevents conflicting majorities); tombstone buildup; cascading rebalancing during overload; thundering herd on cache miss after node loss (cold cache hits DB).

## 8. Tradeoffs
- CP (linearizable, unavailable minority side) vs AP (always writable, reconcile later).
- Smart client (fewer hops, harder upgrades) vs proxy/coordinator (simple clients, extra hop).
- Memory (fast, expensive, volatile) vs SSD LSM (cheaper, higher tail latency).
- LWW (simple) vs vector clocks (correct, burdens client).
- Higher RF (durability, cost, write amplification).

## 9. What to say out loud
"First: cache or durable store? I will design a Dynamo-style store. I partition with consistent hashing and virtual nodes, replicate to N=3 across AZs, and use quorums with R+W>N for tunable consistency. Failures are handled by gossip detection, hinted handoff, read repair and Merkle anti-entropy. Conflicts use LWW by default; I would note its data-loss risk and offer vector clocks or CRDTs. Hot keys are my main operational concern."

## 10. Follow-ups
- Walk through a node failure during a write at W=2. (hinted handoff, sloppy quorum)
- How do you guarantee read-your-writes? (R+W>N, sticky routing, version tokens)
- How would you add transactions? (per-key CAS cheap; multi-key needs consensus/2PC; see week 4)
- Why can quorum reads still return stale data? (sloppy quorums, concurrent writes, failed partial writes)
- How is this different from Redis Cluster? (slots, async replication, leader per shard, can lose acked writes on failover)
