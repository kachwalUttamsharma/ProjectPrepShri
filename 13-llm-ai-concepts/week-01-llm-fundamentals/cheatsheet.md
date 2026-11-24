# Week 1 Cheatsheet: LLM Fundamentals

## Pipeline
text -> tokenizer -> tokens -> transformer (attention + FFN, stacked) -> logits -> sampler -> next token -> append -> repeat.

## Numbers (rough; verify per model, check current docs)
- 1 token about 4 chars about 0.75 English words.
- Output tokens: slower and pricier than input tokens.
- Latency = time-to-first-token (prefill, grows with prompt) + output_tokens / tokens-per-sec.
- Cost per call = in_tokens * in_price + out_tokens * out_price (get prices from current docs).

## Attention
score = softmax(Q.K / sqrt(d)); output = sum(weight * V). Causal mask = no peeking ahead. Naive cost about O(n^2) in sequence length.

## KV cache
Prefill (parallel, compute-bound) then decode (sequential, memory-bound). Cache grows with length and concurrency. Prompt caching: stable prefix first, variable text last.

## Training stages
Pretrain (knowledge) -> SFT (follow instructions) -> preference tuning/RLHF/DPO (helpful, safe, tone). New knowledge: retrieve, do not fine-tune.

## Sampling
- T=0 greedy; T low = focused; T high = diverse. Top-p = nucleus. Tune one knob.
- Deterministic tasks: low T. Still validate.

## Model choice
Cheap/small: classify, extract, route. Mid: most RAG/agents. Large/reasoning: hard multi-step. Patterns: route, cascade, distill. Always benchmark on customer data.

## Hallucination playbook
Ground -> cite and verify -> constrain output -> abstain path -> verify pass -> human for high stakes -> eval with unanswerable questions.

## Prompt patterns
System prompt (stable rules) | delimiters for untrusted data | few-shot (diverse, include edge cases) | CoT (more tokens) | structured output (schema + validate + retry) | decomposition | self-consistency | reflection.

## Structured output ladder
Prompt-only < JSON mode < schema-constrained / tool-call. Always validate meaning; handle truncation and refusals.

## Prompt injection
Direct vs indirect. No hard instruction/data boundary. Defend with: least privilege, human approval, allowlists, output URL stripping, isolation of untrusted content, no secrets in prompts, red-team evals. Avoid trifecta: private data + untrusted content + exfil channel.

## Failure modes
No max_tokens/timeout/retry; free-text parsing; model doing math/dates; prompt changes without eval; unpinned model version; PII in logs; trusting citations unchecked.

## One-liners for interviews
- "LLMs are plausibility engines; I add grounding and verification."
- "Treat the model as an untrusted component; enforce auth in code."
- "I would measure on your data before choosing a model."
