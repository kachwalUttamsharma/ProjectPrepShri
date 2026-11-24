# Week 5 Interview Q&A: Lakehouse and Formats

Cover the answer, say yours out loud, then compare. Version-specific defaults: check current docs.

---

**1. Why is Parquet faster than CSV/JSON for analytics?**
Columnar layout means only needed columns are read; typed, compressed (dictionary, RLE, delta + Snappy/ZSTD) data is much smaller; footer statistics allow skipping row groups; no parsing of text. Probe: "When is CSV/JSON fine?" Tiny data, interchange, landing zone where you need human readability.

**2. Describe the structure of a Parquet file.**
Magic bytes, row groups, each containing column chunks, each made of pages (dictionary + data pages), then a footer with schema and per-chunk metadata and statistics. Readers read the footer first, then byte ranges for needed columns/row groups.

**3. How does predicate pushdown work and when does it fail?**
Engine compares filter to min/max (and page index, dictionary, Bloom filter) to skip row groups/pages. Fails when data is not clustered on the filter column (min/max ranges overlap everywhere), on functions applied to the column (`WHERE date(ts) = ...` may block pushdown in some engines), on non-sargable expressions, or with high-cardinality strings lacking Bloom filters. Fix: sort/cluster/Z-order on filter columns, write predicates in a pushdown-friendly form.

**4. What are Parquet encodings and when does dictionary encoding stop helping?**
Dictionary (distinct values + codes), RLE/bit-pack, delta. Dictionary helps low-cardinality columns; for high-cardinality columns the dictionary grows, writers fall back to plain encoding, and gain disappears.

**5. Row group size trade-offs?**
Large row groups: better compression, fewer metadata entries, but more memory to write/read and coarser skipping. Small: finer skipping but more overhead and worse compression. Defaults are often about 128 MB (check current docs); align with HDFS/S3 read size and executor memory.

**6. Parquet vs ORC vs Avro?**
Parquet and ORC: columnar for analytics (Parquet has the widest ecosystem; ORC strong with Hive ACID). Avro: row-based with embedded schema and great schema evolution; ideal for Kafka and CDC payloads, poor for scans.

**7. How does Avro schema evolution work?**
Writer schema is stored with the data (or in a registry); reader supplies its own schema; resolution matches fields by name, uses defaults for fields missing in the writer data and ignores fields unknown to the reader. Backward compatible changes: add field with default, remove field with default. Registry compatibility modes (backward, forward, full) enforce this.

**8. Partitioning vs clustering vs Z-order?**
Partitioning: directory-level split on low-cardinality columns for exact pruning. Clustering/sorting: orders data within files for tight stats on other columns. Z-order: multi-column locality via bit interleaving, for filters on several columns, at the cost of an expensive rewrite and diminishing returns with more columns. Newer: liquid clustering, Iceberg partition evolution (check current docs).

**9. How would you choose a partition column for a 5 TB/day events table?**
Event date (maybe plus a coarse, bounded column like region if queries always filter on it and partitions stay large). Not user_id. Cluster/sort by commonly filtered high-cardinality columns. Verify with actual query patterns and partition sizes.

**10. What is the small files problem, symptoms, and fix?**
Many tiny files: slow listing, high S3 request counts, task-scheduling overhead, poor compression and stats. Symptoms: planning takes minutes, thousands of tiny tasks. Fix at write (repartition/coalesce, AQE, optimized writes, longer streaming triggers) and with scheduled compaction (OPTIMIZE / rewrite_data_files). Target about 128 MB-1 GB files. Cleanup of old files via vacuum/expire.
Probe: "Does compaction block readers?" No, it commits a new snapshot; readers on older snapshots keep working until files are vacuumed. Concurrent writers may conflict, so schedule/partition-scope compaction.

**11. Why can't you just use Parquet files in S3 as a table?**
No atomic multi-file commit, no isolation (readers see partial writes), no row-level update/delete, no schema enforcement or history, slow listing, no safe concurrent writers. Table formats add a transaction log/manifest layer.

**12. Explain how Delta Lake achieves ACID.**
`_delta_log` holds ordered JSON commit files (actions: add/remove file, metadata, protocol) with periodic Parquet checkpoints. A table version = replay of the log. Writers write data files first, then atomically create the next log file (needs put-if-absent semantics); on conflict, validate and retry or fail (optimistic concurrency). Readers snapshot a version.

**13. Explain Iceberg's metadata structure.**
Catalog holds pointer to current metadata JSON; metadata lists snapshots; each snapshot references a manifest list; manifest list references manifests; manifests list data/delete files with column-level stats and partition values. Commit = atomic swap of the catalog pointer. Planning uses manifest stats to prune files without listing directories.

**14. What is Hudi's niche?**
Record-level upserts/deletes with a record key and precombine field, built-in indexing, MOR/COW table types, incremental pull queries, streaming-style ingestion; strong for CDC into the lake. Timeline of instants instead of snapshots.

**15. How do you choose between Delta, Iceberg, Hudi?**
Ecosystem and engine mix first (Databricks-centric: Delta; multi-engine, Snowflake/Trino/Athena/Flink: Iceberg; heavy CDC upserts on EMR/Spark: Hudi), then features (partition evolution, deletion vectors, governance), catalog support, team skills. Formats are converging and bridges exist (UniForm, XTable; check current docs). Do not claim a "winner" without context.

**16. Copy-on-write vs merge-on-read?**
CoW rewrites files on update: simple fast reads, heavy writes. MoR writes delta/delete files merged at read or compaction: fast writes, slower reads until compaction. Choose by update frequency and read latency needs.

**17. How does time travel work and what limits it?**
Old snapshots/versions still reference older data files, so you can read them by version/timestamp. Limited by retention: vacuum/expiry deletes files no longer referenced by retained snapshots. Long retention costs storage; GDPR deletions require expiring old snapshots.

**18. What does VACUUM do and what can go wrong?**
Deletes files no longer referenced by the retained table versions (older than the retention threshold). Danger: vacuuming below the duration of long readers/streams or concurrent writes causes failures; deleting files manually corrupts the table. Default retention 7 days in Delta (check current docs).

**19. How does schema evolution work, and what breaks it?**
Add columns, widen types, rename/drop depending on format support (Iceberg uses column IDs; Delta uses column mapping). Breaks: incompatible type changes, reusing names, downstream readers pinned to old schema, schema-on-read by position in CSV. Use a contract, enforcement on write, and a controlled evolution path.

**20. How do you handle concurrent writers?**
Optimistic concurrency with conflict detection: non-overlapping partitions/files usually commit fine; overlapping updates fail and retry. Design: one writer per partition, retry with backoff, narrow MERGE predicates (include partition column in the condition), queue/serialize writers on hot tables.

**21. What is the medallion architecture and its criticisms?**
Bronze raw, silver cleaned/conformed, gold business-ready. Benefits: replayability, clear quality gates. Criticisms: more layers than needed adds latency and cost; "silver" is vague; ownership unclear. Use only the layers you can justify and define contracts per layer.

**22. Data lake vs warehouse vs lakehouse in one answer.**
Lake: cheap files, schema on read, no ACID. Warehouse: managed, schema on write, ACID, SQL-first. Lakehouse: lake storage with a table format and catalog to get ACID/governance for BI and ML on the same data with multiple engines. Trade-off is operational burden (compaction, catalog, permissions).

**23. What does a catalog do and why does it matter?**
Name-to-location mapping, schemas, partition metadata, permissions, sometimes lineage. For Iceberg the catalog is also the atomic commit point. Options: Hive Metastore, Glue, Unity, REST/Polaris/Nessie. Matters for interoperability (every engine must reach it), governance and availability.

**24. How do you cut Athena cost?**
Convert to Parquet/ORC with compression, partition and prune, select only needed columns, use partition projection, compact small files, use CTAS to materialize, workgroup data-scanned limits, and pick Iceberg for efficient planning. Athena bills by data scanned (check current docs for price).

**25. Glue crawlers: good or bad?**
Convenient for discovery, but they can infer unstable schemas and mis-detect partitions, cost money, and make schema changes implicit. Prefer explicit DDL/IaC and schema contracts for production tables; crawlers for exploration.

**26. How does Lake Formation fit with Athena, EMR and Redshift Spectrum?**
It is the permission layer over Glue catalog resources: grant table/column/row permissions (and LF-tags) to IAM principals; integrated engines enforce them, avoiding raw S3 access grants. Probe: "What if a user can read S3 directly?" Then LF is bypassed; lock down bucket access so only trusted engines/roles read data.

**27. Design a lakehouse on AWS for CDC from Postgres.**
DMS (or Debezium into MSK) -> S3 bronze (Parquet/Avro with op, ts, lsn) -> Spark (Glue/EMR) MERGE into silver Iceberg/Delta/Hudi tables keyed by primary key, handling out-of-order events via source LSN/timestamp and deletes via tombstones -> gold marts for Athena/Redshift -> Lake Formation for access, compaction and snapshot expiry scheduled, data quality checks, orchestration with Airflow/MWAA. Discuss initial snapshot plus change stream handoff and schema evolution.

**28. A dashboard on Athena got 20x slower overnight. Debug.**
Check file count and size distribution in the partition (small-file explosion from a new streaming job), partition projection or partition metadata missing, a schema change breaking pushdown, query changed to `SELECT *`, concurrency/queue limits, and recent compaction failure. Look at bytes scanned and execution stats per stage.

**29. How do you do GDPR delete in a lakehouse?**
Row-level DELETE/MERGE (rewrite or deletion vectors), then expire old snapshots/vacuum so prior file versions with the data are physically removed; also handle bronze raw files, backups and derived tables. Track subject-to-file mapping if deletes are frequent. Encryption-key-per-subject (crypto shredding) is an alternative.

**30. What are the risks of Z-ordering/clustering everywhere?**
Rewrite cost grows with table size; benefits fade with many columns or filters on non-clustered columns; ongoing maintenance on frequently updated data. Measure files skipped before/after.

---

## Drills
- Draw Iceberg metadata tree and Delta log from memory (2 min each).
- Explain compaction + vacuum + time travel interaction in 60 seconds.
- Given 3 query patterns, choose partition and sort columns and defend.
