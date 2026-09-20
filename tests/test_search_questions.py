from uuid import uuid4

from app.agents.runner import STEPS
from app.db.models import DocumentChunk
from app.services.chunking import chunk_pages
from app.services.pdf import ExtractedPage
from app.services.retrieval import lexical_rank
from demo.documents import GRIEVANCE_PAGES, KYC_PAGES, REGULATION_PAGES

CASES = [
    ("clause 3.2", "3.2"),
    ("3.3", "3.3"),
    ("4.1", "4.1"),
    ("5.1", "5.1"),
    ("6.1", "6.1"),
    ("payment aggregators operating in India", "1"),
    ("grievance officer", "3.1"),
    ("48-hour escalation", "3.3"),
    ("KYC policy", "4.1"),
    ("quarterly complaint data", "5.1"),
]


def _corpus() -> list[DocumentChunk]:
    pages: list[ExtractedPage] = []
    page_no = 1
    for block in [*REGULATION_PAGES, *GRIEVANCE_PAGES, *KYC_PAGES]:
        pages.append(ExtractedPage(page_no, block, False))
        page_no += 1
    drafts = chunk_pages(pages)
    chunks: list[DocumentChunk] = []
    for draft in drafts:
        chunks.append(
            DocumentChunk(
                id=uuid4(),
                chunk_index=draft.chunk_index,
                text=draft.text,
                page_start=draft.page_start,
                page_end=draft.page_end,
                clause_number=draft.clause_number,
                section_title=draft.section_title,
            )
        )
    return chunks


def test_ten_known_questions_find_the_right_clause():
    chunks = _corpus()
    for query, clause in CASES:
        ranked = lexical_rank(chunks, query)
        assert ranked, f"no hits for {query}"
        by_id = {chunk.id: chunk for chunk in chunks}
        top = by_id[ranked[0]]
        assert top.clause_number == clause or clause in top.text, (
            f"{query} expected clause {clause}, got {top.clause_number} / {top.text[:80]}"
        )


def test_runner_step_order():
    assert STEPS == (
        "applicability",
        "requirements",
        "impact",
        "gap_detection",
        "risk",
        "action_plan",
        "verification",
    )
    assert STEPS[4] == "risk"
