"""Fixed value lists from spec/04-spec-schema-input-contracts.md section 4.

This is the only code module that defines these lists. Schemas, database
checks, and API validation all import from here.
"""

from __future__ import annotations

from enum import StrEnum


class OrganizationType(StrEnum):
    PAYMENT_AGGREGATOR = "payment_aggregator"
    PAYMENT_GATEWAY = "payment_gateway"
    NBFC = "nbfc"
    LENDING_PLATFORM = "lending_platform"
    PREPAID_INSTRUMENT_ISSUER = "prepaid_instrument_issuer"
    ACCOUNT_AGGREGATOR = "account_aggregator"
    OTHER = "other"


class DocumentType(StrEnum):
    CIRCULAR = "circular"
    MASTER_DIRECTION = "master_direction"
    NOTIFICATION = "notification"
    GUIDELINE = "guideline"
    FAQ = "faq"
    PRESS_RELEASE = "press_release"


class ProcessingStatus(StrEnum):
    QUEUED = "queued"
    EXTRACTING = "extracting"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    COMPLETED = "completed"
    FAILED = "failed"


class ExtractionMethod(StrEnum):
    TEXT = "text"
    UNREADABLE = "unreadable"


class AnalysisStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AnalysisDepth(StrEnum):
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"


class Applicability(StrEnum):
    APPLICABLE = "applicable"
    LIKELY_APPLICABLE = "likely_applicable"
    UNCERTAIN = "uncertain"
    LIKELY_NOT_APPLICABLE = "likely_not_applicable"
    NOT_APPLICABLE = "not_applicable"


class ObligationType(StrEnum):
    MANDATORY = "mandatory"
    RECOMMENDED = "recommended"


class ImpactLevel(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class GapStatus(StrEnum):
    COMPLIANT = "compliant"
    PARTIAL = "partial"
    NON_COMPLIANT = "non_compliant"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class OverallRisk(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class VerificationStatus(StrEnum):
    VERIFIED = "verified"
    PARTIALLY_VERIFIED = "partially_verified"
    UNVERIFIED = "unverified"
    FAILED = "failed"


class ReviewStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ActionStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"


class EvidenceType(StrEnum):
    POLICY = "policy"
    PROCEDURE = "procedure"
    CONTROL_DESCRIPTION = "control_description"
    AUDIT_REPORT = "audit_report"
    OTHER = "other"


class DateBasis(StrEnum):
    CITED_EFFECTIVE = "cited_effective"
    CITED_COMPLIANCE = "cited_compliance"
    INFERRED_RECOMMENDATION = "inferred_recommendation"


class DeadlineProximity(StrEnum):
    OVERDUE = "overdue"
    UNDER_30_DAYS = "under_30_days"
    UNDER_90_DAYS = "under_90_days"
    BEYOND_90_DAYS = "beyond_90_days"
    NONE = "none"


class Effort(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Department(StrEnum):
    COMPLIANCE = "Compliance"
    LEGAL = "Legal"
    RISK = "Risk"
    OPERATIONS = "Operations"
    PRODUCT = "Product"
    ENGINEERING = "Engineering"
    FINANCE = "Finance"
    CUSTOMER_SUPPORT = "Customer Support"
    INFORMATION_SECURITY = "Information Security"
    INTERNAL_AUDIT = "Internal Audit"
    HUMAN_RESOURCES = "Human Resources"


# Chunks-per-search and re-search behaviour from spec 04.
ANALYSIS_DEPTH_CHUNK_LIMIT = {
    AnalysisDepth.QUICK: 10,
    AnalysisDepth.STANDARD: 25,
    AnalysisDepth.DEEP: 50,
}

# "none" | "mandatory" | "all" — re-search per requirement after the first pass.
ANALYSIS_DEPTH_RESEARCH = {
    AnalysisDepth.QUICK: "none",
    AnalysisDepth.STANDARD: "mandatory",
    AnalysisDepth.DEEP: "all",
}

ALL_ENUMS: tuple[type[StrEnum], ...] = (
    OrganizationType,
    DocumentType,
    ProcessingStatus,
    ExtractionMethod,
    AnalysisStatus,
    AnalysisDepth,
    Applicability,
    ObligationType,
    ImpactLevel,
    GapStatus,
    Severity,
    OverallRisk,
    VerificationStatus,
    ReviewStatus,
    ActionStatus,
    EvidenceType,
    DateBasis,
    DeadlineProximity,
    Effort,
    Department,
)


def sql_in_list(enum_cls: type[StrEnum]) -> str:
    return ", ".join(f"'{member.value}'" for member in enum_cls)
