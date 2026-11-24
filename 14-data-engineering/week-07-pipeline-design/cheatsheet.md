# Week 7 Cheatsheet: Pipeline Design

## One-page template (copy to the whiteboard)

```
REQUIREMENTS  consumers / freshness SLA / volume / correctness / sources / history / compliance / budget
HARDEST REQ   ...
ESTIMATES     events/s avg+peak ; GB/day ; TB/yr (x replication) ; partitions
MODE          batch | micro-batch | streaming | hybrid  (slowest that meets SLA)
INGEST        CDC | API cursor | file landing | event bus
LAYERS        bronze(raw, immutable) -> silver(clean, dedupe) -> gold(marts)
PROCESS       idempotent jobs ; event time + watermark ; dedupe key+version
SERVE         warehouse | OLAP | feature store | cache
OPS           orchestration, quality gates, observability, backfill, DLQ
RISKS         dupes, late data, schema drift, skew, small files, cost, PII
EVOLVE        what changes at 10x
```

## Quick numbers

| Item | Rule of thumb |
|---|---|
| 1 day | 86,400 s (use 100K for mental math) |
| Peak vs average | 2-5x (say your factor) |
| JSON event | about 1 KB; Parquet compressed 4-6x smaller |
| Kafka partition | about 5-10 MB/s write; plan partitions by throughput and consumer parallelism |
| Kafka storage | MB/s x 86,400 x retention days x replication 3 |
| Parquet file size | 128 MB to 1 GB target |
| Spark shuffle partitions | aim for 100-200 MB per partition |
| Streaming vs batch cost | often 3-10x more to run and operate |

## Batch vs micro-batch vs streaming

| | Batch | Micro-batch | Streaming |
|---|---|---|---|
| Latency | min-hours | seconds-minutes | ms-seconds |
| Engine | Spark, dbt, SQL | Spark SS | Flink, Kafka Streams |
| Reprocess | trivial | easy | replay + state |
| Use | finance, reports | CDC merge, near-RT BI | fraud, alerting, ops |

## Ingestion patterns

| Source | Pattern | Watch |
|---|---|---|
| DB | log-based CDC | slot lag, deletes, DDL, snapshot handoff |
| DB (no log) | incremental by watermark | misses deletes, overlap window |
| API | cursor pull | rate limits, pagination, idempotent load |
| Files | landing + manifest + checksum | partial files, dupes, late |
| Events | schema registry + Kafka | partition key, event time, PII |

## Delivery semantics

- At-least-once + idempotent sink = exactly-once effect.
- Dedupe: producer event_id; `row_number() over (partition by key order by version desc)`.
- CDC ordering: by LSN/log position, per key.
- Commit offsets/cursors after the durable write.

## Streaming concepts

| Term | Meaning |
|---|---|
| Event time vs processing time | When it happened vs when we saw it |
| Watermark | Estimate that no events older than T will arrive; triggers window close |
| Allowed lateness | Extra time to update closed windows |
| Tumbling / sliding / session window | Fixed, overlapping, gap-based |
| Checkpoint | Snapshot of state + offsets for recovery |
| Backpressure | Slow consumer slows producers |

## Quality checks at gates

Schema, freshness, volume, null/unique, referential, reconciliation (sum/count vs source), distribution drift. Policy: block on correctness (finance totals), warn on soft metrics.

## Failure modes -> mitigation

| Failure | Mitigation |
|---|---|
| Duplicates | idempotent write, dedupe key |
| Late data | watermark + batch correction |
| Schema drift | registry, contracts, quarantine |
| Poison message | DLQ + replay |
| Skew | salt, broadcast, AQE |
| Small files | compaction, larger triggers |
| Slot / backlog growth | lag alerts, heartbeats |
| Silent corruption | reconciliation, time travel rollback |
| Cost runaway | budgets, auto-terminate, lifecycle |
| Wrong joins fan-out | grain tests, control totals |

## Serving choices

| Need | Pick |
|---|---|
| BI, finance, ad hoc | warehouse / lakehouse SQL |
| Sub-second, high concurrency, fresh | Druid / Pinot / ClickHouse |
| Online ML features | Redis / DynamoDB / Cassandra |
| Lookup API | KV + cache |

## Design-specific one-liners

1. Clickstream: dedupe by event_id, session windows, stream provisional + batch authoritative.
2. CDC: Debezium -> Kafka -> raw log -> MERGE by LSN; reconcile; watch replication slots.
3. Real-time metrics: Flink windows -> OLAP + Redis; approximate now, correct later.
4. Finance: cutoffs, control totals, 3-way reconciliation, immutable snapshots, no floats.
5. Feature store: one definition, as-of joins, log served features to catch skew.
6. Self-serve platform: config-driven DAGs, contracts, quotas, PII default-deny.
7. Fraud: sync score under 100 ms, precomputed velocity features, fallback to rules, delayed labels.
8. GDPR: PII inventory, batch deletes, compaction + snapshot expiry, suppression list, crypto-shredding, audit.

## Phrases that signal seniority

- "I would pick the slowest mode that meets the SLA."
- "Raw is immutable, so everything downstream is replayable."
- "Every job is idempotent: same inputs, same outputs."
- "I would detect that with X before the consumer does."
- "At 10x, the first thing that breaks is Y."
- "I am unsure of the current default for Z; I would check the docs."
