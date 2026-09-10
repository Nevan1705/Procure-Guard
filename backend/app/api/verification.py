"""Verification + mock-source APIs (PRD §12, §16)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.enums import SourceType
from app.db.base import get_db
from app.db.models import Bid, ComplianceCheck
from app.services.adapters import get_adapter
from app.services.verification import run_verification

router = APIRouter(prefix="/api", tags=["verification"])


@router.post("/bids/{bid_id}/verify")
def verify_bid(bid_id: int, db: Session = Depends(get_db)):
    """Run the full verification pipeline for a bid (PRD §15)."""
    bid = db.get(Bid, bid_id)
    if not bid:
        raise HTTPException(404, "Bid not found")
    return run_verification(db, bid)


@router.get("/bids/{bid_id}/verifications")
def list_verifications(bid_id: int, db: Session = Depends(get_db)):
    all_checks = (
        db.query(ComplianceCheck)
        .filter(ComplianceCheck.bid_id == bid_id)
        .order_by(ComplianceCheck.created_at.asc())
        .all()
    )
    return [
        {
            "check_id": c.id,
            "requirement_code": c.requirement.code,
            "state": c.state.value,
            "score": c.score,
            "severity": c.severity.value,
            "reason": c.reason,
            "rule_version": c.rule_version,
            "confidence": c.confidence,
            "correlation_id": c.correlation_id,
            "created_at": c.created_at.isoformat(),
        }
        for c in all_checks
    ]


@router.get("/verifications/{verification_id}")
def get_verification(verification_id: int, db: Session = Depends(get_db)):
    c = db.get(ComplianceCheck, verification_id)
    if not c:
        raise HTTPException(404, "Verification not found")
    return {
        "check_id": c.id,
        "bid_id": c.bid_id,
        "requirement_code": c.requirement.code,
        "requirement_description": c.requirement.description,
        "state": c.state.value,
        "score": c.score,
        "severity": c.severity.value,
        "reason": c.reason,
        "rule_version": c.rule_version,
        "confidence": c.confidence,
        "correlation_id": c.correlation_id,
        "evidence": [
            {
                "id": e.id,
                "type": e.type,
                "source": e.source,
                "reference": e.reference,
                "page_or_locator": e.page_or_locator,
                "timestamp": e.timestamp.isoformat(),
            }
            for e in c.evidence
        ],
    }


# ---------------------------------------------------------------- mock playground

mock_router = APIRouter(prefix="/api/mock", tags=["mock-sources"])


@mock_router.get("/sources")
def list_mock_sources():
    return {
        "sources": [s.value for s in SourceType],
        "note": "Mock endpoints are simulated (simulated=true) per PRD §16.",
    }


@mock_router.get("/{source}/verify")
def mock_verify(source: str, identifier: str, db: Session = Depends(get_db)):
    """Mock source playground (PRD §16) — clearly labelled simulated."""
    try:
        source_type = SourceType(source.upper())
    except ValueError:
        raise HTTPException(404, f"Unknown source '{source}'")

    if source_type not in (SourceType.GST, SourceType.UDYAM, SourceType.MCA):
        raise HTTPException(501, f"Adapter for {source_type.value} not implemented in MVP")

    adapter = get_adapter(source_type)
    result = adapter.verify(identifier)
    return {"simulated": True, **result.to_dict()}
