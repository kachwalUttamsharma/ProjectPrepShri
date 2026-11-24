# Week 4 - Interview Q&A: Distributed Algorithms

Cover the answer, say it aloud in ~60-90 seconds, then compare. Numbers marked "check current docs" may change.

---
**Q1. What problem does consensus solve, and why is it hard?**
Getting nodes to agree on a value or ordered log despite crashes, delays, and message loss. Hard because you cannot distinguish a slow node from a dead one (FLP: no deterministic algorithm guarantees termination in a fully asynchronous system with a crash). Practical protocols (Paxos, Raft) always preserve safety and sacrifice liveness only during bad network periods, using timeouts and randomization.

**Q2. Why do consensus clusters use odd sizes (3 or 5)?**
Majority quorum is floor(N/2)+1. N=3 tolerates 1 failure; N=4 still tolerates only 1 (majority 3) but needs more acks; N=5 tolerates 2. Even sizes add cost without fault tolerance and can split into two equal halves with no majority. More than 5-7 nodes slows writes with no extra throughput.

**Q3. Explain Raft leader election.**
Followers expect heartbeats. On randomized election timeout, a follower becomes candidate, increments the term, votes for itself, sends RequestVote. Each node votes once per term, and only for a candidate whose log is at least as up-to-date. Majority wins and starts heartbeats. Randomized timeouts avoid repeated split votes. A node seeing a higher term steps down.

**Q4. How does Raft replicate a log entry and when is it committed?**
Client request goes to leader, which appends it locally and sends AppendEntries (with prevIndex/prevTerm for a consistency check) to followers. Followers reject on mismatch and the leader backs up and overwrites divergent entries. Once a majority stores the entry (in the leader's current term), it is committed; the leader applies it and followers learn commitIndex in later messages.

**Q5. How does Raft guarantee a new leader has all committed entries?**
The election restriction: voters only grant votes to candidates whose log is at least as up-to-date (higher last term, or same term and longer). A committed entry is on a majority; any winning candidate needs a majority; the two majorities overlap, so the winner's log contains every committed entry.

**Q6. Paxos vs Raft - what is the intuition difference?**
Both rely on overlapping majorities. Paxos (single-decree) has Prepare/Promise to discover any possibly chosen value and Accept to choose; Multi-Paxos adds a stable leader for a log. Raft is Multi-Paxos-like but specified as a complete, understandable system: strong leader, terms, explicit log matching, membership changes. Raft is easier to implement correctly; Paxos variants are used in Spanner, Chubby.

**Q7. What happens if the Raft leader is partitioned from the majority?**
The majority side elects a new leader with a higher term and continues. The old leader cannot commit (no majority acks) and, on rejoining, sees a higher term, steps down, and its uncommitted entries are overwritten. Danger: it may serve stale reads before it learns; linearizable reads need ReadIndex/leader-lease checks.

**Q8. When should you not use consensus?**
Not on the bulk data path or for high-throughput writes where a single leader and majority round trips are a bottleneck, or for data tolerating eventual consistency (counters, likes - use CRDTs/quorum). Use it for small critical metadata: leader election, configs, locks, shard maps. Cross-region consensus costs tens to 100+ ms per write.

**Q9. How do you implement leader election in a service using existing tools?**
Take a lease in etcd/ZooKeeper/Consul (or a conditional write in DynamoDB/DB row, or a Kubernetes Lease): create a key with TTL, renew periodically; others watch. Stop acting when renewal fails. Because a paused leader may still believe it is leader, include a fencing token/epoch in downstream operations and make the work idempotent.

**Q10. Why is a Redis SETNX lock not safe for correctness?**
TTL-based locks can expire while the holder is paused (GC, VM stall, network delay); a second client acquires; the first resumes and writes. Also failover of async-replicated Redis can lose the lock. It gives no monotonic token. Fine for efficiency (avoid duplicate work), not for protecting invariants unless the resource enforces fencing.

**Q11. What is a fencing token and how does it fix this?**
A monotonically increasing number issued with each lock grant (etcd revision, ZooKeeper zxid, Raft index). The protected resource tracks the highest token seen and rejects requests with lower tokens, so a stale holder's write is refused. The resource must perform the check, typically a conditional write or version compare-and-set.

**Q12. Why can't you trust wall-clock timestamps to order events across machines?**
Clocks drift and skew (NTP gives ms-level error, can step backward). Two events 5 ms apart on different machines may get reversed timestamps. Last-write-wins on wall-clocks silently drops writes. Use logical clocks (Lamport/vector/HLC), per-key versions, or bounded-uncertainty clocks like Spanner's TrueTime with commit wait. Use monotonic clocks for local timeouts.

**Q13. Lamport clock vs vector clock?**
Lamport: single counter; on receive set to max(local, received)+1. If a happens-before b then L(a) < L(b), but L(a) < L(b) does not imply causality, so it cannot detect concurrency. Vector clock: a counter per node; compare component-wise; if neither dominates the events are concurrent, which enables conflict detection (Dynamo/Riak) at O(N) space per timestamp.

**Q14. Given A=[2,1,0] and B=[1,2,0], what is their relation?**
Neither is component-wise <= the other (2>1 in first slot, 1<2 in second), so they are concurrent: conflicting writes that must be merged (app logic, CRDT) or resolved via LWW with data loss risk.

**Q15. How does gossip work and what is it good for?**
Each node periodically exchanges state with random peers; information spreads exponentially, reaching all N nodes in O(log N) rounds with high probability. It gives scalable, decentralized membership, failure info, and anti-entropy (Cassandra, Consul/Serf, Redis Cluster). Tradeoffs: only eventual convergence, redundant messaging, harder to bound latency.

**Q16. How are failures detected, and why is it imperfect?**
Heartbeats with timeouts, or adaptive detectors (phi accrual in Cassandra/Akka) and SWIM (random ping, indirect ping via k peers, suspect state, then dead). In asynchronous networks you cannot tell slow from dead, so detectors have false positives/negatives and gray failures (responds to pings but broken). Mitigate with suspicion states, indirect probes, deep health checks, and designing for false positives (idempotent failover, fencing).

**Q17. Explain 2PC and its main weakness.**
Phase 1 prepare: participants durably vote and lock; phase 2: coordinator decides commit/abort and broadcasts. Weakness: blocking - if the coordinator fails after votes, participants hold locks in-doubt and cannot decide alone. Also high latency, requires all participants up, and lock contention. Mitigation: replicate coordinator state with consensus (Spanner). 3PC avoids blocking only under crash-only assumptions and fails under partitions, so it is not used.

**Q18. 2PC vs saga - when do you choose each?**
2PC: strict atomicity and isolation inside one system built for it (single DB engine, Spanner/CockroachDB internals), short transactions. Saga: cross-service business flows; local transactions with compensating actions, no cross-service locks, eventual consistency, better availability, but no isolation and compensations to design (idempotent, retryable, semantic undo). Orchestration (Step Functions, Temporal) for visibility; choreography for small flows.

**Q19. In a saga, what if a compensation fails?**
Compensations must be idempotent and retried with backoff indefinitely, backed by durable saga state (orchestrator log). If still stuck, route to dead-letter/manual intervention with alerts. Design steps ordered so the riskiest/non-compensatable action (pivot, e.g. shipping) comes last, and use pending/semantic locks to hide intermediate state.

**Q20. What is a CRDT and where would you use one?**
A replicated data type whose merge is commutative, associative, and idempotent, so replicas converge without coordination (G-Counter: element-wise max, sum; OR-Set; LWW-Register; sequence CRDTs for text). Use for multi-region counters, presence, shopping carts, collaborative editing, offline-first apps. Not for invariants needing coordination (unique constraints, non-negative balance). Costs: metadata/tombstone growth.

**Q21. How does a Bloom filter work and how do you size it?**
Bit array of m bits and k hashes; insert sets k bits; query says "maybe" if all set, "no" if any unset. No false negatives. FPR ~ (1-e^(-kn/m))^k; optimal k ~ 0.69 m/n; about 9.6 bits per element for 1% and 14.4 for 0.1%. 100M items at 1% ~ 120 MB. Use before expensive lookups (LSM SSTables, cache-penetration guard); needs a real check on "maybe"; cannot delete (use counting/cuckoo filters).

**Q22. How does HyperLogLog estimate distinct counts?**
Hash items; track the maximum number of leading zeros per register (bucketed by first bits); 2^(max zeros) estimates cardinality; combine many registers with a harmonic mean. Error ~1.04/sqrt(m); Redis uses 16384 registers, ~0.81% error, up to ~12 KB. Mergeable via register-wise max, so it fits distributed unique-count (daily uniques, union across shards). Can't enumerate or delete.

**Q23. Design: run a nightly job exactly once across 10 replicas.**
Pick a leader via lease in etcd/DB conditional write, or let a scheduler (Kubernetes CronJob, EventBridge) trigger one execution. Accept that "exactly once" is really at-least-once with idempotent work: use an idempotency key (job-date), record completion in a DB with a unique constraint, and fence side effects with a token. Alert if no run completes.

**Q24. A hot-path write must be atomic across a payments service and an inventory service. What do you do?**
Avoid dual writes. Prefer a saga: reserve inventory (pending, TTL), charge with idempotency key, confirm or compensate; use the outbox pattern to publish events atomically with local state. If both resources sit in one database, use a normal ACID transaction. Mention 2PC only to explain why you rejected it (blocking, coupling).
