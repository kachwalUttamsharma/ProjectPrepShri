# Week 3 - Coordination and Messaging: Queues, Logs, Delivery Semantics, Resilience Patterns

Time budget: ~3 hrs. Read lesson (1.5h), Q&A aloud (1h), cheatsheet (30m).
Numbers marked "(check current docs)" change over time; verify before quoting.
AWS cross-link: [../../07-aws/week-05-integration-ops-security](../../07-aws/week-05-integration-ops-security) covers SQS, SNS, EventBridge, Kinesis as managed products. This week is the concepts underneath.

Contents
1. Why messaging at all
2. Queues vs logs
3. Kafka concepts
4. Delivery semantics
5. Idempotency
6. Outbox pattern
7. Pub/sub and fan-out
8. Backpressure
9. Rate limiting algorithms
10. Timeouts, retries, backoff, jitter
11. Circuit breakers (and bulkheads)
12. Putting it together
13. How interviewers probe this

---
## 1. Why messaging at all

Synchronous call chain:

```
 Client -> API -> Payment -> Inventory -> Email -> Analytics
 availability = product of availabilities (0.999^5 ~ 0.995)
 latency      = sum of latencies
 any slow dependency stalls the caller
```

Asynchronous with a broker:

```
 Client -> API -> [ broker ] --> Payment worker
                      |------> Email worker
                      |------> Analytics worker
```

What a broker buys you
- Decoupling in time: producer does not need the consumer to be up.
- Decoupling in rate: absorbs bursts (a buffer / shock absorber).
- Fan-out: one event, many independent consumers.
- Retry and replay: failed work can be redone; a log can be re-read.
- Independent scaling of producer and consumer fleets.

What it costs you
- Eventual consistency: the user sees "accepted", not "done".
- Duplicates and reordering become your problem (section 4, 5).
- Harder debugging (no single stack trace); need correlation IDs and tracing.
- A new critical component to operate (or pay for).

Rule of thumb: put a queue where the user does not need the result in the same request, or where the downstream is slower / less reliable than the upstream.

---
## 2. Queues vs logs

Two mental models. Interviewers love "SQS vs Kafka".

```
 TRADITIONAL QUEUE (SQS, RabbitMQ)            LOG (Kafka, Kinesis, Pulsar)
 msg is a TASK; consumed = deleted            msg is a FACT; retained for N days
 +-------------------+                        +--------------------------------+
 | m5 m4 m3 m2 m1 | -> worker A (m1)          | offset: 0 1 2 3 4 5 6 7 ...    |
 +-------------------+ -> worker B (m2)       |         ^consumer X at 3       |
 competing consumers; ack removes message     |              ^consumer Y at 6  |
 no replay once acked                         +--------------------------------+
                                              each consumer group tracks its own offset
                                              replay = move the offset back
```

| Aspect | Queue | Log |
|---|---|---|
| After consume | deleted (or hidden until ack/visibility timeout) | retained by time/size policy |
| Consumers | competing; each message to one worker | many independent groups, each sees everything |
| Ordering | best effort (FIFO variants exist, with throughput limits) | strict per partition |
| Replay | no (except DLQ redrive) | yes: reset offset |
| Scaling unit | add consumers freely | consumers <= partitions per group |
| Per-message features | visibility timeout, delay, per-message DLQ, priority (some) | usually none; you build retry topics |
| Best for | job/task distribution, work queues | event streams, CDC, analytics, event sourcing, many consumers |

Visibility timeout (SQS style): a received message is hidden for N seconds; if the worker does not delete (ack) it in time, it reappears. This is the origin of at-least-once: slow worker + short timeout = duplicate processing.

Dead-letter queue (DLQ): after K failed attempts, park the message for inspection. Always alarm on DLQ depth; a silent DLQ is a data-loss bug in slow motion.

---
## 3. Kafka concepts

```
 Topic "orders" (3 partitions, replication factor 3)

 Producer --key hash--> P0: [0][1][2][3][4] ...  leader on broker 1, followers on 2,3
                        P1: [0][1][2][3]   ...  leader on broker 2
                        P2: [0][1][2]      ...  leader on broker 3

 Consumer group "billing" (3 consumers)        Consumer group "search-indexer" (1 consumer)
   C1 <- P0                                      C1 <- P0, P1, P2
   C2 <- P1
   C3 <- P2
```

Core terms
- Topic: named stream. Partition: an ordered, append-only, immutable log; the unit of parallelism and ordering.
- Offset: position of a record within a partition. Order is guaranteed only within a partition, never across partitions.
- Key: producer picks partition via hash(key) % N (default). Same key -> same partition -> ordered per key. Use the entity id (user_id, order_id).
- Broker: server storing partitions. Each partition has a leader (serves reads/writes) and followers (replicate).
- ISR (in-sync replicas): followers caught up with the leader. A write with `acks=all` is acknowledged once all ISR have it; with `min.insync.replicas=2` and RF=3 you tolerate one broker loss without losing acked data.
- Consumer group: set of consumers sharing a topic; each partition assigned to exactly one consumer in the group. More consumers than partitions = idle consumers. Different groups are independent.
- Committed offset: consumer group's progress, stored in the internal `__consumer_offsets` topic. Commit after processing for at-least-once.
- Rebalance: when consumers join/leave, partitions are reassigned; processing pauses (stop-the-world in older protocols; cooperative rebalancing reduces this). Frequent rebalances (slow `poll`, long GC) are a classic production issue.
- Retention: time or size based (default 7 days; check current docs). Log compaction: keep latest record per key (good for changelog / "current state" topics; tombstone = null value deletes).
- Metadata: historically ZooKeeper; modern Kafka uses KRaft (Raft-based controller quorum). Check current docs for versions.

Why Kafka is fast
- Sequential disk appends and reads; OS page cache; batching + compression; zero-copy (sendfile) to consumers. Throughput of hundreds of MB/s per broker is realistic (order of magnitude; check benchmarks).

Partition count tradeoffs
- More partitions = more parallelism and throughput, but more open files, longer leader-election/recovery, more end-to-end latency in some cases, and you cannot decrease it. Changing partition count remaps keys (ordering across the change breaks). Size for future peak: target throughput / per-partition throughput.
- Hot key: one key with huge volume saturates one partition. Mitigate by salting the key (loses strict per-key order) or splitting the entity.

Producer reliability settings (mention by name)
```
 acks=0   fire and forget                    (may lose)
 acks=1   leader acked                       (lose if leader dies before replication)
 acks=all + min.insync.replicas=2 + RF=3     (durable, slightly higher latency)
 enable.idempotence=true   broker dedups retries per (producer id, partition, sequence)
 transactions              atomic writes across partitions + offsets (exactly-once in Kafka->Kafka)
```

Kinesis comparison: shard ~ partition; 1 MB/s or 1000 records/s write per shard (check current docs); managed. SQS FIFO: message groups ~ keys, ordering per group. See the AWS week 5 lesson.

Failure modes
- Consumer lag grows: consumers slower than producers. Fix: scale consumers (up to partition count), speed processing, batch, or add partitions.
- Poison message: one record always fails -> consumer stuck retrying forever, blocking the partition (head-of-line blocking). Fix: bounded retries then send to a dead-letter topic and continue.
- Rebalance storm: consumers exceed `max.poll.interval.ms`, are kicked, rejoin, repeat.
- Unclean leader election: allowing an out-of-sync replica to become leader can lose acked data (availability vs durability choice).
- Duplicate processing after rebalance: offset not committed yet when partition moves.

---
## 4. Delivery semantics

Why this is hard: a network can lose the message OR the ack, and the sender cannot tell which (Two Generals problem). So:

```
 Producer --send--> Broker --deliver--> Consumer --ack--> Broker
       ^  loss here?        ^ loss here?       ^ loss here?
```

- At-most-once: send once, never retry. May lose, never duplicates. (Commit offset BEFORE processing; crash = message skipped.) Fine for metrics, telemetry.
- At-least-once: retry until acked. Never loses, may duplicate. (Commit offset AFTER processing; crash = reprocess.) The default practical choice. Requires idempotent consumers.
- Exactly-once: each message's effect happens once. Truly "exactly-once delivery" over an unreliable network is impossible in general; what we achieve is exactly-once PROCESSING / EFFECT = at-least-once delivery + idempotency (or transactional atomic commit of output and offset).

```
 Consumer loop at-least-once:
   msg = poll()
   process(msg)        # side effect
   commit(msg.offset)  # crash between these two lines => duplicate on restart
```

Kafka "exactly-once semantics" (EOS): idempotent producer + transactions + `isolation.level=read_committed`. It makes the consume-process-produce loop within Kafka atomic (output records and consumer offsets commit together). It does NOT make an external side effect (send an email, charge a card, write to Postgres) exactly-once; for that use idempotency keys or write results and offsets in the same DB transaction.

Ordering interplay: retries can reorder (message 1 fails, 2 succeeds, 1 retried). Kafka producer: `enable.idempotence=true` preserves order with in-flight requests up to 5; without it set `max.in.flight=1` for strict order.

---
## 5. Idempotency

Definition: doing the operation N times has the same effect as doing it once. `SET x=5` is idempotent; `x += 1` is not.

Techniques
1. Natural idempotency: upserts, PUT semantics, "set status=SHIPPED".
2. Idempotency key: client generates a UUID per logical operation, sends it with the request (Stripe style `Idempotency-Key` header). Server stores key -> result; a repeat returns the stored result.
3. Dedup table with unique constraint: insert (message_id) first; if conflict, skip.
4. Versioning / conditional writes: `UPDATE ... WHERE version = 7`, DynamoDB conditional put.

```python
# Idempotent consumer: dedupe + effect in ONE transaction (the crucial part)
def handle(conn, msg):
    with conn:  # BEGIN ... COMMIT
        cur = conn.execute(
            "INSERT INTO processed_messages(id) VALUES (%s) ON CONFLICT DO NOTHING",
            (msg.id,))
        if cur.rowcount == 0:
            return  # duplicate, already applied
        conn.execute("UPDATE accounts SET balance = balance + %s WHERE id = %s",
                     (msg.amount, msg.account_id))
```

```python
# Idempotency-key for an HTTP endpoint (FastAPI-flavoured sketch)
def create_payment(key: str, body: dict):
    row = db.get(key)
    if row:
        if row.request_hash != hash(body):
            raise Conflict("key reused with different payload")  # 422/409
        return row.response           # replay stored response
    # claim the key atomically first (unique constraint), then do work
    db.insert(key, status="in_progress", request_hash=hash(body))
    resp = charge_card(body)
    db.update(key, status="done", response=resp)
    return resp
```

Gotchas
- Race: two concurrent requests with the same key; the unique-constraint claim makes one win, the other waits or gets 409.
- Crash after the side effect but before recording the key -> the effect repeats. Hence record key and effect atomically, or pass the key downstream so the downstream dedups too (Stripe's key to the card network).
- Key TTL: keep long enough to cover client retry windows (24h is common; check each provider).
- Dedup state is bounded: a "seen IDs" set cannot grow forever; use TTL or per-producer monotonic sequence numbers (Kafka idempotent producer uses sequence per partition).

---
## 6. Outbox pattern

Problem: dual write. You must update your DB AND publish an event; there is no transaction spanning both.

```
 BAD:  db.commit();  broker.publish(event)   # crash between => DB changed, no event
 BAD:  broker.publish(event); db.commit()    # crash/rollback => event for state that never existed
```

Solution: write the event to an `outbox` table in the SAME local transaction as the business change; a separate relay publishes it.

```
 +-------------- one DB transaction --------------+
 | INSERT INTO orders ...                         |
 | INSERT INTO outbox(id, topic, key, payload)    |
 +------------------------------------------------+
        |
        v   (poller OR CDC log tailing, e.g. Debezium reading the WAL/binlog)
   relay --publish--> Kafka --> consumers (idempotent!)
        then mark outbox row sent (or delete)
```

- Guarantee: at-least-once publish (relay can crash after publish before marking sent). So consumers must be idempotent; outbox row id doubles as the dedup key.
- Polling relay: simple, adds DB load and latency; use `SELECT ... FOR UPDATE SKIP LOCKED` for multiple relays.
- CDC relay (Debezium): reads the transaction log, low latency, no polling load, preserves commit order.
- Mirror image, the inbox pattern: consumer writes the received message id into an inbox table in the same transaction as its effect (this is exactly the dedup code in section 5).
- Alternative: "listen to yourself" / event sourcing: the log is the source of truth, DB is a projection.

---
## 7. Pub/sub and fan-out

```
 Publisher -> Topic -> Subscription A (queue) -> service A
                    -> Subscription B (queue) -> service B
                    -> Subscription C (push webhook)
```

- Pub/sub: publisher does not know subscribers. Each subscription gets a copy.
- Fan-out with a queue per subscriber (SNS -> many SQS) gives each consumer its own buffer, retries, and DLQ, so a slow subscriber does not hurt others. With Kafka, each consumer group is its own subscription.
- Delivery models: push (broker calls you; needs backpressure signal, retries, auth) vs pull (consumer polls at its own pace; natural backpressure).
- Filtering: by topic hierarchy, attributes, or content (EventBridge rules, SNS filter policies).
- Event types: notification (thin: "order 42 changed", consumer calls back) vs event-carried state transfer (fat: payload has the data, no callback, but schema coupling). Version your schemas (Avro/Protobuf + schema registry; add fields compatibly).
- Ordering and exactly-once do not come free with pub/sub; ask what the product guarantees.

---
## 8. Backpressure

Definition: a mechanism by which a slow consumer signals a fast producer to slow down, so queues do not grow without bound and memory/latency do not explode.

```
 producer 1000/s --> [ queue ] --> consumer 400/s
   queue grows 600/s -> unbounded memory, latency = queue_depth / 400 rises forever
```

Little's Law: L = lambda * W (items in system = arrival rate x time in system). An unbounded queue turns overload into unbounded latency; users time out and retry, making it worse (retry amplification).

Options (pick consciously)
1. Bound the queue and block the producer (TCP window, bounded channels, Reactive Streams `request(n)`).
2. Load shed: reject excess immediately (HTTP 429/503 with `Retry-After`). Prefer failing fast to queuing forever. Shed lowest-priority first.
3. Drop (newest or oldest) when data is lossy/perishable (metrics, video frames).
4. Buffer durably (Kafka) and scale consumers; lag is the explicit signal. Autoscale on lag (KEDA / CloudWatch queue depth).
5. Degrade gracefully: serve cached/stale, disable expensive features.
6. Rate limit at the edge (section 9) and use admission control per tenant.

Signals: queue age (oldest message age) is more useful than depth; alert on it. Pull-based consumers have backpressure built in; push-based need explicit handling.

Failure mode: metastable failure / retry storm. A brief overload causes timeouts, clients retry, load doubles, system never recovers even after the trigger vanishes. Defences: load shedding, retry budgets, jittered backoff, circuit breakers.

---
## 9. Rate limiting algorithms

Goals: protect services, enforce fairness and quotas, control cost (especially LLM APIs billed per token), prevent abuse. Return `429 Too Many Requests` with `Retry-After` and headers like `X-RateLimit-Remaining`.

### 9.1 Token bucket
```
 bucket capacity B tokens, refill rate r tokens/sec
 request costs 1 (or n) tokens; if tokens >= cost: allow, subtract; else reject
 allows bursts up to B, long-run rate r
```
```python
import time

class TokenBucket:
    def __init__(self, rate: float, capacity: float):
        self.rate, self.capacity = rate, capacity
        self.tokens, self.ts = capacity, time.monotonic()

    def allow(self, cost: float = 1.0) -> bool:
        now = time.monotonic()
        self.tokens = min(self.capacity, self.tokens + (now - self.ts) * self.rate)  # lazy refill
        self.ts = now
        if self.tokens >= cost:
            self.tokens -= cost
            return True
        return False
```
Lazy refill: no timer thread; compute from elapsed time. Used by AWS API Gateway, Stripe, many others. Memory: 2 numbers per key.

### 9.2 Leaky bucket
```
 requests enter a FIFO queue (the bucket) of size B; drained at a constant rate r
 full bucket => drop
 output is smooth; no bursts downstream
```
Token bucket = bursty-friendly limiter; leaky bucket = traffic shaper that smooths output. (As a meter, they are mathematically equivalent; as a queue, the leaky bucket adds delay.)

### 9.3 Fixed window counter
```
 key = (user, floor(now / 60)); INCR; if count > limit reject; TTL 60s
```
Simple and cheap. Flaw: boundary burst, up to 2x the limit across a window edge (limit 100 at 00:59 and 100 at 01:00 = 200 in 2 seconds).

### 9.4 Sliding window log
Store a timestamp per request in a sorted set; drop entries older than window; count. Exact, but O(requests) memory per user.

### 9.5 Sliding window counter (approximation)
```
 estimate = prev_window_count * (1 - fraction_into_current) + current_count
```
Two counters per key; smooths the boundary problem; error small in practice (Cloudflare reported very low error; check source). Usual practical choice.

| Algorithm | Memory | Bursts | Accuracy | Notes |
|---|---|---|---|---|
| Token bucket | O(1) | allowed up to B | good | default choice |
| Leaky bucket | O(B) queue | smoothed | good | shaping |
| Fixed window | O(1) | 2x at edges | poor edge | simplest |
| Sliding log | O(n) | none | exact | expensive |
| Sliding counter | O(1) | minimal | approx | good tradeoff |

### 9.6 Distributed rate limiting
- Central store (Redis) with atomic ops. Token bucket must be atomic; use a Lua script or `INCR` + `EXPIRE` pattern (race: INCR then crash before EXPIRE leaves a key forever; set expiry in the same script).
```
 -- Redis fixed-window via Lua (atomic)
 local c = redis.call('INCR', KEYS[1])
 if c == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end
 return c
```
- Where: API gateway / edge (coarse, per IP/API key), per-service sidecar (fine, per user/tenant), client-side (be a good citizen).
- Tradeoff: strict global accuracy needs a round trip per request; relax by local token slices (each node leases N tokens from Redis, refills periodically) at the cost of slight over/under-admission.
- Failure policy: if Redis is down, fail open (availability) or fail closed (protect backend)? State it explicitly; many choose fail-open with local fallback limits.
- Dimensions: per user, per API key, per IP, per endpoint, per tenant tier; weigh cost (LLM tokens, heavy queries) rather than request count.
- Clock: use the Redis server time, not app-server clocks.
- Related: concurrency limits (max in-flight requests) often protect better than QPS limits because slow requests pile up (Little's Law).

---
## 10. Timeouts, retries, exponential backoff and jitter

### 10.1 Timeouts
- Every network call needs a timeout; the default in many libraries is infinite. Without one, threads/connections leak and a slow dependency takes you down.
- Set from the dependency's p99 or p99.9 latency plus margin, not a round number. Use connect timeout and read timeout separately.
- Deadline propagation: the client sets an overall deadline (e.g. 2s); each hop passes the remaining budget (gRPC deadlines). A downstream must not keep working on a request the caller already abandoned.
- Timeouts nest: inner timeout < outer timeout, or retries inside will be wasted.
- A timeout does NOT tell you whether the operation happened. Hence idempotency (section 5).

### 10.2 Retries
- Retry only: idempotent operations (or those with idempotency keys) and transient errors (timeouts, 502/503/504, 429 honoring Retry-After, connection reset). Never retry 4xx validation errors.
- Limit attempts (3 is typical) and use a retry budget (e.g. retries <= 10% of requests) so retries cannot multiply load.
- Retry amplification: with depth d and k retries per layer, worst-case load is (k+1)^d. Retry at ONE layer (usually the outermost or the edge), not at every layer.

### 10.3 Exponential backoff + jitter
Without jitter, all clients that failed together retry together (thundering herd), re-crashing the server in synchronized waves.

```
 delay = min(cap, base * 2^attempt)
 Full jitter:         sleep = random(0, delay)               <- AWS recommended
 Equal jitter:        sleep = delay/2 + random(0, delay/2)
 Decorrelated jitter: sleep = min(cap, random(base, prev_sleep*3))
```
```python
import random, time

def retry(fn, attempts=5, base=0.1, cap=10.0, retry_on=(TimeoutError, ConnectionError)):
    for attempt in range(attempts):
        try:
            return fn()
        except retry_on:
            if attempt == attempts - 1:
                raise
            delay = min(cap, base * 2 ** attempt)
            time.sleep(random.uniform(0, delay))   # full jitter
```
The AWS Architecture Blog "Exponential Backoff and Jitter" showed full jitter minimizes total work and completion time vs no jitter. Honor server hints (`Retry-After`) over your own computed delay.

Hedged requests: send a second request after p95 latency to cut tail latency; only for idempotent reads and with a cap on extra load (Google "Tail at Scale").

---
## 11. Circuit breakers (and bulkheads)

Problem: a dependency is failing; continuing to call it wastes threads, adds latency, and prevents recovery.

```
        failures > threshold
 CLOSED --------------------> OPEN  (fail fast, no calls; return fallback)
   ^                            |
   | probe succeeds             | after cool-down timer
   |                            v
   +------------------------ HALF-OPEN (allow a few trial calls)
        probe fails -> back to OPEN
```
```python
import time

class CircuitBreaker:
    def __init__(self, fail_threshold=5, reset_after=30.0):
        self.fail_threshold, self.reset_after = fail_threshold, reset_after
        self.failures, self.opened_at, self.state = 0, 0.0, "closed"

    def call(self, fn, fallback=None):
        if self.state == "open":
            if time.monotonic() - self.opened_at < self.reset_after:
                return fallback() if fallback else self._raise()
            self.state = "half_open"            # let one trial through
        try:
            result = fn()
        except Exception:
            self.failures += 1
            if self.state == "half_open" or self.failures >= self.fail_threshold:
                self.state, self.opened_at = "open", time.monotonic()
            raise
        self.failures, self.state = 0, "closed"
        return result

    def _raise(self):
        raise RuntimeError("circuit open")
```
Production breakers (Resilience4j, Envoy outlier detection, Hystrix historically) use failure RATE over a sliding window and a minimum call volume, not a raw count.

Design points
- Pair with a fallback: cached data, default value, degraded feature, queue for later.
- Per-dependency breakers, not one global.
- Bulkheads: isolate resources per dependency (separate thread/connection pools, per-tenant concurrency limits) so one failing dependency cannot exhaust shared capacity. Named after ship compartments.
- Count timeouts as failures; do not count 4xx client errors.
- Service mesh (Envoy/Istio) can provide breaking, retries, timeouts outside app code.

Combined resilience stack, outer to inner:
```
 deadline -> rate limit/admission -> bulkhead -> circuit breaker -> retry w/ backoff+jitter -> timeout -> call
```
(Order varies by library; the key is that you can explain why each exists.)

---
## 12. Putting it together: order service example

```
 POST /orders (Idempotency-Key: K)
   -> API: dedup on K; BEGIN; insert order + outbox(OrderPlaced); COMMIT; 202 Accepted
   -> Debezium/relay -> Kafka topic orders (key=order_id)
        group payment:   idempotent consumer; charges with key=order_id; retries w/ backoff+jitter;
                         circuit breaker around card gateway; poison -> orders.dlq
        group email:     at-least-once, dedup by event id
        group analytics: at-most-once is fine
   -> rate limiter at gateway per API key; 429 + Retry-After
   -> consumer lag alert; autoscale on lag; DLQ depth alert
```

Failure walkthrough to practise aloud
- Relay crashes after publish, before marking sent -> duplicate event -> consumer dedups on event id.
- Payment gateway slow -> timeouts -> breaker opens -> consumers pause/back off, lag grows (acceptable; messages durable) -> breaker half-open probes -> recover and drain backlog.
- Poison message -> bounded retries -> DLQ -> alert -> fix -> redrive.

---
## 13. How interviewers probe this

- "Can you guarantee exactly-once?" Expected: no for delivery; at-least-once + idempotency gives exactly-once effect; Kafka EOS scope limited to Kafka-to-Kafka; external effects need idempotency keys.
- "How do you update the DB and publish an event atomically?" Outbox + CDC/poller; mention at-least-once relay and idempotent consumers.
- "Your consumer lags. What do you do?" Check producer rate vs consumer rate; partition count limits parallelism; look for slow processing, rebalances, poison messages; scale, batch, add partitions (with ordering caveat).
- "How do you order messages?" Per partition/key only; global order costs throughput (single partition). Ask whether you really need it.
- "Design a rate limiter." Algorithm choice, where it lives, Redis atomicity, fail-open vs closed, headers, multi-tier. (Full walkthrough in week 6.)
- "Retries made the outage worse; why?" Retry amplification, no jitter, no budget, retrying non-transient errors.
- "What if the broker is down?" Producer buffering with limits, outbox keeps events safe in the DB, fall back to sync path, backpressure to clients.
- "Kafka vs SQS vs RabbitMQ?" Log vs queue, replay, ordering, throughput, ops burden, per-message features.
- Probe style: they push on the failure case of each answer ("and if the consumer crashes right there?"). Practise saying "the crash window is between X and Y, so we make it safe by Z."
- What to say out loud: state the guarantee you want, name the failure window, name the mechanism that closes it, name what remains (cost/limitation).
