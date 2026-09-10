"""Audit trail APIs (PRD FR-17)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.db.models import AuditEvent, Bid, Tender

router = APIRouter(prefix="/api", tags=["audit"])


@router.get("/bids/{bid_id}/audit")
def bid_audit(bid_id: int, db: Session = Depends(get_db)):
    bid = db.get(Bid, bid_id)
    if not bid:
        raise HTTPException(404, "Bid not found")
    events = (
        db.query(AuditEvent)
        .filter(AuditEvent.entity_type == "bid", AuditEvent.entity_id == str(bid_id))
        .order_by(AuditEvent.created_at.asc())
        .all()
    )
    return [_serialize(e) for e in events]


@router.get("/tenders/{tender_id}/audit")
def tender_audit(tender_id: int, db: Session = Depends(get_db)):
    tender = db.get(Tender, tender_id)
    if not tender:
        raise HTTPException(404, "Tender not found")
    events = (
        db.query(AuditEvent)
        .filter(AuditEvent.entity_type == "tender", AuditEvent.entity_id == str(tender_id))
        .order_by(AuditEvent.created_at.asc())
        .all()
    )
    return [_serialize(e) for e in events]


def _serialize(e: AuditEvent) -> dict:
    import json

    return {
        "id": e.id,
        "actor_type": e.actor_type,
        "actor_id": e.actor_id,
        "event_type": e.event_type,
        "entity_type": e.entity_type,
        "entity_id": e.entity_id,
        "correlation_id": e.correlation_id,
        "payload_hash": e.payload_hash,
        "details": json.loads(e.details_json) if e.details_json else None,
        "created_at": e.created_at.isoformat(),
    }
