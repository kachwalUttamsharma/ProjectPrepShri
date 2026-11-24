# Mock Interview Prompts and Grading Rubric

Use after finishing the eight designs. Practice out loud with a timer, whiteboard or paper, ideally with a partner. Method: [framework.md](framework.md).

## Time boxes (45 min)
| Phase | Minutes | Output |
|---|---|---|
| Clarify + scope | 5 | Written functional + non-functional list, explicit out-of-scope |
| Estimate | 4 | QPS, storage, bandwidth, one conclusion drawn from them |
| API + data model | 6 | Endpoints, tables/keys, access patterns |
| High-level diagram | 8 | Boxes and flows for the main write and read paths |
| Deep dives (2 areas) | 15 | Chosen with interviewer; tradeoffs, failure modes |
| Wrap-up | 5 | Bottlenecks, monitoring, evolution, what you would do with more time |
For a 60 min slot add time to deep dives. For FDE loops, add 5 min to discuss customer constraints.

## Prompts (pick one, set timer)
1. Design a pastebin / text sharing service with expiry and abuse handling. (focus: storage, TTL, CDN)
2. Design Google Drive / Dropbox file sync. (chunking, dedupe, delta sync, conflict resolution)
3. Design a web crawler. (frontier, politeness, dedupe with Bloom filter, DNS, priorities)
4. Design a typeahead/autocomplete service. (trie, top-k aggregation, offline vs online, caching)
5. Design YouTube/Netflix video streaming. (upload pipeline, transcoding, CDN, adaptive bitrate)
6. Design a payments/ledger service. (idempotency, double-entry, consistency, reconciliation, sagas)
7. Design a distributed job scheduler/cron. (exactly-once-ish, leases, sharding, retries, time zones)
8. Design a metrics/monitoring system (Prometheus/Datadog-like). (time-series storage, ingestion, downsampling, alerting)
9. Design a real-time leaderboard / top-K for a game. (sorted sets, sharding, approximate counts)
10. Design Google Docs real-time collaboration. (OT vs CRDT, websockets, presence, persistence)
11. Design a feature-flag / config service used by 1000 services. (push vs poll, consistency, blast radius)
12. Design a ticket booking system (Ticketmaster). (inventory contention, holds with TTL, queue for flash sales)
13. FDE: An airline wants an LLM assistant over 50k policy PDFs and live booking APIs, with no data leaving their VPC. (RAG + tools, ACLs, evals, deployment, rollout plan)
14. FDE: A customer's nightly ETL of 2 TB now takes 14 hours and misses its SLA. You have two days on site. How do you approach it? (diagnose first: measure, bottleneck, quick wins, then redesign)
15. Failure drill: your Kafka consumer lag grows continuously after a deploy. Walk through diagnosis and mitigation.
16. Scaling drill: your single Postgres at 70% CPU, traffic doubling in 3 months. Plan the evolution.

## Grading rubric (score each 0-4; 0 absent, 2 adequate, 4 strong)
| Dimension | What 4 looks like |
|---|---|
| Requirements | Asks sharp questions, states assumptions, prioritizes, sets scope, identifies the hardest requirement |
| Estimation | Correct arithmetic, state units, uses numbers to drive decisions (e.g., "writes dominate so...") |
| API and data model | Clear contracts, idempotency/pagination considered, schema matches access patterns, keys chosen to avoid hot spots |
| Architecture | Coherent diagram, clear read/write paths, right components, no unnecessary parts |
| Depth | Goes deep on 2 areas with mechanisms (not buzzwords): how it works, how it fails |
| Tradeoffs | Names alternatives and why rejected; connects to requirements; knows CAP/consistency implications |
| Reliability and scale | Failure modes, retries/timeouts, backpressure, multi-AZ/region, capacity growth, hot keys |
| Operability and security | Metrics/alerts/tracing, rollout/rollback, authn/authz, privacy, cost |
| Communication | Structured, narrates thinking, checks in, takes hints, handles pushback calmly, manages time |
| (FDE only) Customer sense | Frames business outcome, constraints, phased delivery, risks, how to explain to non-experts |

Scoring: 28-36 (of 36, excluding FDE row) = strong hire signal; 20-27 = borderline, repeat prompt in a week; <20 = revisit the lessons for the weak dimensions.

## Self-scoring sheet (copy per attempt)
```
Prompt: ______________   Date: ______   Time used: ___ / 45
Requirements __  Estimation __  API/Data __  Architecture __  Depth __
Tradeoffs __  Reliability/Scale __  Ops/Security __  Communication __   Total __/36
Went well: 
Missed / wrong facts:
Time overruns (which phase):
Concepts to review (link lesson):
Redo date:
```

## Red flags interviewers note
- Jumping to boxes before requirements; no numbers; "just use Kafka/Redis" without why.
- One giant diagram with no flows; ignoring failure; claiming exactly-once or "no downtime" casually.
- Not driving: waiting for the interviewer to ask every question.
- Over-engineering (microservices and multi-region for 100 QPS).
- Contradicting earlier choices (said strong consistency, then async replicas).
- Defensive about feedback.

## Practice schedule suggestion
- Week 6, session 1-2: re-do two designs from memory (blank page, timer), then compare against the file.
- Session 3: mock with a prompt from above you have not seen; score honestly.
- Repeat with a different prompt each week alongside DSA until interviews; record yourself once and review pacing.
