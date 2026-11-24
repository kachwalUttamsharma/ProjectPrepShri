# Rapid-fire: 50 questions (cover the answer, one or two sentences each)

Model names, prices and limits change: say "check current docs" for any number.

## LLM fundamentals (1-12)
1. **What is a token?** A sub-word unit from a fixed vocabulary; the unit of billing, context and latency. About 4 English characters.
2. **Why can't LLMs count letters reliably?** They see tokens, not characters; use code tools.
3. **Attention in one sentence?** Each token mixes information from other tokens weighted by query-key relevance.
4. **What is the KV cache?** Stored keys/values of past tokens so decoding does not recompute them; grows with length and concurrency.
5. **Prefill vs decode?** Prefill processes the prompt in parallel (sets time to first token); decode generates one token at a time (sets tokens per second).
6. **Pretraining vs SFT vs RLHF?** Knowledge from next-token prediction; instruction following from supervised examples; preference alignment from ranked outputs.
7. **What does temperature do?** Rescales logits before softmax: low is focused, high is random.
8. **Top-p?** Sample from the smallest token set whose cumulative probability reaches p.
9. **Why might temperature 0 still vary?** Numerical nondeterminism, model updates, tie-breaking, differing context.
10. **Name three hallucination mitigations.** Grounding with retrieval, verified citations, abstention plus schema validation (also verification passes).
11. **Few-shot: when and risks?** When format/judgment needs showing; costs tokens and can bias toward example labels.
12. **Indirect prompt injection?** Instructions hidden in content the system ingests (docs, web, tool output) that the model obeys; defend with least privilege, approvals, isolation.

## Retrieval and RAG (13-24)
13. **RAG in one line?** Retrieve relevant chunks at query time and have the model answer from them with citations.
14. **Cosine vs dot product?** Cosine ignores magnitude; equal on normalized vectors.
15. **Why ANN?** Exact search is O(N*d); ANN trades a little recall for big speedups.
16. **HNSW in one line?** Layered proximity graph with greedy descent; knob efSearch.
17. **IVF in one line?** k-means cells; search only nprobe nearest cells.
18. **Chunk size tradeoff?** Small = precise but context-poor; large = context-rich but diluted and costly.
19. **Why hybrid search?** Dense handles meaning, BM25 handles exact terms and IDs.
20. **RRF formula?** sum over rankers of 1/(k + rank), k about 60.
21. **What does a reranker do?** Cross-encoder rescoring of top candidates for precision.
22. **Query rewriting examples?** Conversational rewrite, multi-query, HyDE, decomposition, filter extraction.
23. **RAG debug order?** Corpus, retrieved, ranked into prompt, used correctly, supported by citation.
24. **RAG vs fine-tune?** RAG for knowledge, fine-tune for behavior and format.

## Agents and tool use (25-33)
25. **How does function calling work?** Model emits a structured call; your code validates, authorizes, executes and returns the result.
26. **Agent vs workflow?** Agent chooses the path; workflow code fixes it. Prefer workflows when path is known.
27. **Agent stop conditions?** Final answer, max steps, budget, timeout, repeated failure, human needed.
28. **Why idempotency keys?** Retries must not duplicate side effects.
29. **ReAct?** Alternate reasoning, action, observation.
30. **MCP in one line?** A standard client-server protocol for discovering and calling tools/resources from independent servers.
31. **Main MCP risk?** Untrusted or changing tool descriptions and over-broad credentials; allowlist and least privilege.
32. **Why do agent costs balloon?** Full history is resent each step; trim, cache, route, cap.
33. **Where do you add humans?** Irreversible or high-impact actions, low confidence, ambiguity.

## Evaluation and production (34-43)
34. **First eval-set ingredients?** Real queries, edge cases, unanswerables, past failures, held-out slice.
35. **LLM judge biases?** Position, verbosity, self-preference; calibrate with humans.
36. **Offline vs online evals?** Fixed dataset gate vs shadow/canary/A-B on live traffic.
37. **Prompt regression testing?** Eval suite in CI on every prompt/model/retrieval change.
38. **What goes in a trace?** Retrieval, each LLM call with version and tokens, tool calls, validation, latency.
39. **Prompt caching rule?** Static content first, dynamic last.
40. **Semantic cache danger?** False hits and cross-user leakage; scope and tune threshold.
41. **How to handle 429s?** Backoff with jitter, Retry-After, limiter, queue, fallback, quota request.
42. **Cost formula?** (in*P_in + out*P_out)/1e6 per call; report cost per successful outcome.
43. **When fine-tune with LoRA?** After prompt/RAG plateau, stable task, clean labeled data, volume or latency justify.

## Classic ML (44-50)
44. **Overfitting fixes?** More data, regularization, simpler model, early stopping, ensembling.
45. **Precision vs recall definitions?** TP/(TP+FP) vs TP/(TP+FN).
46. **When ROC-AUC misleads?** Rare positives; use PR-AUC.
47. **Name three leakage sources.** Future/target features, preprocessing before split, duplicates or same entity across splits.
48. **Bagging vs boosting?** Bagging averages independent trees to cut variance; boosting fits sequential residuals to cut bias.
49. **k-means limits?** Need k, spherical clusters, scale and init sensitivity.
50. **Backprop in one line?** Chain rule computes each weight's gradient of the loss; step against it by the learning rate.
