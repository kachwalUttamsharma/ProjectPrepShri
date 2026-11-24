# Week 1 Interview Q&A: LLM Fundamentals

Cover the answer, say yours out loud, then compare. Model answers are deliberately concise.

---

**1. What is an LLM, in one minute?**
A neural network (usually a decoder-only transformer) trained to predict the next token given previous tokens. At inference it runs in a loop: compute a distribution over the vocabulary, sample a token, append, repeat. Knowledge comes from pretraining; instruction following from SFT and preference tuning. It has no memory across calls beyond what is in the prompt.

**2. What is a token and why do you care?**
A sub-word unit from a fixed vocabulary (BPE-style). Billing, context limits, and latency are all in tokens. Rough rule: about 4 English characters per token; code, JSON, numbers and non-English text cost more. Token counts differ per model family.

**3. Why can models fail at counting letters or long arithmetic?**
They see tokens, not characters, and are trained for plausibility, not exact computation. Fix by using tools (code execution, calculator) for exact work.

**4. Explain attention without jargon.**
For each token the model computes how relevant every earlier token is (via query/key similarity), then mixes their value vectors by those weights. It lets "it" look back at "cat". Causal masking stops tokens seeing the future.

**5. What is the context window and what are its practical limits?**
Max tokens of prompt plus output the model handles in one call. It is shared by system prompt, history, retrieved docs, tool outputs and the answer. Bigger windows cost more and add latency, and quality can degrade for details buried in the middle or among many distractors, so you test with your data rather than trust the headline number.

**6. What is the KV cache?**
Stored key/value vectors for already-processed tokens so decoding does not recompute them each step. Prefill (process the prompt in parallel) sets time-to-first-token; decode (one token at a time) sets tokens/sec. KV memory grows with sequence length and concurrency, limiting batch size. Prompt caching exposes a similar idea at the API level for repeated prefixes.

**7. Why are output tokens priced and timed worse than input tokens?**
Input is processed in parallel (prefill); output is generated sequentially, each step needing a pass through the model and reading the cache. Providers typically price output higher (check current docs).

**8. Pretraining vs instruction tuning vs RLHF?**
Pretraining: next-token prediction on huge corpora, gives knowledge and language. Instruction tuning: supervised on (instruction, response) pairs, gives assistant behavior. RLHF/preference tuning: optimise toward human-preferred outputs, shapes helpfulness, safety, tone; side effects include sycophancy and verbosity.

**9. Temperature and top-p: what do they do and how do you set them?**
Temperature rescales logits (low: sharper, near-deterministic; high: more random). Top-p samples from the smallest set of tokens covering probability mass p. Adjust one, not both. Extraction/classification/tool calls: low. Creative: higher. Low temperature improves repeatability, not correctness.

**10. Same prompt, temperature 0, still different outputs. Why?**
Floating-point non-determinism across batches/hardware, ties between near-equal logits, silent model version updates, differences in prompt whitespace or system context. If reproducibility matters, pin the model version, log inputs/outputs, and design for tolerance (validation, not exact match).

**11. How do you choose between a small and a large model?**
Start from the task requirements: accuracy bar, latency budget, volume, cost, data sensitivity, features needed. Build an eval set from real data, run candidates, pick the cheapest that passes. Common patterns: route by difficulty, cascade with escalation, distill a big model's labels into a small one.

**12. What causes hallucination and how do you mitigate it?**
Plausibility objective, missing or stale knowledge, ambiguous prompts, noisy context, reward for confident answers. Mitigate: ground with retrieval/tools, require quoted citations and verify them, constrain outputs with schemas, allow "I don't know", use verification passes, human review for high risk, and measure with an eval set that includes unanswerable questions.

**13. When is chain-of-thought useful and what are its costs?**
Helps multi-step reasoning, arithmetic, planning. Costs tokens and latency; reasoning text may not faithfully reflect the model's actual computation; dedicated reasoning models may not need explicit prompting. Keep reasoning separate from the final answer field if downstream code consumes the answer.

**14. How do you get reliable structured output?**
Ladder: prompt for JSON and parse; JSON mode; schema-constrained decoding or tool-call outputs. Always validate semantically (enums, ranges, IDs exist), set adequate max tokens to avoid truncation, retry with the error message on failure, and have a fallback or human queue. Constrained decoding guarantees shape, not truth.

**15. What goes in a system prompt and what does not?**
Role, rules, tone, output format, tool policies, refusal behavior. Not secrets, and not security enforcement: it can be leaked or overridden. Real authorization lives in code.

**16. Few-shot vs fine-tuning vs zero-shot?**
Zero-shot first, since it is cheapest. Add few-shot (2 to 5 diverse examples, including edge and "none" cases) when format or judgment needs showing. Fine-tune only when prompting plateaus, volume is high, and you have quality labeled data (Week 4). Dynamic few-shot (retrieve similar examples) is a good middle path.

**17. What is prompt injection and what is indirect prompt injection?**
Untrusted text carrying instructions the model obeys. Direct: user types it. Indirect: it is hidden in content the system ingests (web page, document, email, tool result). The model has no hard boundary between instructions and data.

**18. How do you defend against it?**
Architecture over wording: least-privilege, read-only tools by default, per-user credentials, allowlisted tool arguments, human approval for side effects, strip external URLs/images from output, isolate untrusted content, avoid combining private data + untrusted input + outbound channel, monitor, and red-team in your eval set. Never put secrets in the prompt.

**19. Scenario: "Our chatbot told a customer a refund policy that does not exist. Fix it."**
Triage: reproduce from logs (prompt, retrieved context, model version). Is the policy in the knowledge base? If yes, was it retrieved (retrieval bug) or ignored (faithfulness bug)? If no, the model invented it: ground answers in an authoritative policy source, instruct to answer only from context and abstain otherwise, add citation requirement, add this case to a regression set, add a guardrail for commitments (refunds, prices) that routes to a human. Communicate to the customer the root cause and the fix without overpromising "never again".

**20. Scenario: "Customer says the model is 'getting worse' since last week; nothing changed on our side."**
Check: did the provider alias move to a new model version (pin versions)? Did input distribution shift (new ticket types, longer docs, other languages)? Did a prompt/template/retrieval index change? Did rate limiting/timeouts cause fallbacks or truncation? Compare old vs new outputs on a fixed regression set, using stored logs. Fix: pin versions, add monitoring on quality proxies, run evals on any change, and agree with the customer on a measurable definition of "worse".

---

## Bonus probes
- "Explain temperature using a formula." softmax(logits / T).
- "Why do longer prompts increase latency?" Prefill compute grows with prompt length, delaying first token.
- "What would you log?" Prompt version, model id, token counts, latency, tool calls, validation results; redact PII.
