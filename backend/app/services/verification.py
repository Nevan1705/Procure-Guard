"""Verification pipeline orchestration (PRD §15 evaluation sequence).

Runs synchronously for the MVP. Each stage is a separate function so stages
can move to a job/queue worker later (PRD NFR-06).
"""
import json
import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.core.audit import record_audit_event
from app.core.config import LOW_CONFIDENCE_THRESHOLD
from app.core.enums import (
    BidStatus,
    CrossValidationResult,
    DocumentType,
    RequirementCategory,
    SourceType,
    VerificationState,
)
from app.db.models import (
    Bid,
    Bidder,
    ComplianceCheck,
    Document,
    Evidence,
    ExtractedField,
    Requirement,
    SourceVerification,
)
from app.services.adapters import get_adapter
from app.services.adapters.base import SourceResult
from app.services.crossval import compare_identifier, compare_validity
from app.services.rules import RuleEngine
from app.services.scoring import compute_compliance_score
from app.services.recommendation import generate_clarification_draft, generate_recommendation

# Requirement category → source type + identifier field used to query it.
CATEGORY_SOURCE_MAP: dict[str, tuple[SourceType, str]] = {
    RequirementCategory.REGISTRATION.value: (SourceType.GST, "gstin"),
    RequirementCategory.TAX_COMPLIANCE.value: (SourceType.GST, "gstin"),
    RequirementCategory.STARTUP_MSME_BENEFIT.value: (SourceType.UDYAM, "udyam_id"),
    RequirementCategory.OEM_AUTHORIZATION.value: (SourceType.OEM, "gstin"),
    RequirementCategory.BLACKLISTING.value: (SourceType.BLACKLIST, "legal_name"),
    RequirementCategory.LOCAL_CONTENT.value: (None, None),  # document-only rule
    RequirementCategory.FINANCIAL_ELIGIBILITY.value: (None, None),
    RequirementCategory.DECLARATION.value: (None, None),
}

RULE_ENGINE = RuleEngine()


def _fields_map(doc: Document) -> dict:
    return {f.field_name: (f.normalized_value or f.field_value) for f in doc.extracted_fields}


def _source_type_for(category: str) -> SourceType | None:
    entry = CATEGORY_SOURCE_MAP.get(category)
    return entry[0] if entry else None


def _identifier_for(category: str, fields: dict, bidder: Bidder) -> str | None:
    entry = CATEGORY_SOURCE_MAP.get(category)
    if not entry or not entry[1]:
        return None
    return fields.get(entry[1]) or getattr(bidder, entry[1], None)


def _query_source(category: str, fields: dict, bidder: Bidder,
                  db: Session, bid: Bid, correlation_id: str) -> SourceResult | None:
    source_type = _source_type_for(category)
    if source_type is None:
        return None

    identifier = _identifier_for(category, fields, bidder)
    if not identifier:
        # No identifier extracted ⇒ cannot query ⇒ UNVERIFIABLE semantics.
        return SourceResult(
            source=source_type.value,
            subject_identifier="",
            status="NOT_PROVIDED",
            error="No identifier available to query the source.",
        )

    adapter = get_adapter(source_type)
    result = adapter.verify(identifier)

    db.add(SourceVerification(
        bidder_id=bid.bidder_id,
        bid_id=bid.id,
        source_type=source_type,
        subject_identifier=identifier,
        request_reference=correlation_id,
        status=result.status,
        response_payload_reference=json.dumps(result.to_dict())[:250],
        simulated=result.simulated,
        freshness=result.freshness,
    ))
    record_audit_event(
        db, "SOURCE_QUERIED", "bid", bid.id,
        correlation_id=correlation_id,
        details={"source": result.source, "status": result.status,
                 "identifier": identifier, "simulated": result.simulated},
    )
    return result


def _evaluate_requirement(requirement: Requirement, docs: list[Document],
                          bidder: Bidder, db: Session, bid: Bid,
                          correlation_id: str) -> ComplianceCheck:
    # Gather extracted fields across the bid's documents.
    fields: dict = {}
    for doc in docs:
        fields.update(_fields_map(doc))

    source = _query_source(requirement.category.value, fields, bidder,
                           db, bid, correlation_id)

    # Local-content declarations: extract a percentage if present.
    if requirement.category.value == RequirementCategory.LOCAL_CONTENT.value:
        for doc in docs:
            for f in doc.extracted_fields:
                if f.field_name == "local_content_percent":
                    fields["local_content_percent"] = f.normalized_value or f.field_value

    out = RULE_ENGINE.evaluate(requirement, fields, source)

    # Identifier cross-validation against the source response (PRD FR-07).
    comparisons = list(out.comparisons)
    if source is not None and source.status not in ("NOT_PROVIDED", "UNAVAILABLE"):
        id_field = _identifier_for(requirement.category.value, fields, bidder)
        if id_field and source.fields:
            src_value = source.fields.get(id_field) or source.fields.get("gstin") \
                or source.fields.get("udyam_id") or source.fields.get("cin")
            if src_value:
                comparisons.append(compare_identifier(
                    id_field, fields.get(id_field), "DOCUMENT",
                    src_value, source.source,
                ))

    # Expiry detection on validity dates (PRD FR-10).
    if source and source.fields.get("valid_upto"):
        comparisons.append(compare_validity(source.fields["valid_upto"], source.source, date.today()))

    # Aggregate worst cross-validation outcome into the final state.
    if comparisons:
        worst, summary = evaluate_comparisons_safe(comparisons)
        if worst == CrossValidationResult.MATERIAL_MISMATCH.value and out.state == VerificationState.VERIFIED:
            out.state = VerificationState.NON_COMPLIANT
            out.score = 0.0
            out.severity = RiskLevel.CRITICAL
            out.reason = f"Cross-validation mismatch: {summary}"
        elif worst == CrossValidationResult.MINOR_MISMATCH.value and out.state == VerificationState.VERIFIED:
            out.state = VerificationState.REVIEW
            out.score = 50.0
            out.severity = RiskLevel.MEDIUM
            out.reason = f"Cross-validation minor mismatch: {summary}"

    check = ComplianceCheck(
        bid_id=bid.id,
        requirement_id=requirement.id,
        state=out.state,
        score=out.score,
        severity=out.severity,
        reason=out.reason,
        rule_version=out.rule_version,
        confidence=out.confidence,
        correlation_id=correlation_id,
    )
    db.add(check)
    db.flush()  # assign check.id for evidence rows

    # Evidence rows (PRD FR-15 evidence chain).
    for doc in docs:
        db.add(Evidence(
            check_id=check.id,
            type="DOCUMENT",
            source=doc.filename,
            reference=f"DOC-{doc.id}",
            snapshot_uri=doc.storage_uri,
            page_or_locator=None,
        ))
    if source is not None:
        db.add(Evidence(
            check_id=check.id,
            type="OFFICIAL_SOURCE",
            source=source.source,
            reference=f"SRC-{correlation_id}-{requirement.code}",
            snapshot_uri=None,
            page_or_locator=json.dumps(source.to_dict())[:250],
        ))

    record_audit_event(
        db, "RULE_EVALUATED", "bid", bid.id,
        correlation_id=correlation_id,
        details={"requirement": requirement.code, "state": out.state.value,
                 "rule": out.rule_version},
    )
    return check


# Imported late to avoid a circular import at module load.
from app.services.crossval import evaluate_comparisons  # noqa: E402
from app.core.enums import RiskLevel  # noqa: E402


def evaluate_comparisons_safe(comparisons):
    return evaluate_comparisons(comparisons)


def run_verification(db: Session, bid: Bid) -> dict:
    """Run the full verification pipeline for a bid (PRD §15)."""
    correlation_id = uuid.uuid4().hex[:12]
    tender = bid.tender
    requirements = [r for r in tender.requirements if r.status != "HIDDEN"]
    bidder = bid.bidder
    docs = bid.documents

    if not requirements:
        return {"error": "Tender has no analyzed requirements. Run tender analysis first."}

    record_audit_event(
        db, "VERIFICATION_STARTED", "bid", bid.id, correlation_id=correlation_id,
        details={"requirements": len(requirements), "documents": len(docs)},
    )

    bid.status = BidStatus.PROCESSING

    checks: list[ComplianceCheck] = []
    for requirement in requirements:
        checks.append(_evaluate_requirement(requirement, docs, bidder, db, bid, correlation_id))

    score_result = compute_compliance_score(checks)
    recommendation = generate_recommendation(checks, score_result)

    # Clarification drafts for non-verified mandatory items (PRD FR-13).
    clarifications = []
    for c in checks:
        if c.requirement.mandatory and c.state in (VerificationState.REVIEW, VerificationState.UNVERIFIABLE):
            text = generate_clarification_draft(c.requirement, c.reason or "Unresolved finding.")
            clarifications.append({"requirement_code": c.requirement.code, "draft": text})

    bid.status = BidStatus.VERIFIED_DONE

    record_audit_event(
        db, "VERIFICATION_COMPLETED", "bid", bid.id, correlation_id=correlation_id,
        details={
            "score": score_result.score,
            "risk": score_result.risk_level.value,
            "states": {s: sum(1 for c in checks if c.state == s)
                       for s in VerificationState},
        },
    )
    db.commit()

    return {
        "bid_id": bid.id,
        "correlation_id": correlation_id,
        "score": score_result.to_dict(),
        "recommendation": recommendation.to_dict(),
        "clarifications": clarifications,
        "checks": [
            {
                "check_id": c.id,
                "requirement_code": c.requirement.code,
                "requirement_description": c.requirement.description,
                "state": c.state.value,
                "severity": c.severity.value,
                "reason": c.reason,
                "rule_version": c.rule_version,
                "confidence": c.confidence,
                "mandatory": c.requirement.mandatory,
            }
            for c in checks
        ],
    }
