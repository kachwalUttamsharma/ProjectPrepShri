# Week 4 interview Q&A: Kafka and streaming

**1. Why is Kafka a "log" and not a queue? Why does it matter?**
Records are appended to a retained, offset-addressed sequence; consuming doesn't delete. So many consumer groups read independently, you can replay, and downstream state can be rebuilt from it.
*Follow-ups:* When would you still prefer SQS? (Work distribution, per-message ack/visibility timeout, no need for replay.) How does compaction change the "log" contract? (Latest per key only; history lost.)

**2. How does a record end up in a partition, and what does that imply?**
Key hash modulo partition count (murmur2 in the default Java partitioner); null key uses sticky batching. Same key goes to the same partition, so per-key order. Partition is the unit of ordering and parallelism.
*Follow-ups:* What happens when you add partitions? (Key-to-partition mapping changes; per-key ordering across the boundary breaks; stateful consumers need migration.) How do you handle a hot key? (Salting with aggregation downstream, custom partitioner, split by sub-key.) Why not Python `hash()`? (Randomized per process.)

**3. Walk me through replication, ISR and leader election.**
Each partition has a leader and followers that fetch from it. ISR = replicas within `replica.lag.time.max.ms`. A record is committed (visible to consumers, high watermark) when all ISR have it. On leader loss the controller picks a new leader from the ISR.
*Follow-ups:* What if the ISR shrinks to 1? (With `min.insync.replicas=2` and acks=all producers get NotEnoughReplicas: you choose consistency over availability.) Unclean leader election? (Availability over durability; can lose committed data.)

**4. How would you configure for no data loss?**
RF=3, min.insync.replicas=2, acks=all, idempotence on, unclean election off, retries via `delivery.timeout.ms`, and rack-aware placement. Consumer side: commit after processing.
*Follow-ups:* Cost? (Higher latency, lower availability when 2 brokers down.) Is fsync required? (Kafka relies on replication rather than per-write fsync by default.)

**5. Explain acks and the idempotent producer.**
acks=0/1/all control how many replicas confirm. Idempotence: broker tracks (producer id, partition, sequence); retried duplicates are dropped and out-of-order sequences rejected. Scope: one producer session and partition; a restarted producer gets a new id unless transactional.id is set.
*Follow-ups:* Does idempotence give exactly-once end to end? (No.) max.in.flight? (Up to 5 keeps ordering with idempotence.)

**6. What triggers a consumer group rebalance, and how do you reduce its pain?**
Join/leave/crash, missed heartbeats, exceeding `max.poll.interval.ms`, subscription or partition changes. Reduce: cooperative-sticky assignor, static membership, tuned timeouts, smaller `max.poll.records`, faster processing or hand-off to worker threads with pause/resume, avoid deploys that restart all pods at once.
*Follow-ups:* Why range vs round-robin matters? (Range can skew when many topics each have few partitions; round-robin spreads evenly but moves more.) What's in KIP-848? (Broker-side group coordination; (check current docs).)

**7. Describe the three delivery semantics and how you get each.**
At-most-once: commit before processing. At-least-once: commit after. Exactly-once: Kafka transactions (atomic produce + offset commit, read_committed) inside Kafka; with external systems use idempotent writes or a transaction spanning data and offset.
*Follow-ups:* Where does exactly-once break? (Any non-idempotent side effect: email, HTTP call.) How do you dedupe? (Event id with unique constraint/upsert, bounded dedupe state with TTL; show the key choice.) What is the 2-phase commit in Flink sinks? (Pre-commit on checkpoint, commit on checkpoint-complete notification.)

**8. A consumer group's lag is growing. Walk through the diagnosis.**
Compare produce rate vs consume rate; check per-partition lag (skew -> hot key/partition), rebalance storms, slow downstream (DB), GC, poll interval overruns, a poison message looping. Remedies: scale consumers (up to partition count), batch writes, fix skew, increase partitions with a plan, backpressure/rate-limit upstream.
*Follow-ups:* Lag in time rather than count? (Oldest unprocessed message age; Burrow-like or timestamp-based.) What if lag is concentrated on one partition? (Hot key or stuck consumer.)

**9. Retention vs compaction: when each?**
Retention for event streams (clicks, logs): keep N days. Compaction for changelogs/entity state (user profile, CDC of a table): keep the newest record per key; tombstones delete. Compaction is not instant and the active segment isn't compacted, so consumers may still see multiple versions.
*Follow-ups:* GDPR erasure on a compacted topic? (Tombstone plus wait for compaction; on delete-retention topics you rely on expiry or crypto-shredding.) Can you rebuild a table from it? (Yes: that's the point.)

**10. What is Schema Registry and how do compatibility modes work?**
Central store of versioned schemas per subject; producers register/lookup an id embedded in each message. BACKWARD: consumers on the new schema can read old data (safe to add fields with defaults, delete fields); FORWARD: old consumers can read new data; FULL both. Transitive variants check all versions, not just the previous.
*Follow-ups:* Upgrade order for BACKWARD? (Consumers first.) For FORWARD? (Producers first.) Why not plain JSON? (No enforced contract, bigger payloads.) Breaking change plan? (New topic/subject version, dual publish, migrate, retire.)

**11. Event time vs processing time; what is a watermark?**
Event time is when it occurred (in the payload); processing time is arrival time. Using event time gives deterministic results on replay but needs a way to know completeness: the watermark, an estimate that no earlier events will arrive. Bounded out-of-orderness: max_ts - delay.
*Follow-ups:* Trade-off in choosing delay? (Latency vs completeness.) Idle source? (Watermark stalls; set idleness timeout.) What can go wrong with a bad producer clock? (A future timestamp pushes the watermark ahead and makes valid events late: validate or clamp timestamps.)

**12. Tumbling vs sliding vs session windows. Give a use for each.**
Tumbling: per-minute counts. Sliding: 5-min moving average updated each minute (each event is in size/slide windows, so state and output grow). Session: user activity bursts separated by inactivity; windows merge as events bridge gaps.
*Follow-ups:* State cost of sliding? (size/slide multiplier; use incremental aggregates/panes.) Late event bridging two sessions? (Sessions merge and re-emit.)

**13. How do you handle late data?**
Decide per use case: drop and count in a metric, side output to a late topic for reconciliation, `allowedLateness` to update already-emitted results (downstream must accept upserts/retractions), or batch correction (nightly recompute of affected partitions).
*Follow-ups:* How does Spark differ? (Watermark drops state older than the threshold; append mode emits once after the watermark passes, update mode emits updates.) How to measure? (Late-event ratio, lateness distribution to choose the delay.)

**14. Flink vs Spark Structured Streaming vs Kafka Streams: how do you choose?**
Flink for low-latency, complex event time and large state; Spark SS if you want one engine for batch+stream, SQL/DataFrame, lakehouse sinks; Kafka Streams for Kafka-to-Kafka microservices without a cluster.
*Follow-ups:* Micro-batch latency implications? (Seconds-level; continuous mode experimental (check current docs).) Rescaling stateful jobs? (Flink: savepoint + new parallelism within max-parallelism/key groups; Kafka Streams: bounded by partitions.)

**15. What does checkpointing do and how does it differ from a savepoint?**
Periodic distributed snapshot of operator state and source positions, enabling recovery to a consistent point (Flink via barriers). Savepoints are user-triggered, versioned, portable snapshots for upgrades/migration.
*Follow-ups:* Checkpoint too slow? (Backpressure delays barriers; use unaligned checkpoints, incremental RocksDB checkpoints, reduce state.) Recovery replays from what? (Source offsets in the checkpoint; sinks must be idempotent/2PC.)

**16. What is backpressure and where do you see it?**
Downstream is slower than upstream, so buffers fill and producers are throttled. In Flink: backpressure/busy metrics per task; Spark: input rate vs processing rate, batch duration growth; Kafka: consumer lag rises (the broker is the buffer).
*Follow-ups:* Is it bad? (It's the correct signal; dropping is the bad alternative.) Fixes? (Scale the bottleneck operator, async I/O for enrichment, batching, skew handling.)

**17. Design a CDC pipeline from Postgres to the lakehouse.**
Debezium on logical replication slot -> Kafka (topic per table, key = PK, Avro + registry) -> sink (Connect/Flink/Spark) applying upserts/deletes with MERGE into Iceberg/Delta using the op and source LSN/ts to order. Initial snapshot then streaming; schema evolution through registry.
*Follow-ups:* Slot lag filling the WAL? (Monitor, heartbeat events, drop unused slots.) Out-of-order or duplicate events? (Dedupe by (PK, LSN), take latest.) Deletes? (op=d, soft-delete or MERGE delete.) Large TOAST columns? (Unchanged TOAST placeholder gotcha.)

**18. What is the outbox pattern and why not dual write?**
A service writing to its DB and to Kafka separately can do one and fail the other. Outbox: write the domain row and an outbox row in one DB transaction; a relay (Debezium outbox event router or poller) publishes. Gives at-least-once publishing in commit order per aggregate.
*Follow-ups:* Consumers? (Idempotent, dedupe on event id.) Outbox table growth? (Delete/partition after publish.) Alternative? (Event sourcing; transactional producer cannot span the DB.)

**19. Lambda vs Kappa?**
Lambda: separate batch and speed layers merged at serving; correct but duplicate logic. Kappa: only a streaming path; reprocess by replaying the log with new code. Tradeoffs: replay cost and retention, exact reprocessing semantics. Modern: streaming + lakehouse with batch backfill sharing code.
*Follow-ups:* How do you reprocess in Kappa without downtime? (Run new job version to a new output/table, catch up, swap.) Limits? (Retention, expensive long-range replays, external lookups that changed.)

**20. How do you size topics and partitions?**
Start with target throughput / measured per-partition throughput (producer and consumer sides), then desired consumer parallelism, then headroom for growth because partitions can't be decreased and increasing disrupts key order. Constraints: broker limits, recovery time, end-to-end latency, ordering domain.
*Follow-ups:* Why not 1000 partitions "just in case"? (Overhead, longer failovers, memory, more files.) Message size? (Keep small; large payloads to object store with a pointer.)

**21. Kinesis vs MSK vs SQS?**
Kinesis: managed shard-based log, simple ops, AWS-integrated; MSK: Kafka protocol/ecosystem (Connect, Streams) with some ops responsibility; SQS: queue with per-message ack, DLQ and no replay. Choose by need for replay/ordering/ecosystem/portability/ops. Check current docs for limits and pricing.
*Follow-ups:* Kinesis ordering? (Per shard via partition key; resharding changes mapping.) SQS FIFO ordering? (Per message group id; throughput limits (check current docs).) Lambda consumers? (Event source mappings with batch size, partial batch failure reporting.)

**22. How would you design a dead-letter queue strategy?**
Distinguish transient (retry with backoff, then park) from permanent (schema/validation: park immediately). DLQ record keeps payload, error, stack, source topic/partition/offset, attempt count. Alert on DLQ rate; build a replay tool; keep ordering implications in mind (a retry topic breaks order for that key).
*Follow-ups:* Non-blocking retries? (Retry topics with delays.) Should a DLQ ever be skipped? (Fail-fast when any loss is unacceptable and ordering matters, halt the partition.)

**23. How do you test a streaming job?**
Unit test pure functions; use deterministic event-time tests with a controllable watermark (Flink test harness / Spark MemoryStream) including late and out-of-order events; integration with Testcontainers Kafka; replay golden datasets; chaos (kill workers) to verify checkpoint recovery and idempotent sinks.
*Follow-ups:* Verifying no loss/dup in prod? (Reconciliation counts per window between source and sink; sequence number gaps.)

**24. Ordering: a consumer processes records with a thread pool and the output is out of order. What do you do?**
Order is only guaranteed if processing preserves per-key sequence. Dispatch by key hash to a fixed single-threaded lane (per-partition or per-key executors), or process a partition's batch serially and parallelize across partitions; commit only the contiguous processed offset watermark.
*Follow-ups:* Offset commit with out-of-order completion? (Track highest contiguous completed offset; otherwise you lose records on crash.)
