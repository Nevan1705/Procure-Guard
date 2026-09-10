"""Compliance rule engine (PRD FR-08).

Each rule consumes extracted fields + a SourceResult and emits one of the four
verification states with an explanation. Rules are versioned for reproducibility
(PRD NFR-05).
"""
from app.core.enums import CrossValidationResult, RiskLevel, SourceStatus, VerificationState
from app.services.adapters.base import SourceResult
from app.services.crossval import FieldComparison, compare_identifier, compare_legal_name


class RuleOutput:
    def __init__(self, state: VerificationState, score: float, severity: RiskLevel,
                 reason: str, rule_version: str, confidence: float,
                 comparisons: list[FieldComparison] | None = None):
        self.state = state
        self.score = score
        self.severity = severity
        self.reason = reason
        self.rule_version = rule_version
        self.confidence = confidence
        self.comparisons = comparisons or []

    def to_dict(self) -> dict:
        return {
            "state": self.state.value,
            "score": self.score,
            "severity": self.severity.value,
            "reason": self.reason,
            "rule_version": self.rule_version,
            "confidence": self.confidence,
            "comparisons": [c.to_dict() for c in self.comparisons],
        }


def category_rule_id(requirement) -> str:
    code = getattr(requirement, "code", None) or "RULE"
    return code


class RuleEngine:
    """Evaluates a requirement against extracted fields and a source result."""

    RULE_VERSION = "1.0"

    def evaluate(self, requirement, fields: dict, source: SourceResult | None) -> RuleOutput:
        category = (requirement.category.value
                    if hasattr(requirement.category, "value")
                    else str(requirement.category))
        handler = getattr(self, f"_rule_{category.lower()}", self._rule_generic)
        return handler(requirement, fields, source)

    # ---------------------------------------------------------------- helpers

    def _ver(self, requirement) -> str:
        return f"{category_rule_id(requirement)}@{self.RULE_VERSION}"

    def _unverifiable(self, requirement, source: SourceResult | None, why: str) -> RuleOutput:
        """Technical failure/missing integration ⇒ UNVERIFIABLE (PRD §17)."""
        return RuleOutput(
            VerificationState.UNVERIFIABLE, 40.0, RiskLevel.HIGH,
            why, self._ver(requirement), 0.5,
        )

    def _compare_name(self, requirement, fields: dict, source: SourceResult) -> RuleOutput | None:
        doc_name = fields.get("legal_name")
        src_name = source.fields.get("legal_name") or source.fields.get("enterprise_name")
        if not doc_name or not src_name:
            return None
        cmp = compare_legal_name(doc_name, "DOCUMENT", src_name, source.source)
        return cmp

    def _with_name_check(self, requirement, fields, source, base: RuleOutput) -> RuleOutput:
        """Augment a rule output with legal-name cross-validation."""
        cmp = self._compare_name(requirement, fields, source)
        if cmp is None:
            return base
        comparisons = base.comparisons + [cmp]

        if cmp.result == CrossValidationResult.MATERIAL_MISMATCH:
            return RuleOutput(
                VerificationState.NON_COMPLIANT, 0.0, RiskLevel.CRITICAL,
                f"Legal-name mismatch: {cmp.detail} "
                f"(document: '{cmp.value_a}' vs {source.source}: '{cmp.value_b}').",
                base.rule_version, base.confidence, comparisons,
            )
        if cmp.result == CrossValidationResult.MINOR_MISMATCH:
            return RuleOutput(
                VerificationState.REVIEW, 50.0, RiskLevel.MEDIUM,
                f"Minor legal-name variation requires review: {cmp.detail} "
                f"(document: '{cmp.value_a}' vs {source.source}: '{cmp.value_b}').",
                base.rule_version, base.confidence, comparisons,
            )
        base.comparisons = comparisons
        base.reason = f"{base.reason} Legal name matches."
        return base

    # ------------------------------------------------------------------ rules

    def _rule_generic(self, requirement, fields: dict, source: SourceResult | None) -> RuleOutput:
        if source is None or source.status == SourceStatus.UNAVAILABLE.value:
            return self._unverifiable(requirement, source,
                                      "Official source could not be queried; verification is not possible.")
        if source.status == SourceStatus.ACTIVE.value:
            base = RuleOutput(
                VerificationState.VERIFIED, 100.0, RiskLevel.LOW,
                f"{source.source} record is active in the official registry.",
                self._ver(requirement), 0.95,
            )
            return self._with_name_check(requirement, fields, source, base)
        if source.status == SourceStatus.NOT_FOUND.value:
            return RuleOutput(
                VerificationState.NON_COMPLIANT, 0.0, RiskLevel.HIGH,
                f"Identifier not found in {source.source} registry.",
                self._ver(requirement), 0.9,
            )
        if source.status in (SourceStatus.INACTIVE.value,
                             SourceStatus.EXPIRED.value,
                             SourceStatus.MISMATCH.value):
            return RuleOutput(
                VerificationState.NON_COMPLIANT, 0.0, RiskLevel.HIGH,
                f"{source.source} record status is {source.status}.",
                self._ver(requirement), 0.9,
            )
        return self._unverifiable(requirement, source,
                                  f"Unrecognized source status: {source.status}.")

    def _rule_registration(self, requirement, fields: dict, source: SourceResult | None) -> RuleOutput:
        return self._rule_generic(requirement, fields, source)

    def _rule_tax_compliance(self, requirement, fields: dict, source: SourceResult | None) -> RuleOutput:
        return self._rule_generic(requirement, fields, source)

    def _rule_financial_eligibility(self, requirement, fields: dict, source: SourceResult | None) -> RuleOutput:
        # MVP: no financial source adapter → cannot be verified automatically.
        return self._unverifiable(requirement, source,
                                  "No authorized financial-eligibility source configured for the MVP.")

    def _rule_local_content(self, requirement, fields: dict, source: SourceResult | None) -> RuleOutput:
        value = fields.get("local_content_percent")
        if not value:
            return RuleOutput(
                VerificationState.UNVERIFIABLE, 40.0, RiskLevel.MEDIUM,
                "No local-content percentage could be extracted from the declaration.",
                self._ver(requirement), 0.5,
            )
        try:
            pct = float(str(value).replace("%", "").strip())
        except ValueError:
            return RuleOutput(
                VerificationState.REVIEW, 50.0, RiskLevel.MEDIUM,
                f"Local-content value '{value}' is not parseable; officer must review.",
                self._ver(requirement), 0.4,
            )
        threshold = float(getattr(requirement, "applicability_rule", None) or 50)
        if pct >= threshold:
            return RuleOutput(
                VerificationState.VERIFIED, 100.0, RiskLevel.LOW,
                f"Declared local content {pct:.0f}% meets the {threshold:.0f}% threshold.",
                self._ver(requirement), 0.9,
            )
        return RuleOutput(
            VerificationState.NON_COMPLIANT, 0.0, RiskLevel.HIGH,
            f"Declared local content {pct:.0f}% is below the {threshold:.0f}% threshold.",
            self._ver(requirement), 0.9,
        )

    def _rule_oem_authorization(self, requirement, fields: dict, source: SourceResult | None) -> RuleOutput:
        if source is None or source.status == SourceStatus.UNAVAILABLE.value:
            return self._unverifiable(requirement, source,
                                      "OEM authorization could not be verified against a source.")
        if source.status == SourceStatus.NOT_FOUND.value:
            return RuleOutput(
                VerificationState.NON_COMPLIANT, 0.0, RiskLevel.HIGH,
                "No OEM authorization found for this bidder in the authorization registry.",
                self._ver(requirement), 0.9,
            )
        if source.status == SourceStatus.ACTIVE.value:
            # An authorization is evidence only while it is valid.
            expiry = source.fields.get("valid_upto")
            if expiry:
                from datetime import date
                from app.services.crossval import _parse_date
                d = _parse_date(expiry)
                if d and d < date.today():
                    return RuleOutput(
                        VerificationState.NON_COMPLIANT, 0.0, RiskLevel.HIGH,
                        f"OEM authorization expired on {d.isoformat()}.",
                        self._ver(requirement), 0.95,
                    )
            base = RuleOutput(
                VerificationState.VERIFIED, 100.0, RiskLevel.LOW,
                f"OEM authorization from '{source.fields.get('oem_name', 'OEM')}' is active and valid.",
                self._ver(requirement), 0.95,
            )
            return self._with_name_check(requirement, fields, source, base)
        return self._unverifiable(requirement, source,
                                  f"Unrecognized OEM registry status: {source.status}.")

    def _rule_labour_compliance(self, requirement, fields: dict, source: SourceResult | None) -> RuleOutput:
        return self._rule_generic(requirement, fields, source)

    def _rule_startup_msme_benefit(self, requirement, fields: dict, source: SourceResult | None) -> RuleOutput:
        if source is None or source.status == SourceStatus.UNAVAILABLE.value:
            return self._unverifiable(requirement, source,
                                      "Udyam registry could not be queried.")
        if source.status == SourceStatus.EXPIRED.value:
            return RuleOutput(
                VerificationState.NON_COMPLIANT, 0.0, RiskLevel.MEDIUM,
                f"Udyam registration has expired ({source.fields.get('valid_upto', 'date unknown')}).",
                self._ver(requirement), 0.9,
            )
        return self._with_name_check(requirement, fields, source,
                                     self._rule_generic(requirement, fields, source))

    def _rule_blacklisting(self, requirement, fields: dict, source: SourceResult | None) -> RuleOutput:
        if source is None or source.status == SourceStatus.UNAVAILABLE.value:
            return self._unverifiable(requirement, source,
                                      "Blacklisting/debarment source could not be queried.")
        if source.status == SourceStatus.NOT_FOUND.value:
            return RuleOutput(
                VerificationState.VERIFIED, 100.0, RiskLevel.LOW,
                "Bidder does not appear in the debarment list (absence is the pass condition).",
                self._ver(requirement), 0.9,
            )
        return RuleOutput(
            VerificationState.NON_COMPLIANT, 0.0, RiskLevel.CRITICAL,
            f"Bidder appears in debarment source with status {source.status}.",
            self._ver(requirement), 0.9,
        )

    def _rule_declaration(self, requirement, fields: dict, source: SourceResult | None) -> RuleOutput:
        if fields.get("declaration_signed"):
            return RuleOutput(
                VerificationState.VERIFIED, 100.0, RiskLevel.LOW,
                "Signed declaration is present in the submission.",
                self._ver(requirement), 0.85,
            )
        return RuleOutput(
            VerificationState.REVIEW, 50.0, RiskLevel.MEDIUM,
            "Declaration presence could not be confirmed automatically.",
            self._ver(requirement), 0.5,
        )
