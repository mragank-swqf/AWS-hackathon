from uuid import uuid4

import httpx
import pytest
from app.db.models import Company, RegulatoryDocument
from app.enums import Applicability, DocumentType, OrganizationType, RegulatoryDomain
from app.regulators.rbi.catalog import CATALOG
from app.services.applicability import assess_document
from app.services.regulatory_ingest import DownloadFailed, fetch_official_pdf
from app.services.requirement_diff import diff_requirement_text


def _company(**overrides) -> Company:
    data = {
        "id": uuid4(),
        "company_name": "PayFlow Technologies",
        "organization_type": OrganizationType.PAYMENT_AGGREGATOR.value,
        "operating_regions": ["India"],
        "products": ["Payments"],
        "customer_segments": ["Merchants"],
        "regulatory_entities": ["RBI"],
        "has_outsourced_operations": True,
        "uses_customer_data": True,
    }
    data.update(overrides)
    return Company(**data)


def _document(**overrides) -> RegulatoryDocument:
    data = {
        "id": uuid4(),
        "title": "PA circular",
        "regulator": "RBI",
        "document_type": DocumentType.CIRCULAR.value,
        "s3_key": "regulations/x.pdf",
        "content_hash": "abc",
        "processing_status": "completed",
        "applicable_entity_types": [OrganizationType.PAYMENT_AGGREGATOR.value],
        "regulatory_domain": RegulatoryDomain.CUSTOMER_PROTECTION.value,
        "lifecycle_status": "active",
        "source_kind": "seeded",
    }
    data.update(overrides)
    return RegulatoryDocument(**data)


def test_payment_aggregator_matches_pa_document():
    decision = assess_document(_company(), _document())
    assert decision.applicability == Applicability.APPLICABLE
    assert decision.human_review_required is False


def test_nbfc_does_not_match_pa_only_document():
    decision = assess_document(
        _company(organization_type=OrganizationType.NBFC.value),
        _document(),
    )
    assert decision.applicability == Applicability.NOT_APPLICABLE


def test_outsourcing_uncertain_when_profile_omits_flag():
    decision = assess_document(
        _company(has_outsourced_operations=None),
        _document(regulatory_domain=RegulatoryDomain.OUTSOURCING.value),
    )
    assert decision.applicability == Applicability.UNCERTAIN
    assert decision.human_review_required is True


def test_missing_company_type_is_uncertain():
    decision = assess_document(
        _company(organization_type=""),
        _document(),
    )
    assert decision.applicability == Applicability.UNCERTAIN


def test_requirement_diff_added_modified_removed_unchanged():
    previous = """
3.1 Every payment aggregator shall appoint a grievance officer.
3.2 Every payment aggregator shall maintain a documented grievance redressal process.
5.1 Every payment aggregator shall publish quarterly complaint data on its website.
"""
    current = """
3.1 Every payment aggregator shall appoint a grievance officer.
3.2 Every payment aggregator shall maintain a documented grievance redressal process with board approval.
3.3 The grievance redressal process shall include a 48-hour escalation path.
"""
    kinds = {item.clause_number: item.kind.value for item in diff_requirement_text(previous, current)}
    assert kinds["3.1"] == "unchanged"
    assert kinds["3.2"] == "modified"
    assert kinds["3.3"] == "added"
    assert kinds["5.1"] == "removed"


def test_fetch_official_pdf_rejects_non_rbi_host():
    with pytest.raises(DownloadFailed):
        fetch_official_pdf("https://example.com/circular.pdf")


def test_fetch_official_pdf_rejects_non_pdf_body():
    import respx

    with respx.mock:
        respx.get("https://www.rbi.org.in/file.pdf").mock(
            return_value=httpx.Response(200, content=b"<html>not a pdf</html>")
        )
        with pytest.raises(DownloadFailed):
            fetch_official_pdf("https://www.rbi.org.in/file.pdf")


def test_fetch_failed_download_status():
    import respx

    with respx.mock:
        respx.get("https://www.rbi.org.in/missing.pdf").mock(return_value=httpx.Response(404))
        with pytest.raises(DownloadFailed):
            fetch_official_pdf("https://www.rbi.org.in/missing.pdf")


def test_catalog_has_official_source_urls_and_versions():
    keys = [entry.corpus_key for entry in CATALOG]
    assert keys.count("rbi.grievance.pa") == 2
    assert all(entry.source_url.startswith("https://www.rbi.org.in/") for entry in CATALOG)
    versions = [entry.version_label for entry in CATALOG if entry.corpus_key == "rbi.grievance.pa"]
    assert versions[0] != versions[1]


def test_seed_pdfs_are_valid_pdfs():
    for entry in CATALOG:
        data = entry.seed_pdf()
        assert data.startswith(b"%PDF")
        assert entry.publication_date is not None


def test_hash_skip_helper_matches_same_bytes():
    from app.services.hashing import sha256_bytes

    first = CATALOG[0].seed_pdf()
    assert sha256_bytes(first) == sha256_bytes(first)
    assert sha256_bytes(first) != sha256_bytes(CATALOG[-1].seed_pdf())
