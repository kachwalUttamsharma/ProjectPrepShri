# Week 4 cheatsheet: Kafka and streaming

## Kafka vocabulary
topic > partitions (ordered, offset-addressed) > replicas (1 leader + followers). ISR = in-sync replicas. Committed = replicated to all ISR. Order only within a partition.

## Durability recipe
`replication.factor=3`, `min.insync.replicas=2`, producer `acks=all`, `enable.idempotence=true`, `unclean.leader.election.enable=false`.

## Producer knobs
| Knob | Effect |
|---|---|
| acks 0/1/all | durability vs latency |
| linger.ms, batch.size | bigger batches, more throughput, more latency |
| compression.type | lz4/zstd for CPU vs ratio |
| max.in.flight (<=5 + idempotence) | keeps order on retry |
| key | picks partition (hash % N) |

## Consumer knobs
`group.id`, `enable.auto.commit`, `auto.offset.reset` (earliest/latest), `max.poll.records`, `max.poll.interval.ms`, `session.timeout.ms`, `heartbeat.interval.ms`, `isolation.level=read_committed`, `partition.assignment.strategy` (CooperativeSticky), `group.instance.id` (static membership).

## Delivery semantics
- at-most-once: commit then process
- at-least-once: process then commit (dupes possible)
- exactly-once: idempotent producer + transactions (Kafka to Kafka); otherwise at-least-once + idempotent sink / dedupe key

## Lag
lag = log_end_offset - committed_offset (per partition). Watch trend and time-lag.

## Retention vs compaction
delete: by time/size. compact: latest per key, tombstone (null) deletes. Both possible (`cleanup.policy=compact,delete`).

## Windows
- tumbling [k*size, (k+1)*size)
- sliding(size, slide): event in size/slide windows
- session: gap of inactivity merges events

## Watermarks
`W = max_event_ts - max_delay`. Fire window when W >= window_end. Event with window_end <= W is late: drop / side output / allowed lateness with updates. Min over inputs; idle partitions stall it.

## Engines
Flink: per-record, best event time + state. Spark SS: micro-batch, `withWatermark`, `foreachBatch`. Kafka Streams: library, state in RocksDB + changelog topics.

## Patterns
CDC (Debezium log-based) | outbox (row + event in one txn) | DLQ (bounded retry then park with error metadata) | replay (new group / reset offsets) | lambda (two paths) vs kappa (replay log).

## Sizing
partitions >= max(T/p_prod, T/p_cons) x headroom. Can't shrink; growing remaps keys.

## AWS
Kinesis = shards (1MB/s in, 2MB/s out each), MSK = managed Kafka, SQS = queue (no replay, no order unless FIFO + group id). Check current docs for limits.

## Say-it-in-interview lines
- "Exactly-once always has a boundary; beyond Kafka it is at-least-once plus idempotence."
- "Partition key = the unit of ordering and the unit of parallelism."
- "Watermark is a heuristic, lateness policy is a business decision."
