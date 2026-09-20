from uuid import uuid4

import pytest
from app.db.models import Company, CompanyPolicy, DocumentChunk, RegulatoryDocument
from app.enums import DocumentType, EvidenceType, OrganizationType, ProcessingStatus
from app.services.retrieval import list_chunks_for_company
from sqlalchemy.exc import IntegrityError


def _company(session, name: str) -> Company:
    company = Company(
        company_name=name,
        organization_type=OrganizationType.PAYMENT_AGGREGATOR.value,
    )
    session.add(company)
    session.flush()
    return company


def _regulation(session) -> RegulatoryDocument:
    document = RegulatoryDocument(
        title="Example Circular",
        regulator="RBI",
        document_type=DocumentType.CIRCULAR.value,
        s3_key=f"regulations/{uuid4()}/doc.pdf",
        content_hash=str(uuid4()),
        processing_status=ProcessingStatus.QUEUED.value,
    )
    session.add(document)
    session.flush()
    return document


def _policy(session, company: Company) -> CompanyPolicy:
    policy = CompanyPolicy(
        company_id=company.id,
        title="KYC Policy",
        evidence_type=EvidenceType.POLICY.value,
        s3_key=f"policies/{company.id}/{uuid4()}/kyc.pdf",
        content_hash=str(uuid4()),
        processing_status=ProcessingStatus.QUEUED.value,
    )
    session.add(policy)
    session.flush()
    return policy


@pytest.mark.db
def test_create_company_and_read_back(db_session):
    company = _company(db_session, "PayFlow Technologies")
    loaded = db_session.get(Company, company.id)
    assert loaded is not None
    assert loaded.company_name == "PayFlow Technologies"


@pytest.mark.db
def test_chunk_cannot_point_at_both_sources(db_session):
    company = _company(db_session, "PayFlow")
    regulation = _regulation(db_session)
    policy = _policy(db_session, company)
    chunk = DocumentChunk(
        regulatory_document_id=regulation.id,
        company_policy_id=policy.id,
        company_id=company.id,
        chunk_index=0,
        text="both sources",
        page_start=1,
        page_end=1,
    )
    db_session.add(chunk)
    with pytest.raises(IntegrityError):
        db_session.flush()


@pytest.mark.db
def test_company_search_never_returns_another_companys_chunks(db_session):
    company_a = _company(db_session, "Company A")
    company_b = _company(db_session, "Company B")
    regulation = _regulation(db_session)
    policy_a = _policy(db_session, company_a)
    policy_b = _policy(db_session, company_b)

    shared = DocumentChunk(
        regulatory_document_id=regulation.id,
        chunk_index=0,
        text="shared rule text about grievance",
        page_start=1,
        page_end=1,
    )
    own = DocumentChunk(
        company_policy_id=policy_a.id,
        company_id=company_a.id,
        chunk_index=0,
        text="company A policy",
        page_start=1,
        page_end=1,
    )
    other = DocumentChunk(
        company_policy_id=policy_b.id,
        company_id=company_b.id,
        chunk_index=0,
        text="company B secret policy",
        page_start=1,
        page_end=1,
    )
    db_session.add_all([shared, own, other])
    db_session.flush()

    visible = list_chunks_for_company(db_session, company_a.id)
    texts = {chunk.text for chunk in visible}
    assert "shared rule text about grievance" in texts
    assert "company A policy" in texts
    assert "company B secret policy" not in texts
