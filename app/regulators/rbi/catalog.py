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
PPI = OrganizationType.PREPAID_INSTRUMENT_ISSUER.value
LEND = OrganizationType.LENDING_PLATFORM.value
AA = OrganizationType.ACCOUNT_AGGREGATOR.value

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
    CatalogEntry(
        corpus_key="rbi.data.payment_system_storage",
        title="Storage of Payment System Data",
        document_type=DocumentType.CIRCULAR,
        reference_number="DPSS.CO.OD.No.2785/06.08.005/2017-18",
        publication_date=date(2018, 4, 6),
        effective_date=date(2018, 10, 6),
        source_url="https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=11244",
        pdf_url=None,
        regulatory_domain=RegulatoryDomain.DATA,
        applicable_entity_types=(PA, PG, BANK, PB),
        version_label="2018-04-06",
        seed_pages=(
            """RESERVE BANK OF INDIA
Department of Payment and Settlement Systems
Storage of Payment System Data
Official source: https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=11244

1 Scope
This circular applies to payment system operators authorised by the Reserve Bank.

2.1 Every payment system operator shall store the entire payment system data in India.
2.2 The payment system operator shall maintain a documented data localisation control
and name a responsible officer.
""",
        ),
    ),
    CatalogEntry(
        corpus_key="rbi.customer.tat_harmonisation",
        title="Harmonisation of Turn Around Time (TAT) and Customer Compensation for Failed Transactions",
        document_type=DocumentType.CIRCULAR,
        reference_number="DPSS.CO.PD No.629/02.01.014/2019-20",
        publication_date=date(2019, 9, 20),
        effective_date=date(2019, 10, 20),
        source_url="https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=11693",
        pdf_url=None,
        regulatory_domain=RegulatoryDomain.CUSTOMER_PROTECTION,
        applicable_entity_types=(PA, PG, BANK, PB),
        version_label="2019-09-20",
        seed_pages=(
            """RESERVE BANK OF INDIA
Department of Payment and Settlement Systems
Harmonisation of Turn Around Time (TAT) and Customer Compensation
Official source: https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=11693

1 Scope
This circular applies to banks and authorised payment system operators.

3.1 Every payment system operator shall resolve failed transactions within the prescribed
turn around time.
3.2 The payment system operator shall compensate the customer automatically when the
turn around time is missed.
""",
        ),
    ),
    CatalogEntry(
        corpus_key="rbi.payments.card_tokenisation",
        title="Tokenisation – Card Transactions",
        document_type=DocumentType.CIRCULAR,
        reference_number="DPSS.CO.PD.No.1463/02.14.003/2018-19",
        publication_date=date(2019, 1, 8),
        effective_date=date(2019, 1, 8),
        source_url="https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=11668",
        pdf_url=None,
        regulatory_domain=RegulatoryDomain.PAYMENTS,
        applicable_entity_types=(PA, PG, BANK),
        version_label="2019-01-08",
        seed_pages=(
            """RESERVE BANK OF INDIA
Department of Payment and Settlement Systems
Tokenisation – Card Transactions
Official source: https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=11668

1 Scope
This circular applies to card networks, issuers, acquirers and payment aggregators that
store card credentials.

4.1 Every payment aggregator that stores card credentials shall tokenise those credentials.
4.2 The payment aggregator shall not store actual card data after tokenisation except for
the limited purpose permitted by the Reserve Bank.
""",
        ),
    ),
    CatalogEntry(
        corpus_key="rbi.payments.ppi_master_direction",
        title="Master Direction on Prepaid Payment Instruments",
        document_type=DocumentType.MASTER_DIRECTION,
        reference_number="RBI/DPSS/2021-22/82",
        publication_date=date(2021, 8, 27),
        effective_date=date(2021, 8, 27),
        source_url="https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=12156",
        pdf_url=None,
        regulatory_domain=RegulatoryDomain.PAYMENTS,
        applicable_entity_types=(PPI, BANK),
        version_label="2021-08-27",
        seed_pages=(
            """RESERVE BANK OF INDIA
Master Direction on Prepaid Payment Instruments
Official source: https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=12156

1 Scope
This Direction applies to banks and non-bank issuers of prepaid payment instruments.

3.1 Every prepaid payment instrument issuer shall maintain a documented PPI policy.
3.2 The PPI policy shall cover KYC, loading limits and redemption of unused balances.
""",
        ),
    ),
    CatalogEntry(
        corpus_key="rbi.lending.digital_lending",
        title="Guidelines on Digital Lending",
        document_type=DocumentType.GUIDELINE,
        reference_number="RBI/2022-23/111",
        publication_date=date(2022, 9, 2),
        effective_date=date(2022, 9, 2),
        source_url="https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=12382",
        pdf_url=None,
        regulatory_domain=RegulatoryDomain.DIGITAL_LENDING,
        applicable_entity_types=(NBFC, LEND, BANK),
        version_label="2022-09-02",
        seed_pages=(
            """RESERVE BANK OF INDIA
Guidelines on Digital Lending
Official source: https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=12382

1 Scope
These guidelines apply to regulated entities engaged in digital lending, including NBFCs.

5.1 Every regulated entity engaged in digital lending shall disclose the annual percentage
rate to the borrower before the loan is disbursed.
5.2 The regulated entity shall ensure loan servicing and repayment occur only on the
account of the regulated entity.
""",
        ),
    ),
    CatalogEntry(
        corpus_key="rbi.cyber.digital_payment_security",
        title="Master Direction on Digital Payment Security Controls",
        document_type=DocumentType.MASTER_DIRECTION,
        reference_number="RBI/2020-21/74",
        publication_date=date(2021, 2, 18),
        effective_date=date(2021, 3, 31),
        source_url="https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=12032",
        pdf_url=None,
        regulatory_domain=RegulatoryDomain.CYBERSECURITY,
        applicable_entity_types=(BANK, PB),
        version_label="2021-02-18",
        seed_pages=(
            """RESERVE BANK OF INDIA
Master Direction on Digital Payment Security Controls
Official source: https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=12032

1 Scope
This Direction applies to scheduled commercial banks, small finance banks, payments
banks and credit card issuing NBFCs.

4.1 Every scheduled commercial bank shall maintain a digital payment security control
framework.
4.2 The digital payment security control framework shall cover multi-factor authentication
and fraud monitoring.
""",
        ),
    ),
    CatalogEntry(
        corpus_key="rbi.customer.internal_ombudsman_pso",
        title="Internal Ombudsman for Payment System Operators",
        document_type=DocumentType.CIRCULAR,
        reference_number="RBI/2021-22/23",
        publication_date=date(2021, 4, 22),
        effective_date=date(2021, 10, 1),
        source_url="https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=12067",
        pdf_url=None,
        regulatory_domain=RegulatoryDomain.CUSTOMER_PROTECTION,
        applicable_entity_types=(PA, PG),
        version_label="2021-04-22",
        seed_pages=(
            """RESERVE BANK OF INDIA
Internal Ombudsman Scheme for Payment System Operators
Official source: https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=12067

1 Scope
This circular applies to non-bank payment system operators meeting the specified
complaint volume.

3.1 Every payment system operator shall appoint an internal ombudsman.
3.2 The internal ombudsman shall review complaints that the operator proposes to reject.
""",
        ),
    ),
    CatalogEntry(
        corpus_key="rbi.outsourcing.payment_settlement",
        title="Framework for Outsourcing of Payment and Settlement-related Activities by Payment System Operators",
        document_type=DocumentType.CIRCULAR,
        reference_number="RBI/2021-22/111",
        publication_date=date(2021, 10, 28),
        effective_date=date(2021, 10, 28),
        source_url="https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=12176",
        pdf_url=None,
        regulatory_domain=RegulatoryDomain.OUTSOURCING,
        applicable_entity_types=(PA, PG),
        version_label="2021-10-28",
        seed_pages=(
            """RESERVE BANK OF INDIA
Framework for Outsourcing of Payment and Settlement-related Activities
Official source: https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=12176

1 Scope
This framework applies to payment system operators that outsource payment and
settlement-related activities.

3.1 Every payment system operator that outsources payment and settlement activities
shall maintain a documented outsourcing agreement.
3.2 The outsourcing agreement shall preserve the operator’s audit rights and customer
data protection duties.
""",
        ),
    ),
    CatalogEntry(
        corpus_key="rbi.payments.pa_cross_border",
        title="Regulation of Payment Aggregators – Cross Border",
        document_type=DocumentType.CIRCULAR,
        reference_number="RBI/2023-24/80",
        publication_date=date(2023, 10, 31),
        effective_date=date(2023, 10, 31),
        source_url="https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=12522",
        pdf_url=None,
        regulatory_domain=RegulatoryDomain.PAYMENTS,
        applicable_entity_types=(PA,),
        version_label="2023-10-31",
        seed_pages=(
            """RESERVE BANK OF INDIA
Department of Payment and Settlement Systems
Regulation of Payment Aggregators – Cross Border
Official source: https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=12522

1 Scope
This circular applies to payment aggregators that facilitate cross-border payment
collection for online export and import transactions.

4.1 Every payment aggregator that facilitates cross-border payments shall maintain
authorisation for that activity.
4.2 The payment aggregator shall keep import and export collection in separate
nostro / vostro arrangements as specified.
""",
        ),
    ),
    CatalogEntry(
        corpus_key="rbi.nbfc.fraud_risk",
        title="Master Direction on Fraud Risk Management in NBFCs",
        document_type=DocumentType.MASTER_DIRECTION,
        reference_number="RBI/DOS/2024-25/118",
        publication_date=date(2024, 7, 15),
        effective_date=date(2024, 7, 15),
        source_url="https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=12704",
        pdf_url=None,
        regulatory_domain=RegulatoryDomain.OTHER,
        applicable_entity_types=(NBFC, BANK),
        version_label="2024-07-15",
        seed_pages=(
            """RESERVE BANK OF INDIA
Master Direction on Fraud Risk Management in Non-Banking Financial Companies
Official source: https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=12704

1 Scope
This Direction applies to NBFCs in the Base, Middle and Upper Layers.

3.1 Every NBFC shall maintain a documented fraud risk management policy.
3.2 The fraud risk management policy shall name a board-approved reporting channel.
""",
        ),
    ),
    CatalogEntry(
        corpus_key="rbi.payments.offline_small_value",
        title="Framework for Facilitating Small Value Digital Payments in Offline Mode",
        document_type=DocumentType.CIRCULAR,
        reference_number="DPSS.CO.PD.No.S-508/02.14.003/2020-21",
        publication_date=date(2022, 1, 3),
        effective_date=date(2022, 1, 3),
        source_url="https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=12147",
        pdf_url=None,
        regulatory_domain=RegulatoryDomain.PAYMENTS,
        applicable_entity_types=(PA, PG, BANK, PB),
        version_label="2022-01-03",
        seed_pages=(
            """RESERVE BANK OF INDIA
Framework for Facilitating Small Value Digital Payments in Offline Mode
Official source: https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=12147

1 Scope
This framework applies to authorised payment system operators that offer offline
digital payments.

3.1 Every payment system operator that offers offline payments shall apply a
per-transaction limit.
3.2 The payment system operator shall reverse an offline payment that cannot be
reconciled within the stated period.
""",
        ),
    ),
    CatalogEntry(
        corpus_key="rbi.aa.nbfc_account_aggregator",
        title="Master Direction – Non-Banking Financial Company – Account Aggregator",
        document_type=DocumentType.MASTER_DIRECTION,
        reference_number="RBI/DNBR/2016-17/46",
        publication_date=date(2016, 9, 2),
        effective_date=date(2016, 9, 2),
        source_url="https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=10598",
        pdf_url=None,
        regulatory_domain=RegulatoryDomain.DATA,
        applicable_entity_types=(AA,),
        version_label="2016-09-02",
        seed_pages=(
            """RESERVE BANK OF INDIA
Master Direction – Non-Banking Financial Company – Account Aggregator
Official source: https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=10598

1 Scope
This Direction applies to NBFCs registered as account aggregators.

3.1 Every account aggregator shall obtain explicit consent before sharing financial
information.
3.2 The account aggregator shall not access the financial information it transfers
except as required to provide the service.
""",
        ),
    ),
)


def catalog_by_key() -> dict[str, list[CatalogEntry]]:
    grouped: dict[str, list[CatalogEntry]] = {}
    for entry in CATALOG:
        grouped.setdefault(entry.corpus_key, []).append(entry)
    return grouped
