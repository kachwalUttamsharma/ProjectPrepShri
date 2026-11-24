# Week 2: Spark

pyspark is not installed here. Code blocks below are **not run here**; they show what you would write on a real cluster. The exercises simulate the same ideas in plain Python so you can test your understanding offline.

## 1. Architecture
- **Driver**: runs your `main`, builds the plan (DAG), schedules tasks, holds the SparkSession. A single point of failure; collecting big data to it causes driver OOM.
- **Executors**: JVM processes on workers that run **tasks** and hold cached data and shuffle files. Each has cores (parallel task slots) and memory.
- **Cluster manager**: allocates resources (YARN, Kubernetes, standalone, Mesos is deprecated; managed offerings like Databricks/EMR wrap these).
- Deploy mode: client (driver on submitter) vs cluster (driver on the cluster).
- Parallelism = executors x cores per executor. A task processes exactly one partition.

## 2. Lazy evaluation, transformations, actions
- **Transformations** (`select`, `filter`, `withColumn`, `join`, `groupBy().agg`) only build a logical plan and return a new immutable DataFrame.
- **Actions** (`count`, `collect`, `show`, `write`, `take`) trigger a job.
- Why lazy: Spark sees the whole plan and can prune columns, push filters down, and fuse steps (Catalyst).
- Consequence: an expensive DataFrame used by two actions is computed twice unless cached.

```python
# not run here
from pyspark.sql import SparkSession, functions as F
spark = SparkSession.builder.appName("demo").getOrCreate()

orders = spark.read.parquet("s3://bucket/orders/")           # no data read yet (schema only)
big = orders.filter(F.col("amount") > 100).select("user_id", "amount")  # still lazy
big.explain(True)             # parsed -> analyzed -> optimized -> physical plan
big.groupBy("user_id").agg(F.sum("amount").alias("total")).write.mode("overwrite").parquet("out/")  # action
```

## 3. Narrow vs wide, DAG, stages, tasks
- **Narrow dependency**: each output partition depends on one input partition (`map`, `filter`, `select`, `union`, `coalesce`). Pipelined in memory, no network.
- **Wide dependency**: output partition depends on many inputs (`groupBy`, `join` (non-broadcast), `distinct`, `orderBy`, `repartition`). Requires a **shuffle**: write partitioned map output to local disk, then fetch over the network.
- **Job** = one action. **Stage** = a run of narrow ops between shuffles. **Task** = one stage applied to one partition. Stages = shuffles + 1 along a linear chain.
- Shuffles are the main cost: disk I/O, serialization, network, plus skew risk. Minimise and place them wisely (filter before the shuffle, pre-aggregate).

## 4. Partitions
- Input partitions follow file splits (`spark.sql.files.maxPartitionBytes`, default 128 MB, check current docs).
- After a shuffle, partitions = `spark.sql.shuffle.partitions` (default 200; with AQE it is coalesced at runtime, check current docs).
- Rule of thumb: partitions about 2-4x total cores, each roughly 100-200 MB. Too few: idle cores, OOM, spill. Too many: scheduling overhead, tiny files.
- `repartition(n[, cols])`: full shuffle, can grow or shrink, balances data. `coalesce(n)`: only merges existing partitions, no shuffle, can only shrink, can leave imbalance.
- `repartition("col")` hash-partitions by column (co-locates keys); `partitionBy` on **write** controls directory layout, a different thing.

## 5. Joins
| Strategy | When | Cost |
|---|---|---|
| Broadcast hash join | one side small (under `spark.sql.autoBroadcastJoinThreshold`, default 10 MB, check current docs) | no shuffle of the big side; small side sent to every executor |
| Sort-merge join | default for two large sides, equi-joins | shuffle + sort both sides; scales, spills safely |
| Shuffle hash join | one side noticeably smaller but too big to broadcast | shuffle both, build hash table per partition; OOM risk |
| Broadcast nested loop / cartesian | non-equi joins | very expensive |

```python
# not run here
from pyspark.sql.functions import broadcast
enriched = events.join(broadcast(dim_country), "country_code", "left")
```
Join hints: `broadcast`, `merge`, `shuffle_hash`, `shuffle_replicate_nl`. Always check `explain()` for `BroadcastHashJoin` vs `SortMergeJoin`.

## 6. Data skew
Symptom: in the Spark UI stage page, most tasks finish in seconds while a few run for minutes; max task time and shuffle read are far above the median.
Causes: hot keys (null, "unknown", a celebrity user), bad partition column.
Fixes, in the order to try:
1. **AQE skew join** (Spark 3+): `spark.sql.adaptive.enabled` + `spark.sql.adaptive.skewJoin.enabled` splits oversized shuffle partitions at runtime.
2. **Broadcast** the smaller side (removes the shuffle).
3. **Filter or handle hot keys separately** (nulls never match in joins anyway: drop or split them out).
4. **Salting**: append a random 0..N-1 suffix to the hot key on the big side, replicate the small side N times, join on (key, salt), then (for aggregations) aggregate again to remove the salt.
5. Pre-aggregate before the join; increase shuffle partitions.

```python
# not run here: salting an aggregation (two-phase)
N = 8
salted = df.withColumn("salt", (F.rand() * N).cast("int"))
partial = salted.groupBy("user_id", "salt").agg(F.sum("amt").alias("s"))
final = partial.groupBy("user_id").agg(F.sum("s").alias("total"))
```

## 7. Caching
- `df.cache()` = `persist(MEMORY_AND_DISK)` for DataFrames (lazy: filled by first action). `persist(StorageLevel.X)`: `MEMORY_ONLY`, `MEMORY_AND_DISK`, `DISK_ONLY`, `_SER` variants, `_2` replicated (levels vary by API/version, check current docs).
- Cache only data reused multiple times and expensive to recompute. `unpersist()` when done.
- Caching is not free: it uses executor storage memory, evicts LRU, and a lost executor means recompute from lineage.
- `checkpoint()` truncates lineage by writing to reliable storage (long iterative jobs).

## 8. API levels, Catalyst, Tungsten
- **RDD**: low-level, typed objects, no optimizer, Python RDDs pay serialization costs. Use rarely.
- **DataFrame**: rows with a schema; goes through **Catalyst** (logical plan -> optimizer rules such as predicate pushdown, column pruning, constant folding, join reordering -> physical plan, plus cost-based choices). Execution on **Tungsten**: off-heap binary format and whole-stage code generation.
- **Dataset**: typed API, Scala/Java only. In PySpark you use DataFrames.
- SQL, DataFrame and Dataset code compile to the same plans; prefer them over RDDs.

## 9. Window functions
```python
# not run here
from pyspark.sql.window import Window
w = Window.partitionBy("user_id").orderBy(F.col("ts").desc())
latest = (events.withColumn("rn", F.row_number().over(w))
                .filter("rn = 1").drop("rn"))             # latest row per user
running = events.withColumn("running", F.sum("amt").over(
    Window.partitionBy("user_id").orderBy("ts").rowsBetween(Window.unboundedPreceding, Window.currentRow)))
```
A window partition is shuffled to one task: a window without `partitionBy` puts all data in a single partition. `rank` vs `dense_rank` vs `row_number`; `lag`/`lead` for deltas.

## 10. UDF pitfalls
- A Python UDF is a black box to Catalyst (no pushdown, no codegen) and ships each row JVM <-> Python worker (pickle).
- Prefer built-ins (`F.when`, `F.regexp_extract`, `F.transform`, SQL expressions). Next best: **pandas UDF** (Arrow, vectorised, `@pandas_udf`) or `applyInPandas`. Scala UDFs are cheaper than Python ones.
- UDFs must be deterministic (or marked non-deterministic), handle nulls, and avoid large closures (they are serialized per task).

## 11. Memory, OOM, spill
- Executor memory = heap (execution + storage in a unified region, `spark.memory.fraction`) + overhead (off-heap, Python workers; `spark.executor.memoryOverhead`). YARN/K8s killing a container usually means overhead too small.
- **Spill**: when shuffle/sort/aggregation does not fit, data is written to disk. Visible as "Spill (memory/disk)" in the UI. Slow but alive; heavy spill means too few/too large partitions.
- Driver OOM: `collect()`, `toPandas()`, big broadcast variables, huge number of partitions/files in the plan.
- Executor OOM: skewed partitions, huge groups in `collect_list`, shuffle hash join build side, too few partitions.

## 12. Small files
Thousands of tiny files hurt: listing cost, a task per file, NameNode/S3 request pressure. Causes: too many shuffle partitions at write, high-cardinality `partitionBy`, streaming micro-batches. Fixes: `coalesce`/`repartition` before write, `maxRecordsPerFile`, AQE coalescing, table compaction (Delta `OPTIMIZE`, Iceberg `rewrite_data_files`). The opposite: one huge unsplittable gzip file means one task.

## 13. Reading the Spark UI
- **Jobs / Stages**: duration, shuffle read/write, spill, GC time. Compare min/median/max task durations: a big gap = skew.
- **SQL tab**: the physical plan with metrics; find the join type, rows output per node, whether filters were pushed down (`PushedFilters`).
- **Executors**: memory use, GC time, failed tasks, dead executors.
- **Storage**: what is cached and what fraction.
- Debug order: which stage is slow -> skew or spill or shuffle-bound? -> which operator in the SQL plan -> fix (partitioning, join type, caching).

## 14. Structured Streaming pointer
Same DataFrame API on unbounded input: `readStream`, triggers, output modes (append/update/complete), event-time windows + **watermark** for late data, **checkpoints** for state and offsets, exactly-once sinks via idempotent/transactional writes. Out of scope for the exercises; know the vocabulary.

## 15. Exercises map
1 hash_partition, 2 wordcount_shuffle, 3 skew detection, 4 broadcast vs shuffle join, 5 salted join, 6 LazyDataset, 7 narrow/wide + stages, 8 partition sizing, 9 coalesce vs repartition, 10 row_number window.
