# Week 4: Kafka and stream processing

Goal: explain how a distributed log works, what delivery guarantees you really get, and how event-time windows, watermarks and state work in Flink / Spark Structured Streaming. Version-specific facts are marked "(check current docs)".

## 1. The log abstraction
- A **log** is an append-only, totally ordered sequence of records, each with an **offset**. Readers keep their own position; data is not deleted on read.
- Consequences: many independent consumers, replay (seek back), cheap sequential disk I/O, and the log doubles as a source of truth from which tables (views) are derived (stream-table duality).
- Contrast with a queue (SQS): a queue deletes on ack and has no replay; a log retains by time/size/compaction.

## 2. Kafka architecture
- **Topic** = named log split into **partitions**. Order is guaranteed only *within a partition*.
- **Broker** = server. Each partition has one **leader** and N-1 **follower** replicas (replication factor N). Producers/consumers talk to the leader.
- **ISR** (in-sync replicas): followers caught up with the leader. A write is "committed" once all ISR have it. If the leader dies, the controller elects a new leader from the ISR (so no committed data lost). `unclean.leader.election.enable=true` allows an out-of-sync replica to lead: availability over durability.
- Durability knobs: `replication.factor=3`, `min.insync.replicas=2`, producer `acks=all`. With RF=3, min.isr=2 you tolerate one broker down for writes and two for reads.
- Metadata/controller: KRaft (Raft-based, no ZooKeeper) is the default in current releases; ZooKeeper removed in 4.0 (check current docs).
- Retention: by `retention.ms` / `retention.bytes` (delete policy) or **log compaction** (keep the latest record per key; tombstone = null value deletes the key after `delete.retention.ms`). Compaction suits changelogs / state, not event history.

## 3. Producers
- **Partitioning**: record with a key -> `hash(key) % partitions` (murmur2); no key -> sticky/round-robin batching. Same key, same partition, so per-key ordering. **Changing the partition count remaps keys** and breaks per-key ordering for in-flight data and stateful consumers.
- **acks**: `0` fire and forget; `1` leader only (lost if leader dies before replication); `all` all ISR (use with min.insync.replicas).
- **Idempotent producer** (`enable.idempotence=true`, default in recent clients (check current docs)): broker dedupes retries using producer id + per-partition sequence numbers -> no duplicates or reordering from retries within one producer session.
- **Batching/throughput**: `linger.ms`, `batch.size`, `compression.type` (lz4/zstd/snappy/gzip; zstd and lz4 are common choices), `max.in.flight.requests.per.connection` (<=5 keeps ordering with idempotence).
- Delivery timeout and retries: set `delivery.timeout.ms` rather than counting retries.

## 4. Consumers
- **Consumer group**: partitions of a topic are divided among the group's consumers; each partition is read by exactly one member of a group at a time. Max useful parallelism = number of partitions. Different groups each get all data.
- **Assignment strategies**: Range (contiguous per topic), RoundRobin, Sticky/CooperativeSticky (minimize movement; cooperative rebalancing avoids stop-the-world). The newer KIP-848 consumer protocol moves assignment to the broker (check current docs).
- **Rebalance** triggers: member joins/leaves/crashes, missed heartbeat (`session.timeout.ms`), too slow between polls (`max.poll.interval.ms`), partition count change. Eager rebalance pauses all consumption; use cooperative + static membership (`group.instance.id`) to reduce churn.
- **Offsets**: committed to the internal `__consumer_offsets` topic = "next offset to read". Auto-commit can lose or duplicate; for control use manual commit *after* processing.
- **Lag** = log end offset - committed offset, per partition. Rising lag means consumers are slower than producers; alert on lag trend and age of oldest unprocessed message, not just absolute count.
- Poison messages: catch, retry bounded, then route to a **dead-letter topic** with headers (error, original topic/partition/offset) so you can inspect and replay.

## 5. Delivery semantics
| Semantics | How | Failure mode |
|---|---|---|
| At-most-once | commit offset *before* processing | crash -> lost records |
| At-least-once | process, then commit | crash -> reprocess -> duplicates |
| Exactly-once | see below | - |

- **Exactly-once inside Kafka** (read-process-write between topics): idempotent producer + **transactions** (`transactional.id`, atomic writes across partitions and the consumer-offset commit via `sendOffsetsToTransaction`). Consumers must use `isolation.level=read_committed`. Kafka Streams: `processing.guarantee=exactly_once_v2`.
- **End-to-end** exactly-once with an external sink is really **at-least-once + idempotent/transactional sink**: upsert by key, dedupe by event id, or write data and offsets in one DB transaction. Exercise 6 models the dedupe. "Exactly-once" claims always have a boundary; ask where it ends.
- Flink: checkpoint barriers (Chandy-Lamport style) give exactly-once state; sinks need two-phase commit or idempotence for end-to-end.

## 6. Ordering guarantees (the exam favourite)
- Per partition: total order. Across partitions: none. For per-entity order, key by entity id.
- Retries without idempotence + `max.in.flight > 1` can reorder. With idempotence this is safe up to 5 in flight.
- Rebalances and consumer-side parallelism (thread pool per record) can break processing order even though read order was fine.

## 7. Schemas, serialization, connectors
- **Schema Registry**: stores Avro/Protobuf/JSON Schema versions; messages carry a schema id (magic byte + 4-byte id). Compatibility modes: BACKWARD (new reader reads old data; default), FORWARD, FULL, plus *_TRANSITIVE and NONE. Choose subject naming (TopicNameStrategy etc.) deliberately.
- Avro evolution rules: add fields with defaults; remove only fields that had defaults; renaming needs aliases.
- **Kafka Connect**: framework for source/sink connectors (JDBC, S3, Debezium, Elasticsearch); workers, tasks, converters, SMTs, offset storage in Kafka, a DLQ for sink errors (`errors.tolerance`, `errors.deadletterqueue.topic.name`).
- **Kafka Streams** (library, runs in your app, state in RocksDB with changelog topics, KStream/KTable) and **ksqlDB** (SQL over Streams; check current status/licensing in docs).

## 8. Stream processing concepts
- **Event time** (when it happened, in the record) vs **processing time** (when we see it) vs ingestion time. Correct analytics use event time; processing time is simpler but wrong under delay/replay.
- **Windows**: tumbling (fixed, no overlap), sliding/hopping (size + slide; an event lands in size/slide windows), session (gap of inactivity, merge on arrival), global/count windows.
- **Watermark**: a heuristic assertion "no more events with timestamp < W are expected". Bounded out-of-orderness: `W = max_event_ts - max_delay`. A window fires when W passes its end. Events behind the watermark are **late**: drop, send to a side output/DLQ, or allow within `allowedLateness` and emit **updated** results (retractions/upserts).
- Idle partitions hold the watermark back (it is the min over inputs): configure idleness timeouts.
- **State**: keyed state (counts, joins, dedupe) lives in the operator, usually RocksDB; must be bounded with TTL or windows. **Checkpointing** snapshots state + source offsets consistently; **savepoints** are manual, portable checkpoints for upgrades (Flink).
- **Backpressure**: a slow operator makes upstream buffers fill and the source slows; Kafka naturally buffers (lag grows) rather than dropping. Diagnose via Flink backpressure metrics/Spark input rate vs processing rate.
- **Joins**: stream-stream (windowed, state heavy), stream-table (enrichment; table must be co-partitioned in Kafka Streams), temporal joins.

## 9. Flink vs Spark Structured Streaming vs Kafka Streams
- **Flink**: true per-record streaming, rich event-time/state/timers, low latency, exactly-once via checkpoints; more operational weight.
- **Spark Structured Streaming**: micro-batch by default (continuous mode experimental), unified batch/stream API and DataFrames, `withWatermark`, `foreachBatch` for idempotent sinks, `trigger(availableNow=True)` for incremental batch. Good if you already run Spark/Databricks.
- **Kafka Streams**: embedded library, Kafka-only in/out, simplest deployment; scaling = more app instances up to partition count.

## 10. Patterns
- **CDC with Debezium**: reads the DB transaction log (MySQL binlog, Postgres WAL via logical replication slot) -> change events (before/after, op, ts) in Kafka via Connect. Pros: no dual write, low load, captures deletes. Watch: unbounded WAL growth from an idle slot, schema changes, initial snapshot, ordering per primary key (key the topic by PK).
- **Outbox pattern**: write business row + outbox event in ONE DB transaction; CDC (or poller) publishes the outbox table. Solves the dual-write problem; consumers must still be idempotent.
- **Lambda** (batch layer + speed layer, two code paths) vs **Kappa** (one streaming path; reprocess by replaying the log). Kappa needs long retention or a lakehouse as the replay source; modern lakehouse/streaming engines blur this.
- **Replay/backfill**: new consumer group with `auto.offset.reset=earliest`, or `seek`/reset offsets to a timestamp (`kafka-consumer-groups --reset-offsets`). Side effects of replay (emails, API calls) must be guarded.
- **Sizing partitions**: partitions >= max(target / producer-per-partition, target / consumer-per-partition), plus headroom, since you cannot reduce partitions and increasing breaks key mapping. Too many partitions = more file handles, longer leader election/recovery, more end-to-end latency, memory per partition. Measure; typical per-partition throughput is on the order of 10s of MB/s (hardware dependent).

## 11. Kinesis / MSK / SQS (check current docs for limits and pricing)
- **Kinesis Data Streams**: managed log; shards (1 MB/s or 1000 rec/s in; 2 MB/s out per shard), on-demand or provisioned capacity, 24h default retention up to 365 days, enhanced fan-out. Simpler ops, AWS-only, fewer ecosystem tools.
- **MSK** (Managed Streaming for Kafka; Serverless and provisioned variants): real Kafka APIs and ecosystem, you still choose broker sizing/partitions; cross-cloud portable.
- **SQS**: queue, not a log. Visibility timeout, at-least-once (Standard) or FIFO (ordered by message group, dedupe id, lower throughput), DLQ via redrive policy, no replay, no partition concept. Pick when you need decoupling/work distribution, not streaming analytics.
- **SNS+SQS** fan-out for small pub/sub; Kafka/Kinesis when you need replay, multiple readers over history, ordering per key, high throughput.

## 12. Code walkthrough: a toy offset commit (different from the exercises)
```python
# at-least-once consumer loop, pseudo-Kafka
while True:
    batch = consumer.poll(timeout=1.0)
    for rec in batch:
        sink.upsert(key=rec.key, value=rec.value, offset=rec.offset)  # idempotent
    consumer.commit()   # AFTER the sink succeeded
```
If the process dies between upsert and commit, the batch is re-read and the upsert is a no-op replay: effectively-once.

## Common mistakes
- Using Python `hash()` or non-stable hashing for partitioning across processes.
- Assuming global ordering across partitions.
- Auto-commit with slow processing: offsets committed for records not yet processed.
- Adding partitions to a keyed topic without planning for key remapping.
- `acks=1` or `min.insync.replicas=1` with RF=3 and calling it durable.
- Calling a pipeline exactly-once when the sink is non-idempotent.
- Unbounded state (dedupe set, join buffers) with no TTL.
- Processing-time windows for analytics that must be reproducible on replay.
- Ignoring idle partitions stalling the watermark.
- Alerting on lag count only; a big, steady backlog and a growing one are different incidents.

## Your task
Fill in `exercises.py`, run `../../.venv/bin/pytest -q`, then drill `interview-qa.md` aloud and skim `cheatsheet.md` the night before.
