# Week 2 interview Q&A: Spark

**1. Explain Spark architecture.**
A driver builds the logical/physical plan and a DAG, and schedules tasks. A cluster manager (YARN, Kubernetes, standalone) provides executors: JVMs with cores and memory that run tasks, cache partitions, and store shuffle files. One task processes one partition on one core.
*Follow-ups:* What lives only on the driver? What happens if an executor dies (lineage recompute, shuffle files lost unless an external shuffle service)? Client vs cluster deploy mode?

**2. What is lazy evaluation and why does Spark use it?**
Transformations only extend a plan; actions trigger execution. Seeing the whole plan lets Catalyst prune columns, push predicates to the source, reorder joins and pipeline narrow steps into one stage.
*Follow-ups:* How do you accidentally run a pipeline twice? (Two actions on an uncached DataFrame.) Is `read` an action? (Schema inference may trigger a small job.)

**3. Transformation vs action; give examples and a trap.**
Transformations: select, filter, join, groupBy. Actions: count, collect, write, show. Trap: `df.count()` for a debug print in production code doubles the work; `collect()` on big data kills the driver.
*Follow-up:* Is `cache()` an action? No, it is lazy.

**4. Narrow vs wide dependency. Why does it matter?**
Narrow: a partition depends on one parent partition, so steps are pipelined and recompute is cheap. Wide: needs data from many partitions, so a shuffle (disk + network) and a stage boundary. Fewer wide operations means faster jobs and cheaper failure recovery.
*Follow-ups:* Is `join` always wide? (Broadcast join is not; pre-partitioned bucketed tables can also avoid it.) Is `coalesce` narrow? Yes.

**5. How is a job split into stages and tasks?**
An action creates a job; the DAG scheduler cuts it at shuffle boundaries into stages; each stage has one task per partition. Number of tasks of a stage = number of partitions of its final RDD.
*Follow-up:* A stage has 200 tasks and 50 cores: how many waves? (4.) Why can adding cores not fix one slow task?

**6. What is a shuffle and why is it expensive?**
Redistribution of data by key: map tasks write partitioned files to local disk, reduce tasks fetch blocks over the network, with serialization, sorting/aggregation and possible spill. It also is a barrier between stages.
*Follow-ups:* How to reduce shuffle? (Filter early, pre-aggregate with `reduceByKey`/partial aggregation, broadcast joins, bucketing, avoid needless `repartition`.) What is the external shuffle service for?

**7. repartition vs coalesce.**
`repartition(n)` does a full shuffle, produces balanced partitions, can increase or decrease. `coalesce(n)` merges partitions without a shuffle, only decreases, can leave imbalance. Use coalesce to reduce output files cheaply, repartition to fix skew or increase parallelism.
*Follow-ups:* Why might `coalesce(1)` before a heavy transformation be harmful? (It collapses upstream parallelism too, as the stage is fused.) What does `repartition("key")` do?

**8. How do you choose the number of partitions?**
Aim for 100-200 MB partitions and a few times the total core count; tune `spark.sql.shuffle.partitions` or rely on AQE coalescing. Too few: spill/OOM and idle cores. Too many: scheduler overhead and small output files.
*Follow-up:* How do input partitions get decided? (File splits, `maxPartitionBytes`; non-splittable formats such as gzip give one partition per file.)

**9. Describe Spark's join strategies and how it picks one.**
Broadcast hash join when one side is below the broadcast threshold (or hinted); sort-merge join as the default for large equi-joins; shuffle hash join when one side is much smaller; nested loop/cartesian for non-equi conditions. Choice is driven by size statistics, hints, and with AQE can switch at runtime (e.g. sort-merge to broadcast).
*Follow-ups:* Why is sort-merge safer than shuffle hash? (Can spill; no in-memory hash table.) What goes wrong when broadcasting a table that is too large? (Driver/executor OOM, timeouts.) How do you check what was used? (`explain()`, SQL tab.)

**10. A join stage has 199 tasks done in 20 s and one running for 40 min. Diagnose and fix.**
Data skew: one key dominates one partition. Confirm in the stage task metrics (max vs median shuffle read) and by counting keys. Fixes: enable AQE skew join; broadcast the other side if possible; handle null/default keys separately; salt the hot key (random salt on the big side, replicate the small side); pre-aggregate before joining.
*Follow-ups:* Why does salting an aggregation need two phases? How do you salt only hot keys? What if both sides are huge and skewed? (Salt with replication on the smaller side for the hot keys only, or split into hot/cold joins.)

**11. What is AQE?**
Adaptive Query Execution (Spark 3+) re-optimizes using runtime shuffle statistics: coalesces small shuffle partitions, switches join strategy, splits skewed partitions. Enabled by default in recent versions (check current docs).
*Follow-up:* What can it not fix? (Skew in aggregations is not split the same way, bad data layout, UDF cost.)

**12. cache vs persist vs checkpoint.**
`cache()` is `persist` with the default level (MEMORY_AND_DISK for DataFrames). `persist` lets you choose level (memory only, disk, serialized, replicated). Both keep lineage and are lost with the application. `checkpoint` writes to reliable storage and truncates lineage.
*Follow-ups:* When does caching hurt? (Used once, or big enough to evict other data and trigger GC.) Is the cache populated immediately? No.

**13. RDD vs DataFrame vs Dataset.**
RDD: low level, no schema, no Catalyst; you control everything but get no optimization. DataFrame: schema'd rows, optimized by Catalyst and executed by Tungsten. Dataset: JVM-typed objects plus the optimizer (Scala/Java only). In PySpark use DataFrames; reach for RDDs only for truly unstructured custom logic.
*Follow-up:* Why is a Python RDD map slower than a DataFrame expression? (Serialization to Python workers per row, no codegen.)

**14. What are Catalyst and Tungsten?**
Catalyst: rule-based and cost-based optimizer turning the parsed plan into an optimized logical plan then physical plans (predicate pushdown, column pruning, constant folding, join selection). Tungsten: execution engine work: binary memory layout, off-heap memory management, cache-friendly operations, whole-stage code generation.
*Follow-up:* What does `explain(True)` show? What blocks pushdown? (Python UDFs on the filter column, some casts.)

**15. Why are Python UDFs slow and what are the alternatives?**
Opaque to Catalyst and row-at-a-time serialization between JVM and Python. Use built-in functions or SQL expressions first; then pandas UDFs (Arrow batches, vectorised) or `mapInPandas`/`applyInPandas`; or a Scala UDF.
*Follow-ups:* How do UDFs affect null handling and determinism? Why can they break predicate pushdown/optimization?

**16. Window functions: how are they executed and what is the pitfall?**
Data is shuffled by the `partitionBy` keys and sorted by `orderBy` within each partition. A window with no `partitionBy` moves everything into one partition (single task). Hot partition keys cause skew. `row_number` filtered to 1 is the standard "latest per key" pattern; alternatives are `max_by` or aggregate + join.
*Follow-up:* rank vs dense_rank vs row_number on ties? What does the default frame of an ordered aggregate window mean? (range between unbounded preceding and current row; ties are included.)

**17. Executor OOM vs driver OOM: causes and fixes?**
Driver: `collect`/`toPandas`, large broadcast, huge plan or file listing. Fix: write to storage, aggregate first, raise driver memory. Executor: skewed or oversized partitions, big `collect_list`, shuffle hash build side, insufficient overhead (container killed by YARN/K8s). Fix: more partitions, handle skew, raise memory/`memoryOverhead`, fewer cores per executor.
*Follow-ups:* What is spill, and is it an error? How would you tell heap OOM from container kill? (Exit code/ "killed by YARN" messages vs `java.lang.OutOfMemoryError`.)

**18. How do you deal with the small files problem?**
Prevent: right-size shuffle partitions, `coalesce`/`repartition` before writes, avoid high-cardinality partition columns, AQE. Remediate: scheduled compaction (Delta `OPTIMIZE`, Iceberg rewrite files, or rewrite jobs). Tune streaming trigger intervals.
*Follow-up:* What is the cost of too-large partitions/files? (Parallelism, memory, no splitting for gzip.)

**19. Walk me through debugging a slow Spark job with the UI.**
Jobs/Stages: find the stage taking most time. Stage detail: task time distribution (skew), shuffle read/write size, spill, GC time. SQL tab: operator metrics, join types, pushed filters, rows exploding after joins. Executors: failed tasks, GC, dead nodes. Then pick the fix: skew handling, join strategy, partition count, caching, avoiding UDFs.
*Follow-up:* Which numbers say "GC problem"? How do you tell shuffle-bound from compute-bound?

**20. Batch vs Structured Streaming in Spark?**
Same DataFrame API; streaming treats input as an unbounded table processed in micro-batches (continuous mode is experimental, check current docs). Key concepts: triggers, output modes, event-time windows with watermarks for late data, checkpointing for offsets/state, and idempotent or transactional sinks for end-to-end exactly-once.
*Follow-ups:* What does a watermark drop? How do you recover after failure? How do you avoid small files in streaming sinks?

**21. Design question: aggregate 5 TB of daily events by user, but 1% of users are bots with 40% of rows.**
Filter/early-prune columns; partial (map-side) aggregation is automatic for built-in aggregates; enable AQE; for joins to a user dimension, broadcast the dim (or salt hot users); two-phase salted aggregation for the bot keys; write with controlled file counts. Verify with task-time distribution before/after.
*Follow-up:* How would you detect bots dynamically? (Approximate key counts via a sample or `approx_count_distinct`/count by key, then split hot/cold.)
