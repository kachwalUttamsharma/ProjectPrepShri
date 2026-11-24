# Week 1 - Fundamentals: Estimation, Scalability, Availability, Load Balancing, Caching

Time budget: ~3 hrs. Read lesson (1.5h), Q&A aloud (1h), cheatsheet (30m).
Numbers marked "(check current docs)" change over time; verify before quoting. Latency numbers are order-of-magnitude, which is all an interview needs.

AWS cross-links: ELB/Auto Scaling in `../../07-aws/week-02-compute/lesson.md`; ElastiCache/DynamoDB in `../../07-aws/week-03-storage-databases/lesson.md`; CloudFront/Route 53 in `../../07-aws/week-04-networking/lesson.md`.

---
## 1. Latency vs throughput (and why they are not the same)

- Latency: time for ONE request (ms). Think "how long does one car take to cross the bridge".
- Throughput: requests (or bytes) per unit time (QPS, MB/s). Think "cars per hour".
- Bandwidth: maximum capacity of the pipe (upper bound on throughput).
- You can have high throughput with high latency (a cargo ship), and low latency with low throughput (a single-threaded server).

Little's Law (the one formula worth memorizing):

```
  L = lambda * W
  L      = average number of requests in the system (concurrency)
  lambda = arrival rate (QPS)
  W      = average time each request spends in system (latency)

  Example: 2,000 QPS, 50 ms avg latency  -> L = 2000 * 0.05 = 100 concurrent requests.
  If a downstream slows to 500 ms, concurrency needed becomes 1,000.
  => thread pools / connection pools exhaust -> cascading failure (see week 3).
```

### Percentiles, not averages
- p50 (median), p95, p99, p99.9. Averages hide the tail.
- Tail latency amplification: if one user request fans out to N backends in parallel, the request is as slow as the slowest. With N=100 and each backend slow 1% of the time, P(at least one slow) = 1 - 0.99^100 = ~63%. So the user sees "p99" behaviour most of the time. (Dean & Barroso, "The Tail at Scale".)
- Mitigations: hedged requests (send a duplicate after p95 timeout, take first), timeouts, load shedding, smaller fan-out, caching.
- Latency numbers on SLOs are almost always p99 (or p99.9), not mean.

### Latency numbers every engineer should know (approximate, order of magnitude)

```
  L1 cache reference                         ~1 ns
  Branch mispredict                          ~3 ns
  L2 cache reference                         ~4 ns
  Mutex lock/unlock                          ~17-25 ns
  Main memory (RAM) reference                ~100 ns
  Compress 1 KB (fast codec)                 ~2-3 us
  Send 1 KB over 1 Gbps network              ~10 us
  SSD random read (NVMe)                     ~16-100 us
  Read 1 MB sequentially from RAM            ~3-30 us   (varies a lot by source)
  Round trip within same data center         ~0.5 ms
  Read 1 MB sequentially from SSD            ~50-200 us (NVMe) up to ~1 ms (SATA)
  HDD seek                                   ~2-10 ms
  Read 1 MB sequentially from HDD            ~1-20 ms
  Cross-region round trip (US east<->west)   ~60-80 ms
  US <-> Europe round trip                   ~80-150 ms
  US <-> Asia round trip                     ~150-250 ms
  TCP handshake + TLS 1.3 handshake          ~1-2 RTT (TLS 1.2: 2 RTT)
```

Rules of thumb derived from the table:
1. Memory is ~100x faster than SSD, SSD ~100x faster than HDD seek.
2. Network inside a DC is cheap; across continents is bounded by the speed of light (~200,000 km/s in fiber; NYC<->London ~5,600 km => >= ~56 ms RTT physics floor).
3. Avoid round trips: batching, caching, CDN, co-location.
4. Sequential beats random on every medium.
5. Serialization/compression cost is small next to a network hop (unless payloads are huge).

---
## 2. Back-of-envelope estimation

Why: shows you can size a system and pick architecture accordingly (does this fit on one box? need sharding? need a CDN?). Aim for ~5 minutes, round aggressively, state assumptions out loud.

### Numbers to memorize

```
  Powers of two                        Time
  2^10 = 1 thousand  (KB)              1 day   = 86,400 s  ~ 10^5 s  (use 100,000)
  2^20 = 1 million   (MB)              1 month ~ 2.5 million s
  2^30 = 1 billion   (GB)              1 year  ~ 31.5 million s ~ 3 * 10^7 s
  2^40 = 1 trillion  (TB)
  2^50 = 1 quadrillion (PB)

  Handy conversions
  1 million req/day   ~ 12 QPS          (10^6 / 10^5)
  100 million req/day ~ 1,200 QPS
  1 billion req/day   ~ 12,000 QPS
  Peak ~ 2-5x average (state your assumption; social apps often 2-3x, event-driven 10x+)

  Availability -> downtime per year
  99%      3.65 days
  99.9%    8.76 hours
  99.99%   52.6 minutes
  99.999%  5.26 minutes
```

Typical capacity of one machine (very rough, check current docs / benchmark):
- Web/app server doing simple work: ~1k-10k QPS per core-ish range; a typical stateless API instance: hundreds to few thousand QPS.
- Single Postgres/MySQL node: ~1k-10k+ simple writes/s, ~10k-50k+ simple reads/s depending on hardware, schema, cache hit rate.
- Redis single node: ~100k ops/s (more with pipelining).
- Kafka broker: hundreds of MB/s throughput per broker is common on good disks/NICs.
- SSD: ~100s of thousands of IOPS (NVMe); NIC: 10-25 Gbps common in cloud; 1 Gbps = ~125 MB/s.
- RAM on a big box: 256 GB - several TB. Disk per box: tens of TB.

Typical data sizes:
- char/ASCII: 1 byte; UUID: 16 B (36 chars as text); int64: 8 B; timestamp: 8 B.
- Tweet-like text: ~300 B incl. metadata; DB row w/ a few columns: ~100 B - 1 KB.
- Image (compressed photo): ~200 KB - 2 MB; thumbnail: ~10-50 KB.
- Video: ~1 MB/min low quality, 5-10 MB/min HD (varies with codec; ~3-8 Mbps HD streaming).

### Worked example A: Twitter-like service

Assumptions (state them!): 300M MAU, 100M DAU, each user posts 0.5 tweets/day, reads 100 tweets/day (timeline views).

```
  Write QPS
    tweets/day     = 100M * 0.5 = 50M
    avg write QPS  = 50M / 100k s = 500 QPS
    peak (x3)      = 1,500 QPS

  Read QPS
    reads/day      = 100M * 100 = 10B tweet-reads/day
    avg read QPS   = 10B / 100k = 100,000 QPS
    peak (x3)      = 300,000 QPS
    read:write     = 200:1  -> read-heavy -> cache, replicas, fan-out on write

  Storage (text only)
    tweet size     = ~300 B (text 140-280 chars + ids + timestamps)
    per day        = 50M * 300 B = 15 GB/day
    per year       = ~5.5 TB/year; 5 years ~ 27 TB  (x3 replication ~ 80 TB)  -> fits sharded, trivially
  Storage (media): 20% have a 500 KB image
    50M * 0.2 * 500 KB = 5 TB/day -> 1.8 PB/year  -> object store + CDN, NOT the DB
  Bandwidth
    egress  : 100k read QPS * 1 KB (text payload) = 100 MB/s ~ 0.8 Gbps (text) -- easy
              media dominates: if 10% of reads include 200 KB image: 10k * 200 KB = 2 GB/s = 16 Gbps -> CDN
```
Takeaway: text is small; media dominates storage and bandwidth; read QPS drives the cache design.

### Worked example B: URL shortener

```
  Writes: 100M new URLs/month -> 100M / 2.5M s = ~40 QPS write (peak ~120)
  Read:write = 100:1       -> 4,000 QPS read (peak ~12k)
  Record = short code 7 B + long url ~200 B + metadata ~50 B ~ 300 B (round up to 500 B)
  Storage: 100M * 12 months * 5 years = 6B records * 500 B = 3 TB. Fits on one big box; shard for throughput/availability, not size.
  Key space: base62, 7 chars = 62^7 = ~3.5 trillion >> 6B. OK.
  Cache: 80/20 rule: cache top 20% of daily reads. Daily reads = 4,000*100k = 400M; unique ~?? say 100M; 20% * 100M * 500 B = 10 GB -> one Redis node.
```

### Worked example C: Photo upload service bandwidth

```
  10M DAU, each uploads 2 photos/day of 2 MB.
  Uploads/day = 20M -> 230 QPS avg (~700 peak)
  Ingress     = 230 * 2 MB = 460 MB/s avg (~3.7 Gbps)  peak ~1.4 GB/s
  Storage/day = 40 TB; per year = ~14.6 PB (before replication/erasure coding)
  => object storage (S3-like), multipart/presigned uploads straight to storage, async thumbnailing via queue, CDN for reads.
```

### Estimation method (say this out loud)
1. Clarify scale (DAU/MAU, read:write).
2. Derive QPS (avg + peak). 3. Derive storage (per-record size * count * retention * replication).
4. Derive bandwidth (QPS * payload). 5. Derive memory for cache (hot set).
6. Conclude: "so single node suffices / we need N shards / need CDN".
Common mistakes: forgetting peak vs average, forgetting replication factor (x3), mixing bits and bytes (Gbps vs GB/s: divide by 8), 86,400 vs 100,000 (use 10^5 and say so), over-precise arithmetic.

---
## 3. Scalability: vertical vs horizontal

```
  Vertical (scale up)                 Horizontal (scale out)
  +----------+                        +----+ +----+ +----+ +----+
  |  BIGGER  |                        | S1 | | S2 | | S3 | | S4 |
  |   BOX    |                        +----+ +----+ +----+ +----+
  +----------+                              ^ load balancer
```

| | Vertical | Horizontal |
|---|---|---|
| Complexity | Low (no code change) | High (distribution, consistency, partial failure) |
| Ceiling | Hard limit (largest instance) | Practically unbounded |
| Failure | Single point of failure | Survives node loss |
| Cost curve | Superlinear at the top end | Roughly linear, commodity |
| Downtime to scale | Often restart | Add nodes live |

Guidance: scale vertically first while it is cheap and simple (one big Postgres goes a long way: many companies run on a single primary + replicas for years), but design so that horizontal is possible: stateless services, partitionable data, idempotent operations.

Scaling a typical system in stages (a good narrative for interviews):
1. Single server (app + DB). 2. Split DB from app. 3. Add load balancer + multiple stateless app servers. 4. Add read replicas + cache. 5. CDN for static/media. 6. Message queue for async work. 7. Shard the DB. 8. Multi-AZ, then multi-region. 9. Observability + autoscaling throughout.

Scaling axes (Scale Cube): X = clone (replicas behind LB), Y = functional split (microservices), Z = data partitioning (sharding by key).

Amdahl's law: speedup is limited by the serial fraction. If 5% of work is serial (e.g. a single lock, a single leader), max speedup is 20x no matter how many nodes. Universal Scalability Law adds coherence cost: adding nodes can reduce throughput (contention + crosstalk). Hot spots (one hot key / one lock / one primary) are the practical form of this.

### Autoscaling basics
- Scale on a leading metric that correlates with load (CPU, requests per target, queue depth) not lagging errors.
- Scale-out is quick (minutes), keep headroom for the warm-up time; scale-in slowly (cooldowns) to avoid flapping.
- Pre-warm for known events (sales, launches). See AWS Auto Scaling in `../../07-aws/week-02-compute/lesson.md`.
- Stateful tiers (DB, cache) do not autoscale nearly as easily as stateless ones.

---
## 4. Stateless services

A service is stateless if any request can be served by any instance, because no per-client state lives in instance memory/disk between requests.

```
  STATEFUL (sticky)                          STATELESS
  client -> LB -> S1 (session in RAM)        client -> LB -> any of S1..Sn
  if S1 dies the session is lost             state in: DB, Redis, signed token (JWT), client cookie
```

Where state goes:
- Session -> Redis / DB, or stateless signed tokens (JWT). Tradeoff: JWT cannot be revoked easily (needs short expiry + deny-list/refresh tokens), larger request size.
- Uploaded files -> object storage (S3), never local disk.
- Background jobs/schedules -> queue + workers, or a distributed scheduler with leader election (week 4).
- Websocket connections are inherently stateful: keep a connection registry (user -> gateway node) in Redis (week 6 chat design).
- Local caches are fine as an optimization (not the source of truth), but accept inconsistency across nodes.

Benefits: trivial horizontal scaling, rolling deploys, easy failover, autoscaling, spot instances.
12-factor hints: config in env, logs to stdout, disposable processes, fast startup/graceful shutdown.
Sticky sessions (LB affinity) are a crutch: uneven load, lost on node failure, complicate deploys. Use only if unavoidable.

FastAPI tie-in: your app instances should hold no per-user state in module globals; use dependency-injected DB/Redis clients; run multiple uvicorn workers/containers behind a LB; use `/healthz` (liveness) and `/readyz` (readiness) endpoints.

---
## 5. Availability and reliability

- Availability = fraction of time the system is able to serve correct requests = uptime / (uptime + downtime). Also = MTBF / (MTBF + MTTR).
- Reliability = probability of performing correctly over a period (fewer failures). Durability = data not lost (S3 quotes "11 nines" annual durability design target - check current docs). Availability and durability are different: you can be down but lose nothing.
- Fault (component deviates) vs failure (system stops serving users). Goal: fault tolerance - faults do not become failures.

### The nines

```
  Availability   Downtime/year   Downtime/month   Typical meaning
  99%            3.65 days       7.3 h            hobby
  99.9%          8.76 h          43.8 min         "three nines" typical SaaS
  99.95%         4.38 h          21.9 min
  99.99%         52.6 min        4.4 min          "four nines" needs automation, multi-AZ
  99.999%        5.26 min        26 s             "five nines" needs multi-region, hard
```

### Composing availability

```
  Serial (all must work):   A = A1 * A2 * A3
     3 services at 99.9% each => 0.999^3 = 99.7%  (~26 hours/year!)
     => deep dependency chains destroy availability. Reduce hard dependencies; make some soft (degrade gracefully).

  Parallel (any one suffices, independent failures):  A = 1 - (1-A1)(1-A2)
     2 replicas at 99%   => 1 - 0.01*0.01 = 99.99%
     Caveat: failures are rarely independent (shared deploy, shared config, shared region, same bug). Correlated failure is the real enemy.
```

### Techniques
- Redundancy: N+1 instances across AZs; no single point of failure (SPOF). Ask for every box on the diagram: "what if this dies?"
- Failover: active-passive (standby takes over; detection + promotion delay) vs active-active (all serve; need conflict handling for state).
- Health checks + automatic removal from LB; fast detection vs false positives tradeoff.
- Graceful degradation: serve stale cache, disable recommendations, read-only mode.
- Load shedding & rate limiting; bulkheads (isolate resource pools per dependency); timeouts; retries with backoff (week 3); circuit breakers (week 3).
- Safe deploys: canary, blue/green, feature flags, fast rollback (week 5). Most outages are caused by changes.
- Chaos engineering; game days; capacity planning.
- Blast radius reduction: cells/shards so one bad tenant/shard affects a fraction.

### Common failure modes (name these in interviews)
- Cascading failure: slow dependency -> threads pile up -> upstream times out -> retries multiply load (retry storm) -> total outage.
- Thundering herd / cache stampede after a restart or expiry.
- Split brain: two nodes both think they are leader.
- Gray failure: node is "up" but slow/partial; health checks pass; hardest to detect.
- Correlated failure: bad config push, expired certificate, full disk, clock skew, leap-second, DNS.
- Metastable failure: system stuck in overloaded state even after trigger is gone (retries + cold caches keep it down).
- Resource exhaustion: connection pools, file descriptors, memory leaks, ephemeral ports.

### MTTR matters more than MTBF
You cannot prevent all failures; shorten detection and recovery. Good alerts, runbooks, automated rollback, one-click failover.

---
## 6. SLI, SLO, SLA, error budgets

```
  SLI  (indicator): a measured number.            e.g. fraction of requests < 300 ms and non-5xx
  SLO  (objective): internal target on an SLI.    e.g. 99.9% over 30 days
  SLA  (agreement): contract with consequences.   e.g. below 99.5% => service credits
  Rule: SLO is stricter than SLA, so you notice before you owe money.
```

- Choose SLIs the user feels: availability (good requests / total), latency (p99 < X ms), correctness/freshness, durability, throughput for batch. The "four golden signals": latency, traffic, errors, saturation. RED (Rate, Errors, Duration) for services; USE (Utilization, Saturation, Errors) for resources.
- Error budget = 1 - SLO. SLO 99.9% over 30 days => 43.2 min of allowed badness. Budget remaining -> ship features; budget spent -> freeze risky launches, work on reliability. This turns reliability vs velocity into an objective negotiation.
- Burn-rate alerts: alert when budget is consumed too fast (e.g. 14.4x burn over 1 hour pages; slower burn opens a ticket) rather than on every blip. Multi-window multi-burn-rate is the Google SRE workbook recommendation.
- SLO of a dependency bounds yours: cannot promise 99.99% on top of a 99.9% hard dependency (see serial math).
- Measure from the user's perspective (load balancer / client / synthetic probes), not from inside the server which cannot see its own outages.
- Good SLO is not 100%: users cannot tell 99.99 from 99.999 when their own network is 99.9; cost grows ~10x per nine.

---
## 7. Load balancing

Purpose: spread requests over many servers, remove dead ones, terminate TLS, give one stable entry point.

```
                 +-- DNS (round robin / geo / latency routing) --+
   clients ----> |      L4/L7 Load Balancer (HA pair/managed)    | ---> app1
                 +-----------------------------------------------+ ---> app2
                        health checks <----------------------------> app3
```

### L4 vs L7

| | L4 (transport) | L7 (application) |
|---|---|---|
| Sees | IP, port, TCP/UDP | HTTP: path, headers, cookies, method |
| Speed | Very fast, low CPU, millions of conns | Slower (parses HTTP, terminates TLS) |
| Features | Simple forwarding, NAT-like | Path/host routing, TLS termination, auth, rewrites, WAF, gRPC-aware, sticky via cookie, canary by header |
| Examples | AWS NLB, HAProxy tcp mode, LVS, IPVS, Maglev (Google) | AWS ALB, Nginx, Envoy, HAProxy http mode |
| Use | Extreme throughput, non-HTTP protocols, static IPs | Microservices routing, HTTP features |

AWS mapping: NLB (L4), ALB (L7), Gateway LB (L3 appliances); see `../../07-aws/week-02-compute/lesson.md`.
Layering pattern: DNS/GeoDNS -> L4 (anycast/ECMP) -> L7 fleet -> services. Also client-side LB (gRPC, service mesh sidecar) and server-side.
Important: the LB itself must not be a SPOF - managed LBs are multi-AZ; self-run use active-passive with VRRP/keepalived or ECMP + anycast.
TLS termination at LB (offload) vs passthrough vs re-encrypt to backend (zero-trust).
Connection draining on deploy: stop new requests, finish in-flight ones.

### Algorithms

| Algorithm | How | Good for | Caveat |
|---|---|---|---|
| Round robin | rotate | Homogeneous, similar request cost | Ignores load |
| Weighted round robin | rotate by weight | Heterogeneous machines | Static weights |
| Least connections | fewest active conns | Variable-duration requests (websockets, long calls) | Needs conn tracking |
| Least response time / EWMA | fastest + fewest | Latency-sensitive | Can herd to a "fast" node |
| Power of two choices (P2C) | pick 2 at random, take less loaded | Large fleets, distributed LBs; near-optimal | Needs load info |
| IP hash / source hash | hash(client IP) % N | Cheap affinity | Remapping when N changes; NAT skew |
| Consistent hashing | hash ring, minimal remap | Caches, sharded backends, sticky by key | Needs virtual nodes for balance (week 2) |
| Random | random | Simple | Variance |
| Resource-based | agents report CPU/mem | Heavy heterogenous work | Staleness |

Health checks: active (LB probes /healthz at intervals; N failures to eject, M successes to re-add) and passive (outlier detection on observed errors). Shallow vs deep check: deep check that touches the DB can take the whole fleet out when DB hiccups -> prefer shallow liveness + separate readiness and be careful what readiness depends on.
Slow start: ramp traffic to new instances while JVM/caches warm up.
Pitfall: "least connections" with a new empty node can flood it; fix with slow start.
Pitfall: retries at LB + client + service = multiplicative amplification; budget retries.
Global load balancing: GeoDNS, anycast, latency-based routing (Route 53 policies, see `../../07-aws/week-04-networking/lesson.md`); failover with health checks; DNS TTL tradeoff (low TTL = fast failover but more DNS load; clients/ISPs may ignore TTL).

---
## 8. Caching

Why: reduce latency, offload backends, absorb read spikes. Works because of locality (temporal and spatial) and skewed popularity (Zipf: a few keys get most reads).
Key metrics: hit ratio, latency, eviction rate, memory. Effective latency = h * t_cache + (1-h) * t_origin. With 95% hit at 1 ms vs 50 ms origin: 0.95*1 + 0.05*50 = 3.45 ms. Going 95% -> 99% hit gives 1.5 ms: tail matters.

### Where caches live
```
  Browser cache -> CDN edge -> API gateway/reverse proxy -> app local (in-process) -> distributed cache (Redis/Memcached) -> DB buffer pool/page cache -> disk
```
In-process: fastest, no network, but per-node, duplicated, inconsistent, cleared on deploy. Distributed: shared, bigger, extra hop (~0.5-1 ms), a new dependency to run. Often use both (L1 local small TTL + L2 Redis).

### Strategies

```
  Cache-aside (lazy loading)               Read-through
  app: get(k) from cache                   app only talks to cache;
   miss -> read DB -> set cache -> return  cache loads from DB on miss (library/provider)
  writes: update DB, then DELETE key
  + resilient to cache outage              + simpler app code
  - first read slow, stale window          - cache layer must know the loader

  Write-through                            Write-back (write-behind)
  write -> cache AND DB synchronously      write -> cache only; flushed to DB async
  + cache always consistent with DB        + very fast writes, batching/coalescing
  - write latency = both; cache pollution  - data loss if cache dies before flush; complex
    for never-read data                    use for counters, metrics, with durable log/AOF

  Write-around: write to DB only, cache fills on read (avoid polluting cache with write-once data)
  Refresh-ahead: proactively refresh hot keys before TTL expiry (avoids stampede, wastes work on cold keys)
```
Default answer: cache-aside + TTL + invalidate (delete) on write. Delete rather than update the cache on writes to avoid races (two writers can leave an older value in the cache: W1 writes DB, W2 writes DB, W2 sets cache, W1 sets cache => stale). Even delete has a race: reader reads old DB value, writer updates DB and deletes key, reader sets cache with old value. Mitigations: short TTL, versioned values/CAS, delayed double-delete, or invalidation via CDC/binlog stream (Debezium) - what Facebook's "Scaling Memcache" does with leases to prevent stale sets and stampedes.

### Eviction policies
- LRU (least recently used): the default; good for recency. Approximate LRU in Redis (sampling).
- LFU (least frequently used): resists scan pollution, better for stable popularity; Redis `allkeys-lfu`; TinyLFU/W-TinyLFU (Caffeine) high hit ratio.
- FIFO, random, TTL-based (expire soonest), CLOCK (cheap LRU approximation), ARC/2Q (scan-resistant).
- Redis `maxmemory-policy`: noeviction, allkeys-lru, volatile-lru, allkeys-lfu, volatile-ttl, etc. (check current docs). Be able to implement LRU with hashmap + doubly linked list: O(1) get/put (classic DSA tie-in).

### Invalidation ("two hard things")
- TTL: simple, bounded staleness; choose from business tolerance; add jitter to TTLs to avoid synchronized expiry.
- Explicit invalidation on write (delete key / publish event); needs knowing all keys derived from the changed data (tag/dependency keys).
- Versioned keys: `user:42:v17` - bump version rather than delete; old entries age out. Great for CDN assets (content-hash filenames, cache-forever).
- Event-driven (CDC -> invalidate).
- Accept eventual consistency for most reads; read-your-own-writes may need bypass/short-lived "recently written" flag.

### Cache problems

```
  Stampede / thundering herd / dogpile: hot key expires; 10,000 requests miss simultaneously and hit DB.
     Fixes: request coalescing / single-flight (one loader, others wait), mutex/lease on key,
            stale-while-revalidate (serve stale, refresh in background), TTL jitter, refresh-ahead, probabilistic early expiration (XFetch).
  Penetration: requests for keys that don't exist always miss and hit DB (often malicious).
     Fixes: cache negative results (short TTL), Bloom filter in front (week 4), input validation.
  Breakdown (hot key expiring) = stampede on a single key; same fixes.
  Avalanche: many keys expire at once, or the whole cache goes down.
     Fixes: TTL jitter, multi-AZ replicated cache, circuit breaker + load shedding to protect DB, warm-up before cutover.
  Hot key: one key exceeds a single node's capacity (celebrity). Fixes: local in-process replica, key splitting `key#0..k` with random suffix on read, replicate hot keys.
  Cold start: empty cache after deploy/failover -> pre-warm or ramp traffic.
  Consistency: stale reads, dual-write races (above).
  Big keys / big values: block single-threaded Redis; split or compress.
```

### Redis vs Memcached (quick)
- Redis: rich types (hash, list, set, sorted set, streams), persistence (RDB/AOF), replication, Cluster (16384 hash slots), Lua/transactions, pub/sub; mostly single-threaded command execution (I/O threads optional). Use for cache + counters + leaderboards + rate limiting + locks (caveat week 4).
- Memcached: simple key-value, multithreaded, no persistence; very simple and fast for pure cache.
- Managed: ElastiCache / MemoryDB (see `../../07-aws/week-03-storage-databases/lesson.md`).
- Redis is a cache and may lose data on failover (async replication) - do not treat as the system of record unless you accept that.

### CDN
```
   user -> nearest edge POP -(miss)-> regional/origin shield -(miss)-> origin (S3/app)
```
- Caches static assets (images, JS/CSS, video segments) and can cache API GETs; reduces origin load and latency (user hits nearby POP; TLS terminates near user; persistent connections to origin).
- Control with `Cache-Control: max-age, s-maxage, stale-while-revalidate, no-store, private/public`, `ETag`/`If-None-Match` (conditional GET -> 304), `Vary` (careful: Vary: Cookie kills hit ratio).
- Invalidation: purge API (slow/expensive/rate-limited) vs versioned URLs (preferred).
- Push vs pull CDN: pull (lazy from origin; default) vs push (you upload; good for large, rarely-changing files).
- Origin shield: collapses misses from many POPs into one to protect origin.
- Security: signed URLs/cookies for private content; DDoS absorption; WAF at edge.
- AWS CloudFront details: `../../07-aws/week-04-networking/lesson.md`.

### Real-world examples
- Facebook Memcache: look-aside cache, leases against stampede/stale sets, regional pools, McSqueal invalidations reading MySQL commit log.
- Twitter timeline: Redis lists of tweet IDs per user (fan-out on write; week 6).
- Netflix Open Connect: CDN appliances inside ISPs, pre-positioned popular content overnight.
- DynamoDB DAX: write-through item cache in front of DynamoDB (microsecond reads).

---
## 9. How interviewers probe this week's topics

- "How many servers do you need?" -> expect QPS math and per-server capacity assumption, then headroom (target 50-70% utilization peak) and N+1/AZ redundancy.
- "What if the cache goes down?" -> DB overload; circuit breaker, load shed, multi-AZ replicas, warm-up, local fallback.
- "What is your SLO and how would you measure it?" -> SLI definition, error budget, where measured.
- "Walk me through a hot key / celebrity problem." -> local caching, key splitting, replicas.
- "Why not just scale vertically?" -> ceiling, SPOF, cost; but say it is a fine first step.
- "L4 or L7 here?" -> match features needed; mention both in layers.
- "Your three services are 99.9% each - what is the combined availability?" -> 99.7% and how to improve (parallel redundancy, async decoupling, caching, degrading).
- "Cache and DB are inconsistent. How?" -> race conditions; TTL; delete-after-write; CDC.
- "Where do sessions go?" -> externalize.
- Follow-ups probe whether you reason about failure modes unprompted. Always state: assumptions, numbers, tradeoffs, what breaks first.

---
## 10. Self-check (answer without notes)
1. State Little's law and use it to size a thread pool.
2. Compute QPS for 50M requests/day, with peak 3x.
3. Availability of 3 serial 99.95% components?
4. Name 4 cache failure modes and a fix each.
5. L4 vs L7: two differences and one example of each.
6. Cache-aside vs write-through: when each?
7. Why delete instead of update the cache on write?
8. What is an error budget and what happens when it is exhausted?
