# 11 - Low-Level Design (LLD) interview practice

Eight classic LLD problems, each with a `lesson.md` (how to talk it through), `exercises.py` (stubs to fill in) and `test_exercises.py` (deterministic tests, injected clocks, no sleeps).

| # | Problem | Core ideas |
|---|---|---|
| 01 | LRU cache | dict + doubly-linked list, O(1), sentinels |
| 02 | Rate limiter | Strategy, token bucket, sliding window, injectable clock, locks |
| 03 | Elevator system | state machine, scheduling strategy |
| 04 | Vending machine | State pattern, change-making |
| 05 | Seat booking | concurrency, holds with TTL, double-booking prevention |
| 06 | Game engine | extensible rules, Strategy, Command |
| 07 | Pub-sub / notifications | Observer, retry, dead-letter, channel strategy |
| 08 | Expense sharing | split strategies, balances, debt simplification |

Run one: `.venv/bin/pytest 11-lld/problem-01-lru-cache -v` (from the repo root). Tests start red; your job is to make them green, then rehearse the lesson out loud.

## The 45-minute framework

| Step | Minutes | What you do |
|---|---|---|
| 1. Clarify requirements | 5 | Ask questions, state assumptions, fix scope (in / out) |
| 2. Entities and relationships | 5 | Nouns to classes, verbs to methods; has-a vs is-a |
| 3. Public API | 5 | Write method signatures first; agree them with the interviewer |
| 4. Class diagram | 5 | Boxes and arrows; mark the patterns |
| 5. Code the core | 15 | Happy path first, then edge cases; keep methods short |
| 6. Walk through / test | 5 | Trace one example by hand; mention edge cases |
| 7. Extensions and concurrency | 5 | Follow-ups: what changes, what does not |

Rules of thumb:
- Never start coding before the API is agreed.
- Say trade-offs out loud ("I chose X over Y because...").
- Keep time/clock/randomness injected; it shows you think about testability.
- Prefer a small correct core to a sprawling design.
- Name what you are NOT building.

## Requirement-clarification checklist
- Who are the actors? Scale (single process vs distributed)?
- Core operations and their complexity expectations?
- Error behavior: raise, return False, return None?
- Concurrency: single thread or multi-thread? Ordering guarantees?
- Persistence, time, money (use ints), ids?
- Extensions likely to be asked (so you leave seams, not code).

## SOLID checklist
- **S** - each class has one reason to change (e.g. the cache does not know how time works).
- **O** - new behavior = new class (new strategy, new state, new rule), not edits to `if/elif` chains.
- **L** - subclasses honor the base contract (every `Limiter` obeys `allow`).
- **I** - small interfaces (a `Subscriber` only needs `on_message`).
- **D** - depend on abstractions, inject collaborators (clock, strategy, notifier).

## Pattern cheat sheet

| Pattern | Use when | Seen in |
|---|---|---|
| Strategy | interchangeable algorithms | rate limiter algorithms, elevator scheduling, split types, pricing |
| State | behavior depends on a mode, many transitions | vending machine, elevator |
| Observer / Pub-Sub | one event, many listeners | notifications |
| Command | operations as objects (undo, queue, log) | game moves |
| Factory | construct the right subclass from config | limiter / channel creation |
| Template Method | fixed skeleton, varying steps | split validation then compute |
| Singleton | exactly one shared instance (use sparingly, hurts tests) | usually say "inject instead" |
| Decorator | add behavior by wrapping | retrying subscriber, logging notifier |
| Builder | many optional constructor params | complex configuration |
| Facade | simple front for a subsystem | `ElevatorController`, `BookingService` |

## Concurrency cheat sheet (Python)
- A `threading.Lock` around check-then-act sequences; keep the critical section small.
- Lock per resource (per show, per key) beats one global lock; always acquire in a fixed order to avoid deadlock.
- `dict` operations are atomic individually, but check-then-set is not.
- Compute expiry lazily with an injected clock instead of timer threads.
- Mention for distributed versions: DB row locks / optimistic version column, Redis `SET NX`, idempotency keys.

## Common mistakes across all problems
- Coding before clarifying; silent assumptions.
- God class holding all logic; no seams for the follow-up.
- Reading `time.time()` directly (untestable).
- Floats for money.
- Check-then-act without a lock.
- Ignoring error cases and invalid input.
- Pattern name-dropping without a reason.

## Self-review before you say "done"
- [ ] Requirements and assumptions stated
- [ ] Public API written before the bodies
- [ ] Each class has a single responsibility
- [ ] New variants add classes rather than edit old ones
- [ ] Time and randomness injected
- [ ] Errors are a small, named hierarchy
- [ ] I can state complexity of each operation
- [ ] I traced an example by hand and one edge case
- [ ] I can answer the concurrency question
