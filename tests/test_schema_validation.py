import pytest
from app.enums import ALL_ENUMS, OrganizationType
from app.schemas.models import AnalysisCreate, CompanyCreate
from pydantic import ValidationError


def test_every_fixed_list_rejects_unknown_value():
    for enum_cls in ALL_ENUMS:
        with pytest.raises(ValueError):
            enum_cls("not_on_the_list")


def test_missing_company_name_is_rejected():
    with pytest.raises(ValidationError) as exc:
        CompanyCreate(company_name="", organization_type=OrganizationType.PAYMENT_AGGREGATOR)
    assert "company_name" in str(exc.value)


def test_unknown_organization_type_is_rejected():
    with pytest.raises(ValidationError):
        CompanyCreate(company_name="PayFlow", organization_type="unknown")


def test_unknown_field_is_rejected():
    with pytest.raises(ValidationError):
        CompanyCreate(
            company_name="PayFlow",
            organization_type=OrganizationType.PAYMENT_AGGREGATOR,
            surprise="nope",
        )


def test_analysis_requires_company_and_regulation():
    with pytest.raises(ValidationError):
        AnalysisCreate()


def test_valid_company_passes():
    payload = CompanyCreate(
        company_name="PayFlow Technologies",
        organization_type=OrganizationType.PAYMENT_AGGREGATOR,
        business_model="Online merchant payment processing",
        operating_regions=["India"],
    )
    assert payload.company_name == "PayFlow Technologies"
