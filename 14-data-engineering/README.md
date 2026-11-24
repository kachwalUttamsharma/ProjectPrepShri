# Data Engineering Study Track (senior interview prep, ~7 weeks at 6-8 hrs/week)

Goal: pass senior data engineer interviews: modeling, Spark, orchestration, streaming, lakehouse, quality/governance, and end-to-end pipeline design. Assumes you can write intermediate Python and basic SQL (see `../06-sql/`, `../10-python-depth/`, `../07-aws/`). The system design track (`../08-system-design/`) pairs with week 7.

## Honest caveats
- Written from memory, without live access to vendor docs. Concepts are stable; defaults, limits, prices, config names and feature availability change. Anything version-specific is marked "(check current docs)". Verify before quoting a number in an interview.
- Code that runs in this repo's venv is verified (SQL on sqlite3, stdlib Python). Spark, Airflow, Kafka, dbt and cloud snippets are illustrative unless stated otherwise, and need their own installs and credentials.
- Interview answers are templates: adapt to your real experience. Interviewers at senior level care about trade-offs, failure modes and operations more than API recall.

## Study order
| Week | Folder | Topics |
|---|---|---|
| 1 | week-01-modeling-warehousing | OLTP/OLAP, normalization, star/snowflake, fact types, dimensions, grain, SCD 1/2/3/6, Kimball/Inmon/Data Vault, late data, columnar warehouses, cost control, ELT vs ETL, modeling cases |
| 2 | week-02-spark | Architecture, DAG/stages/shuffles, joins, skew, partitioning, AQE, caching, memory, Structured Streaming basics, tuning, debugging via Spark UI |
| 3 | week-03-orchestration-dbt | Airflow concepts (DAGs, scheduling, idempotency, backfills, sensors, XCom, executors), dbt (models, incremental, snapshots, tests), CI/CD |
| 4 | week-04-kafka-streaming | Kafka (partitions, consumer groups, offsets, delivery semantics, exactly-once), stream processing (windows, watermarks, state), CDC, schema registry |
| 5 | week-05-lakehouse-formats | Parquet internals, ORC/Avro, partitioning, small files, Delta/Iceberg/Hudi, medallion, catalogs, AWS tie-ins |
| 6 | week-06-quality-governance | Data quality, contracts, observability, lineage, privacy/PII, access control, SLAs, incident handling |
| 7 | week-07-pipeline-design | End-to-end pipeline design interviews, capacity math, reliability, cost, mock scenarios |

Then: `rapid-fire.md` (one-liners across all weeks), reviewed daily in the last two weeks.

Note: weeks 2, 3, 4, 6 and 7 may be added separately; check which folders exist.

## Weekly routine
1. Read `lesson.md` (2-3 hrs). Run every code block; predict output first, then change an input and predict again.
2. Do `interview-qa.md` out loud, cover-and-compare (2 hrs). Record yourself on design/scenario questions.
3. Memorize `cheatsheet.md`; redraw the central diagram from memory (30-45 min).
4. Build something small: a tiny pipeline on local files with sqlite/DuckDB, a toy SCD2 loader, a Parquet-inspecting script.
5. Last 30 min: explain the week's three key trade-offs without notes.

## Interview habits to practice
- Clarify first: data volume, latency/freshness, consumers, SLAs, correctness needs, budget, team skills.
- State grain, keys and idempotency up front for every pipeline step.
- Always cover failure modes: late/duplicate/out-of-order data, backfills, schema changes, bad records, retries.
- Mention observability, data quality tests and cost unprompted.
- Give a phased plan (MVP then hardening). Justify choices with trade-offs, not brand names.
- When unsure of a number, give the order of magnitude and say how you would verify.

## Suggested external resources (by area)
- Modeling: Kimball, "The Data Warehouse Toolkit" (3rd ed.); Kimball Group design tips; Data Vault 2.0 overview (Linstedt); dbt "How we structure our dbt projects".
- Warehouses: Snowflake, BigQuery and Redshift official docs (architecture and cost sections; check current docs).
- Storage/systems: Martin Kleppmann, "Designing Data-Intensive Applications" (chapters on storage, batch, streams, consistency).
- Spark: "Spark: The Definitive Guide"; official Spark tuning guide and SQL/AQE docs; Databricks blog posts on skew, AQE and Delta.
- Orchestration: Apache Airflow docs (core concepts, best practices); dbt docs (incremental models, snapshots, tests); "Fundamentals of Data Engineering" (Reis and Housley).
- Streaming: Kafka documentation (design section); "Kafka: The Definitive Guide"; Confluent blog on exactly-once; Flink docs (time and watermarks); Tyler Akidau, "Streaming 101/102".
- Lakehouse: Delta Lake, Apache Iceberg and Apache Hudi docs and specs; Parquet format spec (GitHub apache/parquet-format); Dremel paper for nested encoding.
- Quality/governance: Great Expectations and Soda docs; dbt tests; OpenLineage; data contracts writing (e.g. Chad Sanderson) and DAMA-DMBOK as vocabulary.
- AWS: AWS Well-Architected Data Analytics lens; Athena, Glue and Lake Formation docs (check current docs).
- Practice: SQL window functions and sessionization (`../06-sql/`), LeetCode/StrataScratch SQL, system design case studies of pipelines at large companies' engineering blogs.

## Files
- week-NN-*/lesson.md, interview-qa.md, cheatsheet.md
- week-01 also has `scd2_demo.sql` (run: `sqlite3 :memory: < scd2_demo.sql`)
- rapid-fire.md at the track root
