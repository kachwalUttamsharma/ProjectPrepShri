# Progress

## How to work
1. Open the week's `lesson.md`, read it, and type the examples into the REPL.
2. Fill in `exercises.py` (replace each `...`).
3. Run that week's tests from this folder (one week at a time):
   `.venv/bin/pytest 01-basics/week-01-first-steps -v`
4. Show me your code for review before moving on.

Pace: ~7-8 hrs/week. Basics ~8 weeks, OOP ~5 weeks, DSA ~24 weeks.

## Stage 1: Basics (`01-basics/`)
- [ ] 1 first-steps
- [ ] 2 conditions-loops
- [ ] 3 functions
- [ ] 4 lists-tuples
- [ ] 5 dicts-sets
- [ ] 6 files-errors-modules
- [ ] 7 comprehensions-generators
- [ ] 8 projects-review

## Stage 2: OOP (`02-oop/`)
- [ ] 1 classes-objects
- [ ] 2 encapsulation-dunders
- [ ] 3 inheritance-polymorphism
- [ ] 4 design-patterns
- [ ] 5 project-parking-lot

## Stage 3: DSA (`03-dsa/`)
- [ ] 1 big-o-complexity
- [ ] 2 arrays-strings
- [ ] 3 hash-maps-sets
- [ ] 4 two-pointers
- [ ] 5 sliding-window
- [ ] 6 prefix-sums-intervals
- [ ] 7 stacks
- [ ] 8 queues-deque-monotonic-queue
- [ ] 9 linked-lists
- [ ] 10 binary-search
- [ ] 11 recursion
- [ ] 12 sorting-checkpoint
- [ ] 13 binary-trees
- [ ] 14 bsts
- [ ] 15 heaps
- [ ] 16 tries
- [ ] 17 graphs-basics
- [ ] 18 topo-sort-union-find
- [ ] 19 shortest-paths
- [ ] 20 backtracking
- [ ] 21 dp-1d
- [ ] 22 dp-2d
- [ ] 23 greedy-bits
- [ ] 24 capstone (mock interviews)

## Stage 2.5: FastAPI (`04-fastapi/`, 4 weeks, after OOP, before DSA)
- [ ] 1 first-endpoints
- [ ] 2 pydantic-validation
- [ ] 3 database-and-integrations (heaviest, ~8 hrs)
- [ ] 4 auth-deploy-project

## FDE projects (`05-fde-projects/`, ~2 hrs/week alongside DSA)
- [ ] 1 llm-basics
- [ ] 2 ticket-triage
- [ ] 3 document-qa-rag
- [ ] 4 tool-calling-agent
- [ ] 5 evaluation
- [ ] 6 capstone-messy-data-demo

## SQL (`06-sql/`, 5 weeks; do weeks 1-3 around Basics week 8 / before FastAPI week 3)
- [ ] 1 select-filter-aggregate
- [ ] 2 joins-subqueries
- [ ] 3 cte-window-case-dates
- [ ] 4 schema-indexes-transactions
- [ ] 5 interview-problem-set (+ cheatsheet.md inside)

### General SQL (`06-sql/general-sql/`, 6 parts, plain `.sql`, run with the `sqlite3` CLI; see its README.md)
- [ ] 1 language map, DDL/DML
- [ ] 2 set ops, functions, pagination, JSON
- [ ] 3 views, triggers, procedures, roles
- [ ] 4 how databases work (indexes, planner, EXPLAIN)
- [ ] 5 concurrency and reliability
- [ ] 6 engines, warehouses, modeling
Postgres/MySQL snippets are marked "not run here, verify".

## AWS (`07-aws/`, 6 weeks, study + interview Q&A; see its README.md)
- [ ] 1 core-iam
- [ ] 2 compute
- [ ] 3 storage-databases
- [ ] 4 networking
- [ ] 5 integration-ops-security
- [ ] 6 architecture-fde (+ scenarios, mock-interview, rapid-fire.md)
Written from memory: verify numbers marked "check current docs".

## System design (`08-system-design/`, 6 weeks, study + interview Q&A; see its README.md)
- [ ] 1 fundamentals
- [ ] 2 data-storage
- [ ] 3 coordination-messaging
- [ ] 4 distributed-algorithms
- [ ] 5 architecture-operations
- [ ] 6 hld-designs (8 designs + framework + mock-interview)

## Behavioral and career (`09-behavioral-career/`, 7 files; start with README.md, schedule in 06-master-study-schedule.md)
- [ ] behavioral fundamentals, FDE scenarios, interview process, resume/portfolio, communication

## Python depth (`10-python-depth/`, 4 weeks, with tests)
- [ ] 1 functions-deep-dive
- [ ] 2 data-model-and-memory
- [ ] 3 concurrency (asyncio)
- [ ] 4 quality-and-tooling (+ rapid-fire.md)

## Low-level design (`11-lld/`, 8 problems, with tests; see README.md)
- [ ] 1 lru-cache  - [ ] 2 rate-limiter  - [ ] 3 elevator  - [ ] 4 vending-machine
- [ ] 5 seat-booking  - [ ] 6 game-engine  - [ ] 7 pubsub-notifications  - [ ] 8 expense-sharing

## CS fundamentals (`12-cs-fundamentals/`, 5 weeks, study + Q&A; commands/manifests not run)
- [ ] 1 networking  - [ ] 2 operating-systems  - [ ] 3 linux-shell  - [ ] 4 git-collaboration  - [ ] 5 containers-orchestration

## LLM and AI concepts (`13-llm-ai-concepts/`, 5 weeks, study + Q&A)
- [ ] 1 llm-fundamentals  - [ ] 2 retrieval-rag  - [ ] 3 agents-tool-use  - [ ] 4 evaluation-production  - [ ] 5 classic-ml-essentials

## Data engineering (`14-data-engineering/`, 7 weeks; weeks 2, 3, 4, 6 have tests; see README.md)
- [ ] 1 modeling-warehousing  - [ ] 2 spark  - [ ] 3 orchestration-dbt  - [ ] 4 kafka-streaming
- [ ] 5 lakehouse-formats  - [ ] 6 quality-governance  - [ ] 7 pipeline-design (8 designs) + mock-interview.md, rapid-fire.md
Spark, Airflow, dbt, Kafka and warehouse details are from memory (not run): verify items marked "check current docs".

## Study site
Open `site/index.html` in a browser (double-click; works offline, diagrams need internet).
Rebuild after any content change: `.venv/bin/python tools/build_site.py` (add `--open` to open it).
Your "done" ticks live in the browser (localStorage); use Export/Import on the home page to back them up.
Recommended order follows 09-behavioral-career/06-master-study-schedule.md (DSA starts early alongside others, FastAPI in Phase 2).

Note: a few tests pass on the blank stubs (they check things already provided). That is expected.
