# Week 4 Cheatsheet - Distributed Algorithms

## Core facts
- No shared clock, partial failure, slow == dead (indistinguishable). Timeout = suspicion, not proof.
- FLP: async consensus can't guarantee termination with 1 crash -> real systems keep safety, may lose liveness.
- Majority quorum: N=2f+1 tolerates f. 3 -> 1, 5 -> 2, 7 -> 3. Even sizes are wasteful. Majorities overlap = safety.

## Raft in 10 lines
- States: Follower, Candidate, Leader. Terms are monotonic; max one leader per term.
- Election timeout (randomized) -> candidate, term+1, RequestVote. Vote once per term, only if candidate log >= voter log.
- Leader appends, AppendEntries(prevIndex, prevTerm); followers reject on mismatch; leader overwrites divergence.
- Commit = stored on majority (current term entry). Then apply. Snapshots compact logs.
- Linearizable reads: ReadIndex / lease, not just "ask leader". Stale ex-leader can serve stale reads.
- Used by: etcd (Kubernetes), Consul, CockroachDB, TiKV, Kafka KRaft. ZooKeeper = ZAB. Spanner = Paxos + TrueTime.
- Failure modes: slow disk/fsync -> leader flap; quorum loss; disjoint majorities from bad membership change.

## Paxos in 3 lines
Prepare(n) -> Promise (+ highest accepted value). Proposer must adopt that value. Accept(n,v) -> chosen when majority accepts. Multi-Paxos = stable leader skips phase 1.

## Locks and leaders
- Lease/TTL lock + process pause = two holders. Fix: FENCING TOKEN (monotonic; resource rejects lower).
- Token sources: etcd revision, ZK zxid, Raft index, DB version column. Resource must enforce (CAS).
- Redis SETNX/Redlock: OK for efficiency, not correctness. Prefer: avoid lock (idempotent, CAS, single-writer partition) > DB lock > etcd/ZK + fencing.
- Leader election: lease in etcd/ZK/Consul, K8s Lease, DB conditional write. Stop acting when renewal fails; make work idempotent.

## Time
| Clock | Property | Use |
|---|---|---|
| Wall (NTP) | drifts, can jump back | display, rough TTL; NOT ordering |
| Monotonic | local only, never back | timeouts, durations |
| Lamport | a->b => L(a)<L(b); converse false | total order (with tie-break), cheap |
| Vector | detects concurrency, O(N) | Dynamo/Riak conflict detection |
| HLC | physical + logical | CockroachDB, MongoDB |
| TrueTime | [earliest, latest] + commit wait | Spanner external consistency |
- Lamport: send -> L++; receive T -> L = max(L,T)+1.
- Vector: receive W -> V = max(V,W) componentwise, then V[i]++. Neither <= -> concurrent.
- LWW + wall clock = silent data loss under skew.

## Failure detection and gossip
- Heartbeat timeout (brittle), phi accrual (adaptive; Cassandra, Akka), SWIM (random ping + k indirect pings, suspect -> dead; Consul/Serf).
- Gossip: random peer exchange, O(log N) rounds, push/pull/push-pull. Membership, anti-entropy (Merkle trees).
- Gray failure = alive but broken; use deep health checks and latency outlier ejection.

## Transactions
| | 2PC | Saga |
|---|---|---|
| Atomic | yes | eventual (compensate) |
| Isolation | yes (locks) | no (semantic locks) |
| Blocking | yes if coordinator dies | no |
| Where | inside DB / Spanner-like | microservices |
- 2PC: prepare (durable YES = promise) -> commit/abort. In-doubt blocking. 3PC unused (breaks on partition).
- Saga: local txns + compensations (reverse order). Orchestration (Step Functions, Temporal) vs choreography (events). Steps + compensations idempotent; retry forever; pivot step last; outbox for atomic publish. TCC = Try-Confirm-Cancel.
- Same DB? Just use an ACID transaction.

## CRDTs
- Merge commutative + associative + idempotent -> converge without coordination.
- G-Counter: per-replica slots, merge = max, value = sum. PN-Counter = two G-Counters. G-Set: union. OR-Set: add-wins with unique tags. LWW-Register loses concurrent writes.
- Not for invariants (unique, non-negative). Cost: tombstones/metadata. Used in Redis Active-Active, Riak, Akka, collab editors.

## Probabilistic structures
- Bloom: no false negatives. FPR ~ (1-e^(-kn/m))^k. k = 0.69 m/n. 1% ~ 9.6 bits/elem (k~7); 0.1% ~ 14.4 bits/elem (k~10). 100M @1% ~ 120 MB. No delete (counting/cuckoo). Uses: LSM reads, cache penetration, crawler dedupe.
- HyperLogLog: max leading zeros -> 2^z; error 1.04/sqrt(m); Redis 16384 regs ~0.81%, ~12 KB; mergeable (max). PFADD/PFCOUNT/PFMERGE.
- Count-Min Sketch: approximate frequencies (over-estimates), heavy hitters. Merkle tree: find divergence fast. t-digest/HDR: mergeable percentiles (never average percentiles).

## System map
etcd/K8s: Raft | ZK: ZAB, zxid, ephemeral nodes | Kafka: KRaft + ISR | Cassandra: gossip, phi, Merkle repair, bloom, LWW, Paxos for LWT | Spanner: Paxos + 2PC + TrueTime | CockroachDB: Raft per range + HLC | Consul: Raft + SWIM.

## Say-out-loud checklist
1. "Timeouts are guesses, so I design for false positives: idempotency and fencing."
2. "Consensus for small critical metadata, not the data path; it's CP and needs a majority."
3. "I avoid distributed transactions: sagas with idempotent steps and outbox; 2PC only inside systems built for it."
4. "Logical clocks or versions for ordering, never raw wall-clock."
5. "Bloom/HLL trade exactness for orders-of-magnitude memory; I know the error bounds."
