# HLD 7 - Ride-Hailing Dispatch (Uber-style)

Background: [sharding, replication](../week-02-data-storage/lesson.md), [queues/Kafka, backpressure](../week-03-coordination-messaging/lesson.md), [locks, consensus, clocks](../week-04-distributed-algorithms/lesson.md). Framework: [framework.md](framework.md).

## 1. Clarify requirements
Functional: rider requests a ride (pickup/dropoff); system finds nearby available drivers, offers the trip, driver accepts; live tracking; ETA and fare estimate; surge pricing; trip lifecycle and payments (payments out of scope but state integration).
Non-functional: match latency few seconds; location freshness ~ 4-5 s; high availability in dispatch; a driver must not be double-assigned; a rider must not get two cars; regional isolation (a city outage must not take down others).
Scope question: single-city or global? Say "cell/region sharded by city".

## 2. Estimate
- 5M drivers online at peak globally, each sends GPS every 4 s -> 1.25M updates/s. Payload ~100 B -> 125 MB/s ingest. (Check: 5M/4 = 1.25M.)
- Rides: 20M/day -> ~230/s avg, peak ~1k/s requests. Each request queries nearby drivers: small compared to location writes.
- Location state in memory: 5M x ~100 B = 500 MB - trivially fits in memory; the problem is write rate, not size.
- Trip storage: 20M/day x 2 KB = 40 GB/day; ~15 TB/yr; plus GPS traces to cold storage (object store) for analytics: 1.25M x 100 B x 86,400 ~ 10 TB/day if all retained - so sample/compress.

## 3. API
```
POST /v1/rides            {rider_id, pickup:{lat,lng}, dropoff, product} -> 202 {ride_id}
GET  /v1/rides/{id}       status, driver, ETA
WS   /v1/rides/{id}/stream  driver location, state changes (WebSocket/SSE)
POST /v1/drivers/location {driver_id, lat, lng, heading, ts}   (batched, UDP/MQTT/gRPC stream)
POST /v1/drivers/{id}/offers/{offer_id}/accept | decline
PUT  /v1/drivers/{id}/status  online|offline
```

## 4. Data model
- Driver location (hot, in-memory): `driver_id -> {lat,lng,cell,ts,status,vehicle}` plus per-cell set `cell -> {driver_ids}` (Redis/in-memory service).
- Trip (durable, strongly consistent per trip): `trip_id, rider_id, driver_id, state, pickup, dropoff, fare, timestamps`. Sharded by trip_id (or city); SQL/Spanner-like or Cassandra with LWT for state transitions.
- Driver state machine: offline -> available -> offered -> on_trip -> available.
- Event log in Kafka for location and trip events -> analytics, ETA models, surge.

## 5. High-level diagram
```
 Driver app --(GPS every 4s)--> [Location gateway] --> Kafka(loc, key=driver/cell)
                                                        |       |
                                         [Location index svc]  [GPS trace sink -> S3]
                                         in-memory geo index (sharded by city/cell)
 Rider app --request--> [API GW] --> [Ride service] --> [Dispatch/Matching svc (per region)]
                                         |  trip DB            | 1 query nearby cells (index)
                                         |                     | 2 rank by ETA (routing svc)
                                         |                     | 3 offer to best driver (push)
                                         |                     | 4 timeout/decline -> next candidate
                                         v                     v
                                   [Trip state machine] <-- driver accepts (atomic CAS)
 [Pricing/surge svc] <-- demand/supply per cell (stream agg)     [ETA/Routing svc]
 [WebSocket tracking svc] <-- location events for active trips
```

## 6. Deep dives
**Geospatial indexing.**
- Geohash: string prefix = cell; neighbors via prefix + 8 adjacent cells; edge discontinuities and varying cell shape (distorted near poles).
- Quadtree: adaptive to density (split when > K drivers); in-memory, harder to distribute.
- S2 (Google): sphere projected onto cube, Hilbert-curve cell ids, hierarchical, good area-covering of a radius.
- H3 (Uber): hexagonal grid, uniform neighbor distance (6 neighbors, equidistant) - good for surge and ETA aggregations.
Approach: index each driver by cell id at a chosen resolution (~ a few hundred meters to 1 km); a nearby query expands rings (k-ring) around the pickup cell until enough candidates; then exact distance filter. Shard the index by cell range or city so each shard is in memory.
**Location ingestion.** 1.25M writes/s: use lightweight protocol, batching, and drop-oldest semantics (only latest position matters). Update the in-memory index directly, write to Kafka async. Skip update if the driver barely moved. Cell changes require removing from old cell set and adding to new.
**Matching.** Naive: nearest driver. Better: rank by ETA via routing graph (road distance, not straight line), driver rating, acceptance probability. Batch matching (collect requests for ~2 s and solve assignment, e.g., bipartite/Hungarian-like) improves global efficiency vs greedy. Offer sequentially or to a small wave; offer timeout ~10-15 s.
**No double assignment.** Offer a driver => driver state `available -> offered` via atomic compare-and-set (per-driver lock/lease with TTL, or DB conditional write). Accept => `offered -> on_trip` and trip `requested -> matched` as one atomic step (single-shard transaction or state machine with CAS). Lease expiry returns driver to the pool. Use fencing/version numbers so a delayed accept from an expired offer is rejected. See distributed locks in week 4.
**Dispatch service scaling.** Shard by geography (city/cell range); a request is routed to its region's dispatcher (consistent hashing or ownership via ringpop-style gossip). Dispatcher state in memory + recoverable from the log. Failover: another node takes the range; re-read state.
**Surge pricing.** Stream-aggregate demand (requests) vs supply (available drivers) per H3 cell over sliding windows -> multiplier with smoothing and caps to avoid oscillation; publish via cache. Regulatory/ethical limits apply.
**ETA.** Road graph with contraction-hierarchies-type precompute plus live traffic from GPS streams and ML correction; cache popular segments.
**Tracking.** WebSocket/SSE fan-out only for active trips (~ millions); pub/sub keyed by trip_id; fall back to polling.
**Reliability.** Driver app offline/flaky network: heartbeat TTL marks driver unavailable; idempotent accept; trip state persisted so app reconnect resumes.

## 7. Bottlenecks and failure modes
- Hot cells (airport, stadium event): sub-shard dense cells, finer resolution adaptively.
- Location write storm after network blip (all drivers reconnect): jittered reconnect, rate limits.
- Stale locations => offers to ghost drivers: TTL + status checks.
- Dispatcher crash mid-offer: leases expire; offers idempotent.
- Region outage: failover to neighboring region with replicated trip state (async; accept small data loss window or use sync consensus for trips).
- Matching thrash or starvation of far riders: batch window + max-wait escalation.

## 8. Tradeoffs
- Greedy vs batch matching (latency vs efficiency). Straight-line vs routed ETA (speed vs accuracy).
- Geohash (simple, string-indexable in any KV) vs H3/S2 (better geometry, library dependency).
- In-memory index (fast, rebuild on crash from stream) vs durable geo DB (slower).
- Strong consistency for trip state only; eventual for locations.

## 9. What to say out loud
"Two very different workloads: a huge write stream of locations that only needs the latest value, and a small low-volume but strongly consistent trip state machine. I will keep locations in a sharded in-memory geo index (H3 cells) fed via Kafka, and make assignment atomic with a CAS on driver and trip state so no one is double-booked. Dispatch is partitioned by geography so cities fail independently."

## 10. Follow-ups
- How do you find drivers near a rider at a cell boundary? (k-ring neighbors)
- Handle driver GPS drift/spoofing? (map matching, speed sanity checks)
- Shared rides/pooling? (route insertion heuristics, more complex matching)
- Cancel race: rider cancels as driver accepts? (state machine, single serialization point on trip row)
- How do you test dispatch changes safely? (shadow traffic, simulation, canary by city)
