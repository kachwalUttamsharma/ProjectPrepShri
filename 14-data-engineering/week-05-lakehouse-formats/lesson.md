# Week 5: Lakehouse and File/Table Formats

Goal: explain, from the bytes up, why Parquet is fast, why object storage needs a table format, how Delta/Iceberg/Hudi give you ACID, and what operational chores (compaction, vacuum, snapshot expiry) they create. Version-specific defaults are marked "(check current docs)".

Python snippets here use only the stdlib and run on the venv python (`/Users/uttam.sharma/Desktop/python/.venv/bin/python`). pyarrow/Spark are not installed in the venv; real-library snippets are labeled "not run here".

---

## 1. Row vs columnar

| | Row-oriented (CSV, JSON, Avro, Postgres heap) | Columnar (Parquet, ORC, warehouse storage) |
|---|---|---|
| Layout | All fields of a record adjacent | All values of one column adjacent |
| Good at | Whole-record read/write, appends, streaming | Scans of a few columns, aggregations |
| Compression | Weak (mixed types) | Strong (homogeneous values: dictionary, RLE, delta) |
| Writes | Cheap per record | Buffer many rows, write in batches |
| Typical use | OLTP, Kafka messages, landing zone | Analytics, lake tables |

Rule of thumb: Avro (or JSON/Protobuf) on the wire and in the landing zone; Parquet (or ORC) for analytical storage.

## 2. Parquet internals

Structure (outside in):
- File: magic `PAR1` at start and end; footer holds schema, row-group/column-chunk metadata and statistics. Readers fetch the footer first (a ranged GET on S3), then only the byte ranges they need.
- Row group: horizontal slice of rows (commonly 128 MB uncompressed in Spark/parquet-mr defaults; check current docs). Unit of parallelism and of statistics-based skipping. Each task typically reads whole row groups.
- Column chunk: all values of one column within a row group.
- Page: unit of encoding/compression inside a chunk (about 1 MB default). Types: dictionary page, data pages. Newer files may also carry a column index / offset index for page-level skipping.
- Statistics: per column chunk (and per page with the page index): min, max, null count. Optional Bloom filters for high-cardinality equality lookups.

Encodings (applied before general compression):
- Dictionary (RLE_DICTIONARY): distinct values stored once, rows store small integer codes. Great for low-cardinality strings (country). Falls back to plain when the dictionary grows too big.
- RLE / bit-packing hybrid: repeated runs and small ints; also used for definition/repetition levels (nesting and nulls, from the Dremel model).
- Delta encodings (DELTA_BINARY_PACKED, DELTA_BYTE_ARRAY): sorted/monotonic ints, timestamps, similar strings.
- Then block compression: Snappy (fast, common default), ZSTD (better ratio, increasingly preferred), Gzip (slow, small), LZ4.

Predicate pushdown: the engine evaluates `WHERE` against footer min/max (row-group skip), page index (page skip), dictionary/Bloom filter (equality), and applies column projection so unread columns are never fetched. Effectiveness depends on data being sorted/clustered on the filter column: if every row group spans the full min..max range, nothing is skipped. This is why writing sorted data (or clustering/Z-ordering) matters.

Pitfalls:
- Too-small files and row groups: footer overhead, per-file request latency on S3, poor compression and weak stats.
- Wide string columns with high cardinality blow up dictionaries; large JSON blobs in a column kill scan speed.
- Schema mismatches across files (int vs long, decimal precision): reads fail or silently upcast; engine-specific "mergeSchema" options exist and are costly.
- Legacy INT96 timestamps and time zone semantics differ between engines (check current docs for each engine's setting).
- Parquet files are immutable: there is no in-place update. Updates mean rewriting files, which is exactly why table formats exist.

### Demo: row groups, dictionary + RLE, min/max pruning (stdlib)

```python
# Toy illustration (stdlib only): dictionary + RLE encoding, row-group min/max pruning
from itertools import groupby

rows = [{"day": f"2024-01-{d:02d}", "country": c, "amount": a}
        for d in range(1, 9) for c, a in (("IN", d), ("IN", d + 1), ("US", d * 2), ("US", d * 3))]
ROW_GROUP = 8

# columnar layout: one list per column, split into row groups
cols = {k: [r[k] for r in rows] for k in rows[0]}
groups = [{k: v[i:i + ROW_GROUP] for k, v in cols.items()} for i in range(0, len(rows), ROW_GROUP)]

def dict_rle(values):
    d = {v: i for i, v in enumerate(dict.fromkeys(values))}
    codes = [d[v] for v in values]
    return list(d), [(k, len(list(g))) for k, g in groupby(codes)]

# per-row-group statistics
stats = [{k: (min(g[k]), max(g[k])) for k in ("day", "amount")} for g in groups]
print("row groups:", len(groups))
print("dict+RLE country, group0:", dict_rle(groups[0]["country"]))

# predicate pushdown: WHERE day >= '2024-01-07'
want = "2024-01-07"
scan = [i for i, s in enumerate(stats) if s["day"][1] >= want]
print("groups scanned:", scan, "of", len(groups))
result = sum(a for i in scan for d, a in zip(groups[i]["day"], groups[i]["amount"]) if d >= want)
assert result == sum(r["amount"] for r in rows if r["day"] >= want)
print("sum(amount) day>=2024-01-07:", result)
```

Output (verified): 4 row groups; country dictionary `['IN','US']` with RLE runs; only 1 of 4 groups scanned for `day >= 2024-01-07`; sum 107.

Real-library version (not run here; needs `pip install pyarrow`):

```python
import pyarrow as pa, pyarrow.parquet as pq
t = pa.table({"day": ["2024-01-01"] * 4, "country": ["IN", "IN", "US", "US"], "amount": [1, 2, 3, 4]})
pq.write_table(t, "/tmp/t.parquet", row_group_size=2, compression="zstd")
md = pq.ParquetFile("/tmp/t.parquet").metadata
print(md.num_row_groups, md.row_group(0).column(2).statistics)   # min/max/null_count per column chunk
```

## 3. ORC and Avro

- ORC: columnar like Parquet (stripes ~64 MB or 256 MB depending on version, with built-in lightweight indexes every 10k rows, Bloom filters, file footer statistics). Hive-native, supports Hive ACID tables. Strong in Hive/Presto/Trino-on-Hadoop shops; Parquet has the broader ecosystem (Spark, Arrow, Iceberg default, Delta only Parquet).
- Avro: row-oriented, schema stored in the file header (JSON schema), compact binary, splittable blocks, rich schema evolution via reader/writer schema resolution (add field with default, remove field with default, aliases). The standard for Kafka messages with a schema registry. Not for analytical scans.
- Choose: Avro for streaming/landing and CDC payloads; Parquet for analytics; ORC if you are already in Hive with ACID.

## 4. Partitioning, clustering, Z-order

- Hive-style partitioning: directories `dt=2024-01-01/country=IN/`. The engine prunes directories from the path using filter predicates (partition pruning), which avoids even listing/opening files.
- Choose partition columns that are low cardinality, commonly filtered, and produce partitions of at least hundreds of MB. Date is the usual one. Bad: user_id (millions of tiny partitions), timestamps at second precision.
- Rule of thumb: if a partition holds less than about 1 GB at your scale, you probably partitioned too finely (check against your engine's guidance).
- Clustering / sorting within files: tightens min/max statistics for other columns. Z-ordering interleaves bits of several columns so rows near each other on multiple dimensions land in the same files (Delta `OPTIMIZE ... ZORDER BY (a, b)`). Gains diminish as you add columns; works best for 1-4 columns; rewrite cost is nontrivial. Newer alternatives: Delta liquid clustering, Iceberg sort orders and partition evolution, Hudi clustering (check current docs for each; they evolve quickly).
- Iceberg hidden partitioning: partition by transform (`days(ts)`, `bucket(16, user_id)`, `truncate`), users filter on the source column (`ts`), engine maps it. Partition spec can evolve without rewriting old data (old files keep the old spec).
- Bucketing (hash into N files by key): helps joins/aggregations without shuffle in some engines; fixed N is awkward; modern lakehouse engines lean on clustering instead.
- Hive-style partition columns appear in the path rather than the file: data type inference from paths can surprise you.

## 5. The small files problem

Cause: streaming micro-batches, over-partitioning, many tasks each writing a tiny file (`spark.sql.shuffle.partitions` mismatch), frequent upserts.
Cost: S3 request latency and listing cost per file, Spark task scheduling overhead (one task per small file/split), metadata (Hive metastore, manifest) bloat, worse compression and stats.
Fixes:
1. Right-size at write: repartition/coalesce before write, tune shuffle partitions, adaptive query execution (AQE) coalescing, Delta optimized writes / Iceberg write distribution mode (check current docs).
2. Compaction job: Delta `OPTIMIZE` (bin-packing, target about 1 GB by default, check current docs), Iceberg `rewrite_data_files`, Hudi compaction/clustering; schedule per partition after it is mostly "cold".
3. Streaming: longer trigger intervals, auto-compaction, separate "hot" and compacted layers.
4. Target file size roughly 128 MB to 1 GB, depending on engine and table size.
Compaction creates new files and marks old ones removed in the log. Old files stay until `VACUUM`/snapshot expiry (readers and time travel still need them), so storage temporarily grows.

## 6. Why a table format? (ACID on object storage)

Object storage (S3, GCS, ADLS) gives cheap, durable, scalable immutable objects. Problems when a "table" is just a directory of files:
- No atomic multi-file commit: a reader may see half a write.
- Listing is slow and (historically) eventually consistent; S3 now offers strong read-after-write consistency for objects (since Dec 2020), but there is still no atomic rename and listing a million files is slow.
- No row-level update/delete, no schema enforcement, no concurrent-writer protection, no history.

Table formats add a metadata layer (a transaction log or tree of manifests) that defines which files make up the table at each version. Commit = atomically publish new metadata that references new files. Readers use a snapshot of metadata, so they are isolated from in-flight writes (snapshot isolation). Writers use optimistic concurrency: read version N, write files, try to commit N+1; if someone else committed, check for conflicts and retry or fail.

Atomic commit on S3 needs a "put-if-absent" primitive. Delta on S3 historically needed a coordination service (DynamoDB LogStore) for multi-cluster writers; S3 now supports conditional writes and some engines use them (check current docs). Iceberg commits via the catalog (Glue, REST, Nessie, Hive) which does an atomic pointer swap to the new metadata file.

### Demo: a toy transaction log (stdlib)

```python
# Toy transaction log (Delta/Iceberg-flavoured): snapshots, time travel, optimistic commit, compaction
class Table:
    def __init__(self):
        self.log = []          # list of commits; each: {"add": set(files), "remove": set(files)}
        self.files = {}        # file name -> list of rows (immutable once written)
        self.n = 0
    def _write(self, rows):
        self.n += 1; name = f"part-{self.n:04d}.parquet"; self.files[name] = list(rows); return name
    def snapshot(self, version=None):
        v = len(self.log) if version is None else version + 1
        live = set()
        for c in self.log[:v]:
            live |= c["add"]; live -= c["remove"]
        return live
    def commit(self, base_version, add, remove):
        # optimistic concurrency: fail if someone committed since we read
        if base_version != len(self.log) - 1:
            raise RuntimeError("conflict: table moved, retry")
        self.log.append({"add": set(add), "remove": set(remove)})
    def read(self, version=None):
        return [r for f in sorted(self.snapshot(version)) for r in self.files[f]]

t = Table()
t.commit(-1, [t._write([1, 2])], [])           # v0
t.commit(0, [t._write([3])], [])               # v1
t.commit(1, [t._write([4])], [])               # v2 -> 3 small files
print("files v2:", len(t.snapshot()))
# compaction: rewrite small files into one, remove old ones (data unchanged)
old = t.snapshot()
t.commit(2, [t._write([r for f in sorted(old) for r in t.files[f]])], old)  # v3
print("files v3:", len(t.snapshot()), "rows:", t.read())
print("time travel v1:", t.read(1))
try:
    t.commit(2, [], [])                        # stale writer
except RuntimeError as e:
    print("stale writer:", e)
# 'vacuum' = physically delete files not referenced by any retained snapshot
```

Output (verified): 3 files, compaction yields 1 file, time travel to v1 returns `[1, 2, 3]`, the stale writer is rejected. This is the essence of Delta/Iceberg: immutable data files + an ordered log of add/remove + optimistic commit.

## 7. Delta vs Iceberg vs Hudi

| | Delta Lake | Apache Iceberg | Apache Hudi |
|---|---|---|---|
| Metadata | `_delta_log/` JSON commits + periodic Parquet checkpoints (actions: add, remove, metaData, protocol, txn) | Catalog pointer -> table metadata JSON -> manifest list -> manifests -> data files; snapshots | `.hoodie/` timeline of instants (commit, deltacommit, compaction, clean...) |
| Origin / strength | Databricks; best on Spark/Databricks, broad connectors now | Netflix; engine-neutral, hidden partitioning, partition evolution, big multi-engine adoption (Spark, Flink, Trino, Athena, Snowflake, BigQuery, etc.) | Uber; record-level upserts/CDC, incremental pulls, streaming ingestion |
| Row-level changes | Copy-on-write rewrite; deletion vectors (merge-on-read-like) in newer versions (check current docs) | CoW or MoR via position/equality delete files (spec v2); deletion vectors in v3 (check current docs) | CoW or MoR table types; log files merged by compaction |
| Time travel | `VERSION AS OF`, `TIMESTAMP AS OF`; retention governed by log + file retention | Snapshots by id/timestamp, branches and tags | Time travel by instant; incremental queries |
| Schema evolution | add/rename/drop with column mapping; enforcement on write | By column ID: add, drop, rename, reorder, widen types safely | Supported, engine-dependent |
| Maintenance | `OPTIMIZE`, `VACUUM`, checkpoints | `rewrite_data_files`, `rewrite_manifests`, `expire_snapshots`, `remove_orphan_files` | compaction, clustering, cleaning, archival |
| Primary index | none | none | record key + index (bloom, bucket, etc.) |

Note: Delta UniForm and Apache XTable aim to expose one table through several format interfaces. Formats converge quickly; verify feature claims (check current docs).

### Copy-on-write vs merge-on-read
- CoW: an update rewrites the affected data files. Reads are simple and fast; writes are slower and amplify (update 1 row, rewrite a 128 MB file). Best for read-heavy, batch-updated tables.
- MoR: updates/deletes written as small delta/delete files; merged at read time or by background compaction. Writes are fast; reads pay merge cost until compaction. Best for frequent small updates and CDC/streaming upserts.
- The knob is write amplification vs read amplification. Compaction is the debt you pay later.

### Schema evolution gotchas
- Safe: add nullable column, widen int->long, rename (formats with column IDs/mapping handle renames without breaking old files).
- Dangerous: changing types incompatibly, dropping a column other readers need, reusing a column name for a different meaning. Parquet files written before the change must still be readable (Iceberg tracks by field ID, plain Parquet by name or position).
- Schema enforcement on write (reject mismatches) vs evolution (opt in with `mergeSchema` or `ALTER TABLE`).

### Time travel, snapshots, vacuum
- Each commit produces a new version/snapshot. Query old versions for audit, debugging, rollback, reproducing ML training sets.
- Retention is finite: old data files are physically deleted by `VACUUM` (Delta; default 7 day retention, check current docs) or `expire_snapshots` + `remove_orphan_files` (Iceberg). After that, time travel to those versions fails.
- Pitfalls: vacuuming with a retention shorter than the longest-running reader/stream breaks them; GDPR deletes require removing old file versions too (delete then vacuum/expire).
- Deleting S3 files manually corrupts the table (log points at missing files).

## 8. Data lake vs warehouse vs lakehouse

| | Data lake | Warehouse | Lakehouse |
|---|---|---|---|
| Storage | Files in object store | Managed proprietary (or managed external) | Files in object store + table format |
| Schema | Schema on read | Schema on write | Enforced, evolvable |
| ACID / updates | No | Yes | Yes (via format) |
| Data types | Structured, semi, unstructured | Mostly structured | All |
| Engines | Many | Vendor's | Many (Spark, Trino, Flink, warehouse engines) |
| Governance | Ad hoc | Strong | Catalog-based (Unity, Glue + Lake Formation, Polaris) |
| Risk | "Data swamp" | Lock-in, cost, ML access | Operational complexity (maintenance, small files) |

Honest take: lakehouse = open file format + table format + catalog + any engine. The warehouse engines now read Iceberg too, so the boundary blurs. Pick based on team skills, workloads (BI vs ML vs streaming), governance and cost.

## 9. Medallion architecture

- Bronze: raw, append-only, as landed (plus ingestion metadata: source, load time, batch id). Keep schema loose; retains replay ability.
- Silver: cleaned, deduplicated, typed, conformed; business keys resolved; joins of related entities. Quality checks and quarantine of bad rows.
- Gold: business-level aggregates, star schemas and feature tables for BI/ML.
- Rules: each layer is reproducible from the previous; idempotent writes (MERGE / partition overwrite); contract and tests at layer boundaries. It is a convention, not a product: names vary (raw/staging/marts). Do not add layers without a reason (every layer costs storage, latency, and ownership).

## 10. Catalogs

A catalog maps table names to locations/metadata and holds schema, partitions and permissions.
- Hive Metastore (HMS): the classic. Stores table schema and partition locations in an RDBMS; used by Spark, Hive, Presto/Trino. Weak at huge partition counts; not transactional for multi-table.
- AWS Glue Data Catalog: managed, HMS-compatible catalog; used by Athena, EMR, Glue ETL, Redshift Spectrum; integrates with Lake Formation; has Iceberg support.
- Unity Catalog (Databricks): metastore plus governance (grants, lineage, row/column security, volumes, models) across workspaces; has open-source variant.
- Iceberg REST catalog, Nessie (git-like branches), Apache Polaris, Snowflake's catalog integrations: aim for engine-neutral access (check current docs).
- Catalog is a critical dependency and the atomic-commit authority for Iceberg: pick a managed or highly available one. Migrating catalogs is possible (table registration) but needs planning.

## 11. AWS tie-ins

- S3: data lake storage; prefixes, storage classes (Standard, IA, Glacier tiers), lifecycle policies, versioning, SSE-S3/SSE-KMS encryption, bucket policies, VPC endpoints. Strong read-after-write consistency. Request-rate limits are per prefix (thousands of requests/s; check current docs); many small files hurt.
- Glue: Data Catalog, crawlers (infer schema/partitions; convenient, but can drift schemas and cost; many teams prefer explicit DDL/IaC), ETL jobs (managed Spark or Python shell), workflows, schema registry (for Kafka/Kinesis).
- Athena: serverless interactive SQL (Trino/Presto lineage; engine versions change, check current docs) over S3 using the Glue catalog. Billed by data scanned: columnar format + compression + partition pruning + column selection cut cost. Features: CTAS, partition projection (avoids metastore partition lookups for predictable layouts), Iceberg tables with MERGE/OPTIMIZE/VACUUM.
- EMR: managed Spark/Hive/Flink/Trino clusters (EC2, EKS, or Serverless); for heavy ETL, custom libs, tuning control. Use Glue Catalog as metastore; spot for task nodes.
- Redshift Spectrum: query S3 external tables from Redshift (Glue catalog); joins local warehouse tables with lake data. Scan-priced; pushes filters down to Spectrum layer.
- Lake Formation: central permissions on Glue catalog databases/tables/columns/rows (row and cell filters, LF-tags for tag-based access) enforced across Athena, EMR, Redshift Spectrum, Glue. Also governed data sharing. Replaces scattered S3 bucket policies for table-level access.
- Related: Kinesis/MSK to Firehose into S3 (Parquet conversion), DMS for CDC into S3, S3 Tables (managed Iceberg; check current docs), EventBridge triggers.
- Typical reference design: sources -> (DMS/Kafka/Firehose) -> S3 bronze (Avro/JSON/Parquet) -> Glue/EMR Spark jobs -> S3 silver/gold as Iceberg or Delta (Glue Catalog) -> Athena/Redshift/QuickSight; Lake Formation governs access; CloudWatch/Airflow (MWAA) orchestrate.

## 12. Operations checklist for a lakehouse table
1. Format and partition spec chosen from query filters, not from ingestion convenience.
2. Target file size and compaction schedule.
3. Snapshot expiry/vacuum retention with documented time-travel window.
4. Schema change policy and contract.
5. Idempotent write path (MERGE keys or partition overwrite).
6. Concurrency expectations (single writer? concurrent MERGEs may conflict).
7. Access control via catalog, encryption, audit.
8. Monitoring: file counts and size distribution, table growth, commit failures, stale data.
