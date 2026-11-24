# Week 6 interview Q&A: data quality and governance

**1. How do you define and measure data quality?**
By dimensions tied to use: completeness, validity, uniqueness, consistency, timeliness, accuracy. For each critical dataset agree with consumers on measurable rules and thresholds, track pass rate over time, and tie severity to business impact.
*Follow-ups:* Which dimension is hardest and why? (Accuracy: needs an external truth.) How do you prioritize which tables to monitor? (Usage via lineage/query logs, business criticality, blast radius.)

**2. Where in a pipeline do you place checks?**
At ingestion (schema, basic validity, quarantine), after key transforms (assertions on invariants: row counts after joins, uniqueness), and at the serving layer (freshness, reconciliation to source). Early checks fail cheaply; late checks protect consumers.
*Follow-ups:* Block vs warn? (Block when wrong data is worse than late; otherwise quarantine/warn.) Write-Audit-Publish? (Stage, audit, atomically publish.)

**3. A table loads daily; yesterday the row count was 40% lower and no job failed. How would you have caught it, and what now?**
Volume anomaly detection against a seasonal baseline (median/MAD by weekday). Now: check upstream freshness and partial extract, compare to source counts, quarantine the partition, notify consumers, backfill, add the missing check/contract.
*Follow-ups:* Why median/MAD over mean/stdev? (Robust to earlier outages and heavy tails.) False positives on holidays? (Calendar features, manual suppression, wider thresholds.)

**4. Freshness vs timeliness vs latency?**
Freshness: age of the newest data. Timeliness: availability by the agreed time (SLO). Latency: delay of one record through the pipeline. Measure freshness from event time when possible, not job-finish time (a job can succeed on stale input).
*Follow-ups:* How to distinguish "no new data" from "pipeline broken"? (Heartbeat/synthetic rows, source-side counters, separate ingestion lag metric.)

**5. How do you detect distribution drift?**
Compare current vs reference windows: PSI or KS for numerics, category share shifts (chi-square/JS divergence), null-rate and cardinality changes. Pick the reference deliberately (last week vs training set). Alert on sustained drift, not single-day noise.
*Follow-ups:* PSI thresholds? (<0.1/0.25 are rules of thumb.) Bin choice effects? (Quantile bins from the reference are more stable.)

**6. dbt tests vs Great Expectations vs Soda vs Deequ?**
dbt tests: SQL-native, in the transformation DAG, simple generics; great for warehouse models. GE: Python expectation suites and docs, flexible for files/Spark. Soda: declarative YAML checks plus cloud UI. Deequ: Spark-scale, metrics-based constraint suggestion. Choose by stack and who writes checks; don't run four. (Check current docs.)
*Follow-ups:* How do tests gate deployment? (`dbt build` stops downstream on failure; CI runs on slim/changed models.) Storing results? (Persist results to a table for trend and SLO reporting.)

**7. What is a data contract and how is it enforced?**
A versioned agreement between producer and consumers covering schema, semantics, SLAs, ownership, PII tags and change policy. Enforced in CI (breaking change detection against a registry), at publish time (schema validation), and at runtime (checks/quarantine), with a deprecation process.
*Follow-ups:* Who owns it? (Producer, with consumers consulted.) How is it different from a schema? (Adds semantics, SLAs, ownership, process.) Pitfall? (Contracts without enforcement or without producer buy-in.)

**8. Explain backward vs forward vs full compatibility with an example.**
Backward: new schema reads old data; adding `email` with a default or deleting a field is OK. Forward: old schema reads new data; adding a field is OK (old readers ignore it), deleting needs the field to have had a default. Full: both. Which to choose depends on who upgrades first: backward -> consumers first; forward -> producers first.
*Follow-ups:* Is renaming compatible? (No, unless aliases.) Why default BACKWARD in Schema Registry? (Allows rewinding consumers to old data.) Parquet/warehouse analogue? (Adding nullable column OK; type change often breaks.)

**9. What is lineage and what do you use it for?**
A graph of how datasets and columns derive from one another (OpenLineage events, SQL parsing, dbt manifest). Impact analysis before changes, root-cause upstream search, compliance (PII flow), deprecation of unused assets, ownership routing of alerts.
*Follow-ups:* Column-level vs table-level? (Column-level is costlier but needed for PII/impact.) Gaps? (Dynamic SQL, notebooks, external tools.)

**10. SLI, SLO, SLA for a data product?**
SLI: "fraction of days the daily_sales table is complete by 07:00". SLO: 99% over 30 days. SLA: contractual commitment with penalties. Error budget decides whether to pause features for reliability work.
*Follow-ups:* What do you do when you burn the budget? (Freeze risky changes, invest in checks/automation.) How to alert? (Burn-rate alerts rather than every miss.)

**11. How do you reduce alert fatigue for data quality?**
Tier by severity and business impact, ownership routing, dedupe/grouping by root cause via lineage, thresholds tuned from history, auto-resolve, weekly review of noisy checks, and delete checks nobody acts on.
*Follow-ups:* Metric for alert quality? (Actionable ratio, time to acknowledge/resolve.)

**12. Describe a data incident process.**
Detect, declare severity, assign an incident lead, assess blast radius (lineage), mitigate (stop downstream publishing, rollback/restore, backfill), communicate to consumers with ETA, resolve, blameless postmortem with root cause and prevention (new check/contract/test), follow-up tracking.
*Follow-ups:* How do you restore a bad overwrite? (Time travel/snapshots, rerun idempotent job from raw.) Communicating wrong numbers already consumed? (Proactive notice, versioned fix, restate reports.)

**13. How would you implement GDPR right-to-erasure in a lake + warehouse + Kafka platform?**
Central subject registry/ID resolution; a deletion service fans requests out to every store; lakehouse DELETE/MERGE then compaction and snapshot expiry/VACUUM so old files disappear; warehouse deletes plus time-travel expiry; downstream marts/features rebuilt; Kafka: short retention, compaction with tombstones, or crypto-shredding with per-subject keys; backups age out with documented lag; audit evidence without PII; SLA to complete (one month under GDPR, check current law).
*Follow-ups:* Immutable logs? (Crypto-shredding or avoid PII in logs.) Analytics needing history? (Pseudonymize/aggregate so deletion doesn't break metrics.) ML models trained on the data? (Policy question; retrain cadence; legal guidance.)

**14. Masking vs tokenization vs hashing vs encryption?**
Masking: obscure display (irreversible, role-based or static copies). Tokenization: random surrogate with vault mapping, reversible for authorized services, preserves joins if deterministic. Hashing: one-way; use HMAC with secret since unsalted hashes of emails/phones can be brute-forced. Encryption: reversible with keys; protects at rest/in transit and field-level for high sensitivity.
*Follow-ups:* Join across datasets without exposing email? (Deterministic HMAC/token with shared key under access control.) Is a hash of a user ID anonymous? (No, pseudonymous; still personal data under GDPR.)

**15. Row-level and column-level security: how do you implement them?**
RLS: policy/filter bound to role or session attributes (Snowflake row access policies, BigQuery row access policies, Postgres RLS, Unity Catalog filters; check current docs). CLS: policy tags/masking policies so unauthorized roles see masked or null values. Manage via groups, not users; test policies; audit access.
*Follow-ups:* Performance cost? (Predicate pushdown/caching differences.) Derived tables leaking? (Policies don't follow copies: enforce at the source, propagate tags via lineage.)

**16. How do you test a data pipeline?**
Unit tests for transformations; integration tests on a small dataset in an ephemeral environment; contract tests at boundaries; idempotency and backfill-equivalence tests; data diff between old and new logic on a sample; production data-quality tests continue after deploy.
*Follow-ups:* Test data with PII? (Synthetic or masked; never prod PII in dev.) Testing time logic? (Inject clock; boundary and timezone cases.)

**17. How do you verify a backfill or migration?**
Shadow-write to a new table; compare counts, key sums, min/max dates, distinct keys; partition-level checksums to localize diffs; row-level diff on mismatches; define tolerances (late data, rounding); swap atomically; keep rollback.
*Follow-ups:* Equal counts but different data? (Checksums catch it.) Reconciling against a moving source? (Snapshot/as-of both sides.)

**18. How do you handle duplicates in a warehouse where PKs are not enforced?**
Detect with GROUP BY HAVING COUNT>1 on the business key per snapshot; prevent by idempotent loads (MERGE/upsert, dedupe with ROW_NUMBER over latest ingestion), natural/surrogate key strategy, unique tests in CI/prod; investigate source of duplicates (at-least-once delivery, retries).
*Follow-ups:* Which row wins? (Latest by event time then ingestion time, documented rule.) Late duplicates? (Dedupe window or full-key MERGE.)

**19. What goes in a data catalog and what makes it succeed?**
Technical metadata (schema, stats, lineage), business context (glossary, owner, description, certification), usage/popularity, quality status and tags (PII). Success needs automated ingestion from code/orchestrator, enforced ownership, and integration in workflows (access requests, alerts).
*Follow-ups:* Build vs buy? (OpenMetadata/DataHub vs commercial; depends on team capacity.) How to keep docs fresh? (Docs-as-code, CI requires descriptions.)

**20. Where does data cost go and how do you cut it?**
Storage, compute (scans, shuffles, always-on clusters), egress, streaming infra, and people-time on reprocessing. Cut with partition pruning, incremental processing, compaction, right-sizing/auto-suspend, lifecycle tiers, retention, eliminating unused assets, query guardrails, and showback. Challenge freshness SLAs that drive cost.
*Follow-ups:* How to find waste? (Query/billing logs by table, cost per pipeline, access-recency report.) Tradeoff with reliability? (Retries/duplicated environments cost money: tier by criticality.)

**21. What is MDM and how does it relate to quality?**
Managing shared master entities (customer/product) with matching, merge/survivorship rules, and cross-reference IDs to produce a golden record. It attacks duplication and inconsistency at the root, supported by stewardship and governance.
*Follow-ups:* Deterministic vs probabilistic matching? (Exact keys vs scored fuzzy matches with review thresholds.) How to handle unmerge? (Keep source records and match history.)

**22. Who owns data quality?**
Producers own correctness at the source and the contract; the data platform provides tooling and defaults; consumers define fitness-for-use and report issues; stewards arbitrate definitions. "Everyone" with no named owner means no one.
*Follow-ups:* How to get producers to care? (Contracts in CI, quality metrics visible to their leadership, incident attribution.)
