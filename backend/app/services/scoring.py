"""Compliance scoring (PRD FR-10, FR-11).

Score = mandatory gate + weighted state scores + risk adjustment.
A mandatory NON_COMPLIANT cannot be hidden by a high weighted score.
"""
from dataclasses import dataclass

from app.core.config import SCORE_BANDS, STATE_SCORES
from app.core.enums import RiskLevel, VerificationState


@dataclass
class ScoreResult:
    score: float
    risk_level: RiskLevel
    mandatory_gate_failed: bool
    mandatory_gate_uncertain: bool
    band: str
    summary: str

    def to_dict(self) -> dict:
        return {
            "score": round(self.score, 1),
            "risk_level": self.risk_level.value,
            "mandatory_gate_failed": self.mandatory_gate_failed,
            "mandatory_gate_uncertain": self.mandatory_gate_uncertain,
            "band": self.band,
            "summary": self.summary,
        }


def _band_for(score: float) -> str:
    if score >= SCORE_BANDS["medium_min"] and score < SCORE_BANDS["low_min"]:
        return "MEDIUM"
    if score >= SCORE_BANDS["low_min"]:
        return "LOW"
    if score >= SCORE_BANDS["high_min"]:
        return "HIGH"
    return "CRITICAL"


def compute_compliance_score(checks: list) -> ScoreResult:
    """checks: ComplianceCheck rows (state, score, severity, requirement)."""
    from app.core.enums import VerificationState as VS

    if not checks:
        return ScoreResult(0.0, RiskLevel.CRITICAL, False, True, "CRITICAL",
                           "No compliance checks have been run yet.")

    mandatory_failed = [c for c in checks
                        if c.requirement.mandatory and c.state == VS.NON_COMPLIANT]
    mandatory_uncertain = [c for c in checks
                           if c.requirement.mandatory and c.state == VS.UNVERIFIABLE]
    mandatory_review = [c for c in checks
                        if c.requirement.mandatory and c.state == VS.REVIEW]

    # Weighted score across all checks.
    weighted = sum(c.score for c in checks) / len(checks)

    # Risk adjustment: severity-weighted penalty for problem states.
    penalty = 0.0
    for c in checks:
        if c.state == VS.NON_COMPLIANT:
            penalty += 12 if c.requirement.mandatory else 5
        elif c.state == VS.UNVERIFIABLE:
            penalty += 8 if c.requirement.mandatory else 3
        elif c.state == VS.REVIEW:
            penalty += 4 if c.requirement.mandatory else 2

    score = max(0.0, min(100.0, weighted - penalty))

    # Mandatory gate overrides the band (PRD FR-11 design principle).
    if mandatory_failed:
        risk = RiskLevel.CRITICAL
        band = "CRITICAL"
        gate_failed = True
        gate_uncertain = False
        summary = (
            f"Mandatory gate FAILED: {len(mandatory_failed)} mandatory requirement(s) "
            f"non-compliant despite weighted score {weighted:.0f}."
        )
    elif mandatory_uncertain:
        risk = RiskLevel.HIGH
        band = "HIGH"
        gate_failed = False
        gate_uncertain = True
        summary = (
            f"Mandatory gate UNCERTAIN: {len(mandatory_uncertain)} mandatory "
            f"requirement(s) unverifiable — officer attention required."
        )
    else:
        gate_failed = False
        gate_uncertain = False
        if mandatory_review:
            risk = RiskLevel.MEDIUM
            band = _band_for(score)
            summary = f"{len(mandatory_review)} mandatory item(s) under review."
        else:
            band = _band_for(score)
            risk = {
                "LOW": RiskLevel.LOW,
                "MEDIUM": RiskLevel.MEDIUM,
                "HIGH": RiskLevel.HIGH,
                "CRITICAL": RiskLevel.CRITICAL,
            }[band]
            summary = "No mandatory gate issues."

    return ScoreResult(score, risk, gate_failed, gate_uncertain, band, summary)
