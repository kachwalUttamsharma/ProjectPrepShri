import numpy as np
import pytest

from exercises import *


def make_pdf(pages):
    """Build a tiny valid PDF (one line of text per page) with correct xref offsets."""
    objs = {}
    n = len(pages)
    kids = " ".join(f"{3 + 2 * i} 0 R" for i in range(n))
    objs[1] = "<< /Type /Catalog /Pages 2 0 R >>"
    objs[2] = f"<< /Type /Pages /Kids [{kids}] /Count {n} >>"
    font_id = 3 + 2 * n
    for i, text in enumerate(pages):
        page_id, content_id = 3 + 2 * i, 4 + 2 * i
        objs[page_id] = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents {content_id} 0 R "
            f"/Resources << /Font << /F1 {font_id} 0 R >> >> >>"
        )
        stream = f"BT /F1 12 Tf 50 700 Td ({text}) Tj ET" if text else ""
        objs[content_id] = f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream"
    objs[font_id] = "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
    out = b"%PDF-1.4\n"
    offsets = {}
    for num in sorted(objs):
        offsets[num] = len(out)
        out += f"{num} 0 obj\n{objs[num]}\nendobj\n".encode()
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    for num in sorted(objs):
        out += f"{offsets[num]:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return out


class FakeLLM:
    """Deterministic: records prompts; replies with a canned string."""

    def __init__(self, reply="Refunds take 14 days [1]."):
        self.reply = reply
        self.prompts = []

    def __call__(self, prompt):
        self.prompts.append(prompt)
        return self.reply


DOCS = [
    (1, "Refund policy: customers may request a refund within 14 days of purchase. "
        "Refunds are returned to the original payment method."),
    (2, "Shipping: standard shipping takes 5 business days. Express shipping takes 2 days."),
    (3, "Security: all passwords are hashed and two factor authentication is available."),
]


@pytest.fixture
def retriever():
    chunks = build_chunks(DOCS, "policy.pdf", chunk_size=100, overlap=0)
    return Retriever(BagOfWordsEmbedder(), chunks)


# ---- loading ----
def test_load_text_file(tmp_path):
    p = tmp_path / "a.txt"
    p.write_text("hello world", encoding="utf-8")
    assert load_text_file(p) == "hello world"
    assert load_text_file(str(p)) == "hello world"


def test_load_pdf_pages(tmp_path):
    p = tmp_path / "a.pdf"
    p.write_bytes(make_pdf(["Alpha page one", "Beta page two"]))
    pages = load_pdf(p)
    assert len(pages) == 2
    assert "Alpha page one" in pages[0]
    assert "Beta page two" in pages[1]


def test_load_document_txt_and_pdf_and_errors(tmp_path):
    t = tmp_path / "n.txt"
    t.write_text("  some notes  ")
    assert load_document(t) == [(1, "some notes")]
    p = tmp_path / "d.pdf"
    p.write_bytes(make_pdf(["First", "", "Third"]))
    docs = load_document(p)
    assert [n for n, _ in docs] == [1, 3]  # blank page skipped, numbering kept
    assert docs[1][1] == "Third"
    with pytest.raises(ValueError):
        load_document(tmp_path / "x.docx")


# ---- chunking ----
def test_chunk_text_overlap():
    text = " ".join(f"w{i}" for i in range(10))
    assert chunk_text(text, 4, 1) == ["w0 w1 w2 w3", "w3 w4 w5 w6", "w6 w7 w8 w9"]


def test_chunk_text_edges():
    assert chunk_text("", 4, 1) == []
    assert chunk_text("a b c", 10, 2) == ["a b c"]
    assert chunk_text("a b c d", 2, 0) == ["a b", "c d"]  # no trailing empty/duplicate chunk
    for size, ov in [(0, 0), (3, 3), (3, 5), (3, -1)]:
        with pytest.raises(ValueError):
            chunk_text("a b c d", size, ov)


def test_build_chunks_metadata():
    pages = [(1, "a b c d"), (3, "e f")]
    chunks = build_chunks(pages, "f.pdf", chunk_size=2, overlap=0)
    assert [c.text for c in chunks] == ["a b", "c d", "e f"]
    assert [c.chunk_id for c in chunks] == [0, 1, 2]
    assert [c.page for c in chunks] == [1, 1, 3]
    assert all(c.source == "f.pdf" for c in chunks)


# ---- similarity / retrieval ----
def test_cosine_similarity():
    assert cosine_similarity([1, 0], [1, 0]) == pytest.approx(1.0)
    assert cosine_similarity([1, 0], [0, 1]) == pytest.approx(0.0)
    assert cosine_similarity([1, 1], [2, 2]) == pytest.approx(1.0)
    assert cosine_similarity([0, 0], [1, 1]) == 0.0


def test_embedder_is_deterministic_and_normalised():
    e = BagOfWordsEmbedder()
    v = e.embed("refund policy")
    assert np.allclose(v, e.embed("refund policy"))
    assert np.linalg.norm(v) == pytest.approx(1.0)
    assert e.embed_many(["a b", "c d"]).shape == (2, e.dim)


def test_top_k_orders_and_breaks_ties():
    m = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0], [1.0, 0.0]])
    res = top_k([1.0, 0.0], m, 3)
    assert [i for i, _ in res] == [0, 3, 2]
    assert res[0][1] == pytest.approx(1.0)
    assert top_k([1.0, 0.0], m, 10).__len__() == 4
    assert top_k([1.0, 0.0], np.zeros((0, 2)), 3) == []


def test_retriever_finds_relevant_chunk(retriever):
    hits = retriever.retrieve("How many days do I have to request a refund?", k=2)
    assert hits[0][0].page == 1
    assert hits[0][1] >= hits[-1][1]
    hits = retriever.retrieve("how long does express shipping take", k=1)
    assert hits[0][0].page == 2


def test_retriever_min_score_filters(retriever):
    assert retriever.retrieve("quantum chromodynamics lattice", k=3, min_score=0.1) == []
    assert retriever.retrieve("", k=3) == []


# ---- prompt / citations ----
def test_build_prompt_numbers_sources(retriever):
    hits = retriever.retrieve("refund days", k=2)
    prompt = build_prompt("What is the refund window?", hits)
    assert "[1]" in prompt and "[2]" in prompt
    assert "policy.pdf" in prompt and "p.1" in prompt
    assert hits[0][0].text in prompt
    assert "What is the refund window?" in prompt
    assert "ONLY" in prompt
    assert prompt.index("[1]") < prompt.index("[2]") < prompt.index("Question:")


def test_extract_citations():
    assert extract_citations("A [2] and B [1], again [2].") == [1, 2]
    assert extract_citations("no cites") == []
    assert extract_citations("array[x] and [10]") == [10]


# ---- end to end ----
def test_answer_question_with_citations(retriever):
    llm = FakeLLM("Refunds are allowed within 14 days [1].")
    ans = answer_question("What is the refund window?", retriever, llm, k=2)
    assert ans.text == "Refunds are allowed within 14 days [1]."
    assert len(llm.prompts) == 1 and "refund" in llm.prompts[0].lower()
    assert [c.page for c in ans.citations] == [1]
    assert ans.hits[0][0] is ans.citations[0] or ans.hits[0][0] == ans.citations[0]


def test_answer_ignores_hallucinated_citation_numbers(retriever):
    llm = FakeLLM("Yes [1] and also [9].")
    ans = answer_question("refund window days", retriever, llm, k=2)
    assert len(ans.citations) == 1


def test_answer_idk_without_calling_llm(retriever):
    llm = FakeLLM()
    ans = answer_question("quantum chromodynamics lattice", retriever, llm)
    assert ans.text == IDK
    assert ans.citations == [] and ans.hits == []
    assert llm.prompts == []


def test_full_pipeline_from_pdf(tmp_path):
    p = tmp_path / "handbook.pdf"
    p.write_bytes(make_pdf(["Vacation: employees receive 25 vacation days per year.",
                            "Remote work: employees may work remotely two days per week."]))
    chunks = build_chunks(load_document(p), "handbook.pdf", 30, 5)
    r = Retriever(BagOfWordsEmbedder(), chunks)
    ans = answer_question("How many vacation days per year?", r, FakeLLM("25 days [1]"))
    assert ans.citations[0].page == 1 and ans.citations[0].source == "handbook.pdf"
