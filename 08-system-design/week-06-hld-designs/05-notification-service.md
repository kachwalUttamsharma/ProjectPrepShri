# HLD 5 - Notification Service (push, SMS, email, in-app)

Framework: see [framework.md](framework.md). Background: [queues, idempotency, retries, rate limiting](../week-03-coordination-messaging/lesson.md).

## 1. Clarify requirements
Functional
- Channels: mobile push (APNs/FCM), SMS, email, in-app. Triggered by services (transactional) and by campaigns (bulk).
- User preferences (opt-out per channel/category), quiet hours, templates + localization.
- Scheduling, priority (OTP > order update > marketing), dedupe.
Non-functional
- Transactional: p99 < a few seconds end to end. Marketing: throughput over latency.
- At-least-once delivery with dedupe (exactly-once to a phone is impossible); never lose a transactional message.
- Third-party providers are slow/flaky/rate-limited: isolate and degrade gracefully.
Out of scope (say it): content creation UI, analytics warehouse.

## 2. Estimate (worked)
- 50M DAU, avg 5 notifications/user/day = 250M/day -> 250M / 86,400 ~ 2,900/s avg; peak 5x ~ 15k/s.
- Campaign: 20M users blast in 10 min = 33k/s burst. Needs its own lane.
- Storage: 250M/day x 500 B log record = 125 GB/day; keep 30 days hot = ~3.75 TB; archive older to object storage.
- Provider limits dominate: FCM/APNs allow high concurrency, SMS is per-country and costly (check current provider docs/pricing).

## 3. API
```
POST /v1/notifications            (internal services)
 { idempotency_key, user_id, category: "order_update", priority: "high",
   template_id, params: {...}, channels_hint?: ["push","sms"], send_at? }
 -> 202 { notification_id }
GET  /v1/notifications/{id}       status: queued|sent|delivered|failed|suppressed
PUT  /v1/users/{id}/preferences   { category -> {push:true, sms:false}, quiet_hours }
POST /v1/devices                  register push token
POST /v1/webhooks/provider/{name} delivery receipts / bounces
```
Return 202 after durable enqueue, not after provider send.

## 4. Data model
- `notification(id PK, idempotency_key UNIQUE, user_id, category, priority, status, created_at)` - wide-column/DynamoDB keyed by user_id or id.
- `user_prefs(user_id, category, channel, enabled)`; `devices(user_id, token, platform, last_seen)` (prune on provider "unregistered" errors).
- `templates(id, version, locale, body)` cached in memory.
- Delivery log (append-only, by id) for audit/receipts.

## 5. High-level diagram
```
 Producers --> [Notification API] --validate/idempotency--> [Kafka: ingest]
                                                              |
                                              [Orchestrator workers]
                                 prefs lookup, dedupe, template render, channel pick,
                                 rate-limit per user, quiet hours -> schedule if needed
                                                              |
        +-------------+---------------+------------------+----+---------+
        v             v               v                  v
  [q: push-high] [q: sms-high]   [q: email-high]   [q: *-bulk lanes]
        |             |               |                  |
  push workers   sms workers     email workers     bulk workers (throttled)
        |             |               |
   APNs / FCM   SMS vendor A/B   SES/SendGrid
        ^             ^               ^
        +--- provider webhooks (receipts, bounces) -> status store, suppress list
 Failure: retry w/ backoff+jitter -> retry topic(s) -> DLQ -> alert/replay tool
```

## 6. Deep dives
**Priority isolation.** Separate topics/consumer groups per priority and channel so a marketing blast cannot starve OTPs. Bulk lane is rate-shaped (token bucket per provider).
**Idempotency/dedupe.** Producer supplies idempotency_key; API does conditional insert (unique key) so retries do not double-send. Worker also writes "sent" marker keyed (notification_id, channel) *before* calling provider with provider-side dedupe token where supported. Crash between provider call and marker = possible duplicate; accept at-least-once ([idempotency](../week-03-coordination-messaging/lesson.md)).
**Outbox.** Producers that change DB state and emit a notification use the outbox pattern so event and state commit atomically.
**Retries.** Exponential backoff + jitter, bounded attempts, per-provider circuit breaker; on open circuit fail over to secondary vendor (SMS) or channel fallback (push -> SMS for critical only). Distinguish permanent (invalid token, unsubscribed) from transient errors.
**Preferences and compliance.** Check prefs at send time, not enqueue time (user may opt out in between). Legal: unsubscribe, consent, regional rules (check current regulations).
**Scheduling.** Delayed sends: store in a time-bucketed table or delay queue (e.g. SQS delay up to 15 min, otherwise scheduler scanning `send_at` index); quiet hours rewrite send_at to user's local morning.
**Fan-out for campaigns.** Campaign service pages through segment (cursor), emits batches to bulk topic; workers render per-user. Avoid loading 20M IDs in memory.
**Ordering.** Rarely needed; if so, partition by user_id.

## 7. Bottlenecks and failure modes
- Provider outage/throttle (429): backpressure -> queue depth grows; bulk lane pauses, transactional switches vendor.
- Hot partition: one celebrity-style segment - partition by notification_id, not user, unless ordering required.
- Poison message: bad template crashes workers - cap retries, DLQ.
- Thundering retries after outage: jitter, token-bucket drain rate.
- Stale device tokens waste quota: prune on feedback.
- Duplicate sends from at-least-once; mitigate, do not promise zero.

## 8. Tradeoffs
- Queue per channel/priority (isolation, more ops) vs one topic (simple, head-of-line blocking).
- Check prefs early (cheap, stale) vs late (accurate, extra read) - do late with cache.
- Sync send in API (simple, couples latency to vendors) vs async (needs status tracking). Choose async.
- Multi-vendor SMS: cost/resilience vs complexity.

## 9. What to say out loud
"I will return 202 once the request is durably in Kafka, then process asynchronously. I am separating lanes by priority so marketing cannot delay OTPs. Delivery is at-least-once with idempotency keys; exactly-once to a device is not achievable, so I minimize duplicates. Providers are the weakest link, so I add circuit breakers, retries with jitter, and a DLQ. Let me know if you want to go deeper on scheduling or campaigns."

## 10. Follow-ups
- How do you guarantee an OTP arrives in 5 s if APNs is slow? (parallel channel fallback, short TTL on push)
- How do you support 1 B users with per-user rate caps? (Redis counters sharded by user; see [rate limiter](02-rate-limiter.md))
- How do you track open/click? (redirect/pixel -> event stream; privacy caveats)
- How would you replay failed notifications after an incident? (DLQ + tooling, idempotency makes safe)
