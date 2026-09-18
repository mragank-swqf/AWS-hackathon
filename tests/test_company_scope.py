from uuid import uuid4

from app.services.retrieval import chunk_visible_to_company


def test_regulation_chunks_are_visible_to_every_company():
    viewer = uuid4()
    assert chunk_visible_to_company(None, viewer) is True


def test_company_chunks_are_not_visible_to_another_company():
    company_a = uuid4()
    company_b = uuid4()
    assert chunk_visible_to_company(company_a, company_a) is True
    assert chunk_visible_to_company(company_a, company_b) is False
