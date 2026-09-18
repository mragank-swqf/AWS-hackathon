"""Demo documents for PayFlow Technologies (spec 16)."""

from __future__ import annotations

from uuid import UUID

from app.services.pdf import build_text_pdf

DEMO_COMPANY_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")

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
Customers may file a complaint through the in-app form or email. A ticket number is issued.

2 Grievance officer
A named grievance officer in Compliance owns the queue.

3 Documented process
PayFlow maintains this documented grievance redressal process for merchant and consumer complaints.
""",
    """4 Records
An audit trail of tickets is retained for 8 years.

This policy does not state an escalation timeline or a 48-hour turnaround.
""",
]

KYC_PAGES = [
    """PayFlow Technologies
Know Your Customer Policy
Owner: Compliance

1 Purpose
This KYC policy describes customer identification for merchants onboarded onto the PayFlow platform.

2 Controls
Access reviews and audit logging apply to KYC records.
""",
]


def regulation_pdf() -> bytes:
    return build_text_pdf(REGULATION_PAGES)


def grievance_pdf() -> bytes:
    return build_text_pdf(GRIEVANCE_PAGES)


def kyc_pdf() -> bytes:
    return build_text_pdf(KYC_PAGES)
