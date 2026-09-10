"""Officer review APIs (PRD FR-16). Officer is the final decision-maker."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record_audit_event
from app.core.enums import BidStatus, VerificationState
from app.db.base import get_db
from app.db.models import Bid, Clarification, ComplianceCheck, ReviewAction
from app.schemas.api import FinalDecisionIn, ReviewActionIn
from app.services.recommendation import generate_clarification_draft

router = APIRouter(prefix="/api", tags=["review"])


@router.post("/checks/{check_id}/review")
def review_check(check_id: int, payload: ReviewActionIn, db: Session = Depends(get_db)):
    """Record an officer review action with a mandatory reason (PRD FR-16)."""
    check = db.get(ComplianceCheck, check_id)
    if not check:
        raise HTTPException(404, "Check not found")

    action = ReviewAction(
        bid_id=check.bid_id,
        check_id=check.id,
        user_id="officer-demo",
        previous_state=check.state.value,
        new_state=payload.new_state.value if payload.new_state else None,
        action=payload.action,
        reason=payload.reason,
        notes=payload.notes,
    )
    db.add(action)

    if payload.new_state:
        check.state = payload.new_state

    record_audit_event(
        db, "OFFICER_REVIEW", "bid", check.bid_id,
        actor_type="USER", actor_id="officer-demo",
        details={
            "check_id": check.id,
            "action": payload.action,
            "previous_state": action.previous_state,
            "new_state": action.new_state,
            "reason": payload.reason,
        },
    )
    db.commit()
    return {"status": "recorded", "check_id": check.id, "state": check.state.value}


@router.post("/checks/{check_id}/override")
def override_check(check_id: int, payload: ReviewActionIn, db: Session = Depends(get_db)):
    """Officer override with full before/after capture (PRD FR-16)."""
    check = db.get(ComplianceCheck, check_id)
    if not check:
        raise HTTPException(404, "Check not found")
    if not payload.new_state:
        raise HTTPException(422, "Override requires new_state")

    action = ReviewAction(
        bid_id=check.bid_id,
        check_id=check.id,
        user_id="officer-demo",
        previous_state=check.state.value,
        new_state=payload.new_state.value,
        action="OVERRIDE",
        reason=payload.reason,
        notes=payload.notes,
    )
    db.add(action)
    check.state = payload.new_state
    record_audit_event(
        db, "OFFICER_OVERRIDE", "bid", check.bid_id,
        actor_type="USER", actor_id="officer-demo",
        details={
            "check_id": check.id,
            "previous_state": action.previous_state,
            "new_state": action.new_state,
            "reason": payload.reason,
        },
    )
    db.commit()
    return {"status": "overridden", "check_id": check.id, "state": check.state.value}


@router.post("/bids/{bid_id}/clarifications", status_code=201)
def create_clarification(bid_id: int, payload: ReviewActionIn,
                         db: Session = Depends(get_db)):
    """Generate a clarification draft for a specific check (PRD FR-13)."""
    bid = db.get(Bid, bid_id)
    if not bid:
        raise HTTPException(404, "Bid not found")

    requirement = None
    check = None
    if payload.notes and payload.notes.isdigit():
        check = db.get(ComplianceCheck, int(payload.notes))
        if check and check.bid_id == bid_id:
            requirement = check.requirement

    if not requirement:
        raise HTTPException(422, "Provide the check id in 'notes' to target a requirement")

    draft = Clarification(
        bid_id=bid_id,
        requirement_id=requirement.id,
        draft_text=generate_clarification_draft(requirement, check.reason or payload.reason),
        status="DRAFT",
    )
    db.add(draft)
    record_audit_event(db, "CLARIFICATION_DRAFTED", "bid", bid_id,
                       details={"requirement": requirement.code})
    db.commit()
    return {"id": draft.id, "draft_text": draft.draft_text, "status": draft.status}


@router.get("/bids/{bid_id}/clarifications")
def list_clarifications(bid_id: int, db: Session = Depends(get_db)):
    rows = db.query(Clarification).filter(Clarification.bid_id == bid_id).all()
    return [
        {"id": c.id, "requirement_code": None, "draft_text": c.draft_text, "status": c.status}
        for c in rows
    ]


@router.post("/bids/{bid_id}/final-decision")
def final_decision(bid_id: int, payload: FinalDecisionIn, db: Session = Depends(get_db)):
    """Record the officer's final qualification decision (PRD FR-16)."""
    bid = db.get(Bid, bid_id)
    if not bid:
        raise HTTPException(404, "Bid not found")
    if payload.decision not in ("QUALIFIED", "DISQUALIFIED"):
        raise HTTPException(422, "decision must be QUALIFIED or DISQUALIFIED")

    action = ReviewAction(
        bid_id=bid_id,
        check_id=None,
        user_id="officer-demo",
        action="FINAL_DECISION",
        new_state=payload.decision,
        reason=payload.reason,
    )
    db.add(action)
    bid.status = BidStatus.DECIDED

    record_audit_event(
        db, "FINAL_DECISION", "bid", bid_id,
        actor_type="USER", actor_id="officer-demo",
        details={"decision": payload.decision, "reason": payload.reason},
    )
    db.commit()
    return {"status": "recorded", "bid_id": bid_id, "decision": payload.decision}
