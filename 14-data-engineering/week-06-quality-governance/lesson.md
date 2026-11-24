# Week 6: Data quality, observability and governance

Goal: be able to design a quality program (what to check, where, who gets paged), explain schema/contract evolution, and answer privacy/governance questions (GDPR erasure, masking, access control) at senior level. Tool facts are version-sensitive: "(check current docs)".

## 1. Quality dimensions
| Dimension | Question | Example check |
|---|---|---|
| Completeness | Is required data present? | null ratio of `customer_id` <= 0.1% |
| Validity | Does it conform to type/format/range/domain? | `age` in 0..120, email regex, enum membership |
| Uniqueness | No unintended duplicates? | PK/natural key unique per snapshot |
| Consistency | Do related data agree (within and across systems)? | order total = sum(line items); same customer count in source and warehouse |
| Timeliness / freshness | Is it recent enough for its SLA? | `max(loaded_at)` within 2h |
| Accuracy | Does it reflect reality? | hardest; sample vs source of truth, reconcile to finance |
Plus integrity (referential), and volume/distribution (statistical signals that catch "unknown unknowns").

## 2. Types of checks
- **Schema**: columns, types, nullability, order-insensitive; detect added/removed/retyped columns.
- **Null / completeness** with thresholds instead of absolute zero where upstream is messy.
- **Range / domain / regex** checks.
- **Uniqueness** on declared keys (warehouses often don't enforce PKs: BigQuery/Snowflake constraints are informational (check current docs)).
- **Referential integrity** (orphans): facts whose dimension key is missing; handle late-arriving dimensions with an "unknown" member.
- **Freshness**: compare max event/load time to now; distinguish "pipeline didn't run" from "source sent nothing".
- **Volume anomaly**: today's row count vs history. Use robust statistics (median/MAD) or day-of-week seasonality; plain mean/stdev is distorted by past outages.
- **Distribution drift**: PSI, KS test, category-share shifts, null-rate shifts; important for ML features.
- **Cross-table / reconciliation**: counts and checksums between source and target; sums of money columns; the primary tool for migrations and backfills.

Run checks where cheap and early: at ingestion (reject/quarantine), after transforms (assertions), and on the served layer (SLA monitors).

## 3. Tooling (check current docs for each)
- **dbt tests**: `unique`, `not_null`, `accepted_values`, `relationships` generic tests, plus singular SQL tests and packages (dbt-utils, dbt-expectations); severity `warn`/`error`; `dbt build` runs tests in the DAG so failed tests block downstream models; **dbt contracts** (enforced column types/constraints on models) and model versions.
- **Great Expectations**: expectation suites, checkpoints, data docs; Python-native, works on pandas/Spark/SQL.
- **Soda** (SodaCL YAML checks, Soda Cloud), **Deequ** (Scala/Spark library; PyDeequ), **Monte Carlo / similar observability platforms** (automated freshness/volume/schema anomaly detection and lineage).
- Choose by where data lives: SQL-first warehouse -> dbt tests + a monitor; Spark -> Deequ/GE; need business-user friendliness -> Soda/commercial.
- Key design: checks as code in the repo, versioned and reviewed; failures routed to owners, not a shared inbox.

## 4. Handling failures: block, quarantine or warn
- **Circuit breaker** (stop publishing) for critical tables where wrong data is worse than late data.
- **Quarantine/DLQ table** for bad rows, keep the good flow moving; track quarantine rate.
- **Warn** for low-severity; but warnings nobody reads are noise: tier checks (P1 blocks, P2 pages in hours, P3 weekly review).
- Write-Audit-Publish: write to staging, audit, then swap/publish (Iceberg branches, Delta table swap, partition exchange).

## 5. Data contracts and schema evolution
- A **data contract** is an explicit, versioned agreement between producer and consumers: schema, semantics, SLAs (freshness/availability), ownership, PII classification, change process. Enforce in CI (producer PR fails if it breaks a registered contract), at the registry (Schema Registry compat mode) and at runtime (validation).
- **Compatibility** (Avro vocabulary): BACKWARD = new schema can read old data (add field with default, delete field); FORWARD = old schema can read new data (add field, delete field only if it had a default); FULL = both. Transitive = against all prior versions. Rename = remove + add: needs aliases or a dual-write migration.
- Safe change recipe for a breaking change: add new column/version alongside, dual-populate, migrate consumers, deprecate with a date, remove.
- In warehouses/lakehouses: additive columns are generally safe; type widening is sometimes supported by table formats (check current docs); dropping/renaming breaks SELECT * consumers and downstream views.

## 6. Observability: lineage, SLAs, incidents
- Five pillars (popular framing): freshness, volume, schema, distribution, lineage.
- **Lineage**: table-level and column-level graph (OpenLineage standard, dbt docs, catalog tools). Uses: impact analysis before changes, root cause (walk upstream), compliance (where does PII flow?).
- **SLI/SLO/SLA** for data: SLI = measurable (percent of days table ready by 07:00; freshness lag); SLO = target (99% of days); SLA = external promise with consequences. Use error budgets to decide reliability vs feature work.
- **Alerting**: alert on symptoms tied to SLOs, route by ownership, deduplicate, include a runbook link and the failing check details. Avoid alert fatigue: tier severity, tune thresholds, auto-resolve.
- **Incident process**: detect -> triage (blast radius via lineage) -> mitigate (pause downstream, roll back, backfill) -> communicate (status to consumers) -> root cause -> blameless postmortem with action items (add a check so it can't recur silently). **Runbooks**: symptom, likely causes, diagnostic queries, fix steps, escalation.

## 7. Catalogs and metadata
- Technical metadata (schema, stats, lineage), business metadata (glossary, owner, description, certification), operational metadata (run history, freshness, usage).
- Catalog examples: DataHub, OpenMetadata, Amundsen, Unity Catalog, AWS Glue Data Catalog / DataZone, Collibra/Alation (check current docs). Value comes from ownership, tags (PII), and search/trust signals, not from the tool alone; keep metadata automated from code (dbt, orchestrator).

## 8. Governance and privacy
- **PII classification**: direct identifiers (email, SSN), quasi-identifiers (zip + birth date + gender can re-identify), sensitive categories (health, biometrics). Tag at column level; propagate tags via lineage.
- **Techniques**:
  - *Masking* (static: irreversible copy for lower environments; dynamic: masked at query time by role).
  - *Tokenization* (replace with a random token; mapping in a secured vault; reversible by authorized service; preserves joins if deterministic).
  - *Hashing* with a secret salt/HMAC (deterministic join key; plain unsalted hash of low-entropy values like emails/phones is reversible by dictionary attack).
  - *Encryption* at rest (KMS-managed keys, envelope encryption), in transit (TLS), column-level/field-level for the most sensitive; key rotation.
  - *Generalization/aggregation, k-anonymity, differential privacy* for analytics release.
- **Access control**: RBAC/ABAC, least privilege, separation of duties; **row-level security** (policies/filters by region/tenant) and **column-level security** (policy tags, masking policies); service accounts per pipeline; short-lived credentials; **audit logs** (who queried what) retained and reviewed.
- **GDPR/CCPA**: lawful basis and purpose limitation, data minimization, right of access, **right to erasure/deletion** and rectification, retention limits, breach notification (GDPR: 72h to the authority), DPIA; CCPA/CPRA adds "do not sell/share" opt-out. (Not legal advice; check current regulations with counsel.)
- **Erasure in data platforms** is the hard part: copies in raw, curated, marts, backups, logs, ML features, Kafka topics. Patterns: central subject-ID registry + deletion jobs propagating to all stores; lakehouse `DELETE`/`MERGE` followed by compaction/vacuum so files are physically rewritten (Delta/Iceberg snapshots keep old files until expired); *crypto-shredding* (per-subject key, delete key = data unreadable) for immutable stores and logs; pseudonymize so analytics survive; define backup expiry as the lawful lag; keep an erasure audit trail without the PII.
- **Retention**: per-dataset retention periods enforced automatically (lifecycle policies, partition drops, table TTL); legal hold exceptions.

## 9. Testing data pipelines
- **Unit tests**: pure transformation functions with small fixtures, edge cases (nulls, dupes, timezone, empty input).
- **Integration tests**: run the pipeline on a small realistic dataset in an isolated environment (ephemeral schema, containers); assert on outputs.
- **Contract tests**: producer output validated against the registered schema/contract; consumer-driven expectations.
- **Data tests in production** (the quality checks above) vs **CI tests** (code correctness): you need both.
- **Test data**: synthetic or masked production subset; never raw prod PII in dev; seed generators with edge cases; keep golden datasets for regression; snapshot/diff tests on a sample ("data diff" between old and new transformation).
- Idempotency test: run twice, same result. Backfill test: rerun over history gives identical output to prod.

## 10. Reconciliation and backfill verification
- Compare **row counts**, **sums** of key measures, **min/max** of dates, distinct key counts; then **checksums** (order-independent hash of rows, aggregated per partition to localize differences); finally **row-level diff** on sampled or mismatching partitions.
- For backfills: run into a shadow table/partition, reconcile vs old output and vs source, swap atomically, keep rollback.
- Expect legitimate differences (late data, timezone, float rounding): define tolerances up front.

## 11. Cost management (FinOps for data)
- Know unit economics: cost per TB scanned/stored/processed, per pipeline, per team. Tag resources and chargeback/showback.
- Levers: partition/cluster pruning, avoid SELECT *, incremental models instead of full refresh, columnar formats and compression, file sizing/compaction, materialize hot aggregates, auto-suspend warehouses and right-size, spot/preemptible for batch, lifecycle tiers for cold data, retention policies, delete unused tables (lineage + access logs), query cost guardrails and budgets/alerts. Streaming: partitions/brokers, retention, over-provisioned clusters.
- Trade-off: freshness SLAs drive cost (hourly vs daily); challenge unnecessary real time.

## 12. MDM basics
- **Master data**: slow-changing, shared business entities (customer, product, supplier). MDM creates a **golden record** through matching (deterministic/probabilistic/fuzzy), merging with survivorship rules (most recent, most trusted source), and keeps cross-reference IDs to source systems. Styles: registry, consolidation, coexistence, centralized. Relates to quality: duplicates, conflicting attributes; governance: stewardship and ownership.

## 13. Small example (different from exercises): a SQL-based check with a threshold
```python
def pct_late_shipments(conn, max_pct=2.0):
    late, total = conn.execute(
        "SELECT SUM(shipped_at > promised_at), COUNT(*) FROM shipments").fetchone()
    pct = 100.0 * (late or 0) / total if total else 0.0
    return {"name": "late_shipments", "passed": pct <= max_pct, "pct": pct}
```
Business-rule checks like this are consistency/accuracy checks; thresholds come from stakeholders, not guesses.

## Common mistakes
- Checking only schema/null and missing volume, freshness and drift.
- Alert fatigue from untiered, un-owned checks.
- Plain hash of email/phone treated as anonymization.
- Erasing from the serving table but not raw, backups, caches, features, topics.
- Using mean/stdev anomaly detection on seasonal or outage-polluted history.
- Comparing source vs target counts only (equal counts with different data).
- Letting dev/test use raw production PII.
- Contracts as documents nobody enforces.
- Treating warehouse PK constraints as enforced.

## Your task
Fill in `exercises.py`, run `../../.venv/bin/pytest -q`, then drill `interview-qa.md`.
