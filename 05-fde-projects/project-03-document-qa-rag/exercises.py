"""Project 3: document Q&A (RAG). Read lesson.md first.

Provided: tokenize, BagOfWordsEmbedder, Chunk, Answer, STOPWORDS.
Implement everything marked `...`. No network or API key is needed: the LLM is
an injected callable `llm(prompt: str) -> str`.
"""
from __future__ import annotations

import re
import zlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from pypdf import PdfReader

IDK = "I don't know based on the provided documents."

STOPWORDS = frozenset(
    "a an the is are was were be to of in on at for and or by with from as it its this that "
    "what which who how do does did can i you we our your my".split()
)


def tokenize(text: str) -> list[str]:
    """PROVIDED. Lowercase word tokens with stopwords removed."""
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in STOPWORDS]


class BagOfWordsEmbedder:
    """PROVIDED. Deterministic hashing bag-of-words embedder (no model, no network).

    Each token is hashed (crc32, stable across runs) into one of `dim` buckets;
    the count vector is L2-normalised. Stands in for a real embedding model.
    """

    def __init__(self, dim: int = 512):
        self.dim = dim

    def embed(self, text: str) -> np.ndarray:
        vec = np.zeros(self.dim, dtype=float)
        for tok in tokenize(text):
            vec[zlib.crc32(tok.encode()) % self.dim] += 1.0
        norm = np.linalg.norm(vec)
        return vec / norm if norm else vec

    def embed_many(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim))
        return np.vstack([self.embed(t) for t in texts])


@dataclass(frozen=True)
class Chunk:
    text: str
    source: str  # file name, e.g. "handbook.pdf"
    page: int  # 1-based page number (text files are page 1)
    chunk_id: int  # position in the whole index, 0-based


@dataclass
class Answer:
    text: str
    citations: list[Chunk]  # chunks the answer actually cites, in citation order
    hits: list[tuple[Chunk, float]]  # everything retrieved, best first


def load_text_file(path) -> str:
    """Return the full text of a UTF-8 text file. `path` may be a str or Path.

    Hint: pathlib.Path(path).read_text(encoding="utf-8")
    """
    ...


def load_pdf(path) -> list[str]:
    """Return one string per PDF page (stripped). A page with no extractable text -> "".

    Hint: pypdf.PdfReader(str(path)).pages; page.extract_text() may return None/"".
    """
    ...


def load_document(path) -> list[tuple[int, str]]:
    """Load .txt/.md/.pdf into [(page_number, text), ...] with 1-based page numbers.

    - text files are a single page 1
    - texts are stripped; blank pages are SKIPPED but numbering of the others is kept
    - any other extension -> ValueError
    Hint: reuse load_text_file / load_pdf; Path(path).suffix.lower().
    """
    ...


def chunk_text(text: str, chunk_size: int = 50, overlap: int = 10) -> list[str]:
    """Split text into chunks of `chunk_size` WORDS, consecutive chunks sharing `overlap` words.

    chunk_text("w0 ... w9", 4, 1) -> ["w0 w1 w2 w3", "w3 w4 w5 w6", "w6 w7 w8 w9"]
    - empty text -> []
    - stop as soon as a chunk reaches the end (no trailing duplicate/tiny chunk)
    - ValueError unless chunk_size > 0 and 0 <= overlap < chunk_size
    Hint: step = chunk_size - overlap; range(0, len(words), step).
    """
    ...


def build_chunks(pages, source: str, chunk_size: int = 50, overlap: int = 10) -> list[Chunk]:
    """Chunk every (page_number, text) page into Chunk objects.

    chunk_id counts 0, 1, 2... across ALL pages (not reset per page); chunks never span pages.
    """
    ...


def cosine_similarity(a, b) -> float:
    """Cosine similarity of two vectors as a Python float. If either has zero norm -> 0.0.

    Hint: np.dot(a, b) / (norm(a) * norm(b)); np.linalg.norm.
    """
    ...


def top_k(query_vec, matrix, k: int) -> list[tuple[int, float]]:
    """Return [(row_index, score), ...] for the k rows of `matrix` most similar to query_vec.

    Sorted best first; ties broken by LOWER row index. Fewer than k rows -> return them all.
    Empty matrix or k <= 0 -> [].
    Hint: sorted(range(n), key=lambda i: (-scores[i], i)).
    """
    ...


class Retriever:
    """Index chunks once, then answer many queries."""

    def __init__(self, embedder, chunks: list[Chunk]):
        """Store embedder and chunks; precompute self.matrix = embedder.embed_many(texts)."""
        ...

    def retrieve(self, query: str, k: int = 3, min_score: float = 0.0) -> list[tuple[Chunk, float]]:
        """Return up to k (Chunk, score) best first. Drop hits with score <= 0 or < min_score.

        A query sharing no words with anything (score 0) must return [].
        """
        ...


def build_prompt(question: str, hits) -> str:
    """Build the RAG prompt from (Chunk, score) hits (best first).

    Must contain, in this order: instructions (say "ONLY" the sources may be used, and
    to reply exactly IDK when they lack the answer, and to cite like [1]), then a
    "Sources:" section with one line per hit: "[n] (source, p.page) text" numbered from 1,
    then "Question: <question>" and a final "Answer:" line.
    """
    ...


def extract_citations(answer: str) -> list[int]:
    """Return the sorted unique ints found in [n] markers: "A [2] B [1] [2]" -> [1, 2].

    Hint: re.findall(r"\[(\d+)\]", answer). "array[x]" is not a citation.
    """
    ...


def answer_question(question: str, retriever, llm, k: int = 3, min_score: float = 0.15) -> Answer:
    """The whole pipeline: retrieve -> prompt -> llm -> citations.

    - hits = retriever.retrieve(question, k=k, min_score=min_score)
    - no hits -> Answer(IDK, [], []) and DO NOT call the llm (cheaper and no hallucination)
    - else text = llm(build_prompt(question, hits)).strip()
    - citations = chunks for cited numbers, in ascending number order; ignore numbers
      outside 1..len(hits) (models invent citations!)
    - return Answer(text, citations, hits)
    """
    ...
