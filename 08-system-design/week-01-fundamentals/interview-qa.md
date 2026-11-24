# Week 1 - Interview Q&A (Fundamentals)

How to use: cover the answer, answer aloud in 60-90 seconds, then compare. Numbers marked "check current docs" vary.

---
**1. Latency vs throughput - what is the difference, and can you improve one without the other?**
Latency is time per request; throughput is requests per unit time. Pipelining, batching, and parallelism raise throughput (often at the cost of latency); caching and fewer round trips lower latency. A big batch size is a classic trade: higher throughput, higher per-item latency.

**2. Why do we talk about p99 instead of average latency?**
Averages hide the tail, and users and fan-out systems feel the tail. If a request fans out to 100 backends each slow 1% of the time, ~63% of requests hit at least one slow call. SLOs are usually set on p99/p99.9. Mitigations: hedged requests, timeouts, smaller fan-out, caching, load shedding.

**3. State Little's Law and use it.**
L = lambda * W (concurrency = arrival rate * time in system). At 2,000 QPS and 50 ms, ~100 requests in flight; if latency rises to 500 ms the same QPS needs ~1,000 concurrent slots, so pools exhaust. Use it to size thread/connection pools and to explain why slow dependencies cause cascading failure.

**4. Walk me through a back-of-envelope estimate for 100M DAU, each doing 10 reads and 1 write per day.**
Reads 1B/day / 10^5 s = ~10k QPS avg, peak 3x = ~30k. Writes 100M/day = ~1k QPS avg, ~3k peak. Read:write 10:1. If a write is 1 KB: 100 GB/day, ~36 TB/year, x3 replication ~110 TB. Conclusion: reads need cache/replicas, writes fit a modest sharded DB. I would state assumptions first, round freely, and conclude with an architecture decision.

**5. Convert requests per day to QPS quickly.**
Divide by ~10^5 (86,400 rounded). 1M/day ~ 10-12 QPS; 1B/day ~ 10-12k QPS. Then multiply by 2-5x for peak, depending on traffic shape.

**6. What latency numbers should every engineer know?**
RAM ~100 ns; SSD random read ~10-100 us; same-DC round trip ~0.5 ms; HDD seek ~5-10 ms; cross-continent round trip ~100-200 ms (speed-of-light bound). Implications: memory is ~100x faster than SSD; avoid cross-region synchronous calls; minimize round trips.

**7. Vertical vs horizontal scaling - when each?**
Vertical: simple, no code changes, but capped and a SPOF. Horizontal: near-unbounded and fault-tolerant but requires stateless design, partitioning, and handling partial failure. Start vertical for stateful stores while cheap, scale out stateless tiers early, and design so you can shard later.

**8. What makes a service stateless and why does it matter?**
Any instance can serve any request because state is externalized (DB, Redis, object store, signed token). It enables autoscaling, rolling deploys, and instance failure without user impact. Websockets and caches are exceptions needing a connection registry or tolerance of inconsistency.

**9. Sticky sessions: good or bad?**
Mostly a crutch: uneven load, lost sessions on node death, harder deploys. Prefer externalized sessions. Acceptable for websocket affinity or per-key cache locality, using consistent hashing.

**10. Calculate the availability of a request path crossing three 99.9% services; how do you improve it?**
0.999^3 = ~99.7% (~26 h downtime/year). Improve: make dependencies soft (graceful degradation), cache, add redundancy in parallel (1-(1-A)^2), async decoupling via queues, reduce hops. Beware: parallel redundancy assumes independent failures, but shared deploys/config/region correlate them.

**11. Availability vs reliability vs durability?**
Availability: fraction of time the service answers correctly. Reliability: continuity of correct operation (failure frequency). Durability: data is not lost (e.g. S3 design target of 11 nines - check current docs). A system can be down yet durable.

**12. Define SLI, SLO, SLA, and error budget.**
SLI = measurement (e.g. % requests under 300 ms and non-5xx). SLO = internal target on it (99.9%/30 days). SLA = contractual with penalties, looser than the SLO. Error budget = 1 - SLO (43 min/month at 99.9%); spend it on launches, and freeze risky changes when it runs out. Alert on burn rate, not on single blips.

**13. How would you pick SLIs for a search API?**
Availability (non-5xx / total, measured at the LB or client), latency (p99 < 500 ms), quality/freshness (index lag, % of queries returning results), and saturation signals internally. Use golden signals: latency, traffic, errors, saturation.

**14. L4 vs L7 load balancing?**
L4 routes on IP/port at the TCP/UDP level: fast, protocol-agnostic, static IPs (NLB, HAProxy tcp). L7 understands HTTP: path/host routing, TLS termination, header-based canaries, WAF, gRPC (ALB, Envoy, Nginx) at higher CPU cost. Typical: DNS -> L4 -> L7 -> services.

**15. Name load-balancing algorithms and when to use each.**
Round robin for homogeneous cheap requests; weighted for mixed hardware; least connections for long/variable requests; power-of-two-choices for large fleets (near-optimal, cheap); IP hash/consistent hashing for affinity or caches. Consistent hashing minimizes remapping when nodes change.

**16. How do health checks work, and what can go wrong?**
Active probes plus passive outlier detection eject unhealthy nodes. Risks: deep checks that call the DB can eject the whole fleet when the DB blips; too-aggressive thresholds flap; gray failures pass shallow checks. Use separate liveness/readiness, slow start, and connection draining.

**17. Explain cache-aside, write-through, and write-back.**
Cache-aside: app reads cache, on miss loads DB and populates; writes update DB and invalidate. Resilient to cache loss; stale windows. Write-through: writes go to cache and DB synchronously; consistent but slower writes. Write-back: write to cache, flush async; fastest writes but risks data loss; use for counters/metrics with durability backing.

**18. Why delete the cache entry on write rather than update it?**
Concurrent writers can leave stale data if updates arrive out of order; a delete forces the next read to fetch the latest. Even delete races with an in-flight reader populating stale data; mitigate with short TTLs, leases/versioning, delayed double delete, or CDC-based invalidation.

**19. What is a cache stampede and how do you prevent it?**
A hot key expires and many concurrent requests miss and hammer the DB. Fixes: single-flight/mutex per key, stale-while-revalidate, TTL jitter, refresh-ahead, probabilistic early expiration, and caching on a lease (Facebook memcache).

**20. Cache penetration vs avalanche vs hot key?**
Penetration: lookups for nonexistent keys always miss; fix with negative caching and Bloom filters. Avalanche: mass expiry or cache outage sends load to the DB; fix with TTL jitter, replication, load shedding, circuit breakers. Hot key: a single key overloads one node; fix with local caches, key splitting/suffixing, replication.

**21. LRU vs LFU?**
LRU evicts least recently used: good general default, vulnerable to scans. LFU evicts least frequently used: better for stable popularity, needs aging; W-TinyLFU gets high hit rates. Implement LRU with hashmap + doubly linked list for O(1).

**22. How do you design cache invalidation for a CDN?**
Prefer versioned/content-hashed URLs with long max-age (no invalidation needed) and short TTL + revalidation (ETag) for HTML/API. Use purge APIs sparingly. Control with Cache-Control, s-maxage, Vary; avoid Vary on cookies. Origin shield reduces origin load.

**23. Redis or Memcached for a cache?**
Memcached if pure simple multithreaded caching; Redis when you need data structures, persistence/replication, atomic ops, pub/sub, or rate limiting. Both lose data on failure by design as caches; Redis replication is async, so failover can drop recent writes.

**24. Your database falls over when the cache restarts. What do you do?**
Cold cache sends all traffic to the DB. Pre-warm, replicate the cache across AZs, ramp traffic gradually, add request coalescing, rate limit/shed load to the DB, and use circuit breakers. Prevent the dependency from being load-bearing by sizing the DB for a tolerable miss rate or degrading features.

**25. How many app servers do you need for 30k peak QPS?**
Measure/assume per-instance capacity (say 1,000 QPS), target ~60% peak utilization: 30k / 600 = 50, spread across 3 AZs with N+1 so a lost AZ still carries load (e.g. 75 total). Confirm with load tests; state that the DB/cache is likely the real bottleneck.
