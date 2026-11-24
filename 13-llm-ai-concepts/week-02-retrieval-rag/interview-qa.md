# Week 2 Interview Q&A: Retrieval and RAG

---

**1. Explain RAG end to end.**
Offline: parse documents, chunk, embed, store vectors with metadata (and a keyword index). Online: take the question (optionally rewrite it), retrieve top-k by vector and keyword search, rerank, assemble a prompt with instructions and the chunks, generate an answer with citations, log everything. Quality is bounded by retrieval.

**2. What is an embedding and what are the gotchas?**
A dense vector representing meaning, so similar texts are near each other. Gotchas: query and docs must share the model and version; truncation past max input length; weak on identifiers and jargon; changing models requires full re-embedding; vectors are sensitive data.

**3. Cosine vs dot product vs L2?**
Cosine compares direction only; dot product includes magnitude and equals cosine on normalized vectors; L2 is straight-line distance and ranks the same as cosine on normalized vectors. Use what the embedding model was trained for; normalize for consistency.

**4. When do you need an ANN index instead of brute force?**
Brute force is O(N*d) per query; fine up to roughly hundreds of thousands of vectors with vectorized math. Beyond that, or with strict latency, use ANN and accept slightly lower recall. Measure recall@k vs exact search.

**5. Explain HNSW.**
Layered proximity graph. Search enters at a sparse top layer, greedily moves toward the query, descends layers, ending in a dense bottom layer. Knobs: M, efConstruction, efSearch (higher efSearch = better recall, slower). Fast and high-recall, but memory-heavy and deletes are awkward.

**6. Explain IVF and how it differs.**
Cluster vectors with k-means; at query time search only the nprobe nearest clusters. Lower memory, pairs with product quantization, but needs training, and recall suffers near cell boundaries with low nprobe. HNSW: better recall/latency, more RAM. IVF: more compact, tunable, retrain as data drifts.

**7. How would you choose a vector store?**
Scale, filtering and ACL needs, hybrid search, update patterns, existing stack and ops capacity, residency/compliance, cost. For many FDE deployments, pgvector in the customer's Postgres is the least-friction start; move to a dedicated engine when scale or features demand. Compare current options in docs rather than quoting from memory.

**8. How do you pick chunk size?**
Treat as a hyperparameter evaluated on a retrieval test set. Start with structure-aware chunks of a few hundred tokens with modest overlap, add title/section context, consider parent-child (match small, return big). Too small loses context; too large dilutes embeddings and burns prompt budget.

**9. Why hybrid search, and how do you merge results?**
Dense search handles paraphrase but misses exact tokens (SKUs, error codes, names); BM25 does the opposite. Run both and merge with Reciprocal Rank Fusion, score = sum 1/(k + rank), which avoids calibrating score scales across systems.

**10. What does reranking do and what does it cost?**
A cross-encoder scores (query, chunk) jointly for much better precision than bi-encoder similarity. Pattern: retrieve 50 to 200, rerank, keep 3 to 10. Costs added latency and compute; cap candidates by latency budget. MMR can add diversity.

**11. What is query rewriting and when does it help?**
Reformulating the query before retrieval: resolve conversational references, expand to multiple paraphrases, HyDE, decompose multi-part questions, extract metadata filters. Helps with follow-up questions and vague queries; adds an LLM call, so adopt only if retrieval metrics improve.

**12. How do you get trustworthy citations?**
Give chunks stable IDs, instruct to cite per claim with quoted spans, then verify in code: IDs exist, quotes appear in the chunk, optionally an NLI/LLM faithfulness check. Link to the source page. A citation that is not verified is decoration.

**13. RAG gives a wrong answer. How do you debug it?**
Walk the pipeline: was the answer in the corpus (ingestion)? Was the chunk retrieved in top-k (retrieval)? Did it survive rerank into the prompt (ranking/budget)? Was it in the prompt but ignored or misread (generation)? Is the answer right but unsupported (faithfulness)? Logs of the query, rewritten query, chunk IDs and scores, and final prompt make this a five-minute exercise.

**14. How do you evaluate a RAG system?**
Separate retrieval (recall@k, MRR, nDCG on a labeled question-to-chunk set) from generation (faithfulness, correctness, citation accuracy, abstention on unanswerables). Build the golden set from real queries plus synthetic ones reviewed by humans. Track per-category results and run on every change.

**15. RAG vs fine-tuning vs long context?**
RAG for fresh/private knowledge, citations and ACLs. Fine-tuning for behavior, style, format, or distillation, not for facts. Long context for a few documents or whole-document reasoning where infra is overkill, mindful of per-call cost and recall at length. Often combine them.

**16. How do you handle documents with tables, PDFs, scans?**
Parsing quality is the bottleneck: use layout-aware parsing or OCR, preserve headers with rows, keep tables intact or per-row with header context, strip repeated headers/footers, store page numbers. Validate by sampling parsed output visually before blaming the model.

**17. How do you enforce per-user document permissions?**
Store ACL metadata per chunk, filter at query time using the caller's identity/groups, inside the retrieval query (not after generation). Test with a user lacking access to confirm zero leakage, including via cache and logs. Beware shared semantic caches across users.

**18. Scenario: "The bot cannot find answers that are definitely in our docs."**
Confirm the doc was ingested and parsed (look at the stored chunks). Run the query manually and inspect top-k. Typical causes: PDF parsing garbage, chunk splitting the answer, exact-term query needing BM25, filters too strict, stale index, embedding model weak on their jargon. Fix the highest-impact one, add the failing queries to the eval set, show before/after recall.

**19. Scenario: "Answers are sometimes outdated or contradict each other."**
Likely multiple versions of documents indexed together, or deletions not propagating. Add version/date metadata, dedupe, filter to current, reindex incrementally with delete handling, surface the document date in citations, and instruct the model how to handle conflicts (prefer newest, flag disagreement).

**20. Scenario: "Customer wants to upload 10,000 PDFs and have the model answer questions. Timeline: 2 weeks. What do you do?"**
Clarify use cases, question types, accuracy bar, security, users. Week 1: ingestion pipeline on a representative sample, baseline RAG (hybrid + rerank), collect 50 to 100 real questions with expected answers, show a first eval. Week 2: iterate on the worst categories, add citations and abstention, ACLs, logging, a feedback button, and a runbook. Set expectations: measure and report accuracy, list known limits (scanned docs, tables), plan for reindexing and ownership after handoff.

---

## Bonus probes
- "How do you reduce RAG latency?" Parallelize retrieval, smaller rerank pool, cache embeddings and answers, stream, smaller generation model.
- "What if the answer needs info from 20 chunks?" Hierarchical summarization/map-reduce, long context, or agentic multi-step retrieval.
- "How would you detect retrieval drift?" Monitor empty-result rate, mean top-1 score, thumbs-down, "not found" rate; periodic golden-set runs.
