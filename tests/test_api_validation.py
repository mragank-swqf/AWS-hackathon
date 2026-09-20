from uuid import uuid4

from app.enums import OrganizationType
from app.schemas.models import AnalysisCreate, CompanyCreate


def test_create_company_rejects_unknown_org_type(client):
    response = client.post(
        "/api/v1/companies",
        json={"company_name": "PayFlow", "organization_type": "unknown"},
    )
    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "request_id" in body
    assert response.headers.get("X-Request-Id")


def test_create_company_rejects_empty_name(client):
    response = client.post(
        "/api/v1/companies",
        json={"company_name": "  ", "organization_type": "payment_aggregator"},
    )
    assert response.status_code == 400


def test_analysis_without_ids_is_rejected(client, company_header):
    response = client.post("/api/v1/analyses", json={}, headers=company_header)
    assert response.status_code == 400


def test_bad_date_on_regulation_upload_is_rejected(client, company_header):
    response = client.post(
        "/api/v1/regulations",
        data={
            "title": "Circular",
            "regulator": "RBI",
            "document_type": "circular",
            "publication_date": "31-12-2026",
        },
        files={"file": ("doc.pdf", b"%PDF-1.4 test", "application/pdf")},
        headers=company_header,
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_non_pdf_upload_is_rejected(client, company_header):
    response = client.post(
        "/api/v1/regulations",
        data={"title": "Circular", "regulator": "RBI", "document_type": "circular"},
        files={"file": ("notes.txt", b"hello", "text/plain")},
        headers=company_header,
    )
    assert response.status_code == 415


def test_missing_company_header_is_rejected(client, monkeypatch):
    monkeypatch.delenv("DEMO_COMPANY_ID", raising=False)
    from app.config import get_settings

    get_settings.cache_clear()
    response = client.get("/api/v1/regulations")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "MISSING_COMPANY_ID"


def test_request_id_on_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("X-Request-Id")


def test_schema_helpers_exist():
    payload = CompanyCreate(
        company_name="PayFlow",
        organization_type=OrganizationType.PAYMENT_AGGREGATOR,
    )
    assert payload.organization_type == OrganizationType.PAYMENT_AGGREGATOR
    analysis = AnalysisCreate(company_id=uuid4(), regulation_id=uuid4())
    assert analysis.analysis_depth.value == "standard"
