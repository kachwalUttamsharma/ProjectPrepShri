# Week 1 Cheatsheet - Fundamentals

## Estimation constants
- 1 day ~ 10^5 s; 1 month ~ 2.5M s; 1 year ~ 3*10^7 s
- 1M req/day ~ 12 QPS; 1B/day ~ 12k QPS; peak = 2-5x avg
- 2^10 KB, 2^20 MB, 2^30 GB, 2^40 TB, 2^50 PB
- Gbps / 8 = GB/s; 1 Gbps ~ 125 MB/s
- Storage = records * size * retention * replication (x3)
- Cache sizing: hot set ~ 20% of daily unique items (80/20)
- Target 50-70% utilization at peak; N+1 across AZs

## Latency (order of magnitude)
```
RAM 100 ns | NVMe read 10-100 us | same-DC RTT 0.5 ms | HDD seek 5-10 ms
Cross-US RTT 60-80 ms | US-EU 80-150 ms | US-Asia 150-250 ms
```
Memory 100x SSD; SSD 100x HDD seek. Avoid round trips; sequential > random.

## Formulas
- Little: L = lambda * W
- Effective latency = h*t_cache + (1-h)*t_origin
- Serial availability = product; parallel = 1 - prod(1-Ai) (assumes independence)
- Fan-out tail: P(slow) = 1 - (1-p)^N
- Error budget = 1 - SLO; 99.9%/30d = 43.2 min
- Amdahl: max speedup = 1 / serial fraction

## Nines (per year)
99% 3.65 d | 99.9% 8.76 h | 99.99% 52.6 min | 99.999% 5.26 min

## SLI / SLO / SLA
SLI = metric; SLO = internal target; SLA = contract (looser). Golden signals: latency, traffic, errors, saturation. RED for services, USE for resources. Burn-rate alerts.

## Scaling
Vertical: simple, capped, SPOF. Horizontal: stateless + partition. Scale cube: X clone, Y functional, Z data. Stateless = state in DB/Redis/S3/JWT. Prefer leading autoscale metrics (RPS/target, queue depth).

## Availability toolbox
Redundancy (multi-AZ), failover (active-passive/active-active), health checks, timeouts, retries+backoff, circuit breaker, bulkhead, load shedding, graceful degradation, canary/rollback, cells. Failure modes: cascading, retry storm, split brain, gray failure, correlated (config/cert/disk), metastable.

## Load balancing
- L4: IP/port, fast, NLB/HAProxy/LVS. L7: HTTP-aware, TLS, routing, ALB/Envoy/Nginx.
- Algos: RR, weighted RR, least conn, P2C, IP hash, consistent hash, EWMA
- Health: active+passive; liveness vs readiness; slow start; connection draining
- Global: GeoDNS/latency routing/anycast; low DNS TTL for failover

## Caching
| Pattern | Read | Write | Risk |
|---|---|---|---|
| Cache-aside | app loads on miss | DB then delete key | stale window, races |
| Read-through | cache loads | - | loader coupling |
| Write-through | - | cache+DB sync | write latency |
| Write-back | - | cache, async DB | data loss |
| Write-around | - | DB only | first read miss |
| Refresh-ahead | proactive reload | - | wasted work |

Eviction: LRU (default), LFU/TinyLFU (stable popularity), FIFO, TTL, random.
Problems -> fixes: stampede -> single-flight, SWR, jitter; penetration -> negative cache, Bloom; avalanche -> jitter, replicas, shed; hot key -> local cache, key splitting; cold start -> pre-warm.
CDN: versioned URLs > purge; Cache-Control/ETag/Vary; origin shield; signed URLs.
Redis: types, persistence, async replication, 16384 slots; Memcached: simple, multithreaded.

## Say out loud
Assumptions -> numbers (QPS, storage, bandwidth) -> bottleneck -> design choice -> failure modes -> tradeoff.

## Cross-links
AWS: ../../07-aws/week-02-compute (ELB, ASG), week-03-storage-databases (ElastiCache, DynamoDB), week-04-networking (CloudFront, Route 53).
