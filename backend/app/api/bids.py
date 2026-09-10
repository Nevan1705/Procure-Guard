"""Bid + document intake APIs (PRD FR-03, FR-14)."""
import hashlib
import os

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.audit import record_audit_event
from app.core.config import UPLOAD_DIR
from app.core.enums import BidStatus, DocumentType, VerificationState
from app.db.base import get_db
from app.db.models import (
    Bid,
    Bidder,
    ComplianceCheck,
    Document,
    ExtractedField,
    Tender,
)
from app.schemas.api import (
    BidCreate,
    BidOut,
    CheckOut,
    DashboardOut,
    DocumentOut,
)
from app.services.extraction import extract_fields_from_document
from app.services.recommendation import generate_recommendation
from app.services.scoring import compute_compliance_score

router = APIRouter(prefix="/api", tags=["bids"])


@router.post("/tenders/{tender_id}/bids", response_model=BidOut, status_code=201)
def create_bid(tender_id: int, payload: BidCreate, db: Session = Depends(get_db)):
    tender = db.get(Tender, tender_id)
    if not tender:
        raise HTTPException(404, "Tender not found")

    bidder = Bidder(
        legal_name=payload.bidder.legal_name,
        pan=payload.bidder.pan,
        cin=payload.bidder.cin,
        gstin=payload.bidder.gstin,
        udyam_id=payload.bidder.udyam_id,
        address=payload.bidder.address,
    )
    db.add(bidder)
    db.flush()

    bid = Bid(
        tender_id=tender_id,
        bidder_id=bidder.id,
        submission_reference=payload.submission_reference,
        status=BidStatus.SUBMITTED,
    )
    db.add(bid)
    db.commit()
    record_audit_event(db, "BID_CREATED", "bid", bid.id,
                       details={"bidder": bidder.legal_name})
    db.commit()

    return BidOut(
        id=bid.id, tender_id=bid.tender_id, bidder_id=bid.bidder_id,
        bidder_name=bidder.legal_name, status=bid.status,
        submitted_at=bid.submitted_at, created_at=bid.created_at,
    )


@router.get("/bids", response_model=list[BidOut])
def list_bids(db: Session = Depends(get_db)):
    """List all bids (review queue needs a cross-tender view, PRD Screen 6)."""
    bids = db.query(Bid).order_by(Bid.created_at.desc()).all()
    return [
        BidOut(
            id=b.id, tender_id=b.tender_id, bidder_id=b.bidder_id,
            bidder_name=b.bidder.legal_name, status=b.status,
            submitted_at=b.submitted_at, created_at=b.created_at,
        )
        for b in bids
    ]


@router.get("/bids/{bid_id}", response_model=BidOut)
def get_bid(bid_id: int, db: Session = Depends(get_db)):
    bid = db.get(Bid, bid_id)
    if not bid:
        raise HTTPException(404, "Bid not found")
    return BidOut(
        id=bid.id, tender_id=bid.tender_id, bidder_id=bid.bidder_id,
        bidder_name=bid.bidder.legal_name, status=bid.status,
        submitted_at=bid.submitted_at, created_at=bid.created_at,
    )


@router.post("/bids/{bid_id}/documents", response_model=DocumentOut, status_code=201)
def upload_bid_document(bid_id: int, file: UploadFile, db: Session = Depends(get_db)):
    bid = db.get(Bid, bid_id)
    if not bid:
        raise HTTPException(404, "Bid not found")

    target_dir = os.path.join(UPLOAD_DIR, "bids", str(bid_id))
    os.makedirs(target_dir, exist_ok=True)
    safe_name = (file.filename or "document.bin").replace("/", "_").replace("\\", "_")
    path = os.path.join(target_dir, safe_name)
    content = file.file.read()
    with open(path, "wb") as f:
        f.write(content)
    digest = hashlib.sha256(content).hexdigest()

    # Duplicate detection by content hash (PRD FR-03).
    duplicate = db.query(Document).filter(
        Document.bid_id == bid_id, Document.hash == digest
    ).first()

    doc = Document(
        bid_id=bid_id,
        type=DocumentType.OTHER,
        filename=file.filename or safe_name,
        storage_uri=path,
        hash=digest,
        mime_type=file.content_type,
        ocr_status="PENDING",
    )
    db.add(doc)
    db.flush()

    # Stub extraction pipeline (PRD FR-04): classify + extract fields.
    extraction = extract_fields_from_document(file.filename or "", text=None)
    doc.type = extraction.document_type
    doc.classification_confidence = extraction.classification_confidence
    doc.ocr_status = "PROCESSED_STUB"
    for f in extraction.fields:
        db.add(ExtractedField(
            document_id=doc.id,
            field_name=f.field_name,
            field_value=f.field_value,
            normalized_value=f.normalized_value,
            confidence=f.confidence,
            page_number=f.page_number,
            evidence_text=f.evidence_text,
        ))

    db.commit()
    record_audit_event(db, "DOCUMENT_UPLOADED", "bid", bid_id,
                       details={"document_id": doc.id, "filename": doc.filename,
                                "duplicate_of": duplicate.id if duplicate else None,
                                "type": doc.type.value})
    db.commit()
    return doc


@router.get("/bids/{bid_id}/documents", response_model=list[DocumentOut])
def list_bid_documents(bid_id: int, db: Session = Depends(get_db)):
    bid = db.get(Bid, bid_id)
    if not bid:
        raise HTTPException(404, "Bid not found")
    return bid.documents


@router.get("/bids/{bid_id}/dashboard", response_model=DashboardOut)
def bid_dashboard(bid_id: int, db: Session = Depends(get_db)):
    """Bid-level compliance dashboard (PRD FR-14)."""
    bid = db.get(Bid, bid_id)
    if not bid:
        raise HTTPException(404, "Bid not found")

    all_checks: list[ComplianceCheck] = (
        db.query(ComplianceCheck)
        .filter(ComplianceCheck.bid_id == bid_id)
        .order_by(ComplianceCheck.created_at.asc())
        .all()
    )
    # Latest check per requirement (officer overrides included via review actions).
    latest: dict[int, ComplianceCheck] = {}
    for c in all_checks:
        latest[c.requirement_id] = c
    latest_checks = list(latest.values())

    counts = {s.value: 0 for s in VerificationState}
    for c in latest_checks:
        counts[c.state.value] += 1

    score = compute_compliance_score(latest_checks)
    recommendation = generate_recommendation(latest_checks, score)

    mandatory_docs = {
        DocumentType.PAN, DocumentType.GST_CERTIFICATE, DocumentType.UDYAM_CERTIFICATE,
    }
    doc_types = {d.type for d in bid.documents}
    missing_documents = len(mandatory_docs - doc_types)

    expired_count = sum(
        1 for c in latest_checks
        for e in c.evidence
        if "expired" in (e.page_or_locator or "").lower()
    )

    return DashboardOut(
        bid_id=bid.id,
        bidder_name=bid.bidder.legal_name,
        tender_reference=bid.tender.reference_number,
        compliance_score=round(score.score, 1),
        risk_level=score.risk_level.value,
        overall_recommendation=recommendation.overall_state,
        counts=counts,
        missing_document_count=missing_documents,
        expired_document_count=expired_count,
        checks=[
            CheckOut(
                id=c.id,
                requirement_code=c.requirement.code,
                requirement_description=c.requirement.description,
                state=c.state,
                severity=c.severity.value,
                reason=c.reason,
                rule_version=c.rule_version,
                confidence=c.confidence,
                mandatory=c.requirement.mandatory,
            )
            for c in latest_checks
        ],
        recommendation=recommendation.to_dict(),
    )
