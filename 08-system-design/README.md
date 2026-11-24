# System Design Study Track (interview-focused, ~6 weeks at ~3 hrs/week, alongside DSA)

Goal: Google/Uber-level system design interviews and forward-deployed-engineer (FDE) conversations. All material is reading + spoken Q&A; there are no tests. Numbers that change over time are marked "check current docs" - verify before quoting.

Pairs with `../07-aws/` (the AWS services that implement these ideas). Cross-links are in each lesson.

## Study order
| Week | Folder | Topics |
|---|---|---|
| 1 | week-01-fundamentals | Latency/throughput, back-of-envelope math, scaling, availability, SLA/SLO/SLI, load balancing, stateless services, caching |
| 2 | week-02-data-storage | Replication, sharding, consistent hashing, SQL vs NoSQL, indexes, CAP/PACELC, consistency models, quorums |
| 3 | week-03-coordination-messaging | Queues/logs, Kafka, delivery semantics, idempotency, outbox, pub/sub, backpressure, rate limiting, retries, circuit breakers, timeouts |
| 4 | week-04-distributed-algorithms | Raft/Paxos, leader election, locks and fencing, clocks, gossip, failure detection, 2PC vs sagas, CRDTs, bloom filters, HyperLogLog |
| 5 | week-05-architecture-operations | Microservices vs monolith, API design, discovery, gateway, observability, deploys, multi-region/DR, security, LLM/RAG service design |
| 6 | week-06-hld-designs | framework.md, 8 full design walkthroughs, mock-interview.md |

## Weekly routine (~3 hrs)
1. Read lesson.md (~1.5 hrs); redraw the main diagrams by hand once.
2. Answer interview-qa.md out loud, covering the model answer first (~1 hr).
3. Skim cheatsheet.md; flashcard the numbers (~30 min).

Week 6 plan: read framework.md first, then do about 2 designs per session. For each, cover the page, talk through it for 35-40 minutes against a timer, then compare. Finish with mock-interview.md prompts (record yourself).

## Files per week
- lesson.md: first-principles explanation, diagrams, tradeoffs, real systems, failure modes, "how interviewers probe this"
- interview-qa.md: 15-20 concept questions with concise model answers
- cheatsheet.md: one-page recall sheet
- week-06-hld-designs/: framework.md, 01..08 design files, mock-interview.md

## Recommended reading
- Martin Kleppmann, *Designing Data-Intensive Applications* (DDIA): the best single book. Priority chapters: 5 (replication), 6 (partitioning), 7 (transactions), 8 (trouble with distributed systems), 9 (consistency and consensus), 11 (streams). Read alongside weeks 2-4.
- Alex Xu, *System Design Interview* vols 1 and 2: good for the design walkthrough format (week 6).
- Educative "Grokking the System Design Interview" and ByteByteGo newsletter: optional, for more examples.
- Google SRE book and SRE workbook (free online): SLIs/SLOs, monitoring, handling overload, cascading failures.
- Papers (read abstracts and diagrams first): Dynamo, Bigtable, Spanner, Kafka, Raft ("In Search of an Understandable Consensus Algorithm"), Google MapReduce, Google Chubby, Facebook TAO/Memcache. Check current links.
- Engineering blogs: Uber (H3, Cadence/Temporal, Schemaless), Discord (message storage), Netflix, Stripe (idempotency, rate limiting), Cloudflare.
- Jepsen.io analyses: for how real databases fail.
- For the FDE angle: Anthropic and OpenAI docs on RAG, evals and tool use (check current docs).

## Tips
- Always work through: requirements, estimates, API, data model, high-level design, deep dives, bottlenecks, tradeoffs. Say the tradeoff out loud; there is rarely one right answer.
- Do not pick a technology without saying why and what you give up.
- Bring up failure modes, observability and cost without being asked.
- Keep DSA going in parallel; do not let system design crowd it out.
