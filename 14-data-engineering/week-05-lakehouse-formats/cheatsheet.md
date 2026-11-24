# Week 5 Cheatsheet: Lakehouse and Formats

## Parquet
file -> row groups (~128 MB) -> column chunks -> pages; footer = schema + stats; magic PAR1.
Stats: min/max/null count per chunk (+page index); optional Bloom filter.
Encodings: dictionary, RLE/bit-pack, delta; then Snappy/ZSTD/Gzip/LZ4.
Pushdown works only if data is clustered on the filter column. Files are immutable.

## Formats
Parquet: analytics, widest support. ORC: Hive, ACID in Hive. Avro: row, schema in header, Kafka + registry, best evolution. CSV/JSON: interchange/landing only.

## Layout
Partition: low cardinality, filtered often, big partitions (date). Sort/cluster: tight stats on other columns. Z-order: multi-column locality, rewrite cost. Iceberg: hidden partitioning + partition evolution. Avoid partitioning by user_id.

## Small files
Cause: streaming, over-partitioning, many tasks. Cost: listing, requests, tasks, stats. Fix: write-side tuning + compaction (OPTIMIZE / rewrite_data_files). Target 128 MB-1 GB. Compaction then vacuum/expire to free space.

## Table formats
| | Delta | Iceberg | Hudi |
|---|---|---|---|
| Metadata | _delta_log JSON + checkpoints | catalog -> metadata.json -> manifest list -> manifests | .hoodie timeline |
| Strength | Spark/Databricks, simple | multi-engine, hidden partitioning, evolution | upserts/CDC, incremental |
| Row-level | CoW, deletion vectors | CoW/MoR, delete files | CoW/MoR |
| Cleanup | VACUUM | expire_snapshots, remove_orphan_files | clean, compaction |

Commit = write data files, then atomic publish of metadata; optimistic concurrency; snapshot isolation for readers.
CoW: slow write, fast read. MoR: fast write, read merges until compaction.
Time travel bounded by retention; vacuum below longest reader = failures. Never delete files by hand.

## Lake / warehouse / lakehouse
Lake: files, schema on read. Warehouse: managed, ACID. Lakehouse: files + table format + catalog + many engines.

## Medallion
Bronze raw append-only; silver cleaned/deduped/conformed; gold marts/aggregates/features. Idempotent MERGE/overwrite between layers.

## Catalogs
Hive Metastore, Glue Data Catalog, Unity Catalog, Iceberg REST/Polaris/Nessie. Iceberg commit authority = catalog.

## AWS
S3 (strong consistency, prefixes, lifecycle, KMS) | Glue (catalog, crawlers, Spark ETL) | Athena (serverless SQL, pay per scanned data, CTAS, partition projection) | EMR (managed Spark/Hive/Trino) | Redshift Spectrum (S3 external tables) | Lake Formation (table/column/row permissions, LF-tags).
Athena cost: Parquet + partitions + column pruning + compaction.

## Ops checklist
File sizes, compaction schedule, snapshot expiry, schema policy, idempotent writes, concurrency plan, access control, monitoring (file counts, commit failures, freshness).
