# Design 4: Chat System (WhatsApp / Messenger)

Framework: [framework.md](framework.md). Background: [replication and consistency](../week-02-data-storage/lesson.md), [messaging, delivery semantics, idempotency](../week-03-coordination-messaging/lesson.md), [clocks and ordering](../week-04-distributed-algorithms/lesson.md), [service discovery and gateways](../week-05-architecture-operations/lesson.md).

## 1. Clarify requirements

Functional
- 1:1 chat and group chat (up to ~500 members; say so).
- Send/receive text in real time; media via attachments.
- Delivery states: sent, delivered, read (receipts).
- Online/offline presence, last seen.
- Offline delivery: messages queued and delivered when the recipient reconnects; push notifications.
- Multi-device sync (mention; keep simple at first).
- Out of scope: voice/video calls, end-to-end encryption internals (mention Signal protocol), search.

Non-functional
- Low latency delivery (< 200 ms same region when both online).
- Messages must never be lost (durability) and must not be duplicated visibly; per-conversation ordering.
- High availability; consistency: per-chat ordering, eventual elsewhere.
- Scale: hundreds of millions of concurrent connections.

## 2. Estimate

- 500M DAU, 40 messages sent per user per day = 20B messages/day = ~230K msgs/s avg, peak ~500K-700K/s.
- Message size ~100 B text + metadata ~ 200 B stored. 20B x 200 B = 4 TB/day = ~1.5 PB/year before replication (3x = ~4.5 PB). Hence a write-optimized, horizontally scalable store and retention/tiering policy.
- Concurrent connections: assume 200M online at once. One tuned chat server holds ~100K-1M idle WebSocket connections depending on memory and CPU (check current benchmarks; WhatsApp famously reported ~1M+ per server on Erlang). At ~100K per server => 2,000 gateway servers; at 500K => 400.
- Connection memory: ~10-50 KB per connection => 200M x 20 KB = ~4 TB across the fleet.
- Media: say 10% of messages carry 200 KB media: 2B x 200 KB = 400 TB/day to blob store + CDN (dominant cost).

## 3. API

Real-time over a persistent WebSocket (or MQTT / custom protocol over TCP for mobile), plus REST for non-realtime.

```
WS connect  wss://chat.example.com/ws   (auth token)
client -> server:
  { "type":"send", "client_msg_id":"uuid", "chat_id":"c1", "body":"hi", "ts_client":... }
server -> client:
  { "type":"ack", "client_msg_id":"uuid", "msg_id":"snowflake", "status":"sent" }
  { "type":"message", "msg_id":..., "chat_id":..., "sender":..., "body":..., "seq": 1042 }
  { "type":"receipt", "msg_id":..., "status":"delivered|read" }
  { "type":"presence", "user":..., "state":"online" }

REST
GET  /v1/chats/{chat_id}/messages?before=<msg_id>&limit=50    (history sync)
POST /v1/media (get presigned upload URL)  -> client uploads to blob store directly
POST /v1/chats (create group), PUT /v1/chats/{id}/members
```
`client_msg_id` provides idempotency: retries after a flaky network must not create duplicates.

## 4. Data model

Access pattern: append messages to a chat, read recent messages of a chat in order, paginate backwards. This is a time-series per partition: ideal for wide-column stores (Cassandra, ScyllaDB, HBase as WhatsApp/Messenger used variants) or DynamoDB.

```
messages(chat_id PARTITION, msg_id CLUSTERING DESC, sender_id, body, type, created_at, seq)
   -- partition key may include a time bucket (chat_id, month) to bound partition size
chats(chat_id PK, type, name, created_at)
chat_members(chat_id, user_id)  +  user_chats(user_id, chat_id, last_read_seq)  -- both directions
inbox/offline_queue(user_id, msg_id) -- undelivered messages (or derive from last_delivered_seq)
receipts(msg_id, user_id, delivered_at, read_at)   -- or per chat "last_read_seq" cursor (much cheaper)
users, devices(user_id, device_id, push_token)
session_registry (Redis): user_id/device_id -> gateway_server_id   (TTL, heartbeat refreshed)
```

Ordering: use a per-chat monotonically increasing `seq` assigned by the chat's owning shard/partition leader (single writer per chat), or a time-sortable ID. Global ordering is unnecessary and costly; per-conversation ordering is what users perceive. See [Lamport/logical clocks](../week-04-distributed-algorithms/lesson.md).

## 5. High-level diagram

```
 Sender app                                                   Receiver app
   |  WebSocket                                                   ^ WebSocket
   v                                                              |
 [L4 LB] -> [Gateway server A] --(1) send--> [Chat service]  [Gateway server B]
               holds connections              |   ^                  ^
                                              |   |                  | (4) push to connection
                (2) persist                   v   |                  |
                              [Message store (Cassandra/DynamoDB)]   |
                                              |                      |
                (3) lookup recipient's gateway|                      |
                              [Session registry (Redis)] ------------+
                                              |
                      recipient offline? -----+--> [Offline queue] + [Push notif service -> APNs/FCM]
                                              |
                              [Kafka: message events] -> receipts, analytics, search indexing, group fan-out

 Presence: gateways heartbeat -> [Presence service (Redis w/ TTL)] -> pub/sub to interested contacts
 Media: client -> presigned URL -> [S3] -> CDN; message carries only the media URL + key
```

1:1 flow:
1. Sender sends over WebSocket to gateway A; chat service validates and assigns msg_id/seq.
2. Persist to the message store (and ack "sent" to the sender only after a durable write).
3. Look up the recipient's gateway(s) in the session registry.
4. If online: forward to gateway B, which pushes over the socket; the client acks, producing a "delivered" receipt. If offline: write to the offline queue and send a push notification; deliver on reconnect by syncing from last seq.

## 6. Deep dives

### a) Connections and routing
- WebSocket gateways are stateful (they hold the connections) but contain no business state. Use an L4 load balancer (long-lived TCP; sticky not required). Clients reconnect with exponential backoff and jitter after a gateway dies; avoid reconnect storms (a rolling deploy with 100K connections per server must drain slowly).
- Session registry maps user -> gateway. Alternative: chat service publishes to a pub/sub channel per user/gateway (Redis pub/sub, Kafka partitioned by gateway ID) so any service can reach any user without the registry.
- Heartbeats (ping every ~30 s) detect dead connections; the registry entry has a TTL.

### b) Delivery guarantees
- At-least-once delivery with client-side dedupe by `msg_id`. The sender retries until it gets the ack; the server dedupes on `client_msg_id`. Together this gives effectively-once visibility. See [delivery semantics and idempotency](../week-03-coordination-messaging/lesson.md).
- Receiver acks each message (or batched by seq). Unacked messages are redelivered on reconnect. Client requests "messages after seq N" to sync; this also covers multi-device.
- Order within a chat: the client sorts by seq; gaps trigger a fetch.

### c) Group chat
- Small groups (<= ~500): fan-out on write to each member's inbox/delivery stream (like the feed push model). Store the message once in `messages(chat_id)`; per-member state is only a cursor (last_delivered/read seq), not a copy. Large groups/channels: pull model (clients fetch from the chat partition), with push only notifications.
- Membership changes need consistency: a removed member must stop receiving. Version the membership list; the fan-out reads the current version.
- Read receipts in groups: aggregate counts, or only track per-user last_read_seq.

### d) Presence
- Heartbeat sets `online:{user}` in Redis with a ~60 s TTL. Do not broadcast every change to everyone: fan out presence only to a user's active contacts that currently have the chat open, or let clients poll on demand. Last seen is eventually consistent. Presence is the classic place to relax consistency to save cost.

### e) Storage scaling
- Cassandra/Scylla partitioned by chat_id (with time bucket for hot, long chats). Writes are append-only: LSM trees fit. Replication factor 3, LOCAL_QUORUM writes.
- Hot/cold tiering: recent messages in the primary store, old ones archived to cheaper storage. Some systems (WhatsApp) delete from servers after delivery, treating the device as the source of truth; Slack/Messenger keep history server-side. State which model you assume.

### f) Push notifications
- If the user is offline, send via APNs/FCM with minimal content (privacy). Throttle and collapse multiple messages. This integrates with a notification service ([see design 5](05-notification-service.md)).

### g) Security
- TLS everywhere; end-to-end encryption (Signal protocol) means the server stores ciphertext only and cannot index or moderate content; key distribution via a prekey server. Authenticate the WebSocket upgrade with a short-lived token; rate limit senders ([rate limiter](02-rate-limiter.md)).

### h) Multi-device and multi-region
- Each device has its own connection and cursor; the server tracks `last_seq` per device. Messages fan out to all of a user's devices.
- Multi-region: route users to the nearest region; cross-region messages go via the inter-region message bus. Home-region per chat simplifies ordering (single writer); accept cross-region latency for cross-region chats.

## 7. Bottlenecks and failure modes

- Gateway crash: connections drop; clients reconnect to other gateways and sync from last seq. No message loss since messages are persisted before ack.
- Reconnect storms after a regional blip: jittered backoff, connection admission control, and capacity headroom.
- Hot chat partition (a giant group): bucket partitions by time, cap group size, push-pull hybrid.
- Session registry staleness: message sent to the wrong gateway; fall back to offline queue + sync. Design delivery to tolerate this (idempotent, sync-on-reconnect).
- Kafka/consumer lag delays receipts and push notifications; correctness is unaffected since persistence is the source of truth.
- Message ordering across devices/clock skew: use server-assigned seq, not client clocks.
- Poison/oversized messages: validate size, rate limit.

## 8. Tradeoffs

- WebSocket vs long polling vs MQTT: lower latency and battery (MQTT) vs infra simplicity (HTTP).
- Server-side history vs device-only storage: features (multi-device, search) vs privacy and storage cost.
- Per-chat total ordering (single writer, simple, hot spot risk) vs distributed ordering (complex).
- Strong delivery guarantees (ack per message) vs bandwidth/battery (batched acks).
- Fan-out on write for groups (low read latency) vs pull for huge groups (bounded write cost).
- E2EE vs server features.

## 9. What to say out loud

- "The core problem is moving a message from a stateful connection on one server to a stateful connection on another, durably and in order within a chat."
- "I persist before acking the sender, so a gateway crash cannot lose an acknowledged message. Delivery is at-least-once with dedupe by message ID."
- "I only guarantee order within a conversation, using a per-chat sequence number, because global order is unnecessary and expensive."
- "Presence is where I would deliberately accept eventual consistency, with TTL heartbeats and targeted fan-out."

## 10. Follow-up questions to practice

1. How do you guarantee no duplicate messages when the client retries? (client_msg_id idempotency)
2. How does a user on a new phone get history? (sync by seq from the server, or E2EE backup)
3. How do you scale to 1M connections per server? (async IO, tuned kernel/file descriptors, small per-connection state)
4. How do you deploy gateways without dropping everyone? (connection draining, jittered reconnect)
5. How do you implement read receipts in a 500-person group cheaply?
6. How would you support message search with E2EE? (client-side index)
7. What is your sharding key and what breaks with a giant group chat?
