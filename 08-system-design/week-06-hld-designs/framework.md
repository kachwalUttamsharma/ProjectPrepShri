# HLD Interview Framework

Use the same skeleton for every design question. The goal is not a perfect system. It is to show structured thinking, quantified tradeoffs, and the ability to go deep where the interviewer pushes.

Background lessons: [fundamentals](../week-01-fundamentals/lesson.md), [data and storage](../week-02-data-storage/lesson.md), [coordination and messaging](../week-03-coordination-messaging/lesson.md), [distributed algorithms](../week-04-distributed-algorithms/lesson.md), [architecture and ops](../week-05-architecture-operations/lesson.md).

## 45-minute time split

| Min | Phase | Output on the board |
|---|---|---|
| 0-5 | 1. Clarify requirements | Functional list, non-functional list, explicit out-of-scope |
| 5-10 | 2. Estimate | QPS (avg and peak), storage/year, bandwidth, read:write ratio |
| 10-15 | 3. API + data model | 3-6 endpoints, core entities, primary access patterns, DB choice |
| 15-25 | 4. High-level diagram | Boxes and arrows, one request walked end to end for read and write |
| 25-40 | 5. Deep dives | 2-3 hardest components, chosen with (or by) the interviewer |
| 40-45 | 6. Bottlenecks, failure modes, wrap-up | SPOFs, hot keys, scaling next 10x, monitoring |

If the interviewer is senior, they often steer you into deep dives earlier. Let them. Keep phases 1-4 tight (20 min max).

## The repeatable framework

1. Clarify
   - Who are the users? Scale (DAU, MAU)? Read-heavy or write-heavy?
   - Core features only (pick 3-4). Say what you are deferring.
   - Non-functional: latency target (p99), availability vs consistency preference, durability, data retention, geography, compliance.
2. Estimate
   - DAU x actions/user/day / 86,400 = average QPS. Peak = 2-5x average (state your factor).
   - Storage = records/day x bytes/record x retention. Add replication factor (3x).
   - Bandwidth = QPS x payload size.
   - Cache sizing: 80/20 rule, cache the hot 20% of daily data.
   - Round aggressively. Use 1 day = ~100K seconds (86,400) and 1 month = ~2.5M seconds.
3. API
   - REST or gRPC, resource names, pagination, idempotency keys on writes, auth.
4. Data model
   - Entities, keys, indexes. Drive the DB choice from access patterns, not fashion.
5. High-level design
   - Clients -> CDN/LB -> stateless services -> cache -> DB/queue/blob store. Async paths via queue.
6. Deep dives
   - Pick where the real difficulty lives (ID generation, fan-out, ordering, hot keys, consistency).
7. Bottlenecks and failure modes
   - Single points of failure, thundering herd, hot partition, replication lag, retry storms, region outage.
8. Tradeoffs and evolution
   - What you chose, what you gave up, what you would change at 10x.

## Reusable one-page template (copy to the whiteboard)

```
REQUIREMENTS   FR: 1) 2) 3)    NFR: latency / availability / consistency / durability
OUT OF SCOPE:  ...
ESTIMATES      DAU= ; QPS avg/peak = ; storage/yr = ; bandwidth = ; cache =
API            POST /v1/...   GET /v1/...
DATA           table(pk, sk, ...) ; access patterns: ...
DIAGRAM        client -> LB -> svc -> cache -> db ; async: svc -> queue -> worker
DEEP DIVES     (a) ... (b) ...
RISKS          SPOF, hot key, lag, retries
TRADEOFFS      chose X over Y because ...
```

## What to say out loud

- "Before I design, let me confirm scope and numbers. Is it okay if I assume X?" Stating assumptions explicitly is a signal, not a weakness.
- "This is read-heavy at roughly 100:1, so I will optimize the read path with caching and denormalization."
- "I see two options: A is simpler, B scales better. Given our 10K QPS, A is enough now, and here is the trigger to move to B."
- "The failure mode here is X. I would mitigate with Y and detect it with metric Z."
- "I will park that and come back" when a tangent threatens your time budget.
- Name real systems when relevant: "Kafka for the log, Redis for hot counters, Cassandra or DynamoDB for wide-column writes, Spanner if we need global strong consistency."
- Finish with: "Next I would look at observability, load testing, and capacity planning."

## Handling interviewer probes

| Probe | How to respond |
|---|---|
| "What if this node dies?" | Walk the failure: detection (health check/heartbeat), failover (leader election), data loss window (sync vs async replication), client behavior (retry + idempotency). |
| "Why this database?" | Tie to access patterns, scale, consistency need. Admit the alternative and its cost. |
| "Scale this 100x." | Find the first bottleneck (usually DB writes or a hot key), shard/partition, add caching tiers, async-ify, then move to multi-region. |
| "Is this consistent?" | State the model (strong, read-your-writes, eventual), where it applies, and the user-visible anomaly. |
| "How do you handle duplicates?" | At-least-once delivery plus idempotent consumers (dedupe key). Exactly-once is idempotency in practice. |
| "What would you cut with 1 week?" | Show you can ship an MVP: one DB, one cache, no multi-region. |

## Common mistakes

1. Jumping to the diagram without requirements or numbers.
2. Estimating with false precision, or skipping estimation and later being unable to justify sharding.
3. Buzzword stacking (Kafka, Redis, Cassandra everywhere) without saying why.
4. Ignoring the read/write ratio and access patterns.
5. No failure discussion. Every box needs "what if it fails?"
6. Treating the DB as infinitely scalable, or sharding too early at tiny scale.
7. Not driving: waiting for the interviewer to prompt each step. You lead, they probe.
8. Spending 25 minutes on one component and never finishing the end-to-end flow.
9. Hiding tradeoffs. Every design choice has a cost; name it.
10. Forgetting non-functional topics: security, rate limiting, observability, cost.

## Self-check after each practice session

- Did I state requirements and estimates in under 10 minutes?
- Did I walk one read and one write end to end?
- Did I name at least 3 tradeoffs and 3 failure modes?
- Could I explain every component in one sentence of "why"?
