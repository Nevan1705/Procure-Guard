"""Core domain enums for ProcureGuard.

Implements PRD FR-09 (four-state verification model) and FR-10 (risk levels).
"""
from enum import Enum


class VerificationState(str, Enum):
    """The four-state verification model (PRD FR-09).

    Unverifiable must NEVER be collapsed into Verified.
    """
    VERIFIED = "VERIFIED"
    REVIEW = "REVIEW"
    NON_COMPLIANT = "NON_COMPLIANT"
    UNVERIFIABLE = "UNVERIFIABLE"


class RiskLevel(str, Enum):
    """Normalized risk levels (PRD FR-10). Decision-support signal only."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DocumentType(str, Enum):
    """Document categories (PRD FR-03)."""
    PAN = "PAN"
    GST_CERTIFICATE = "GST_CERTIFICATE"
    UDYAM_CERTIFICATE = "UDYAM_CERTIFICATE"
    INCOME_TAX_EVIDENCE = "INCOME_TAX_EVIDENCE"
    EPFO_ESIC = "EPFO_ESIC"
    STARTUP_INDIA = "STARTUP_INDIA"
    NSIC = "NSIC"
    OEM_AUTHORIZATION = "OEM_AUTHORIZATION"
    LOCAL_CONTENT_DECLARATION = "LOCAL_CONTENT_DECLARATION"
    DECLARATION = "DECLARATION"
    OTHER = "OTHER"


class RequirementCategory(str, Enum):
    """Requirement categories (PRD FR-02)."""
    REGISTRATION = "REGISTRATION"
    TAX_COMPLIANCE = "TAX_COMPLIANCE"
    FINANCIAL_ELIGIBILITY = "FINANCIAL_ELIGIBILITY"
    LOCAL_CONTENT = "LOCAL_CONTENT"
    OEM_AUTHORIZATION = "OEM_AUTHORIZATION"
    LABOUR_COMPLIANCE = "LABOUR_COMPLIANCE"
    STARTUP_MSME_BENEFIT = "STARTUP_MSME_BENEFIT"
    BLACKLISTING = "BLACKLISTING"
    DECLARATION = "DECLARATION"


class SourceType(str, Enum):
    """Official source families (PRD FR-06)."""
    GST = "GST"
    UDYAM = "UDYAM"
    MCA = "MCA"
    INCOME_TAX = "INCOME_TAX"
    EPFO = "EPFO"
    ESIC = "ESIC"
    STARTUP_INDIA = "STARTUP_INDIA"
    NSIC = "NSIC"
    DIGILOCKER = "DIGILOCKER"
    OEM = "OEM"
    BLACKLIST = "BLACKLIST"


class SourceStatus(str, Enum):
    """Normalized adapter outcome (PRD FR-06 source result model).

    Technical failure (timeout/unavailable) must map to UNAVAILABLE,
    which downstream becomes UNVERIFIABLE — never NON_COMPLIANT (PRD §17).
    """
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    NOT_FOUND = "NOT_FOUND"
    EXPIRED = "EXPIRED"
    MISMATCH = "MISMATCH"
    UNAVAILABLE = "UNAVAILABLE"


class CrossValidationResult(str, Enum):
    """Cross-validation outcomes (PRD FR-07)."""
    MATCH = "MATCH"
    MINOR_MISMATCH = "MINOR_MISMATCH"
    MATERIAL_MISMATCH = "MATERIAL_MISMATCH"
    MISSING = "MISSING"
    EXPIRED = "EXPIRED"
    DUPLICATE = "DUPLICATE"
    UNVERIFIABLE = "UNVERIFIABLE"


class TenderStatus(str, Enum):
    DRAFT = "DRAFT"
    ANALYZED = "ANALYZED"
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class BidStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    PROCESSING = "PROCESSING"
    VERIFIED_DONE = "VERIFIED_DONE"
    UNDER_REVIEW = "UNDER_REVIEW"
    DECIDED = "DECIDED"


class OverallRecommendation(str, Enum):
    """Top-level recommendation shown to the officer (PRD FR-12)."""
    QUALIFY = "QUALIFY"
    REVIEW = "REVIEW"
    DISQUALIFY = "DISQUALIFY"
