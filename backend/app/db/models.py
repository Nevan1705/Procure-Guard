"""SQLAlchemy models implementing the PRD §11 data model."""
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import (
    BidStatus,
    DocumentType,
    OverallRecommendation,
    RequirementCategory,
    RiskLevel,
    SourceStatus,
    SourceType,
    TenderStatus,
    VerificationState,
)
from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Tender(Base):
    __tablename__ = "tenders"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference_number: Mapped[str] = mapped_column(String(64), unique=True)
    title: Mapped[str] = mapped_column(String(255))
    status: Mapped[TenderStatus] = mapped_column(
        Enum(TenderStatus), default=TenderStatus.DRAFT
    )
    created_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    version: Mapped[int] = mapped_column(Integer, default=1)

    requirements: Mapped[list["Requirement"]] = relationship(
        back_populates="tender", cascade="all, delete-orphan"
    )
    bids: Mapped[list["Bid"]] = relationship(back_populates="tender")
    documents: Mapped[list["Document"]] = relationship(
        back_populates="tender",
        foreign_keys="Document.tender_id",
        cascade="all, delete-orphan",
    )


class Requirement(Base):
    __tablename__ = "requirements"

    id: Mapped[int] = mapped_column(primary_key=True)
    tender_id: Mapped[int] = mapped_column(ForeignKey("tenders.id"))
    code: Mapped[str] = mapped_column(String(32))  # e.g. REQ-GST-001
    category: Mapped[RequirementCategory] = mapped_column(Enum(RequirementCategory))
    description: Mapped[str] = mapped_column(Text)
    applicability_rule: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mandatory: Mapped[bool] = mapped_column(Boolean, default=True)
    source_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rule_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    extraction_confidence: Mapped[float] = mapped_column(Float, default=1.0)
    status: Mapped[str | None] = mapped_column(String(32), nullable=True)

    tender: Mapped["Tender"] = relationship(back_populates="requirements")
    checks: Mapped[list["ComplianceCheck"]] = relationship(back_populates="requirement")


class Bidder(Base):
    __tablename__ = "bidders"

    id: Mapped[int] = mapped_column(primary_key=True)
    legal_name: Mapped[str] = mapped_column(String(255))
    pan: Mapped[str | None] = mapped_column(String(16), nullable=True)
    cin: Mapped[str | None] = mapped_column(String(32), nullable=True)
    gstin: Mapped[str | None] = mapped_column(String(20), nullable=True)
    udyam_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    bids: Mapped[list["Bid"]] = relationship(back_populates="bidder")


class Bid(Base):
    __tablename__ = "bids"

    id: Mapped[int] = mapped_column(primary_key=True)
    tender_id: Mapped[int] = mapped_column(ForeignKey("tenders.id"))
    bidder_id: Mapped[int] = mapped_column(ForeignKey("bidders.id"))
    submission_reference: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[BidStatus] = mapped_column(Enum(BidStatus), default=BidStatus.SUBMITTED)
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    tender: Mapped["Tender"] = relationship(back_populates="bids")
    bidder: Mapped["Bidder"] = relationship(back_populates="bids")
    documents: Mapped[list["Document"]] = relationship(
        back_populates="bid", foreign_keys="Document.bid_id"
    )
    checks: Mapped[list["ComplianceCheck"]] = relationship(back_populates="bid")
    review_actions: Mapped[list["ReviewAction"]] = relationship(back_populates="bid")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    tender_id: Mapped[int | None] = mapped_column(
        ForeignKey("tenders.id"), nullable=True
    )
    bid_id: Mapped[int | None] = mapped_column(ForeignKey("bids.id"), nullable=True)
    type: Mapped[DocumentType] = mapped_column(Enum(DocumentType))
    filename: Mapped[str] = mapped_column(String(255))
    storage_uri: Mapped[str] = mapped_column(String(512))
    hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    ocr_status: Mapped[str | None] = mapped_column(String(32), default="PENDING")
    classification_confidence: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    tender: Mapped["Tender | None"] = relationship(
        back_populates="documents", foreign_keys=[tender_id]
    )
    bid: Mapped["Bid | None"] = relationship(
        back_populates="documents", foreign_keys=[bid_id]
    )
    extracted_fields: Mapped[list["ExtractedField"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class ExtractedField(Base):
    __tablename__ = "extracted_fields"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    field_name: Mapped[str] = mapped_column(String(64))
    field_value: Mapped[str] = mapped_column(Text)
    normalized_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    page_number: Mapped[int] = mapped_column(Integer, default=1)
    bounding_box: Mapped[str | None] = mapped_column(String(255), nullable=True)
    evidence_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    document: Mapped["Document"] = relationship(back_populates="extracted_fields")


class SourceVerification(Base):
    __tablename__ = "source_verifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    bidder_id: Mapped[int] = mapped_column(ForeignKey("bidders.id"))
    bid_id: Mapped[int | None] = mapped_column(ForeignKey("bids.id"), nullable=True)
    source_type: Mapped[SourceType] = mapped_column(Enum(SourceType))
    subject_identifier: Mapped[str] = mapped_column(String(128))
    request_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[SourceStatus] = mapped_column(Enum(SourceStatus))
    response_payload_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    simulated: Mapped[bool] = mapped_column(Boolean, default=True)
    queried_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    freshness: Mapped[str | None] = mapped_column(String(64), nullable=True)

    bidder: Mapped["Bidder"] = relationship()
    bid: Mapped["Bid | None"] = relationship()


class ComplianceCheck(Base):
    __tablename__ = "compliance_checks"

    id: Mapped[int] = mapped_column(primary_key=True)
    bid_id: Mapped[int] = mapped_column(ForeignKey("bids.id"))
    requirement_id: Mapped[int] = mapped_column(ForeignKey("requirements.id"))
    state: Mapped[VerificationState] = mapped_column(Enum(VerificationState))
    score: Mapped[float] = mapped_column(Float, default=0.0)
    severity: Mapped[RiskLevel] = mapped_column(Enum(RiskLevel), default=RiskLevel.LOW)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    rule_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    bid: Mapped["Bid"] = relationship(back_populates="checks")
    requirement: Mapped["Requirement"] = relationship(back_populates="checks")
    evidence: Mapped[list["Evidence"]] = relationship(
        back_populates="check", cascade="all, delete-orphan"
    )
    review_actions: Mapped[list["ReviewAction"]] = relationship(back_populates="check")


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(primary_key=True)
    check_id: Mapped[int] = mapped_column(ForeignKey("compliance_checks.id"))
    type: Mapped[str] = mapped_column(String(32))  # DOCUMENT | OFFICIAL_SOURCE
    source: Mapped[str] = mapped_column(String(64))
    reference: Mapped[str] = mapped_column(String(255))
    snapshot_uri: Mapped[str | None] = mapped_column(String(512), nullable=True)
    page_or_locator: Mapped[str | None] = mapped_column(String(255), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    check: Mapped["ComplianceCheck"] = relationship(back_populates="evidence")


class ReviewAction(Base):
    __tablename__ = "review_actions"

    id: Mapped[int] = mapped_column(primary_key=True)
    bid_id: Mapped[int] = mapped_column(ForeignKey("bids.id"))
    check_id: Mapped[int | None] = mapped_column(
        ForeignKey("compliance_checks.id"), nullable=True
    )
    user_id: Mapped[str] = mapped_column(String(64))
    previous_state: Mapped[str | None] = mapped_column(String(32), nullable=True)
    new_state: Mapped[str | None] = mapped_column(String(32), nullable=True)
    action: Mapped[str] = mapped_column(String(32))
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    bid: Mapped["Bid"] = relationship(back_populates="review_actions")
    check: Mapped["ComplianceCheck | None"] = relationship(
        back_populates="review_actions"
    )


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_type: Mapped[str] = mapped_column(String(32))  # SYSTEM | USER
    actor_id: Mapped[str] = mapped_column(String(64))
    event_type: Mapped[str] = mapped_column(String(64))
    entity_type: Mapped[str] = mapped_column(String(64))
    entity_id: Mapped[str] = mapped_column(String(64))
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    details_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Clarification(Base):
    __tablename__ = "clarifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    bid_id: Mapped[int] = mapped_column(ForeignKey("bids.id"))
    requirement_id: Mapped[int | None] = mapped_column(
        ForeignKey("requirements.id"), nullable=True
    )
    draft_text: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="DRAFT")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
