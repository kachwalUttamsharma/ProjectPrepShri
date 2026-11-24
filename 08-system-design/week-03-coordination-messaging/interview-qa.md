# Week 3 - Interview Q&A: Coordination and Messaging

Cover the answer, say yours aloud (30-60 seconds), then compare. Lesson: [lesson.md](lesson.md).

---
**Q1. Why introduce a message queue between two services?**
Decouple in time and rate: producer is not blocked by a slow/down consumer, bursts are buffered, consumers scale independently, and you get retries and fan-out. Cost: eventual consistency, duplicates/reordering, more infrastructure, harder debugging.

**Q2. Queue vs log (SQS vs Kafka)?**
Queue: messages are tasks, deleted after ack, competing consumers, no replay. Log: retained, partitioned, ordered per partition, each consumer group tracks its own offset, replay by rewinding. Use queue for work distribution with per-message retry/DLQ; log for event streams, many consumers, replay, CDC, high throughput.

**Q3. Explain Kafka partitions, offsets, and consumer groups.**
A topic is split into partitions, each an ordered append-only log; an offset is a record's position. Producers choose the partition by key hash. In a consumer group each partition is read by exactly one member, so parallelism is capped by partition count; separate groups each get all messages. Offsets are committed per group per partition.

**Q4. What ordering guarantees does Kafka give?**
Strictly ordered within a partition only. Use the entity id as the key so related events share a partition. No global order across partitions; global order means one partition, which kills parallelism. Retries can reorder unless the idempotent producer is enabled.

**Q5. At-most-once vs at-least-once vs exactly-once?**
At-most-once: no retry/commit before processing; may lose. At-least-once: retry/commit after processing; may duplicate. Exactly-once delivery is impossible over an unreliable network (can't distinguish a lost message from a lost ack); we get exactly-once effect via at-least-once plus idempotent processing, or transactional atomic commit of output and offset.

**Q6. What does Kafka's exactly-once semantics actually cover?**
Idempotent producer (dedup by producer id + sequence) plus transactions, with consumers using read_committed. It makes consume-transform-produce between Kafka topics atomic, including the offset commit. It does not cover external side effects (email, DB write in another system); those need idempotency keys or same-transaction offset storage.

**Q7. What is idempotency and how do you implement it?**
An operation applied N times equals once. Ways: naturally idempotent ops (upsert, set), client-supplied idempotency key stored with the result, dedup table with a unique constraint inserted in the same transaction as the effect, conditional writes/version checks. Handle concurrent duplicates with an atomic claim of the key; keep keys long enough (TTL) to cover retry windows.

**Q8. A consumer processes a message, then crashes before committing its offset. What happens?**
On restart (or after rebalance) the message is redelivered, so the effect happens twice. Fix by making the handler idempotent: record message id and apply the effect in one DB transaction, or use a natural idempotent write.

**Q9. Explain the outbox pattern and why it is needed.**
Dual write problem: updating the DB and publishing to a broker cannot be atomic. Write the event to an outbox table in the same local transaction as the state change; a relay (poller with SKIP LOCKED, or CDC like Debezium) publishes it and marks it sent. Gives at-least-once publishing, so consumers must dedup. The consumer-side mirror is the inbox/dedup table.

**Q10. Pub/sub vs point-to-point queue?**
Point-to-point: one message goes to one of competing consumers. Pub/sub: every subscriber gets a copy; publisher doesn't know them. Common robust pattern: topic fan-out to one queue per subscriber (SNS->SQS; Kafka consumer groups) so each has its own buffer, retries, DLQ.

**Q11. What is backpressure and how do you apply it?**
A signal from slow consumer to fast producer to prevent unbounded buffering. Options: bounded queues that block producers, pull-based consumption, load shedding with 429/503, dropping perishable data, autoscaling on lag or oldest-message age, degrading features. Unbounded queues convert overload into unbounded latency (Little's Law) and encourage retry storms.

**Q12. Compare token bucket, leaky bucket, fixed window, sliding window.**
Token bucket: refill r/s, capacity B; allows bursts to B, O(1) state. Leaky bucket: queue drained at constant rate; smooths output. Fixed window: simple counter but up to 2x burst at boundary. Sliding log: exact, O(n) memory. Sliding counter: weighted previous+current window, O(1), small error. Default pick: token bucket or sliding counter.

**Q13. How do you build a distributed rate limiter?**
Central Redis with atomic ops (Lua script or INCR+EXPIRE together), key per user/API key/endpoint, using Redis time. Enforce at gateway plus per-service. To cut round trips, lease token slices per node at the cost of precision. Decide fail-open vs fail-closed when Redis is unavailable. Return 429 with Retry-After. Consider cost-weighted limits (LLM tokens) and concurrency limits.

**Q14. Why exponential backoff with jitter?**
Backoff spaces retries so a struggling server can recover; jitter randomizes delays so many clients that failed together don't retry in synchronized waves (thundering herd). Full jitter: sleep = random(0, min(cap, base*2^n)). Honor Retry-After and cap attempts.

**Q15. When is it safe to retry?**
Only for transient failures (timeouts, 503, connection reset, 429) on idempotent operations or those with idempotency keys. Not on 4xx validation errors. A timeout doesn't say whether the op happened. Use retry budgets and retry at one layer; (k+1)^depth amplification can turn a blip into an outage.

**Q16. How do you choose timeout values?**
From the dependency's observed latency distribution (p99/p99.9 plus margin), with separate connect and read timeouts, and inner timeouts smaller than outer ones. Propagate a deadline so downstreams stop work for abandoned requests. Never leave the infinite default.

**Q17. How does a circuit breaker work?**
Closed (normal, counting failures) -> Open when failure rate exceeds threshold (fail fast or fallback, no calls) -> Half-open after cool-down (a few probe calls) -> Closed on success or Open on failure. Protects callers' threads and gives the dependency room to recover. Use per-dependency, a minimum volume, and a fallback.

**Q18. What is a bulkhead?**
Resource isolation per dependency or tenant (separate thread/connection pools, concurrency caps) so one failure or noisy neighbor can't exhaust shared capacity. Complements circuit breakers.

**Q19. What is a poison message and how do you handle it?**
A message that always fails processing and blocks its partition/queue by being retried forever. Use bounded retries (maybe via retry topics with delay), then dead-letter it with error metadata, alert on DLQ depth, and support redrive after a fix.

**Q20. Consumer lag is growing. Diagnose it.**
Compare produce rate vs consume rate. Check: processing time per message (slow dependency?), rebalance storms (poll interval, GC), a stuck poison message, too few consumers or partitions (consumers capped at partition count), hot partition from a skewed key. Remedies: optimize/batch, scale consumers, add partitions (ordering caveat), fix skew, shed/prioritize.

**Q21. What happens if the broker is unavailable when you want to publish?**
Use the outbox so events persist in the DB and drain after recovery; or bounded in-memory buffering with retry; surface backpressure to callers (503) if the event is mandatory. Make producers non-blocking where possible and alert.

**Q22. Metastable failure / retry storm: what is it and how do you defend?**
Overload triggers timeouts, clients retry, load rises, and the system stays down even after the trigger is gone. Defences: load shedding, jittered capped retries, retry budgets, circuit breakers, adaptive concurrency limits, and graceful degradation.
