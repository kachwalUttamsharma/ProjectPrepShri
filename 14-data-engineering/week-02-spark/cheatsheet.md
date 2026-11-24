# Spark cheatsheet

**Architecture**: driver (plan, schedule) -> cluster manager (YARN/K8s/standalone) -> executors (tasks, cache, shuffle files). 1 task = 1 partition on 1 core.

**Lazy**: transformations build a plan; actions (`count`, `collect`, `write`, `show`) run a job. Unused branches never run.

**Narrow** (no shuffle): map, filter, select, withColumn, union, coalesce, mapPartitions.
**Wide** (shuffle): groupBy, join, distinct, orderBy, repartition, window with partitionBy.
Stages = shuffle boundaries + 1. Tasks per stage = partitions.

**Partitions**: shuffle partitions `spark.sql.shuffle.partitions` (200 default). Target 100-200 MB each, 2-4x cores. `repartition` = shuffle, up or down. `coalesce` = no shuffle, down only.

**Joins**: broadcast (small side < threshold, no shuffle) > sort-merge (default large/large) > shuffle hash. Hint with `broadcast(df)`. Verify with `explain()`.

**Skew**: UI shows few straggler tasks. Fix: AQE skew join, broadcast, isolate hot/null keys, salt (N salts big side, replicate small x N), two-phase aggregation.

**Cache**: `cache()` = MEMORY_AND_DISK for DataFrames; only for reused data; `unpersist()`. Lazy: first action fills it.

**Catalyst** optimizes (pushdown, pruning); **Tungsten** executes (binary format, codegen). Prefer DataFrame/SQL over RDD.

**UDF**: built-in > pandas UDF (Arrow) > Python UDF (row at a time, opaque).

**OOM**: driver (collect/toPandas/big broadcast) vs executor (skew, few partitions, overhead too small). Spill = degraded but alive.

**Small files**: coalesce before write, compaction, AQE, avoid high-cardinality partitionBy.

**Config knobs** (check current docs): `spark.sql.adaptive.enabled`, `spark.sql.adaptive.skewJoin.enabled`, `spark.sql.autoBroadcastJoinThreshold`, `spark.sql.files.maxPartitionBytes`, `spark.executor.memoryOverhead`.

**Debug loop**: slow stage -> task min/median/max -> skew? spill? shuffle read? -> SQL tab plan -> fix.
