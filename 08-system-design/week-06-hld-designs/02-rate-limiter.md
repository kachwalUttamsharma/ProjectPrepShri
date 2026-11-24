# Design 2: Distributed Rate Limiter

Framework: [framework.md](framework.md). Background: algorithms and retries in [coordination and messaging](../week-03-coordination-messaging/lesson.md); caching and Redis in [fundamentals](../week-01-fundamentals/lesson.md); API gateway in [architecture and ops](../week-05-architecture-operations/lesson.md).

## 1. Clarify requirements

Functional
- Limit requests per client identity (user ID, API key, IP, tenant) per rule (for example 100 req/min per API key on `POST /orders`).
- Return HTTP 429 with `Retry-After` and `X-RateLimit-Limit/Remaining/Reset` headers.
- Rules configurable per endpoint/tier without redeploy.

Non-functional
- Very low overhead: added latency < 1-5 ms p99; the limiter is on the hot path of every request.
- Highly available. Decide the failure policy: fail open (allow traffic if the limiter is down) for most APIs, fail closed for abuse-critical endpoints.
- Accurate enough: a small overshoot is acceptable; strictness is a tradeoff against latency.
- Works across many API gateway/app instances (distributed, shared state).
- Out of scope: DDoS at L3/L4 (that is WAF/CDN/Shield territory); mention it.

## 2. Estimate

- 1M requests/s across the fleet at peak (assume a large API platform), 10M distinct active keys.
- State per key: counter + timestamp ~ 50-100 bytes. 10M x 100 B = ~1 GB. Fits in memory on a single Redis node, but throughput requires sharding: a Redis node does roughly 100K+ simple ops/s (check current docs/benchmarks), so ~10-20 shards with headroom.
- Each check is 1 Redis round trip (use a Lua script to make read-modify-write atomic): ~0.3-1 ms in-region.
- Sliding-window-log would be much bigger: 100 req/min x 10M keys x 8 B timestamps = ~8 GB, which is why we prefer counters.

## 3. API

Internal check (library or sidecar):
```
allow(key, rule_id, cost=1) -> { allowed: bool, remaining: int, retry_after_ms: int }
```
Admin:
```
PUT /v1/rules/{rule_id}   { "match": {"endpoint": "POST /orders", "tier": "free"},
                            "limit": 100, "window_s": 60, "algorithm": "token_bucket", "burst": 20 }
GET /v1/rules
```
Client-visible: 429 Too Many Requests with
```
Retry-After: 12
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1735689600
```

## 4. Data model

Rules: small, rarely changing; store in a config DB, push/cached in each limiter node (poll or pub/sub updates, short TTL).

Counters in Redis, per algorithm:
```
Token bucket:         key = rl:{rule}:{client}   value = hash {tokens, last_refill_ts}
Fixed window counter: key = rl:{rule}:{client}:{window_start}   value = int, EXPIRE window
Sliding window counter: two fixed-window keys (current + previous), weighted
Sliding window log:   sorted set of timestamps (ZADD/ZREMRANGEBYSCORE/ZCARD)
```

## 5. Algorithms compared

| Algorithm | Idea | Pros | Cons |
|---|---|---|---|
| Fixed window counter | Count in each wall-clock window | Simple, cheap | Boundary burst: 2x limit across a window edge |
| Sliding window log | Store each timestamp | Exact | Memory heavy |
| Sliding window counter | Weighted current + previous window: `prev * (1 - elapsed_fraction) + curr` | Cheap, smooth, approx | Approximation (assumes even distribution) |
| Token bucket | Bucket of capacity B refills at rate r; request costs a token | Allows bursts, simple, used by AWS/Stripe | Two parameters to tune |
| Leaky bucket | Queue drained at fixed rate | Smooth output rate | Bursts get queued or dropped; adds latency |

Default recommendation: token bucket (burst-friendly) or sliding window counter (cheap and smooth).

Token bucket in Redis (atomic via Lua):
```
-- KEYS[1]=key ARGV: rate, capacity, now, cost
local t = redis.call('HMGET', KEYS[1], 'tokens', 'ts')
local tokens = tonumber(t[1]) or capacity
local ts = tonumber(t[2]) or now
tokens = math.min(capacity, tokens + (now - ts) * rate)
local allowed = tokens >= cost
if allowed then tokens = tokens - cost end
redis.call('HSET', KEYS[1], 'tokens', tokens, 'ts', now)
redis.call('EXPIRE', KEYS[1], ttl)
return allowed
```
Use the Redis server clock (TIME inside the script) rather than client clocks to avoid skew.

## 6. High-level diagram

```
 Client
   |
 [Edge / WAF]  (coarse IP limits, DDoS)
   |
 [API Gateway / LB]
   |
 +--------------------------+
 | Rate limit middleware    |   local rule cache <----- [Rules DB / config service]
 | (in gateway or sidecar)  |
 +--------------------------+
   |   allow(key)?              |
   |   (1 RTT, Lua)             |
   v                            |
 [Redis cluster: sharded by hash(client_key), replicas for failover]
   |
 allowed -> [App service]      denied -> 429 + headers
 metrics -> [Prometheus/Kafka] (hits, rejects per rule)
```

Placement options:
1. In the API gateway (central, simplest, one language, covers all services). Most common.
2. As a sidecar/library per service (no extra network hop to a gateway, but more integration).
3. Standalone rate-limit service (Envoy's global rate limit service calls it over gRPC): adds a hop but central control.

## 7. Deep dives

### a) Race conditions and atomicity
Naive GET then SET loses updates under concurrency. Use atomic INCR (fixed window), or a Lua script / `EVALSHA` (token bucket, sliding window) so check-and-update is one atomic step on the shard. Redis single-threaded execution makes the script atomic.

### b) Distributed accuracy versus latency
- Exact global limit requires every check to hit the shared store (1 RTT).
- Reduce cost by local batching: each gateway node reserves a chunk of tokens (for example 10% of the limit) from Redis and serves locally, refilling when exhausted. Trades accuracy (overshoot up to N nodes x chunk) for fewer round trips.
- Eventually consistent counters (gossip/async sync) give very low latency but looser accuracy. Pick by how costly an overshoot is (billing quota vs abuse protection).

### c) Multi-region
- Per-region limits (simple, each region enforces its share) vs global limit (cross-region sync, higher latency). Common: allocate a quota share per region and rebalance periodically. Strict global counting across regions is usually not worth the cross-region latency.

### d) Hot keys
One abusive client or one very large tenant makes a single Redis shard hot. Mitigate: shard that key's counter into N sub-counters (sum approximate), or apply an in-process pre-limit before hitting Redis, or block at the edge.

### e) Failure policy
- Redis down or timeout (set a tight timeout, such as 5-10 ms): fail open with a local in-memory fallback limiter (per-node approximation) and alert. For login/payment brute-force protection, fail closed.
- Use a circuit breaker around the limiter call ([circuit breaker](../week-03-coordination-messaging/lesson.md)).

### f) Identity choice
API key/user ID is best; IP is shared by NAT (many users) and spoofable via X-Forwarded-For (trust only your own proxy chain). Combine tiers: per-IP coarse, per-user fine, per-endpoint cost-weighted.

### g) Client-side cooperation
Return `Retry-After`; clients should use exponential backoff with jitter to prevent retry storms. Cost-based limits (heavy endpoints cost more tokens) are common for LLM APIs (tokens per minute).

## 8. Bottlenecks and failure modes

- Redis shard failover: replicas lag, so recent counts may be lost; the effect is a brief over-allowance. Acceptable.
- Clock skew across nodes: use server-side time in Lua.
- Rule misconfiguration (limit 0) takes down legit traffic: validate rules, staged rollout, dry-run (shadow) mode that logs would-be rejects first.
- Thundering herd at window boundary with fixed window: use sliding window or token bucket.
- Memory growth: set TTLs on every key.

## 9. Tradeoffs

- Accuracy vs latency (central atomic check vs local batching).
- Memory vs precision (log vs counter).
- Fail open vs fail closed.
- Burst allowance (token bucket) vs smooth output (leaky bucket).
- Central gateway enforcement vs per-service enforcement (consistency of policy vs coupling).

## 10. What to say out loud

- "The limiter sits on every request, so the key constraints are sub-millisecond overhead and not becoming a SPOF."
- "I will use token bucket in Redis with a Lua script so the read-modify-write is atomic, and I will use Redis server time."
- "If the limiter backend is down, I fail open for normal APIs and fail closed for login, and I alert either way."
- "Sliding window log is exact but costs memory proportional to the limit; the weighted sliding window counter is about 99% as good at constant memory."

## 11. Follow-up questions to practice

1. Fixed window vs sliding window: show the boundary burst problem with numbers.
2. How would you rate limit by token usage for an LLM API where cost is known only after the response? (reserve estimated, reconcile after)
3. How do you handle 1,000 gateway nodes? (sharded Redis, local token batching)
4. How do you roll out a new rule safely? (shadow mode, percent rollout)
5. How would you rate limit across multiple regions?
6. How is rate limiting different from load shedding and backpressure?
