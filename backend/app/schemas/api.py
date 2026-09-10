"""Pydantic schemas for API requests and responses."""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.core.enums import (
    BidStatus,
    DocumentType,
    RequirementCategory,
    TenderStatus,
    VerificationState,
)


# ------------------------------------------------------------------ tenders

class TenderCreate(BaseModel):
    reference_number: str = Field(max_length=64)
    title: str = Field(max_length=255)


class TenderOut(BaseModel):
    id: int
    reference_number: str
    title: str
    status: TenderStatus
    created_at: datetime
    bid_count: int = 0

    model_config = {"from_attributes": True}


class TenderAnalyzeResult(BaseModel):
    tender_id: int
    requirements_extracted: int
    requirements: list[dict]


# ------------------------------------------------------------------ documents

class DocumentOut(BaseModel):
    id: int
    type: DocumentType
    filename: str
    mime_type: Optional[str] = None
    ocr_status: Optional[str] = None
    classification_confidence: float
    created_at: datetime

    model_config = {"from_attributes": True}


# ------------------------------------------------------------------ bidders/bids

class BidderCreate(BaseModel):
    legal_name: str = Field(max_length=255)
    pan: Optional[str] = None
    cin: Optional[str] = None
    gstin: Optional[str] = None
    udyam_id: Optional[str] = None
    address: Optional[str] = None


class BidCreate(BaseModel):
    bidder: BidderCreate
    submission_reference: Optional[str] = None


class BidOut(BaseModel):
    id: int
    tender_id: int
    bidder_id: int
    bidder_name: str = ""
    status: BidStatus
    submitted_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ------------------------------------------------------------------ checks/review

class CheckOut(BaseModel):
    id: int
    requirement_code: str
    requirement_description: str
    state: VerificationState
    severity: str
    reason: Optional[str] = None
    rule_version: Optional[str] = None
    confidence: float
    mandatory: bool = True


class ReviewActionIn(BaseModel):
    action: str  # ACCEPT | MARK_REVIEW | OVERRIDE | REQUEST_CLARIFICATION | FINAL_DECISION
    new_state: Optional[VerificationState] = None
    reason: str = Field(min_length=3)
    notes: Optional[str] = None


class FinalDecisionIn(BaseModel):
    decision: str  # QUALIFIED | DISQUALIFIED
    reason: str = Field(min_length=3)


class ClarificationOut(BaseModel):
    id: int
    requirement_code: Optional[str] = None
    draft_text: str
    status: str


class AuditEventOut(BaseModel):
    id: int
    actor_type: str
    actor_id: str
    event_type: str
    entity_type: str
    entity_id: str
    correlation_id: Optional[str] = None
    details: Optional[dict] = None
    created_at: datetime


class DashboardOut(BaseModel):
    bid_id: int
    bidder_name: str
    tender_reference: str
    compliance_score: float
    risk_level: str
    overall_recommendation: str
    counts: dict[str, int]
    missing_document_count: int
    expired_document_count: int
    checks: list[CheckOut]
    recommendation: Optional[dict] = None


# ------------------------------------------------------------------ mock verify

class MockVerifyOut(BaseModel):
    source: str
    identifier: str
    result: dict[str, Any]
