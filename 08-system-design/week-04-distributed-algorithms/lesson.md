# Week 4 - Distributed Algorithms: Consensus, Time, Coordination, Probabilistic Structures

Time budget: ~3 hrs. Read lesson (1.5h), Q&A aloud (1h), cheatsheet (30 min).
Numbers marked "(check current docs)" change over time; verify before quoting.
Prereqs: Week 2 (replication, quorums, CAP/PACELC) and Week 3 (queues, idempotency). AWS cross-links: `../../07-aws/week-03-storage-databases` (DynamoDB, Aurora), `../../07-aws/week-05-integration-ops-security` (Step Functions = saga orchestrator, SQS/SNS).

---
## 0. Why distributed algorithms are hard

Three facts that make everything in this week necessary:

1. **Partial failure**: some nodes die while others keep running. A single machine is usually all-up or all-down.
2. **Unbounded delay / no shared clock**: you cannot distinguish "slow" from "dead". A timeout is a *guess*.
3. **No shared memory**: nodes only learn about each other via messages, which can be lost, duplicated, delayed, reordered.

```
 Client --request--> Node A ---(no reply within 1s)---> ???
   Possibilities: (a) A crashed before processing
                  (b) A processed it, reply was lost
                  (c) A is just slow (GC pause, network congestion)
   You cannot tell (b) from (a). => idempotency + consensus + careful protocols.
```

System models you should name: **crash-stop** (nodes die and stay dead), **crash-recovery** (nodes restart, keep disk), **Byzantine** (nodes lie; blockchains, not typical datacenter systems). Network models: **synchronous** (bounded delay), **partially synchronous** (usually bounded - what Raft/Paxos assume for liveness), **asynchronous** (no bounds). 

**FLP impossibility (1985)**: in a purely asynchronous network, no deterministic consensus algorithm can guarantee termination if even one node may crash. Practical systems sidestep this: Paxos/Raft always stay *safe* (never disagree) but may lose *liveness* (stall) during bad network periods; they use timeouts and randomization to make progress in practice.

---
## 1. Consensus

### 1.1 The problem
Get N nodes to agree on a value (or an ordered sequence of values) even though some fail. Properties:
- **Agreement**: no two nodes decide different values.
- **Validity**: the decided value was proposed by someone.
- **Termination**: every non-faulty node eventually decides (liveness).
- **Integrity**: decide at most once.

Why you care: "who is leader?", "what is the next log entry?", "who holds this lock?", "what is the committed config?" are all consensus problems. Replicated state machines: if every replica applies the same log in the same order to a deterministic state machine, they end in the same state.

```
 clients --> [Leader] --append entry--> [Follower 1]
                |                       [Follower 2]
                |   entry committed when a MAJORITY has stored it
                v
          apply to state machine (KV store, lock table, metadata)
```

### 1.2 Majority quorums: the core trick
With N = 2f+1 nodes, any two majorities (f+1) overlap in at least one node. So a decision made by a majority will be seen by any later majority. Tolerates f failures.

| Nodes N | Majority | Failures tolerated |
|---|---|---|
| 3 | 2 | 1 |
| 5 | 3 | 2 |
| 7 | 4 | 3 |

Even sizes are wasteful: 4 nodes tolerate 1 (same as 3), 6 tolerate 2 (same as 5). Production clusters (etcd, ZooKeeper, Consul servers) use 3 or 5. More nodes = slower writes (more acks) and no extra throughput; reads can scale only via followers with relaxed guarantees.

### 1.3 Paxos intuition (single-decree)
Roles: proposers, acceptors, learners (often one node plays all). Two phases:

```
 Phase 1 (Prepare/Promise)
   Proposer picks unique, increasing proposal number n.
   Proposer --Prepare(n)--> acceptors
   Acceptor: if n > any n it has promised, PROMISE not to accept proposals < n,
             and report the highest-numbered proposal it already ACCEPTED (if any).
 Phase 2 (Accept/Accepted)
   If proposer got promises from a majority:
      value = value of highest-numbered accepted proposal reported, ELSE its own value
   Proposer --Accept(n, value)--> acceptors
   Acceptor accepts unless it promised a higher n.
   Value is CHOSEN once a majority accepted the same (n, value).
```
Key intuition: phase 1 *discovers* anything that might already have been chosen and forces the new proposer to adopt it - this is why safety holds. Dueling proposers can livelock (each preempts the other); fix by electing a stable leader (**Multi-Paxos**: run phase 1 once, then stream phase-2 accepts for many log slots). Paxos is notoriously hard to implement from the paper; real systems (Chubby, Spanner, Megastore) use Multi-Paxos variants. You rarely need to recite it; you need the intuition: **majorities overlap + higher number wins + adopt prior accepted value**.

### 1.4 Raft (understandable consensus)
Raft decomposes consensus into leader election, log replication, and safety. Used by etcd, Consul, CockroachDB (per range), TiKV, Kafka KRaft (controller quorum), RabbitMQ quorum queues.

Node states: **Follower**, **Candidate**, **Leader**. Time is divided into **terms** (monotonic integers; a term has at most one leader).

```
        timeout, no heartbeat           wins majority votes
 Follower ---------------> Candidate ---------------------> Leader
    ^                         | ^  timeout / split vote:      |
    |   sees higher term      | +-- new election, new term    |
    +-------------------------+<--------- sees higher term ---+
```

**Leader election**
- Followers expect heartbeats (AppendEntries) from the leader. If an **election timeout** (randomized, e.g. 150-300 ms typical; check current docs for etcd defaults) passes, a follower becomes a candidate: increments term, votes for itself, sends RequestVote.
- A node votes for at most one candidate per term, and only if the candidate's log is **at least as up-to-date** (compare last log term, then last index). This guarantees the winner has all committed entries.
- Majority of votes -> leader. Randomized timeouts make split votes rare and quickly resolved.

**Log replication**
```
 index:     1   2   3   4   5
 Leader:  [t1][t1][t2][t2][t3]      <- leader appends, sends AppendEntries(prevIndex, prevTerm, entries)
 Foll A:  [t1][t1][t2][t2][t3]      <- consistency check passes, appends
 Foll B:  [t1][t1][t2]              <- lagging; leader backs up nextIndex and resends
 Foll C:  [t1][t1][t2][t2']         <- diverged (old leader's uncommitted entry): overwritten by leader
 commitIndex = 4 once a majority (Leader, A, + one more having 4) stored index 4 in the CURRENT term rules
```
- Entry is **committed** when stored on a majority; leader then applies it and tells followers via commitIndex.
- Raft never commits entries from previous terms by counting replicas alone; it commits them indirectly when a current-term entry commits (subtle safety rule - worth mentioning if asked about Figure 8 of the paper).
- Log Matching Property: if two logs have an entry with same index and term, all preceding entries are identical.

**Safety summary**: at most one leader per term; leader never overwrites its log; committed entries are in the logs of all future leaders (election restriction).

**Other Raft features**: log compaction via snapshots; membership changes (joint consensus or single-server changes); **leader leases / read index** for linearizable reads without a log write (leader confirms it's still leader by heartbeat quorum); learners/non-voting members.

**Reads in Raft systems**: a stale leader (partitioned, doesn't know it was deposed) could serve stale reads. Linearizable reads require the leader to confirm leadership (ReadIndex) or rely on bounded clock drift (lease reads). etcd offers linearizable (default) vs serializable (local, possibly stale) reads.

**etcd in practice**: backing store for Kubernetes control plane. Recommended small data (a few GB; check current docs for the default quota), SSD with low fsync latency (every commit fsyncs the WAL), odd member count, separate failure domains (AZs). Slow disks -> missed heartbeats -> leader churn -> API server timeouts. That's the classic production failure.

**ZooKeeper** uses ZAB (similar to Raft/Multi-Paxos: leader, epochs, ordered broadcast). **Spanner** uses Paxos groups per shard plus TrueTime for global ordering.

### 1.5 What consensus costs and when NOT to use it
- Latency: at least one round trip to a majority (plus fsync). Cross-region consensus = tens to ~100+ ms per write.
- Throughput bounded by the leader.
- Unavailable without a majority (the C in CAP: consensus systems are CP).
- Use it for *small, critical metadata* (leader, config, locks, shard maps), not for bulk data path. Data path often uses simpler leader-follower or quorum replication, coordinated by a consensus-backed control plane (Kafka controller, HDFS NameNode HA, Bigtable master + Chubby).

### 1.6 Failure modes
- **Split brain**: two nodes both believe they are leader (old leader partitioned). Raft prevents *two committing leaders* via terms/quorum; but the old leader may still *think* it's leader and serve stale reads or send side-effects. Always check term/epoch downstream.
- **Leader flapping**: slow disk/GC/network jitter triggers elections repeatedly; cluster stalls. Tune timeouts; fix root cause.
- **Quorum loss**: 2 of 3 nodes down -> read/write unavailability by design. Recovery may need manual intervention (force new cluster) with data-loss risk.
- **Disk corruption / lying fsync**: breaks safety assumptions.
- **Membership change errors**: adding/removing several nodes at once can create two disjoint majorities (why joint consensus exists).

**How interviewers probe**: "What happens if the leader crashes mid-replication?" "Why 5 nodes and not 4?" "Can a minority partition serve reads?" "How does Raft avoid two leaders?" "Why not use consensus for every write?" Strong answer: tie quorum overlap to safety, state CP tradeoff, and mention leader election timeout + terms.

---
## 2. Leader election

Needed whenever one node must do a singleton job (primary DB, scheduler, cron runner, partition owner).

Approaches:
| Approach | How | Notes |
|---|---|---|
| Consensus-embedded | Raft/Paxos elect leader as part of protocol | Strongest; you get it by using etcd/ZK/Consul |
| Lease via external store | Candidates try to create/renew a key with TTL in etcd/ZK/Consul/Redis/DynamoDB (conditional write) | Easy to use; must handle lease expiry races (see fencing) |
| Bully algorithm | Highest ID wins; nodes with higher IDs preempt | Textbook; assumes reliable failure detection |
| Ring algorithm | Token passed around ring | Textbook |
| Kubernetes Lease objects | `coordination.k8s.io/Lease` for controller leader election | Backed by etcd |
| Kafka | Controller elected via KRaft quorum (older: ZooKeeper); partition leaders picked from ISR | See week 3 |

Lease-based pattern:
```
 loop:
   if I hold lease: renew every TTL/3
   else: try conditional create key "leader" = myId with TTL
   on renewal failure or elapsed time > TTL: STOP acting as leader immediately
```
Risk: process pauses (GC, VM freeze, SIGSTOP) longer than TTL -> it wakes and still thinks it's leader. Use **fencing tokens** (Section 3).

Failure modes: two leaders for a TTL window; thundering herd of candidates on expiry (use watch on predecessor, as in ZooKeeper's sequential-ephemeral recipe); clock skew when TTL measured with wall clocks (use monotonic clocks locally).

**How interviewers probe**: "How do you ensure only one instance runs the nightly job?" Answer: lease/lock in strongly consistent store + fencing/idempotent job, and acknowledge brief overlap is possible so the job must be idempotent.

---
## 3. Distributed locks (and why they're hard)

### 3.1 Naive Redis lock
`SET lock:resource <random-id> NX PX 30000` to acquire; release with a Lua script that deletes only if value matches. Good for **efficiency** (avoid duplicate work), risky for **correctness**.

### 3.2 The core problem: process pauses and delayed messages
```
 Client 1: acquire lock (TTL 30s) ---- long GC pause ---------------- write(X) !!
 Lock service:        lock expires at 30s
 Client 2:                          acquire lock ---- write(X)
 Storage receives Client 2's write, THEN Client 1's stale write -> corruption
```
A lease expiry cannot stop the old holder from acting; the holder cannot reliably know its lock expired (pause happens between "check" and "use").

### 3.3 Fencing tokens
Lock service returns a **monotonically increasing token** with each grant. The *protected resource* (storage) remembers the highest token seen and rejects requests carrying a lower one.

```
 Client 1 gets lock, token 33 ... pauses
 Client 2 gets lock, token 34 -> write(token=34) accepted, storage max=34
 Client 1 wakes -> write(token=33) REJECTED (33 < 34)
```
Requirements: lock service generates monotonic tokens (ZooKeeper zxid / znode version, etcd revision, a Raft log index); the resource must check them (conditional writes / compare-and-set / version column). If the resource cannot check tokens, the lock is only advisory.

Database equivalent: optimistic concurrency `UPDATE ... SET ..., version = version+1 WHERE id=? AND version=?`. DynamoDB: conditional writes. 

### 3.4 Redlock debate
Redlock acquires on N independent Redis nodes (majority). Critique (Kleppmann): depends on bounded clock drift and pauses, provides no fencing token; fine for efficiency, unsafe for correctness. Antirez's reply: with assumptions it's practical. Interview-safe stance: "For correctness I want a consensus-backed lock (etcd/ZooKeeper) with fencing tokens, or better, avoid locks via idempotency/CAS; Redis locks are fine as an optimization."

### 3.5 Options ladder
1. Avoid the lock: idempotent operations, CAS/conditional write, single-writer partitioning (Kafka partition ownership).
2. DB row lock / `SELECT ... FOR UPDATE` / advisory locks if you already have one strongly consistent DB.
3. etcd/ZooKeeper/Consul lock + fencing token.
4. Redis lock for best-effort efficiency only.

Failure modes: lock holder crash (needs TTL/ephemeral node), lock never released (bug), TTL too short (premature expiry) vs too long (slow failover), lock service partition, non-reentrancy/deadlock, herd effect.

**How interviewers probe**: "Is Redis SETNX enough?" "Client holds lock, gets paused - what happens?" -> fencing tokens. "How do you make a cron run once across 10 pods?"

---
## 4. Time and ordering

### 4.1 Physical clocks
- Wall clocks (NTP-synced) drift; typical NTP error ms to tens of ms over internet, sub-ms in good datacenters with PTP (check current docs). They can jump backward (NTP step, leap second smear). Never use wall clock to order events across machines or as a lock validity proof.
- Monotonic clocks (`time.monotonic()` in Python): never go backward; only meaningful on one machine; use for timeouts/durations.
- **Last-write-wins (LWW)** with wall clocks silently loses writes under skew (Cassandra default conflict resolution uses timestamps; DynamoDB global tables use LWW).
- **Google TrueTime** (Spanner): API returns an interval [earliest, latest] using GPS + atomic clocks; Spanner waits out the uncertainty ("commit wait", a few ms) to guarantee external consistency (linearizable transactions globally). Alternatives: hybrid logical clocks (HLC) in CockroachDB/YugabyteDB; AWS Time Sync Service gives microsecond-ish accuracy on supported instances (check current docs).

### 4.2 Happens-before and Lamport clocks
Event a **happens-before** b (a -> b) if: same process and a before b; or a is send and b is the receive of that message; or transitive. Events not related are **concurrent**.

Lamport clock rules: each process keeps counter L.
1. Before local event or send: L = L + 1 (send carries L).
2. On receive of timestamp T: L = max(L, T) + 1.

Worked example:
```
 P1:  a(1) ---send m1(1)-----------------> 
 P2:                 b(1)    c: recv m1 -> L=max(1,1)+1 = 2, then d(3) send m2(3)
 P3:                                          e(1)   f: recv m2 -> L=max(1,3)+1 = 4
 Timeline timestamps: a=1, b=1, c=2, d=3, e=1, f=4
```
Property: a -> b implies L(a) < L(b). The converse is false: L(b)=1 and L(a)=1 are equal, L(e)=1 < L(c)=2 yet e and c are concurrent. Tie-break by process ID to get a total order (used for total-order broadcast, distributed mutual exclusion). Lamport clocks cannot *detect* concurrency.

### 4.3 Vector clocks
Each process keeps a vector V[1..N]. 
- Local event/send: V[i]++ (send carries V).
- Receive with vector W: V[j] = max(V[j], W[j]) for all j, then V[i]++.

Compare: V1 <= V2 if every component <=. V1 < V2 means a -> b; if neither <=, events are **concurrent**.

Worked example (3 nodes A,B,C):
```
 A: write x=1        A:[1,0,0]
 B: reads A's write  B:[1,1,0]   (after receiving [1,0,0]: max -> [1,0,0], B++ -> [1,1,0])
 C: independent write x=2   C:[0,0,1]
 Compare [1,1,0] vs [0,0,1]: neither dominates -> CONCURRENT -> conflict, app/CRDT must merge
 Compare [1,0,0] vs [1,1,0]: first <= second -> causal predecessor, safe to overwrite
```
Used by Dynamo (original paper; shopping-cart conflict -> client merge), Riak (dotted version vectors). Cost: vector grows with number of writers; mitigations: pruning, dotted version vectors, per-key vs per-node actors. DynamoDB (the AWS service) does not expose vector clocks; Cassandra uses timestamps.

Version vectors vs vector clocks: version vectors track versions of data replicas; vector clocks track events across processes. Often used interchangeably in interviews; note nuance if asked.

### 4.4 Hybrid logical clocks (brief)
HLC = (physical time, logical counter): stays close to wall time but preserves causality like Lamport. Used by CockroachDB, MongoDB (cluster time), YugabyteDB.

**How interviewers probe**: "Why not just use timestamps?" (skew, LWW loses data). "Lamport vs vector clock?" (Lamport: causal implies order, not converse; vector: exact concurrency detection at O(N) space). "How does Spanner get global ordering?" (TrueTime + commit wait).

---
## 5. Failure detection and gossip

### 5.1 Failure detectors
Perfect detection is impossible in asynchronous systems; detectors are **unreliable**: can have false positives (alive node declared dead) and delays.
- **Heartbeat + timeout**: simple; fixed timeouts are brittle (too short = false positives during GC/network blip; too long = slow failover).
- **Phi accrual failure detector** (Cassandra, Akka): outputs a suspicion level phi based on the statistical distribution of heartbeat inter-arrival times; threshold (Cassandra `phi_convict_threshold`, commonly ~8; check current docs) adapts to network conditions.
- **SWIM** (Consul/Serf, memberlist, Hashicorp): each node periodically pings a random peer; on no ack, asks k other nodes to ping indirectly (ping-req) before marking **suspect**, then **dead** after a timeout. Constant per-node load regardless of cluster size, lower false positive rate via indirect probes. Membership updates piggyback on ping messages.

### 5.2 Gossip (epidemic) protocols
Each round, every node picks random peer(s) and exchanges state. Information spreads exponentially: O(log N) rounds to reach all nodes with high probability.

```
 round 0:  [A]                      informed = 1
 round 1:  A->B                     informed ~ 2
 round 2:  A->C, B->D               informed ~ 4
 round k:  ~ 2^k                    => ~log2(N) rounds (plus tail)
```
Styles: push, pull, push-pull (fastest convergence). Uses: cluster membership (Cassandra, Consul, Redis Cluster bus), anti-entropy of replica state (Dynamo/Cassandra Merkle-tree repair), aggregate computation, failure propagation.
Pros: scalable, decentralized, robust, no single point of failure. Cons: eventual (not immediate) convergence, redundant messages, hard to reason about exact latency, only for state tolerating eventual consistency.

**Anti-entropy with Merkle trees**: replicas compare tree hashes top-down to find divergent key ranges quickly without sending all data (Cassandra repair, Dynamo).

### 5.3 Failure modes
- **Gray failure**: node responds to heartbeats but is functionally broken (disk stuck, partial network). Detectors say "healthy". Mitigation: deep health checks, outlier detection, client-side latency-based ejection.
- **Flapping membership** from false positives -> rebalance storms. Use suspect state, hysteresis.
- **Asymmetric partitions**: A sees B, B doesn't see A.

---
## 6. Distributed transactions: 2PC, 3PC, sagas

### 6.1 Two-phase commit (2PC)
Coordinator + participants (resource managers).
```
 Phase 1: PREPARE   Coordinator --"can you commit?"--> all participants
                    Each: write to durable log, take locks, reply YES/NO (a YES is a PROMISE)
 Phase 2: COMMIT    If all YES: coordinator logs decision, sends COMMIT; else ABORT
                    Participants apply, release locks, ack
```
Guarantees atomic commit across participants. Problems:
- **Blocking**: if the coordinator crashes after participants voted YES but before sending the decision, participants hold locks and *cannot unilaterally decide* until the coordinator recovers (in-doubt transactions). 
- Latency: 2 round trips + multiple fsyncs; locks held across them -> low throughput and contention.
- Availability: needs all participants up (all-or-nothing, not majority).
- Mitigation: make the coordinator highly available by replicating its log with consensus (Spanner: each participant is a Paxos group; 2PC across groups). Percolator/TiDB use 2PC over a KV with a primary-lock trick. XA is the standard API; supported by many RDBMS/message brokers, rarely used in modern microservices.
- **3PC** adds a pre-commit phase to be non-blocking under crash assumptions but is unsafe under network partitions; practically unused. Say this in one line.

2PC is *not* consensus: it needs all votes and a single coordinator; consensus tolerates minority failure. Consensus + 2PC combine in Spanner/CockroachDB.

### 6.2 Sagas
A saga is a sequence of **local transactions**, each with a **compensating action** to semantically undo it if a later step fails. No global locks; eventual consistency.

```
 Book flight --> Reserve hotel --> Charge card --> Issue ticket
     |               |                 |
 Cancel flight   Cancel hotel      Refund card      (compensations run in reverse on failure)
```
Two coordination styles:
- **Choreography**: services emit events and react to each other. Decentralized, simple for 2-3 steps, but flow is implicit and hard to trace/debug; risk of cyclic dependencies.
- **Orchestration**: a central orchestrator (state machine) calls steps and compensations. Explicit flow, easier monitoring and timeouts. Examples: AWS Step Functions, Temporal, Netflix Conductor, Camunda.

Design rules:
- Each step and compensation must be **idempotent** and retryable (week 3).
- Compensations can't always truly undo (sent email, external payment) - design "semantic" undo (refund, cancellation notice).
- Lack of isolation: other transactions see intermediate states (dirty reads) -> countermeasures: semantic locks (PENDING status), commutative updates, re-read values, versioning ("ACID without the I").
- Use **outbox pattern** so state change + event publish are atomic (week 3).
- Handle the "pivot transaction" (point of no return) and retriable steps after it.

### 6.3 2PC vs saga

| Aspect | 2PC | Saga |
|---|---|---|
| Atomicity | Strict (all or nothing) | Eventual, via compensation |
| Isolation | Yes (locks held) | No (intermediate states visible) |
| Availability | Lower; blocking | Higher |
| Latency/lock time | Locks across network round trips | Short local txns |
| Coupling | Participants must support XA/prepare | Any service with APIs |
| Complexity | In protocol | In app logic (compensations) |
| Use | Within one DB / one trust domain, Spanner-like systems | Microservices, long-running business flows |

Decision line: "Keep a transaction inside one database when possible (cheap, ACID). Across services, prefer sagas with idempotent steps and outbox. Use 2PC only inside a system built for it."

### 6.4 Other patterns
- **Transactional outbox + CDC** (Debezium) for reliable event publishing.
- **TCC (Try-Confirm-Cancel)**: reserve resources (Try), then Confirm or Cancel; like application-level 2PC with timeouts. Common in payments.
- **Deterministic databases** (Calvin/FaunaDB) - ordering before execution; mention only if asked.
- **Spanner**: externally consistent distributed transactions: Paxos groups + 2PC + TrueTime.

**How interviewers probe**: "Transfer money between two services' DBs" -> reject dual writes; discuss 2PC blocking, saga + compensation + idempotency keys; "What if the compensation fails?" -> retry forever with backoff, dead-letter, human alert; "How do you see saga state?" -> orchestrator state store.

---
## 7. CRDTs (introduction)

**Conflict-free Replicated Data Types**: data structures whose replicas can be updated independently, without coordination, and are guaranteed to converge when they exchange state, because merge is **commutative, associative, idempotent** (a join-semilattice).

Two families:
- **State-based (CvRDT)**: replicas ship full (or delta) state; merge = join/least upper bound (e.g. element-wise max). Tolerates duplicated/reordered delivery.
- **Operation-based (CmRDT)**: ship operations; requires reliable causal delivery, ops commutative.

Examples:
```
 G-Counter (grow-only), one slot per replica:
   A: [3,0,0]   B: [0,2,0]   merge = element-wise max -> [3,2,0], value = sum = 5
 PN-Counter: two G-Counters (increments P, decrements N), value = sum(P)-sum(N)
 G-Set: add-only set, merge = union
 2P-Set: add set + tombstone set (cannot re-add)
 OR-Set (observed-remove): each add tagged with unique id; remove deletes only observed tags
                           -> concurrent add and remove: add wins
 LWW-Register: (value, timestamp), merge = higher timestamp (loses a concurrent write)
 Sequence CRDTs (RGA, Logoot, Yjs/Automerge) power collaborative text editing
```
Where used: Redis Enterprise/Active-Active (CRDB), Riak data types, Azure Cosmos DB (conflict resolution options), Akka Distributed Data, Figma/Notion-style collaboration (some use CRDT-inspired or OT approaches), AntidoteDB.

Tradeoffs: always-available writes and convergence, but limited data types, metadata growth (tombstones, per-replica vectors; need garbage collection), semantics may surprise (add-wins). Not suitable for invariants such as "balance >= 0" or unique usernames - those need coordination. Alternative: **Operational Transformation** (Google Docs) needs a central server.

**How interviewers probe**: "Design a like counter across regions" -> PN-counter/G-counter with async merge; "Collaborative editor" -> OT vs CRDT; "When can't you use CRDT?" -> invariants needing coordination.

---
## 8. Probabilistic data structures

### 8.1 Bloom filter
Set membership: answers "definitely not in set" or "probably in set". **No false negatives; false positives possible.** No deletion (standard version).

Structure: bit array of m bits, k hash functions. Insert: set k bits. Query: all k bits set -> "maybe".
```
 m = 16 bits, k = 3
 insert "cat": h1=2 h2=7 h3=11  -> set bits 2,7,11
 insert "dog": h1=5 h2=7 h3=14  -> set bits 5,7,14
 query "eel": h = 2,5,14 -> all set -> FALSE POSITIVE (never inserted)
 query "owl": h = 3,... bit 3 is 0 -> definitely not present
```
Math: with n items, false-positive rate p ~ (1 - e^(-kn/m))^k. Optimal k = (m/n) ln2 ~ 0.693 m/n. Bits per element for target p: m/n = -ln(p)/(ln2)^2 ~ 1.44 log2(1/p).
- p = 1% -> ~9.6 bits/element, k ~ 7.
- p = 0.1% -> ~14.4 bits/element, k ~ 10.
Worked example: 100M URLs at 1% FPR -> 100M x 9.6 bits = 960 Mbit ~ 120 MB. A hash set would need several GB.

Uses: LSM-tree SSTable lookups avoid disk reads for absent keys (Cassandra, HBase, RocksDB, Bigtable); "have we seen this URL?" in crawlers; cache-penetration protection (check bloom before DB for nonexistent keys); Chrome safe-browsing early versions; deduping events.
Variants: **Counting Bloom** (supports delete), **Cuckoo filter** (supports delete, better space at low FPR), **Scalable Bloom** (grows). Filter can't be resized without rebuilding; saturates if n exceeds design.
Failure mode: overfilled filter -> FPR rises sharply; you must size for peak n.

### 8.2 HyperLogLog (cardinality estimation)
Count distinct elements using tiny memory. Intuition: hash each item to a uniform bit string; if the longest run of leading zeros seen is z, then roughly 2^z distinct items were seen (like getting z heads in a row suggests ~2^z flips). One estimator is noisy, so split into m = 2^p registers by the first p bits ("stochastic averaging") and combine with a harmonic mean.
- Standard error ~ 1.04 / sqrt(m). Redis uses 16384 registers (m = 2^14) -> ~0.81% std error in ~12 KB max (6 bits/register); `PFADD`, `PFCOUNT`, `PFMERGE`.
- Counts billions of distinct items with a few KB. Mergeable (register-wise max) -> great for distributed aggregation, e.g. unique visitors per day, union across shards.
- Cannot list members, cannot delete, no exact counts, intersection only via inclusion-exclusion (inaccurate).
Used by: Redis, BigQuery `APPROX_COUNT_DISTINCT`, Presto/Trino, Druid, Postgres extension, Elasticsearch cardinality agg.

### 8.3 Related structures (one-liners)
- **Count-Min Sketch**: approximate frequency of items (over-estimates); heavy hitters / top-K trending with a heap.
- **Merkle tree**: hash tree for fast divergence detection (Cassandra repair, Git, blockchains, DynamoDB original).
- **Consistent hashing / rendezvous hashing**: from week 2.
- **t-digest / HDR histogram**: percentile estimation (p99 latency) mergeable across nodes. (Averaging percentiles is wrong!)
- **Skip lists, LSM trees** are not probabilistic estimators but randomized structures; skip.

**How interviewers probe**: "Check if a username is taken among 1B users quickly?" -> bloom filter front, DB confirmation for "maybe"; "Count unique visitors per page per day at scale?" -> HLL per key, merge for week/month; "Top-K trending hashtags?" -> count-min sketch + min-heap, windowed.

---
## 9. Putting it together: real systems map

| System | Consensus / coordination | Time/ordering | Other |
|---|---|---|---|
| etcd / Kubernetes | Raft | revision numbers (monotonic) | leases, watches |
| ZooKeeper | ZAB | zxid | ephemeral nodes, sequential znodes |
| Kafka | KRaft (formerly ZK) controller; ISR replication per partition | offsets per partition | idempotent producer, transactions (2PC-like over partitions) |
| Cassandra | none for data (leaderless quorum); Paxos for LWT | timestamps (LWW) | gossip, phi accrual, Merkle repair, bloom filters |
| DynamoDB (service) | Paxos-based replication per partition (leader per partition; check current docs) | conditional writes, transactions | global tables LWW |
| Spanner | Paxos per split, 2PC across | TrueTime | external consistency |
| CockroachDB | Raft per range | HLC | 2PC-ish parallel commits |
| Redis | Cluster: gossip, epoch-based failover (not strongly consistent); Sentinel | - | HLL, bloom (module), Redlock debate |
| Consul | Raft (servers) + SWIM gossip (Serf) | - | service discovery |

---
## 10. Common mistakes to avoid in interviews
1. Saying "just use a distributed lock" without addressing pauses/fencing.
2. Using wall-clock timestamps to order events across nodes.
3. Treating a timeout as proof of failure (it's only suspicion).
4. Proposing 2PC across microservices without discussing blocking.
5. Choosing an even number of consensus nodes or putting all replicas in one AZ.
6. Claiming exactly-once delivery as free; it's at-least-once + idempotency (week 3).
7. Using consensus on the hot data path when a simpler replication suffices.
8. Forgetting that bloom filters have false positives so a "maybe" needs a real check.

## 11. Self-check (can you do these on a whiteboard?)
- Draw a Raft leader election and log replication with a follower that diverged.
- Show a fencing token preventing a stale write.
- Compute vector clocks for a 3-node scenario and mark the concurrent events.
- Size a Bloom filter for 50M items at 0.1% FPR (answer: ~14.4 bits x 50M = 720 Mbit ~ 90 MB, k ~ 10).
- Compare 2PC and saga for "place order + charge + reserve inventory".
