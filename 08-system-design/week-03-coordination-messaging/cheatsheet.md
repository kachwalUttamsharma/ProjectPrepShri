# Week 3 Cheatsheet - Coordination and Messaging

## Queue vs log
- Queue (SQS/RabbitMQ): task, deleted on ack, competing consumers, visibility timeout, DLQ, no replay.
- Log (Kafka/Kinesis): fact, retained, partitioned, per-group offsets, replay, order per partition.
- Scaling: consumers <= partitions per group. Order only within a partition/key.

## Kafka one-liners
- Key -> hash -> partition. Leader + followers; ISR. `acks=all` + `min.insync.replicas=2` + RF=3 = durable.
- `enable.idempotence=true` dedups producer retries; transactions + read_committed = Kafka-to-Kafka EOS.
- Commit offset AFTER processing = at-least-once; BEFORE = at-most-once.
- Retention default ~7 days (check current docs); compaction keeps latest per key.
- Rebalance pauses processing; avoid with fast poll loops, cooperative rebalancing, static membership.
- Can't reduce partitions; adding partitions remaps keys.
- Lag alarm; oldest-message age is better than depth.

## Delivery semantics
```
 at-most-once  : may lose, no dup       (metrics)
 at-least-once : no loss, may dup       (default) + idempotent consumer
 exactly-once  : = at-least-once + idempotency / atomic txn (effect, not delivery)
```

## Idempotency toolkit
Idempotency-Key header -> store result; unique-constraint dedup row in same txn as effect; upsert / SET not INCR; conditional write (version); TTL >= client retry window; claim key atomically.

## Outbox
Same-txn write of business row + outbox row -> relay (poll SKIP LOCKED or CDC/Debezium) -> broker. At-least-once -> consumers dedup (inbox).

## Backpressure menu
Bounded queue / pull / shed (429, 503 + Retry-After) / drop / durable buffer + autoscale on lag / degrade. Little's Law: L = lambda*W.

## Rate limiters
| Algo | State | Burst | Note |
|---|---|---|---|
| Token bucket | 2 nums | up to B | default; lazy refill |
| Leaky bucket | queue | smoothed | shaping |
| Fixed window | 1 counter | 2x at edge | simplest |
| Sliding log | O(n) | none | exact |
| Sliding counter | 2 counters | ~none | approx, practical |
Distributed: Redis + Lua (atomic), server time, fail-open vs closed, token leasing, per-tier keys, cost-weighted, also cap concurrency.

## Retry rules
- Retry transient + idempotent only; 3-5 attempts; honor Retry-After; retry at ONE layer; retry budget ~10%.
- delay = min(cap, base*2^n); full jitter = random(0, delay).
- Amplification = (k+1)^depth.
- Timeouts: always set; connect vs read; inner < outer; propagate deadlines; timeout != "didn't happen".
- Hedged requests: idempotent reads after ~p95, capped.

## Circuit breaker
CLOSED --(fail rate > X, min volume)--> OPEN --(cool-down)--> HALF-OPEN --(probe ok)--> CLOSED / (fail)--> OPEN. Per dependency + fallback. Bulkhead = isolate pools.

## Failure modes to name
Poison message / head-of-line blocking; rebalance storm; hot partition/key; duplicate after crash between process and commit; dual-write inconsistency; retry storm / metastable failure; thundering herd; silent DLQ; unbounded queue; fail-open limiter overload.

## Say-out-loud template
"I need guarantee G. The failure window is between X and Y. I close it with mechanism M. What remains is limitation L, which is acceptable because ..."

## AWS mapping (see ../../07-aws/week-05-integration-ops-security)
SQS (queue, visibility timeout, DLQ, FIFO groups) | SNS (pub/sub, fan-out to SQS) | EventBridge (event bus, rules) | Kinesis (log, shard ~ partition) | MSK (managed Kafka) | API Gateway throttling (token bucket).
