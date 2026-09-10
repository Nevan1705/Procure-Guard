"""Recommendation engine (PRD FR-12, FR-13).

Template-based and strictly grounded in structured verification results —
the LLM-pluggable variant must follow the same contract: it may rephrase
grounded facts but never invent compliance conclusions (PRD §14, Principle 4).
"""
from dataclasses import dataclass, field

from app.core.enums import OverallRecommendation, VerificationState


@dataclass
class Recommendation:
    overall_state: str
    compliance_score: float
    risk_level: str
    summary: str
    critical_findings: list[str] = field(default_factory=list)
    review_items: list[str] = field(default_factory=list)
    unverifiable_items: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    final_decision_authority: str = "PROCUREMENT_OFFICER"

    def to_dict(self) -> dict:
        return {
            "overall_state": self.overall_state,
            "compliance_score": self.compliance_score,
            "risk_level": self.risk_level,
            "summary": self.summary,
            "critical_findings": self.critical_findings,
            "review_items": self.review_items,
            "unverifiable_items": self.unverifiable_items,
            "next_actions": self.next_actions,
            "final_decision_authority": self.final_decision_authority,
        }


def _label(requirement) -> str:
    code = getattr(requirement, "code", "?")
    desc = getattr(requirement, "description", "")
    return f"{code} — {desc[:80]}"


def generate_recommendation(checks: list, score_result) -> Recommendation:
    """Build the officer-facing recommendation from check rows + score result."""
    critical_findings: list[str] = []
    review_items: list[str] = []
    unverifiable_items: list[str] = []
    next_actions: list[str] = []

    for c in checks:
        label = _label(c.requirement)
        if c.state == VerificationState.NON_COMPLIANT:
            critical_findings.append(f"{label}: {c.reason}")
            if c.requirement.mandatory:
                next_actions.append(
                    f"Assess {c.requirement.code} non-compliance against tender terms."
                )
        elif c.state == VerificationState.REVIEW:
            review_items.append(f"{label}: {c.reason}")
            next_actions.append(f"Review {c.requirement.code} supporting evidence.")
        elif c.state == VerificationState.UNVERIFIABLE:
            unverifiable_items.append(f"{label}: {c.reason}")
            next_actions.append(
                f"Arrange authorized verification for {c.requirement.code} "
                f"(technical failure is not non-compliance)."
            )

    if score_result.mandatory_gate_failed:
        overall = OverallRecommendation.DISQUALIFY.value
        summary = (
            f"Mandatory compliance gate failed ({score_result.summary}) "
            f"Recommendation is decision-support only; the officer decides."
        )
    elif score_result.mandatory_gate_uncertain or review_items or unverifiable_items:
        overall = OverallRecommendation.REVIEW.value
        summary = (
            f"{len(review_items)} review item(s), {len(unverifiable_items)} unverifiable "
            f"item(s). {score_result.summary}"
        )
    else:
        overall = OverallRecommendation.QUALIFY.value
        summary = (
            f"All {len(checks)} checks passed. "
            f"Final qualification remains an officer action."
        )

    return Recommendation(
        overall_state=overall,
        compliance_score=score_result.score,
        risk_level=score_result.risk_level.value,
        summary=summary,
        critical_findings=critical_findings,
        review_items=review_items,
        unverifiable_items=unverifiable_items,
        next_actions=next_actions,
    )


def generate_clarification_draft(requirement, check_reason: str) -> str:
    """Draft a clarification request grounded in the failed/ambiguous check (PRD FR-13)."""
    return (
        f"Subject: Clarification required — {requirement.code}\n\n"
        f"Tender requirement \"{requirement.description}\" "
        f"(reference: {requirement.source_reference or 'n/a'}) "
        f"could not be fully verified.\n\n"
        f"System finding: {check_reason}\n\n"
        f"Please provide supporting evidence or an explanation for the above "
        f"requirement. This request was drafted automatically and is subject to "
        f"officer review before sending."
    )
