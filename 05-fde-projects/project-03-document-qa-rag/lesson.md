# Project 3: Document Q&A (RAG) over a customer's messy files

Budget: ~2 hours. Run tests with `cd` into this folder, then `../../.venv/bin/pytest -q`. No network and no API key are needed: the LLM is an injected callable and the tests use a `FakeLLM`.

## The customer scenario
> "Our support team spends hours digging through the 80-page policy PDF and a pile of old `.txt` notes to answer the same questions. Can we get a chatbot that answers from our documents? It must never make things up, and agents need to see where an answer came from."

Your job: build the core of a retrieval-augmented generation (RAG) pipeline. Load -> chunk -> embed -> retrieve -> prompt with citations -> answer -> verify citations.

## Spec (what you implement in `exercises.py`)
| Piece | Behaviour |
|---|---|
| `load_text_file`, `load_pdf`, `load_document` | `.txt/.md` -> one page; `.pdf` -> one entry per page via `pypdf`; blank pages skipped, numbering kept; unknown extension -> `ValueError` |
| `chunk_text`, `build_chunks` | word-based chunks with overlap; `Chunk(text, source, page, chunk_id)` metadata |
| `cosine_similarity`, `top_k` | numpy; zero vector -> 0.0; deterministic tie-breaking |
| `Retriever` | embeds chunks once; `retrieve(query, k, min_score)` |
| `build_prompt`, `extract_citations` | numbered `[n] (file, p.N) text` sources; parse `[n]` markers |
| `answer_question` | refuses (without calling the LLM) when nothing relevant is retrieved; drops invented citation numbers |

Provided for you: `tokenize`, `BagOfWordsEmbedder` (a deterministic hashing embedder standing in for a real embedding model), `Chunk`, `Answer`, `IDK`.

## Concepts
- **Why RAG?** The model does not know the customer's documents, and stuffing 80 pages in every prompt is slow, costly and noisy. Retrieve only the few relevant passages.
- **Chunking**: too big and retrieval is vague; too small and context is lost. Overlap keeps a sentence that straddles a boundary findable. Keep page/source metadata on each chunk, because that is what makes citations possible.
- **Embeddings + cosine similarity**: texts become vectors; similar meaning gives a high cosine. With real embedding models, similar *meaning* matches; our bag-of-words fake only matches shared *words*, which is enough to test the logic.
- **Top-k + threshold**: always return the best k, but drop hits below a minimum score. "I don't know" is a feature.
- **Citations**: number the sources in the prompt, ask the model to cite `[n]`, then *verify* the numbers exist. Models invent citations.
- **Dependency injection**: `llm(prompt) -> str` and `embedder.embed(text)` are passed in, so tests are fast and deterministic and you can swap vendors.

## How an FDE would approach this
1. **Look at the real documents first.** Scanned PDFs have no text layer (`extract_text()` returns empty): detect it and tell the customer you need OCR, rather than silently indexing nothing. Tables, headers/footers and multi-column layouts extract badly.
2. **Ask for 10-20 real questions and the right answers** before writing code. That is your test set (see project 5).
3. **Start with the simplest pipeline**, measure retrieval separately from generation: "was the right chunk in the top 3?" is the number to improve first.
4. **Decide the failure behaviour with the customer**: wrong answer vs. "I don't know, ask a human". Usually refusing wins.
5. **Show sources in the UI.** Trust comes from clickable citations, not from prose quality.
6. Ask about permissions: should every user see every document? Retrieval must respect access control.

## Common mistakes
- Chunking by characters and splitting words in half; or overlap >= chunk size (infinite loop). Validate.
- Emitting a trailing duplicate chunk when the last window already reached the end.
- Resetting `chunk_id` per page, so ids collide.
- Re-embedding the whole corpus on every query. Embed once in `__init__`.
- Forgetting zero vectors (empty or all-stopword text) -> division by zero / NaN.
- Calling the LLM when nothing relevant was retrieved, then trusting its answer.
- Trusting `[7]` when only 3 sources were supplied.
- Sorting scores without a tie-break, which makes tests and demos flaky.

## Demo tips
- Bring one question the docs answer, one they only partly answer, and one they do not (the "I don't know" moment lands well with non-engineers).
- Print the retrieved chunks with scores next to the answer; it shows the audience what "grounded" means.
- Pre-load the documents; never index live on stage.
- Explain tradeoffs plainly: chunk size = precision vs. context; threshold = fewer wrong answers vs. more refusals.

## Optional manual step: plug in the real Claude API
Not used by the tests. Needs `ANTHROPIC_API_KEY` in your environment.
```python
import anthropic

client = anthropic.Anthropic()

def real_llm(prompt: str) -> str:
    msg = client.messages.create(
        model="claude-sonnet-5-5",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text

pages = load_document("policy.pdf")
retriever = Retriever(BagOfWordsEmbedder(), build_chunks(pages, "policy.pdf", 80, 15))
print(answer_question("How long do refunds take?", retriever, real_llm).text)
```
For production you would swap `BagOfWordsEmbedder` for a real embedding model and a vector store; the rest of the code stays the same because of the injected interfaces.
