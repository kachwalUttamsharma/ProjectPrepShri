# Week 1 Cheatsheet: Modeling and Warehousing

## Design recipe
Process -> Grain -> Dimensions -> Facts. State grain in one sentence. Every column true at that grain.

## OLTP vs OLAP
OLTP: row store, normalized, point reads/writes. OLAP: columnar, denormalized, scans/aggregates. ELT: land raw, transform with SQL in warehouse; keep raw immutable.

## Fact types
- Transaction: one row per event.
- Periodic snapshot: one row per entity per period (dense, semi-additive).
- Accumulating snapshot: one row per process instance, updated at milestones.
- Factless: events/coverage, count rows.
Additive / semi-additive (balances: no sum over time) / non-additive (ratios: store num+denom).

## Dimension toolkit
surrogate key | natural key | degenerate (order_no in fact) | role-playing (date) | junk (flags) | conformed (shared) | mini-dimension (fast-changing) | bridge (M:N, weights) | outrigger | unknown/inferred members | date dim.

## SCD
0 fixed | 1 overwrite | 2 versions (valid_from, valid_to, is_current) | 3 prev column | 4 history table | 6 = 1+2+3 | 7 durable key + version key.
SCD2 rules: half-open interval `from <= t < to`; open end 9999-12-31; unique current row per key; fact stores version surrogate key; fact load joins on event time; batch re-runnable; hash tracked columns.

SCD2 skeleton:
```sql
UPDATE dim SET valid_to=s.eff, is_current=0 WHERE is_current=1 AND tracked cols differ;
INSERT INTO dim SELECT ... FROM stg s WHERE NOT EXISTS (current row for key);
```

## Late data
Late fact -> historical version lookup, rebuild affected partitions. Fact before dim -> inferred member. Backdated dim change -> split version, re-point facts.

## Methodologies
Kimball: bus + conformed dims + marts. Inmon: 3NF EDW first. Data Vault: Hub (keys), Link (relationships), Satellite (attributes, history); raw vault + marts. Pragmatic: raw -> staging -> marts.

## Warehouse concepts
Columnar = compression + column pruning + min/max block skipping. Storage/compute separation. MPP: shuffle vs co-location; skew is the enemy.
Partition (exact pruning, low-cardinality date) vs cluster/sort (tight min/max on filter columns).
Snowflake: micro-partitions, warehouses, clustering keys. BigQuery: partition+cluster, bytes scanned or slots. Redshift: dist key + sort key, WLM, Spectrum. (check current docs for pricing/limits)

## Cost control
No SELECT *; filter on partition; incremental models; materialize hot aggregates; auto-suspend; right-size; separate compute per workload; timeouts/budgets; monitor top queries; short retention on staging.

## Traps
Mixed grains | fan-out joins | summing semi-additive | NULL FKs | natural key in SCD2 fact | time zones | SCD2 on everything | undocumented metric definitions.

## Tests
Grain unique; FKs not null and exist; one current row per key; no overlaps; reconciliation to source; freshness.
