# Design 3: News Feed / Twitter Timeline

Framework: [framework.md](framework.md). Background: [sharding and replication](../week-02-data-storage/lesson.md), [queues and Kafka](../week-03-coordination-messaging/lesson.md), [caching](../week-01-fundamentals/lesson.md).

## 1. Clarify requirements

Functional
- Post a tweet/post (text, optional media).
- Follow/unfollow users.
- Home timeline: reverse-chronological (or ranked) feed of posts from people I follow, paginated.
- User timeline: a user's own posts.
- Out of scope: search, trends, DMs, ads, detailed ranking ML (mention a ranking stage).

Non-functional
- Feed reads are far more frequent than writes. Read latency p99 < 200 ms.
- Highly available; eventual consistency is fine (a post may appear in followers' feeds seconds later).
- Handle celebrity accounts with tens of millions of followers.
- Durability for posts.

## 2. Estimate

- 300M DAU, each opens feed ~10 times/day: 3B feed reads/day = ~35K reads/s avg, ~100K+/s peak.
- 100M posts/day = ~1,200 posts/s avg, peak ~3-5K/s.
- Average follower count ~200 (heavily skewed; celebs at 50M+).
- Fan-out on write cost: 1,200 posts/s x 200 followers = 240K feed inserts/s average. Celebs make this spiky: one post from a 50M-follower account = 50M inserts.
- Post storage: 100M/day x 300 B (text+metadata) = 30 GB/day = ~11 TB/year; media goes to object store + CDN (assume 20% of posts x 1 MB = 20 TB/day, blob storage and CDN dominate cost).
- Feed cache: store the latest ~800 post IDs per active user. 300M x 800 x 8 B = ~1.9 TB in Redis (across a cluster), because only IDs are stored. Reasonable.

## 3. API

```
POST /v1/posts                { "text": "...", "media_ids": [...] }       -> 201 {post_id}
GET  /v1/feed?cursor=<opaque>&limit=20     -> { posts: [...], next_cursor }
GET  /v1/users/{id}/posts?cursor=...
POST /v1/users/{id}/follow    DELETE /v1/users/{id}/follow
```
Pagination: cursor-based (last seen post ID/time-sortable ID), not offset. Offsets break when new posts arrive and are slow at depth.

## 4. Data model

```
users(user_id PK, name, ...)
posts(post_id PK [time-sortable, Snowflake-style], author_id, text, media_urls, created_at)
   -- partition by post_id (or author_id for user timeline), store in Cassandra/DynamoDB/sharded MySQL
follows(follower_id, followee_id)   -- two tables/indexes: followers_of(followee) and following_of(follower)
   -- graph store or KV; sharded by user
feed_cache: Redis list/sorted set per user: user_id -> [post_id ...] (newest first, capped ~800)
user_timeline: (author_id, post_id desc) -- clustering by time
```

Snowflake-style IDs (timestamp + machine + sequence, 64-bit) give roughly time-ordered unique IDs without coordination, so sorting by ID is sorting by time.

## 5. High-level diagram

```
 WRITE PATH
 Client -> LB -> [Post service] -> [Posts DB]
                      |
                      +--> [Kafka: new_post] --> [Fan-out workers]
                                                    |  get followers (from graph/follow store)
                                                    v
                                            [Feed cache (Redis)]  LPUSH post_id into each follower's list
                                                    (skip celebrities)
 READ PATH
 Client -> LB -> [Feed service]
                   1. read my feed list (post_ids) from Redis
                   2. merge in recent posts from celebrities I follow (pull at read time)
                   3. hydrate: batch-get posts, authors, counts (post cache / DB)
                   4. (optional) rank, filter blocked/muted
                   -> response
 Media: Client -> upload to [Blob store S3] -> CDN
```

## 6. Deep dives

### a) Fan-out on write (push) vs fan-out on read (pull) vs hybrid

| | Push (write) | Pull (read) |
|---|---|---|
| On post | Insert post ID into every follower's feed | Just store the post |
| On read | Read precomputed list: very fast | Fetch recent posts from all followees, merge, sort |
| Pros | Fast reads, which dominate | Cheap writes, no wasted work for inactive users |
| Cons | Huge write amplification for celebs; wasted work for inactive users | Slow reads, N queries per feed load |

Hybrid (what Twitter did, per their public talks): push for normal users; for celebrities (follower count above a threshold, e.g. 100K-1M), do not fan out. At read time, merge the user's precomputed feed with posts pulled from the followed celebrities' timelines (small set per user). Also fan out only to active users (logged in within N days); rebuild an inactive user's feed on demand from pull.

### b) Fan-out service mechanics
- Post service writes the post durably, then publishes an event to Kafka (or via the outbox pattern so the DB write and event are atomic, see [outbox](../week-03-coordination-messaging/lesson.md)).
- Workers consume partitioned by author or post ID, look up followers in pages, and batch-write into Redis. Idempotent: pushing the same post_id twice into a sorted set (score = post_id) is naturally deduped.
- Lag is acceptable (seconds); monitor consumer lag as an SLI.

### c) Feed storage
- Redis sorted set or list per user holding IDs only (small), capped; older items fall back to a DB query (cold path: fan-in from follows + posts DB).
- Hydration needs a multi-get of post bodies: a second cache of hot posts (celebrity posts get cached heavily, with high hit rate).

### d) Ranking
- Reverse-chronological is simplest. Ranked feeds: a candidate-generation stage (the merged IDs), then a lightweight ML scorer using features (affinity, recency, engagement), then filtering/diversity. Keep it a separate service with a latency budget (~50 ms) and a fallback to chronological.

### e) Counters (likes, retweets, views)
- Hot counters need sharded counters or approximate counting; write via a stream and aggregate asynchronously. Display counts are eventually consistent.

### f) Deletes and privacy
- Deleting a post: tombstone in the DB; the feed hydration step filters missing/deleted posts, so we need not remove IDs from millions of feeds. Block/mute likewise are filtered at read time.

### g) Follow graph storage
- followers_of can be huge (50M). Store as paged, sharded rows (user_id, bucket). Reading followers for fan-out is a scan; do it in batches via workers.

## 7. Bottlenecks and failure modes

- Celebrity post burst: write amplification spike; hybrid approach avoids it. Also thundering reads on that post: CDN/cache with request coalescing.
- Redis memory pressure: cap list length, TTL on inactive users, only store IDs.
- Fan-out lag after worker outage: Kafka retains events; replay catches up. Users see stale feeds but never wrong ones.
- Hot partition on author_id in posts DB for celebs: cache; replicate hot rows.
- New user cold start: feed empty. Build on first request via pull, then cache.
- Cache loss: rebuild lazily using pull. Make sure the DB can survive the rebuild stampede (rate limit and coalesce).

## 8. Tradeoffs

- Push vs pull vs hybrid (write cost vs read latency vs complexity).
- Storing IDs vs full posts in feed (memory vs hydration cost and freshness of edits/deletes).
- Strict ordering vs eventual: feed order may differ slightly per replica; users tolerate it.
- Cassandra/DynamoDB (write-heavy, wide rows) vs relational (rich queries, but sharding burden).
- Ranking quality vs latency.

## 9. What to say out loud

- "The read:write ratio is about 30:1 in requests, but fan-out multiplies write cost, so the fan-out strategy is the core decision."
- "I will push to followers for normal accounts and pull for celebrities, merging at read time; that bounds write amplification."
- "The feed stores only post IDs, hydrated at read, so deletes and edits are consistent without rewriting millions of lists."
- "Cursor pagination on a time-sortable ID so new posts do not shift pages."

## 10. Follow-up questions to practice

1. How do you choose the celebrity threshold? (follower count, fan-out cost, make it dynamic)
2. What if a user follows 5,000 celebrities? (cap pull set, or sample/rank)
3. How do you guarantee a user sees their own post immediately? (read-your-writes: insert into own feed synchronously, or merge own recent posts at read time)
4. How would you add "For You" recommendations? (candidate generation + ranking service)
5. How do you handle edits and deletes? (hydration-time filtering, tombstones)
6. How do you shard the follow graph?
