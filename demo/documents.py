"""Demo company and evidence for PayFlow Technologies (spec 16).

PayFlow is a fictional Paytm-scale Indian payment aggregator: UPI QR, checkout,
payouts, and merchant devices. It is not Paytm and does not copy Paytm documents.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.enums import EvidenceType, OrganizationType
from app.services.pdf import build_text_pdf

DEMO_COMPANY_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")

PAYFLOW_PROFILE = {
    "company_name": "PayFlow Technologies",
    "organization_type": OrganizationType.PAYMENT_AGGREGATOR.value,
    "business_model": (
        "India-wide merchant acquiring: UPI QR and intent, hosted checkout, payouts, "
        "refunds, bill-pay collection, and device-led in-store payments. Consumer "
        "wallets, if used, sit with a partner bank. PayFlow does not issue PPIs."
    ),
    "operating_regions": ["India"],
    "products": [
        "UPI QR and intent collect",
        "Hosted checkout and payment links",
        "In-store soundbox and QR plates",
        "Merchant payouts and refunds",
        "Bharat Bill Pay collection",
        "Cross-border export collections (limited beta)",
        "Merchant dashboard and settlement reports",
    ],
    "customer_segments": [
        "Kirana and MSME merchants",
        "Enterprise marketplaces",
        "Consumers paying those merchants",
    ],
    "regulatory_entities": ["RBI", "NPCI"],
    "uses_customer_data": True,
    "uses_automated_decisioning": True,
    "has_outsourced_operations": True,
    "existing_policies": [
        "Customer Grievance Redressal Policy",
        "Know Your Customer Policy",
        "Merchant Settlement Procedure",
        "Payment System Data Localisation Policy",
        "Card Tokenisation Procedure",
        "Failed Transaction TAT SOP",
        "Information Security Policy",
        "IT Outsourcing Policy",
        "Internal Ombudsman Charter",
    ],
    "internal_controls": [
        "Maker-checker on merchant onboarding",
        "Access reviews",
        "Audit logging",
        "Fraud-rule engine on UPI collect",
        "Daily settlement recon",
        "India data-residency attestations from cloud vendors",
    ],
}

REGULATION_PAGES = [
    """RESERVE BANK OF INDIA
Department of Payment and Settlement Systems
RBI/2026/001
Circular on Payment Aggregators

1 Scope
This circular applies to payment aggregators operating in India.

2 Definitions
Payment aggregator means an entity that facilitates aggregation of payments from customers to merchants.
""",
    """3 Grievance Redressal
3.1 Every payment aggregator shall appoint a grievance officer.
3.2 Every payment aggregator shall maintain a documented grievance redressal process.
3.3 The grievance redressal process shall include a 48-hour escalation path for unresolved complaints.

Compliance with clause 3.2 and 3.3 is required by 2026-12-01.
""",
    """4 Know Your Customer
4.1 Every payment aggregator shall maintain a documented KYC policy consistent with applicable directions.

5 Complaint data
5.1 Every payment aggregator shall publish quarterly complaint data on its website.

6 Settlement
6.1 Merchant settlements shall be completed within the timelines stated in the agreement.
""",
]

GRIEVANCE_PAGES = [
    """PayFlow Technologies
Customer Grievance Redressal Policy v3.1
Owner: Compliance
Approved by: Board
Effective: 2026-04-01

1 Intake
Merchants and consumers may file a complaint in the PayFlow Business app, the
consumer UPI collect screen, or email. A ticket number is issued.

2 Grievance officer
A named grievance officer in Compliance owns the queue.

3 Documented process
PayFlow maintains this documented grievance redressal process for merchant and consumer complaints.
""",
    """4 Records
An audit trail of tickets is retained for 8 years.

5 Coverage
QR, checkout, soundbox, payouts, and refunds complaints are in the same queue.

This policy does not state an escalation timeline or a 48-hour turnaround.
This policy does not require quarterly complaint data on the public website.
""",
]

KYC_PAGES = [
    """PayFlow Technologies
Know Your Customer Policy
Owner: Compliance

1 Purpose
This KYC policy describes customer identification for merchants onboarded onto the PayFlow platform.

2 Merchant onboarding
Kirana, MSME and enterprise merchants submit GSTIN, PAN, bank account, and UPI VPA
before a QR plate or checkout key is issued.

3 Controls
Access reviews and audit logging apply to KYC records.
""",
    """4 Ongoing
Watchlist screening runs on onboarding. Beneficial-owner checks apply above a GMV threshold.

This policy does not name a review cadence or map each control to a current RBI KYC direction.
""",
]

SETTLEMENT_PAGES = [
    """PayFlow Technologies
Merchant Settlement Procedure v2.4
Owner: Operations
Approved by: CFO
Evidence type: procedure

1 Purpose
PayFlow settles UPI, card, and net-banking collections to the merchant's nominated
Indian bank account.

2 Timelines
Merchant settlements follow the timelines stated in the merchant agreement.
Standard QR and checkout collections settle on T+1 bank working days.
Marketplace split settlements settle on T+2.

3 Recon
Operations runs a daily settlement recon against NPCI and acquirer files.
""",
    """4 Exceptions
Failed credits are retried the next working day. Chargebacks follow the card-network
window. This procedure does not cover cross-border export collections.
""",
]

DATA_PAGES = [
    """PayFlow Technologies
Payment System Data Localisation Policy v1.2
Owner: Information Security
Approved by: CISO

1 Scope
Payment system data includes UPI collect payloads, card tokens, settlement files,
and merchant KYC images processed on PayFlow rails.

2. Residency
PayFlow stores the entire payment system data in India.
Primary stores are Mumbai and Hyderabad regions. Backups stay in India.

3 Named officer
The CISO is the responsible officer for data localisation.
""",
    """4 Vendors
Cloud processors may handle payment system data only under contracts that keep
the data in India and preserve PayFlow audit rights.
""",
]

TOKEN_PAGES = [
    """PayFlow Technologies
Card Tokenisation Procedure v1.0
Owner: Product
Approved by: CISO

1 Scope
Hosted checkout may save a card on file for returning payers on merchant sites.

2 Control
PayFlow tokenises stored card credentials through the card network. Checkout does
not keep full PAN after the token is issued.

3 Residual storage
Network tokens and the last four digits may be retained for recurring charges.
This procedure does not yet cover soundbox or offline card-present flows.
""",
]

TAT_PAGES = [
    """PayFlow Technologies
Failed Transaction Turn Around Time SOP v1.1
Owner: Operations
Approved by: Compliance

1 Scope
Failed UPI, card, and net-banking collects on PayFlow checkout and QR.

2 TAT
Operations tracks the RBI turn around time table for failed transactions.
UPI decline-after-debit is queued for auto-reversal the same day where NPCI allows.

3 Compensation
This SOP records the TAT clocks. It does not yet auto-compensate the customer when
the turn around time is missed. Treasury posts those credits by hand.
""",
]

SECURITY_PAGES = [
    """PayFlow Technologies
Information Security Policy v4.0
Owner: Information Security
Approved by: Board

1 Purpose
PayFlow maintains a documented information security policy for UPI, checkout,
soundbox, and settlement systems.

2 Controls
Multi-factor authentication, fraud-rule monitoring, and vendor access reviews apply
to production systems.

3 Review
This policy does not name a fixed review cadence or a single responsible officer
outside the CISO office.
""",
]

OUTSOURCING_PAGES = [
    """PayFlow Technologies
IT Outsourcing Policy v2.0
Owner: Engineering
Approved by: Board

1 Scope
PayFlow outsources cloud hosting, device logistics, and part of 24x7 merchant support.

2. Control
Every vendor that receives payment system data or production access is covered by a
documented outsourcing agreement.

3 Diligence
Vendor due diligence and audit rights are required before go-live.
The policy names Engineering as the responsible officer for IT outsourcing.
""",
]

OMBUDSMAN_PAGES = [
    """PayFlow Technologies
Internal Ombudsman Charter v1.0
Owner: Compliance
Approved by: Board

1 Appointment
PayFlow has appointed an internal ombudsman in Compliance, independent of the
grievance officer who owns the day-to-day queue.

2 Review
The internal ombudsman shall review complaints that the operator proposes to reject.
""",
]


@dataclass(frozen=True)
class PolicySpec:
    title: str
    filename: str
    evidence_type: str
    version_label: str
    owner_department: str
    approved_by: str
    pages: tuple[str, ...]

    def pdf(self) -> bytes:
        return build_text_pdf(list(self.pages))


POLICY_PACK: tuple[PolicySpec, ...] = (
    PolicySpec(
        "Customer Grievance Redressal Policy",
        "payflow-grievance-policy.pdf",
        EvidenceType.POLICY.value,
        "v3.1",
        "Customer Support",
        "Board",
        tuple(GRIEVANCE_PAGES),
    ),
    PolicySpec(
        "Know Your Customer Policy",
        "payflow-kyc-policy.pdf",
        EvidenceType.POLICY.value,
        "v2.0",
        "Compliance",
        "Board",
        tuple(KYC_PAGES),
    ),
    PolicySpec(
        "Merchant Settlement Procedure",
        "payflow-settlement-procedure.pdf",
        EvidenceType.PROCEDURE.value,
        "v2.4",
        "Operations",
        "CFO",
        tuple(SETTLEMENT_PAGES),
    ),
    PolicySpec(
        "Payment System Data Localisation Policy",
        "payflow-data-localisation.pdf",
        EvidenceType.POLICY.value,
        "v1.2",
        "Information Security",
        "CISO",
        tuple(DATA_PAGES),
    ),
    PolicySpec(
        "Card Tokenisation Procedure",
        "payflow-card-tokenisation.pdf",
        EvidenceType.PROCEDURE.value,
        "v1.0",
        "Product",
        "CISO",
        tuple(TOKEN_PAGES),
    ),
    PolicySpec(
        "Failed Transaction TAT SOP",
        "payflow-failed-txn-tat.pdf",
        EvidenceType.PROCEDURE.value,
        "v1.1",
        "Operations",
        "Compliance",
        tuple(TAT_PAGES),
    ),
    PolicySpec(
        "Information Security Policy",
        "payflow-information-security.pdf",
        EvidenceType.POLICY.value,
        "v4.0",
        "Information Security",
        "Board",
        tuple(SECURITY_PAGES),
    ),
    PolicySpec(
        "IT Outsourcing Policy",
        "payflow-it-outsourcing.pdf",
        EvidenceType.POLICY.value,
        "v2.0",
        "Engineering",
        "Board",
        tuple(OUTSOURCING_PAGES),
    ),
    PolicySpec(
        "Internal Ombudsman Charter",
        "payflow-internal-ombudsman.pdf",
        EvidenceType.POLICY.value,
        "v1.0",
        "Compliance",
        "Board",
        tuple(OMBUDSMAN_PAGES),
    ),
)


def regulation_pdf() -> bytes:
    return build_text_pdf(REGULATION_PAGES)


def grievance_pdf() -> bytes:
    return build_text_pdf(GRIEVANCE_PAGES)


def kyc_pdf() -> bytes:
    return build_text_pdf(KYC_PAGES)
