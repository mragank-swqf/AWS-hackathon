from uuid import uuid4

from app.db.models import DocumentChunk
from app.services.chunking import chunk_pages
from app.services.pdf import ExtractedPage, build_text_pdf, extract_pages
from app.services.retrieval import is_clause_query, lexical_rank, rrf_merge


def test_clause_chunks_keep_page_and_number():
    pages = [
        ExtractedPage(1, "3.2 Every payment aggregator shall maintain a documented grievance process.", False),
        ExtractedPage(2, "3.3 The process shall include a 48-hour escalation path.", False),
    ]
    drafts = chunk_pages(pages)
    numbers = {item.clause_number for item in drafts}
    assert "3.2" in numbers
    clause_32 = next(item for item in drafts if item.clause_number == "3.2")
    assert clause_32.page_start == 1


def test_unreadable_page_is_recorded():
    pages = [
        ExtractedPage(1, "Enough text on this page to count as readable content for extraction.", False),
        ExtractedPage(2, "", True),
    ]
    drafts = chunk_pages(pages)
    unread = [item for item in drafts if item.extraction_method == "unreadable"]
    assert unread
    assert unread[0].page_start == 2


def test_text_pdf_round_trip():
    data = build_text_pdf(["1 Scope\nThis circular applies to payment aggregators."])
    pages = extract_pages(data)
    assert pages[0].unreadable is False
    assert "payment aggregators" in pages[0].text.lower()


def test_empty_page_pdf_is_unreadable():
    data = build_text_pdf([""])
    pages = extract_pages(data)
    assert pages[0].unreadable is True


def test_broken_file_raises():
    import pytest
    from app.services.pdf import extract_pages as extract

    with pytest.raises(ValueError):
        extract(b"this is not a pdf")


def test_rrf_keeps_both_lists():
    vector = [uuid4(), uuid4()]
    keyword = [uuid4(), vector[0]]
    scores = rrf_merge(vector, keyword)
    assert set(scores) == set(vector + [keyword[0]])


def test_clause_query_detection():
    assert is_clause_query("3.2") is True
    assert is_clause_query("clause 3.2") is True
    assert is_clause_query("grievance redressal") is False


def test_lexical_rank_finds_clause_number():
    chunk_a = DocumentChunk(
        id=uuid4(),
        chunk_index=0,
        text="Every payment aggregator shall maintain a documented grievance redressal process.",
        page_start=2,
        page_end=2,
        clause_number="3.2",
    )
    chunk_b = DocumentChunk(
        id=uuid4(),
        chunk_index=1,
        text="Merchant settlements shall be completed within agreed timelines.",
        page_start=6,
        page_end=6,
        clause_number="6.1",
    )
    ranked = lexical_rank([chunk_a, chunk_b], "clause 3.2")
    assert ranked[0] == chunk_a.id
