"""RBI domain pack: official catalog, entity types, and seeded extracts.

The compliance engine stays regulator-agnostic. This pack is the RBI-first
intelligence layer: which official sources to fetch, which entity types they
cover, and structured applicability hints. Live PDFs are preferred; seeded
text-layer extracts keep the demo offline (spec 16 CON-001).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from app.enums import DocumentType, OrganizationType, RegulatoryDomain
from app.services.pdf import build_text_pdf

RBI_LISTING_URLS = (
    "https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx",
    "https://www.rbi.org.in/Scripts/NotificationUser.aspx",
)

ALLOWED_HOSTS = ("www.rbi.org.in", "rbi.org.in", "rbidocs.rbi.org.in")


@dataclass(frozen=True)
class CatalogEntry:
    corpus_key: str
    title: str
    document_type: DocumentType
    reference_number: str
    publication_date: date | None
    effective_date: date | None
    source_url: str
    pdf_url: str | None
    regulatory_domain: RegulatoryDomain
    applicable_entity_types: tuple[str, ...]
    version_label: str
    seed_pages: tuple[str, ...]
    supersedes_key: str | None = None
    extra: dict = field(default_factory=dict)

    def seed_pdf(self) -> bytes:
        return build_text_pdf(list(self.seed_pages))


PA = OrganizationType.PAYMENT_AGGREGATOR.value
NBFC = OrganizationType.NBFC.value
BANK = OrganizationType.BANK.value
PG = OrganizationType.PAYMENT_GATEWAY.value
PB = OrganizationType.PAYMENT_BANK.value

CATALOG: tuple[CatalogEntry, ...] = (
    CatalogEntry(
        corpus_key="rbi.kyc.master_direction",
        title="Master Direction – Know Your Customer (KYC)",
        document_type=DocumentType.MASTER_DIRECTION,
        reference_number="RBI/DBR/2015-16/18",
        publication_date=date(2016, 2, 25),
        effective_date=date(2016, 2, 25),
        source_url="https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=11566",
        pdf_url=None,
        regulatory_domain=RegulatoryDomain.KYC_AML,
        applicable_entity_types=(PA, NBFC, BANK, PG, PB),
        version_label="2016-02-25",
        seed_pages=(
            """RESERVE BANK OF INDIA
Master Direction – Know Your Customer (KYC) Direction
Official source: https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=11566

1 Scope
This Direction applies to banks, NBFCs, payment aggregators and other regulated entities
that onboard customers in India.

2.1 Every regulated entity shall maintain a documented KYC policy consistent with
applicable RBI directions.
2.2 The KYC policy shall name a review cadence and a responsible officer.
""",
        ),
    ),
    CatalogEntry(
        corpus_key="rbi.pa.guidelines",
        title="Guidelines on Regulation of Payment Aggregators and Payment Gateways",
        document_type=DocumentType.GUIDELINE,
        reference_number="RBI/DPSS/2019-20/174",
        publication_date=date(2020, 3, 17),
        effective_date=date(2020, 3, 17),
        source_url="https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=11822",
        pdf_url=None,
        regulatory_domain=RegulatoryDomain.PAYMENTS,
        applicable_entity_types=(PA, PG),
        version_label="2020-03-17",
        seed_pages=(
            """RESERVE BANK OF INDIA
Department of Payment and Settlement Systems
Guidelines on Regulation of Payment Aggregators and Payment Gateways
Official source: https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=11822

1 Scope
These guidelines apply to payment aggregators and payment gateways operating in India.

4.1 Every payment aggregator shall maintain a documented KYC policy consistent with
applicable directions.
6.1 Merchant settlements shall be completed within the timelines stated in the agreement.
""",
        ),
    ),
    CatalogEntry(
        corpus_key="rbi.grievance.pa",
        title="Circular on Payment Aggregator Grievance Redressal (superseded extract)",
        document_type=DocumentType.CIRCULAR,
        reference_number="RBI/2025/PA-GRV",
        publication_date=date(2025, 6, 1),
        effective_date=date(2025, 6, 1),
        source_url="https://www.rbi.org.in/Scripts/NotificationUser.aspx",
        pdf_url=None,
        regulatory_domain=RegulatoryDomain.CUSTOMER_PROTECTION,
        applicable_entity_types=(PA,),
        version_label="2025-06-01",
        seed_pages=(
            """RESERVE BANK OF INDIA
Department of Payment and Settlement Systems
Circular on Payment Aggregator Grievance Redressal (2025 extract)

3.1 Every payment aggregator shall appoint a grievance officer.
3.2 Every payment aggregator shall maintain a documented grievance redressal process.

This extract is the previous version used for change detection. It does not require a
48-hour escalation path.
""",
        ),
    ),
    CatalogEntry(
        corpus_key="rbi.grievance.pa",
        title="Circular on Payment Aggregators — Grievance Redressal",
        document_type=DocumentType.CIRCULAR,
        reference_number="RBI/2026/001",
        publication_date=date(2026, 4, 1),
        effective_date=date(2026, 4, 1),
        source_url="https://www.rbi.org.in/Scripts/NotificationUser.aspx",
        pdf_url=None,
        regulatory_domain=RegulatoryDomain.CUSTOMER_PROTECTION,
        applicable_entity_types=(PA,),
        version_label="2026-04-01",
        supersedes_key="rbi.grievance.pa",
        extra={"demo_update": True},
        seed_pages=(
            """RESERVE BANK OF INDIA
Department of Payment and Settlement Systems
RBI/2026/001
Circular on Payment Aggregators
Official listing: https://www.rbi.org.in/Scripts/NotificationUser.aspx

1 Scope
This circular applies to payment aggregators operating in India.

2 Definitions
Payment aggregator means an entity that facilitates aggregation of payments from customers to merchants.

3 Grievance Redressal
3.1 Every payment aggregator shall appoint a grievance officer.
3.2 Every payment aggregator shall maintain a documented grievance redressal process.
3.3 The grievance redressal process shall include a 48-hour escalation path for unresolved complaints.

Compliance with clause 3.2 and 3.3 is required by 2026-12-01.

4 Know Your Customer
4.1 Every payment aggregator shall maintain a documented KYC policy consistent with applicable directions.

5 Complaint data
5.1 Every payment aggregator shall publish quarterly complaint data on its website.

6 Settlement
6.1 Merchant settlements shall be completed within the timelines stated in the agreement.
""",
        ),
    ),
    CatalogEntry(
        corpus_key="rbi.outsourcing.it",
        title="Master Direction on Outsourcing of Information Technology Services",
        document_type=DocumentType.MASTER_DIRECTION,
        reference_number="RBI/2023-24/102",
        publication_date=date(2023, 4, 10),
        effective_date=date(2023, 10, 1),
        source_url="https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=12499",
        pdf_url=None,
        regulatory_domain=RegulatoryDomain.OUTSOURCING,
        applicable_entity_types=(PA, NBFC, BANK, PG, PB),
        version_label="2023-04-10",
        seed_pages=(
            """RESERVE BANK OF INDIA
Master Direction on Outsourcing of Information Technology Services
Official source: https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=12499

1 Scope
This Direction applies to regulated entities that outsource IT services.

3.1 Every regulated entity that outsources IT services shall maintain a documented
outsourcing policy and name a responsible officer.
3.2 The outsourcing policy shall cover vendor due diligence and audit rights.
""",
        ),
    ),
    CatalogEntry(
        corpus_key="rbi.cyber.master_direction",
        title="Master Direction on Information Technology Governance, Risk, Controls and Assurance Practices",
        document_type=DocumentType.MASTER_DIRECTION,
        reference_number="RBI/2023-24/107",
        publication_date=date(2023, 11, 7),
        effective_date=date(2024, 4, 1),
        source_url="https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=12564",
        pdf_url=None,
        regulatory_domain=RegulatoryDomain.CYBERSECURITY,
        applicable_entity_types=(PA, NBFC, BANK, PG, PB),
        version_label="2023-11-07",
        seed_pages=(
            """RESERVE BANK OF INDIA
Master Direction on IT Governance, Risk, Controls and Assurance Practices
Official source: https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=12564

1 Scope
This Direction applies to banks, NBFCs and other regulated entities.

4.1 Every regulated entity shall maintain a documented information security policy.
4.2 The information security policy shall name a review cadence and a responsible officer.
""",
        ),
    ),
    CatalogEntry(
        corpus_key="rbi.nbfc.scale_based",
        title="Scale Based Regulation of Non-Banking Financial Companies",
        document_type=DocumentType.CIRCULAR,
        reference_number="RBI/2021-22/112",
        publication_date=date(2021, 10, 22),
        effective_date=date(2022, 10, 1),
        source_url="https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=12179",
        pdf_url=None,
        regulatory_domain=RegulatoryDomain.OTHER,
        applicable_entity_types=(NBFC,),
        version_label="2021-10-22",
        seed_pages=(
            """RESERVE BANK OF INDIA
Scale Based Regulation (SBR): A Revised Regulatory Framework for NBFCs
Official source: https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=12179

1 Scope
This circular applies to non-banking financial companies registered with the Reserve Bank.

3.1 Every NBFC shall maintain a documented governance policy consistent with its layer.
""",
        ),
    ),
)


def catalog_by_key() -> dict[str, list[CatalogEntry]]:
    grouped: dict[str, list[CatalogEntry]] = {}
    for entry in CATALOG:
        grouped.setdefault(entry.corpus_key, []).append(entry)
    return grouped
