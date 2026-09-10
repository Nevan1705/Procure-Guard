"""Audit event recorder (PRD FR-17). Append-only by design."""
import hashlib
import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models import AuditEvent


def record_audit_event(
    db: Session,
    event_type: str,
    entity_type: str,
    entity_id: str | int,
    actor_type: str = "SYSTEM",
    actor_id: str = "procureguard-engine",
    correlation_id: str | None = None,
    details: dict | None = None,
) -> AuditEvent:
    """Persist an immutable audit event with a payload hash for integrity."""
    payload = json.dumps(details or {}, sort_keys=True, default=str)
    payload_hash = hashlib.sha256(payload.encode()).hexdigest()[:32]

    event = AuditEvent(
        actor_type=actor_type,
        actor_id=actor_id,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=str(entity_id),
        correlation_id=correlation_id,
        payload_hash=payload_hash,
        details_json=payload,
        created_at=datetime.now(timezone.utc),
    )
    db.add(event)
    return event
