# Week 2: Retrieval and RAG

Goal: design, debug, and defend a RAG system, and know when not to use one. Hands-on companion: `05-fde-projects/project-03-document-qa-rag`.

---

## 1. Why RAG

LLMs do not know your private, fresh, or long-tail data, and they hallucinate. RAG (retrieval-augmented generation) retrieves relevant passages at query time and puts them in the prompt so the model answers from them.

```
 INDEXING (offline)                              QUERYING (online)
 docs -> parse -> clean -> chunk                 user question
      -> embed each chunk -> vector index           -> (rewrite) -> embed
      + metadata (source, page, ACL, date)          -> retrieve top-k (vector + keyword)
      + keyword index (BM25)                        -> (rerank) -> top-n
                                                    -> build prompt: instructions + chunks + question
                                                    -> LLM -> answer + citations
                                                    -> (verify / log / feedback)
```

Benefits: fresh data without retraining, source attribution, access control per document, cheaper than fine-tuning for knowledge. Weakness: answer quality is capped by retrieval quality; garbage in, confident garbage out.

---

## 2. Embeddings

An embedding model maps text to a dense vector (hundreds to a few thousand dimensions) such that semantically similar texts are close.

```
 "reset my password"      -> [0.12, -0.40, ...]
 "I forgot my login"      -> [0.10, -0.38, ...]   (close)
 "quarterly revenue chart"-> [-0.55, 0.21, ...]   (far)
```

Notes:
- Query and document embeddings must come from the same model (and version). Changing the model means re-embedding everything.
- Embedding models have a max input length; text beyond it is truncated.
- Domain gap: general embedding models can be weak on jargon, part numbers, code, or other languages. Evaluate on your data; consider domain-tuned or multilingual models (check current docs).
- Dimensionality affects storage and speed; some models support truncated/Matryoshka embeddings. Quantization (int8/binary) shrinks the index.
- Embeddings are not a privacy boundary: they can leak information about the text; treat the vector store as sensitive as the source.

## 3. Similarity metrics

- Cosine similarity: angle between vectors; ignores magnitude. Most common for text.
- Dot product: equals cosine if vectors are normalized; some models are trained for dot product.
- Euclidean (L2): straight-line distance; equals a monotonic function of cosine on normalized vectors.
Use the metric the embedding model recommends. Normalize if using dot/cosine.

Runnable toy (no API key): bag-of-words "embeddings" show the mechanics of retrieval.

```python
import math, re
from collections import Counter

def vec(text):
    return Counter(re.findall(r"[a-z]+", text.lower()))

def cosine(a, b):
    dot = sum(a[k] * b.get(k, 0) for k in a)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0

docs = {
    "d1": "How to reset your password from the login page",
    "d2": "Quarterly revenue report for finance team",
    "d3": "Password policy: minimum length and rotation",
}
q = vec("forgot password reset")
ranked = sorted(docs, key=lambda d: cosine(q, vec(docs[d])), reverse=True)
print(ranked)
```

Real embeddings capture synonyms ("forgot" vs "lost") that bag-of-words misses; that is the point of dense retrieval.

---

## 4. Vector databases and ANN

Exact nearest-neighbor search compares the query with every vector: O(N * d). Fine up to roughly hundreds of thousands of vectors (a numpy matrix multiply). Beyond that you use Approximate Nearest Neighbor (ANN) indexes, trading a little recall for large speedups.

### 4.1 HNSW (Hierarchical Navigable Small World)
A multi-layer graph. Top layers are sparse "highways", bottom layer contains all points. Search starts at the top, greedily walks toward the query, drops a layer, repeats.

```
 Layer 2:   A ------------- F
 Layer 1:   A --- C ------- F --- H
 Layer 0:   A-B-C-D-E-F-G-H-I-J   (all nodes, local neighbors)
 query: enter at A, greedy hop toward closest neighbors, descend
```
Knobs: M (links per node), efConstruction (build quality), efSearch (query-time breadth: higher = better recall, slower). Pros: high recall, low latency, incremental inserts. Cons: memory hungry (graph plus vectors in RAM), slow-ish build, deletes are awkward.

### 4.2 IVF (Inverted File)
Cluster vectors (k-means) into nlist cells with centroids. At query time, find the nprobe closest centroids and scan only those cells.
Knobs: nlist, nprobe. Pros: smaller memory than HNSW, easy to combine with compression (PQ: product quantization, IVF-PQ). Cons: needs training on representative data; recall drops if the query lies near a cell boundary and nprobe is small; reindexing as data drifts.

### 4.3 Others
Flat (exact), PQ/scalar quantization (compress), DiskANN-style (SSD-based for huge corpora). Metadata filtering: pre-filter vs post-filter matters. Post-filtering after top-k can return too few results; good systems filter during traversal. Test filtered recall.

### 4.4 Choosing a store
- pgvector (inside Postgres): one system, transactional, SQL joins and ACL filters; fine into millions of vectors; simplest for many FDE deployments.
- Dedicated vector DBs / search engines (managed or self-hosted): scale, hybrid search features, ops convenience.
- In-memory libraries (FAISS and similar): prototypes, batch, embedded use.
Decision factors: scale, filtering needs, hybrid search, ops burden, existing stack, data residency, cost. Do not state a "best" vendor; compare on needs and say check current docs.

Metrics: recall@k versus exact search, p95 latency, QPS, memory, build time, update/delete cost.

---

## 5. Chunking

Chunking decides what a retrievable unit is. It is often the highest-leverage lever.

Tradeoff: small chunks = precise matching, but lose context; big chunks = more context, but diluted embeddings and more tokens in the prompt.

Strategies:
- Fixed size with overlap (e.g. a few hundred tokens, 10 to 20 percent overlap): baseline, simple.
- Structure-aware: split by headings, paragraphs, sentences, code functions, table rows. Usually better than blind fixed size.
- Semantic chunking: split where embedding similarity between adjacent sentences drops.
- Hierarchical / parent-child: embed small chunks for matching, return the larger parent section for context ("small to big").
- Add context: prepend document title/section path to each chunk; or LLM-generated chunk summaries/context blurbs (contextual retrieval) at index-time cost.
- Tables, PDFs, scans: parsing quality dominates; check OCR, column order, headers repeated, footers noise. Keep tables as structured text or per-row with headers.
- Metadata: source, page, section, date, author, version, ACL groups, language.

```python
def chunk(text: str, size: int = 200, overlap: int = 40):
    words = text.split()
    step = size - overlap
    return [" ".join(words[i:i + size]) for i in range(0, max(1, len(words) - overlap), step)]

doc = "word " * 500
parts = chunk(doc, size=200, overlap=40)
print(len(parts), [len(p.split()) for p in parts])
```

Always eval chunking choices with a retrieval test set rather than argue from taste.

---

## 6. Hybrid search (BM25 plus vectors)

- Dense (vector) search: semantic matching, handles paraphrase. Weak on exact tokens: IDs, SKUs, error codes, names, acronyms.
- Sparse / lexical (BM25): exact term matching with TF-IDF-style weighting and length normalization. Weak on synonyms.
- Hybrid: run both, merge. Common merge: Reciprocal Rank Fusion (RRF): score(d) = sum over rankers of 1 / (k + rank_i(d)), k about 60. Needs no score calibration between systems.

```python
def rrf(rankings, k=60):
    scores = {}
    for ranking in rankings:
        for rank, doc in enumerate(ranking, start=1):
            scores[doc] = scores.get(doc, 0.0) + 1.0 / (k + rank)
    return sorted(scores, key=scores.get, reverse=True)

bm25 = ["d3", "d1", "d7"]
dense = ["d1", "d5", "d3"]
print(rrf([bm25, dense]))     # d1 and d3 float up
```

Rule: if users search by identifiers or exact phrases, lexical must be in the mix.

## 7. Reranking

Two-stage retrieval: a fast first stage (bi-encoder: query and doc embedded independently) gets top 50 to 200 candidates; a cross-encoder reranker reads (query, doc) pairs jointly and scores precisely; keep top 3 to 10. Costs latency and compute; usually a big precision gain. Alternatives: LLM-as-reranker (slower, pricier), MMR (maximal marginal relevance) to diversify and avoid near-duplicates. Tune how many candidates you rerank against latency budget.

## 8. Query rewriting and understanding

- Conversational rewrite: turn "what about the premium plan?" into a standalone query using chat history.
- Expansion / multi-query: generate several paraphrases, retrieve for each, merge (RRF).
- HyDE: have the LLM write a hypothetical answer, embed that, retrieve with it.
- Decomposition: split multi-part questions into sub-queries.
- Routing: decide which index/tool (docs vs SQL vs none) or whether retrieval is needed at all.
- Metadata extraction: "invoices from March for Acme" becomes a filter plus a text query.
Cost: extra LLM call and latency; add only if retrieval evals show a gain.

## 9. Generation, grounding and citations

Prompt pattern:
```
Answer using ONLY the sources below. If they do not contain the answer, say
"I could not find this in the provided documents."
Cite sources as [id] after each claim.

<source id="1" title="Refund policy" page="3"> ... </source>
<source id="2" ...> ... </source>

Question: ...
```
Citation practices: give chunks stable IDs; ask for quoted spans; verify programmatically that cited IDs exist and quoted text appears in the chunk; render links back to the source page. Faithfulness check: does every claim have support? Handle conflicting sources (prefer newest/authoritative, or surface the conflict). Order chunks sensibly; limit total context. Enforce ACLs at retrieval time (filter by the user's permissions), never after generation.

## 10. RAG failure modes and debugging

Debug by stage. Always log: query, rewritten query, retrieved chunk IDs with scores, final prompt, answer.

```
 Wrong answer?
   |-- Was the right chunk in the corpus?             no -> ingestion/parsing/coverage problem
   |-- Was it retrieved in top-k?                     no -> retrieval problem (chunking, embeddings, hybrid, query rewrite, filters)
   |-- Was it ranked high enough to reach the prompt? no -> reranking / k / context budget
   |-- Was it in the prompt but ignored/misread?      yes -> generation problem (prompt, model, lost-in-the-middle, conflicting chunks)
   |-- Was the answer correct but unsupported?        -> faithfulness / citation problem
```

Common failures and fixes:
| Symptom | Likely cause | Fix |
|---|---|---|
| Right doc never found | Bad parsing (PDF columns/tables), chunk too big/small, exact-token query | Fix parser; structure-aware chunking; add BM25 hybrid |
| Retrieves near-duplicates | Overlapping/duplicated docs, versions | Dedup, MMR, version metadata |
| Outdated answer | Stale index, multiple versions | Incremental reindex, date/version filters, deletions propagate |
| Answer ignores context | Too much noise, middle-of-context loss | Rerank, fewer chunks, stronger instruction, reorder |
| Hallucinated when no answer | No abstention path | "Say not found", similarity threshold, eval with unanswerables |
| Multi-hop questions fail | Single retrieval pass | Decomposition, iterative/agentic retrieval |
| Wrong user sees restricted doc | ACL not enforced at retrieval | Metadata filter by user groups in query |
| Good in demo, bad in prod | Test set unrepresentative | Collect real queries, build golden set |
| Slow | Many calls, big k, big model | Cache, smaller rerank pool, stream, parallelize |
| Table/number errors | Chunk splits table | Table-aware parsing, return full table, code tools |

Retrieval metrics: recall@k (is a relevant chunk in top-k), MRR, nDCG, hit rate. Generation metrics: faithfulness/groundedness, answer relevance, correctness vs reference, citation accuracy. Measure retrieval and generation separately (Week 4).

## 11. RAG vs fine-tuning vs long context

| Need | Best first choice | Why |
|---|---|---|
| Private/fresh/changing facts, citations, per-user ACL | RAG | Update by reindex; auditable sources |
| Consistent style, format, domain behavior, small-model distillation | Fine-tuning | Changes behavior, not knowledge store |
| One or a few documents that fit, ad hoc analysis | Long context (maybe with prompt caching) | No infra; but cost per call and recall at length |
| Huge corpus (millions of pages) | RAG | Cannot fit in context |
| Needs reasoning over a whole document (summaries, cross-references) | Long context or hierarchical summarization | Chunks lose global structure |
| Structured data (tables, DB) | Text-to-SQL / tool calls | Retrieval over embeddings is wrong tool |

Combine them: fine-tuned model plus RAG; long context plus retrieval to pre-select. Say the decision criteria: data volatility, volume, latency/cost per query, need for citations/ACLs, behavior vs knowledge, team capacity.

## 12. Production concerns (preview of Week 4)
Incremental ingestion and deletes, idempotent pipelines, versioned indexes (blue/green reindex when changing embeddings or chunking), PII handling, per-tenant isolation (separate index or mandatory filter), caching, monitoring recall proxies (empty-result rate, thumbs-down, "not found" rate), cost of embedding refreshes.

## 13. How interviewers probe
- "Walk me through RAG end to end, and where does it break?" (Use the debugging tree.)
- "Why hybrid search?" (exact identifiers, acronyms; RRF.)
- "HNSW vs IVF?" (graph vs clusters; memory, recall, updates, tuning knobs.)
- "How do you choose chunk size?" (Eval-driven; structure-aware; parent-child.)
- "How do you evaluate retrieval without labels?" (Synthetic questions from chunks, then human review; LLM-labeled relevance; real query logs.)
- "RAG or fine-tuning?" (Knowledge vs behavior.)
- "How do you enforce document permissions?" (Filter at retrieval with user claims.)

## Self-check
1. Draw the indexing and query pipelines and name one log per stage.
2. Write RRF from memory.
3. Explain efSearch and nprobe in one sentence each.
4. Given a bad answer, list the 4 questions in the debugging tree.
