"""Load the PayFlow demo company, policies, and one rule PDF (spec 16)."""

from __future__ import annotations

import argparse
from datetime import date
from uuid import uuid4

from sqlalchemy import select

from app.config import get_settings
from app.db.models import Company, CompanyPolicy, RegulatoryDocument
from app.db.session import get_session_factory
from app.enums import DocumentType, ProcessingStatus
from app.services.hashing import sha256_bytes
from app.services.ingest import ingest_policy, ingest_regulation
from app.services.storage import policy_key, put_private_pdf, regulation_key
from demo.documents import DEMO_COMPANY_ID, PAYFLOW_PROFILE, POLICY_PACK, regulation_pdf


def seed(*, run_ingest: bool = True) -> None:
    get_settings()
    session = get_session_factory()()
    try:
        company = session.get(Company, DEMO_COMPANY_ID)
        if company is None:
            company = Company(id=DEMO_COMPANY_ID, **PAYFLOW_PROFILE)
            session.add(company)
            session.flush()
        else:
            for key, value in PAYFLOW_PROFILE.items():
                setattr(company, key, value)

        def store_regulation() -> RegulatoryDocument:
            data = regulation_pdf()
            digest = sha256_bytes(data)
            existing = session.scalar(
                select(RegulatoryDocument).where(RegulatoryDocument.content_hash == digest)
            )
            if existing:
                return existing
            doc_id = uuid4()
            key = regulation_key(doc_id, "rbi-payment-aggregators.pdf")
            put_private_pdf(key, data)
            document = RegulatoryDocument(
                id=doc_id,
                title="RBI Circular on Payment Aggregators",
                regulator="RBI",
                document_type=DocumentType.CIRCULAR.value,
                reference_number="RBI/2026/001",
                publication_date=date(2026, 9, 1),
                effective_date=date(2026, 12, 1),
                source_url="https://example.gov.in/rbi-2026-001.pdf",
                s3_key=key,
                content_hash=digest,
                processing_status=ProcessingStatus.QUEUED.value,
            )
            session.add(document)
            session.flush()
            return document

        def store_policy(spec) -> CompanyPolicy:
            data = spec.pdf()
            digest = sha256_bytes(data)
            existing = session.scalar(
                select(CompanyPolicy).where(
                    CompanyPolicy.company_id == company.id,
                    CompanyPolicy.content_hash == digest,
                )
            )
            if existing:
                return existing
            doc_id = uuid4()
            key = policy_key(company.id, doc_id, spec.filename)
            put_private_pdf(key, data)
            policy = CompanyPolicy(
                id=doc_id,
                company_id=company.id,
                title=spec.title,
                evidence_type=spec.evidence_type,
                version_label=spec.version_label,
                effective_date=date(2026, 4, 1),
                owner_department=spec.owner_department,
                approved_by=spec.approved_by,
                s3_key=key,
                content_hash=digest,
                processing_status=ProcessingStatus.QUEUED.value,
            )
            session.add(policy)
            session.flush()
            return policy

        regulation = store_regulation()
        policies = [store_policy(spec) for spec in POLICY_PACK]
        session.commit()

        if run_ingest:
            ingest_regulation(session, regulation.id)
            for policy in policies:
                ingest_policy(session, policy.id)
            session.commit()

        print(f"DEMO_COMPANY_ID={company.id}")
        print(f"REGULATION_ID={regulation.id}")
        for policy in policies:
            print(f"POLICY {policy.title}={policy.id}")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-ingest", action="store_true")
    args = parser.parse_args()
    seed(run_ingest=not args.skip_ingest)
