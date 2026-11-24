# Week 2 Cheatsheet: Retrieval and RAG

## Pipeline
Index: parse -> clean -> chunk -> embed -> store (vectors + metadata + BM25).
Query: (rewrite) -> embed -> hybrid retrieve top-50..200 -> rerank -> top 3..10 -> prompt -> answer + citations -> log.

## Similarity
Cosine = angle. Dot = cosine on normalized. L2 ranks like cosine on normalized. Same model for query and docs.

## ANN
| | HNSW | IVF (/PQ) |
|---|---|---|
| Idea | Layered graph, greedy walk | k-means cells, scan nprobe cells |
| Knobs | M, efConstruction, efSearch | nlist, nprobe |
| Strength | High recall, low latency, inserts | Compact, compressible |
| Weakness | RAM heavy, deletes awkward | Needs training, boundary misses |
Brute force fine to about hundreds of thousands of vectors. Measure recall@k vs exact, p95, memory.

## Stores
pgvector (simple, SQL, ACL joins) | dedicated vector DB/search engine (scale, hybrid) | FAISS-like (embedded/batch). Compare on current docs.

## Chunking
Structure-aware > fixed. Few hundred tokens, 10 to 20 percent overlap as baseline. Parent-child. Prepend title/section. Metadata: source, page, date, version, ACL. Eval-driven.

## Hybrid and rerank
RRF: score = sum 1/(k + rank), k about 60. BM25 for IDs and exact terms. Cross-encoder rerank after wide retrieval. MMR for diversity.

## Query rewriting
Conversational rewrite, multi-query, HyDE, decomposition, routing, metadata filters. Only if metrics improve.

## Prompt for grounding
"Use ONLY sources; say not found otherwise; cite [id]." Verify IDs and quotes in code. Enforce ACL at retrieval.

## Debug tree
Corpus? -> Retrieved? -> Ranked into prompt? -> Used correctly? -> Supported by citation?
Log: query, rewrite, chunk IDs + scores, final prompt, answer, model version.

## Metrics
Retrieval: recall@k, hit rate, MRR, nDCG. Generation: faithfulness, relevance, correctness, citation accuracy, abstention rate.

## RAG vs FT vs long context
Knowledge/fresh/citations/ACL = RAG. Behavior/format/distill = fine-tune. Few docs / whole-doc reasoning = long context. Structured data = SQL tool. Combine.

## Failure quick table
Not found -> parsing/chunking/BM25. Duplicates -> dedup/MMR. Stale -> reindex/version filter. Ignored context -> rerank, fewer chunks. Hallucinated no-answer -> abstain + threshold. Multi-hop -> decompose/agentic. Leakage -> ACL filter.
