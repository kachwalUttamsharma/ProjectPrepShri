# Week 6 cheatsheet: quality and governance

## Dimensions
Completeness | Validity | Uniqueness | Consistency | Timeliness | Accuracy (+ integrity, volume, drift)

## Check -> typical implementation
- schema: compare expected vs actual columns/types
- null: `COUNT(*) FILTER (WHERE col IS NULL)/COUNT(*)` vs threshold
- range/domain: `WHERE col NOT BETWEEN a AND b`, accepted_values
- unique: `GROUP BY key HAVING COUNT(*)>1`
- referential: `LEFT JOIN parent ... WHERE parent.key IS NULL`
- freshness: `now() - max(loaded_at) > SLA`
- volume: modified z = 0.6745*(x-median)/MAD, flag |z|>3.5; use day-of-week baselines
- drift: PSI <0.1 stable, 0.1-0.25 watch, >0.25 major (rule of thumb); KS test
- reconcile: counts, sums, per-partition checksums, row diff

## Failure handling
block (circuit breaker) | quarantine bad rows | warn. Write-Audit-Publish. Tier severity.

## Compatibility (Avro/Schema Registry)
- BACKWARD: new reads old. add with default, delete OK. Upgrade consumers first.
- FORWARD: old reads new. add OK, delete only if default existed. Upgrade producers first.
- FULL: both. *_TRANSITIVE: against all versions.
- Type change or rename: breaking; use new field + migration.

## Observability
Freshness, volume, schema, distribution, lineage. SLI measure -> SLO target -> SLA promise. Alert on SLO symptoms, include runbook. Blameless postmortem + new check.

## Privacy toolbox
mask (static/dynamic) | tokenize (vault) | HMAC hash (never plain hash of low-entropy) | encrypt (KMS, envelope) | generalize / k-anon / DP | RLS + CLS | audit logs.

## GDPR/CCPA
access, rectification, erasure, minimization, retention, breach notice (GDPR 72h). Erasure plan: subject registry -> delete in raw/curated/marts/features -> compact/vacuum -> backups expire -> crypto-shred immutable stores -> audit trail.

## Testing pipelines
unit (pure functions) | integration (small dataset, ephemeral env) | contract (schema at the boundary) | prod data tests | idempotency & backfill-equals-prod | masked/synthetic test data.

## Tools (check current docs)
dbt tests (unique, not_null, accepted_values, relationships, contracts), Great Expectations, Soda, Deequ, OpenLineage, DataHub/OpenMetadata/Unity Catalog.

## FinOps levers
prune partitions, incremental models, compaction, right-size/auto-suspend, lifecycle tiers, retention, tag + showback, kill unused tables, question real-time SLAs.

## MDM
golden record = match + merge (survivorship) + cross-reference IDs; stewardship owns it.
