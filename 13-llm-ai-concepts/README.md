# LLM and AI Concepts Study Track (interview-focused, ~5 weeks at 6-8 hrs/week)

Goal: conceptual fluency for forward-deployed-engineer and AI-engineering interviews. This track is reading, Q&A and small runnable Python snippets (no API keys needed). The hands-on build track lives in `../05-fde-projects/`; this folder explains the "why" behind those projects. Model names, prices and limits change quickly: where a number matters, say "check current docs". Prices in worked examples are hypothetical.

## Study order
| Week | Folder | Topics | Pairs with project |
|---|---|---|---|
| 1 | week-01-llm-fundamentals | Tokens, transformers (attention, context, KV cache), training stages, sampling, model tradeoffs, hallucination, prompt patterns, prompt injection | project-01-llm-basics |
| 2 | week-02-retrieval-rag | Embeddings, similarity, ANN (HNSW, IVF), chunking, hybrid search, reranking, query rewriting, citations, RAG debugging, RAG vs fine-tune vs long context | project-03-document-qa-rag |
| 3 | week-03-agents-tool-use | Function calling, agent loops, planning, memory, MCP-style protocols, multi-agent, reliability, HITL, cost control | project-04-tool-calling-agent |
| 4 | week-04-evaluation-production | Eval design, LLM judges, offline/online, regression tests, tracing, latency, caching, rate limits, cost math, versioning, safety/PII, LoRA, customer data privacy | project-05-evaluation, project-06-capstone |
| 5 | week-05-classic-ml-essentials | Supervised/unsupervised, overfitting, bias-variance, splits and leakage, metrics, regression, trees/boosting, clustering, neural nets/backprop | project-02-ticket-triage (metrics) |

Then: `rapid-fire.md` (50 quick Q&A) and `mock-interview.md` (6 FDE scenarios with rubrics).

## Weekly routine
1. Read `lesson.md` (about 2-3 hrs). Run each Python snippet; tweak numbers and predict outputs first.
2. Do `interview-qa.md` out loud, covering the answers (about 2 hrs). Record yourself on the scenario questions.
3. Memorize `cheatsheet.md`; redraw the main diagram from memory (30-45 min).
4. Cross-link: reread the matching `05-fde-projects/project-0*/lesson.md` and map each concept to code you wrote.
5. Last 30 min: explain the week's three key tradeoffs without notes.

## Final two weeks (after finishing week 5)
- Daily: 10 random questions from `rapid-fire.md`.
- Twice per week: one scenario from `mock-interview.md`, timed, self-scored with the rubric.

## Files
- week-NN-*/lesson.md, interview-qa.md (20 Qs each), cheatsheet.md
- rapid-fire.md, mock-interview.md at the folder root

## Interview habits to practice
- Clarify before designing: user, success metric, data, constraints.
- Bring evaluation, security/privacy and cost up unprompted.
- Give a phased plan with a first small deliverable.
- When unsure of a number, give the order of magnitude and how you would verify it.
- Treat the model as an untrusted component; enforce authorization in code.
