# Design 1: URL Shortener (bit.ly / tinyurl)

Framework: see [framework.md](framework.md). Background: [caching](../week-01-fundamentals/lesson.md), [sharding and replication](../week-02-data-storage/lesson.md), [distributed ID/coordination](../week-04-distributed-algorithms/lesson.md).

## 1. Clarify requirements

Functional
- Create a short URL from a long URL (optional custom alias, optional expiry).
- Redirect short URL to the long URL.
- (Optional) basic click analytics, delete/disable link.

Non-functional
- Very read-heavy (redirects >> creates), assume 100:1.
- Redirect latency p99 < 50 ms from the service; high availability (links must keep working).
- Short codes unguessable enough or at least non-sequential if privacy matters; no collisions.
- Durability: a created link must not be lost.
- Out of scope: user accounts UI, malware scanning (mention only).

## 2. Estimate

- 100M new URLs/month. Writes: 100M / 2.5M s = ~40 writes/s average; peak ~100/s.
- Reads at 100:1: ~4,000 reads/s average; peak ~10K/s.
- Storage: 5 years x 12 x 100M = 6B records. At ~500 bytes each (long URL ~200 B, metadata) = ~3 TB; with 3x replication ~9 TB. Fits comfortably on a modest sharded cluster.
- Code length: base62 (a-zA-Z0-9) 7 chars = 62^7 = ~3.5 trillion combos, far more than 6B. 6 chars = 56.8B, also enough; 7 gives headroom.
- Cache: 20% of daily redirect traffic. 4K/s x 86,400 = ~350M reads/day; hot 20% unique URLs at 500 B = tens of GB. Fits a few Redis nodes.
- Bandwidth: redirects are tiny (a 301/302 with a Location header, ~500 B): 10K/s x 500 B = 5 MB/s.

## 3. API

```
POST /v1/urls
  body: { "long_url": "https://...", "custom_alias": "mylink"?, "expires_at": "..."? }
  headers: Authorization, Idempotency-Key
  201 -> { "short_url": "https://sho.rt/aZ3k9Q1", "code": "aZ3k9Q1" }
  409 if alias taken; 400 if invalid URL

GET /{code}
  301/302 -> Location: long_url      404 if missing/expired

DELETE /v1/urls/{code}               204
GET /v1/urls/{code}/stats            (analytics, eventually consistent)
```

301 vs 302: 301 (permanent) lets browsers cache, reducing load but losing analytics and the ability to change/expire the target. 302 (temporary) keeps every click hitting you. Typical choice: 302 if analytics matter, 301 if not.

## 4. Data model

Access pattern: point lookup by code (read), insert (write). No joins, no range scans. A KV or wide-column store fits well.

```
urls(code PK, long_url, user_id, created_at, expires_at, is_active)
users(user_id PK, ...)              -- optional
clicks(code, ts, ...)               -- analytics, via Kafka, stored separately (e.g. columnar/OLAP)
```

DB choice: DynamoDB or Cassandra (partition by code, scales horizontally, simple); or sharded MySQL/Postgres if you prefer relational and 3 TB is fine. State that at 40 writes/s even a single Postgres primary suffices; sharding is for storage/read scale and availability, not write throughput.

## 5. High-level diagram

```
 Client
   |
   v
 [CDN / edge cache] (optional for hot redirects)
   |
 [Load balancer L7]
   |
 +-----------------+        +--------------------+
 | Redirect service|------->| Redis cache        |
 | (stateless)     |  miss  | code -> long_url   |
 +-----------------+        +--------------------+
   |        \                         |
   |         \ miss                   v
   |          +------------------> [KV/DB, sharded by code, 3 replicas]
   |                                  ^
 +-----------------+                  |
 | Create service  |---- write -------+
 | (stateless)     |---- allocate code ---> [Code generator / ID service]
 +-----------------+
   |
   +-- click events --> [Kafka] --> analytics workers --> [OLAP store]
```

Read path: LB -> redirect service -> cache lookup -> on miss read DB, populate cache (cache-aside) -> 302.
Write path: validate URL -> get unique code -> insert with condition "code does not exist" -> return.

## 6. Deep dives

### a) Generating unique codes

Option 1: Hash the long URL (MD5/SHA-256), take first 7 base62 chars.
- Pros: same URL maps to same code (dedupe), no coordination.
- Cons: collisions (birthday paradox); must check DB and re-hash with a salt on collision; two users shortening the same URL share a code, which is a problem for per-user analytics/expiry.

Option 2: Counter + base62 encoding.
- A global counter (single DB sequence, or ZooKeeper/etcd range allocation) gives unique integers; encode in base62. No collisions.
- Con: sequential codes are guessable (enumeration). Fix: pass the counter through a reversible shuffle or format-preserving permutation, or add random bits.
- Scale: each app server leases a range (e.g. 1M IDs) from a coordinator (etcd/ZooKeeper/DB row), and then allocates locally with no per-request coordination. If the server crashes, the unused range is just skipped (gaps are fine).

Option 3: Pre-generated key service (KGS).
- A separate service pre-generates random unused codes into a table with "used/unused" state; app servers fetch batches into memory. Fast, collision-free, and non-guessable. Need to mark keys used atomically and handle server crash (lost keys are acceptable given the huge key space).

Recommendation: range-leased counter with a bijective shuffle, or KGS. State the tradeoff of guessability versus simplicity.

Custom alias: conditional insert (`IF NOT EXISTS`, DynamoDB `attribute_not_exists(code)`) so uniqueness is enforced by the DB, not by app-level check-then-insert (race).

### b) Read scaling and caching

- Cache-aside with Redis, LRU eviction, TTL aligned with link expiry. Traffic is Zipf-like: a few links are very hot. Expect >90% hit rate.
- Hot link (viral) on one cache shard: replicate hot keys across nodes, or add a small in-process local cache (LRU, tiny TTL) in each redirect server. CDN can also cache the redirect for a few seconds.
- Negative caching: cache 404s briefly to stop attackers scanning random codes from hammering the DB. A bloom filter of existing codes in front of the DB is another option.

### c) Expiry and deletion

- Lazy expiry on read (check expires_at), plus a background sweeper. DynamoDB TTL / Cassandra TTL do this natively.
- Must also invalidate the cache on delete/disable (delete key; short TTL as a safety net).

### d) Analytics without slowing redirects

- Redirect service publishes a click event to Kafka asynchronously (fire-and-forget, or batched). Consumers aggregate into an OLAP store. Redirect latency is not affected. Accept some loss or duplicates (counts are approximate), or use idempotent event IDs.

## 7. Bottlenecks and failure modes

- Cache outage: DB gets full read traffic (4-10K/s is still OK for a replicated KV, but verify). Use multiple cache nodes with consistent hashing, request coalescing to prevent a stampede.
- ID service as SPOF: mitigated by range leasing (servers continue running on their local range) and a replicated coordinator.
- Hot partition if the DB shards on a sequential code: use hashed partition keys.
- Abuse: spam/phishing links, rate limit creators per user/IP ([rate limiter design](02-rate-limiter.md)), URL blocklists.
- Region failure: multi-region read replicas; writes go to a home region or use multi-leader/global tables with unique-code namespaces per region (prefix bits) to avoid collisions.

## 8. Tradeoffs

- Hash vs counter vs KGS: dedupe/simplicity versus guessability and coordination.
- 301 vs 302: lower load versus analytics and control.
- NoSQL vs SQL: horizontal scale and simple lookups versus flexible queries (e.g. "all links by user" needs a secondary index in DynamoDB/Cassandra).
- Consistency: create then immediate read should work (read-your-writes). Use primary reads or cache write-through on create; analytics is eventually consistent.

## 9. What to say out loud

- "This is a read-heavy key-value lookup problem; the interesting parts are unique code generation and the cache."
- "At 40 writes/s, write throughput is not the problem. Storage is a few TB, so I would shard for capacity and availability rather than throughput."
- "I will enforce uniqueness in the database with a conditional write, not check-then-insert."
- "I would pick 302 to retain analytics, and mention 301 as an option if we want to offload traffic."

## 10. Follow-up questions to practice

1. How do you avoid sequential, guessable codes? (shuffle/KGS/random)
2. What if two users shorten the same URL? (separate rows vs dedupe, tradeoffs)
3. How would you support 100x traffic? (more cache, CDN, replicas, regional deployments)
4. How do you do per-link click counts accurately? (Kafka + stream aggregation, or sharded counters in Redis)
5. How would you implement link expiry at scale? (TTL, lazy + sweeper)
6. How do you survive a regional outage? (multi-region replication, DNS failover, code namespace per region)
