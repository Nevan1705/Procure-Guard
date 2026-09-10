"""Cross-validation engine (PRD FR-07).

Compares values across bidder documents and official-source results,
producing typed comparison outcomes with both sides as evidence.
"""
from dataclasses import dataclass
from datetime import date, datetime

from app.core.enums import CrossValidationResult


@dataclass
class FieldComparison:
    field_name: str
    result: CrossValidationResult
    value_a: str | None
    source_a: str
    value_b: str | None
    source_b: str
    method: str
    severity: str  # LOW | MEDIUM | HIGH
    confidence: float
    detail: str = ""

    def to_dict(self) -> dict:
        return {
            "field_name": self.field_name,
            "result": self.result.value,
            "value_a": self.value_a,
            "source_a": self.source_a,
            "value_b": self.value_b,
            "source_b": self.source_b,
            "method": self.method,
            "severity": self.severity,
            "confidence": self.confidence,
            "detail": self.detail,
        }


def _norm(s: str | None) -> str:
    return (s or "").strip().upper().replace(" ", "")


def compare_identifier(field_name: str, doc_value: str | None, doc_source: str,
                       source_value: str | None, source_source: str) -> FieldComparison:
    """Compare an identifier-like field (PAN/GSTIN/Udyam/CIN) exactly."""
    a, b = _norm(doc_value), _norm(source_value)
    if not a and not b:
        result = CrossValidationResult.UNVERIFIABLE
        detail = "Neither document nor source provided the identifier."
    elif not b:
        result = CrossValidationResult.UNVERIFIABLE
        detail = "Document has the identifier but the official source returned none."
    elif not a:
        result = CrossValidationResult.MISSING
        detail = "Document does not contain the identifier."
    elif a == b:
        result = CrossValidationResult.MATCH
        detail = "Exact identifier match."
    else:
        result = CrossValidationResult.MATERIAL_MISMATCH
        detail = "Identifiers differ between document and official source."
    return FieldComparison(
        field_name=field_name, result=result,
        value_a=doc_value, source_a=doc_source,
        value_b=source_value, source_b=source_source,
        method="EXACT_MATCH", severity="HIGH",
        confidence=1.0, detail=detail,
    )


def _name_tokens(name: str | None) -> set[str]:
    stop = {"PVT", "LTD", "PRIVATE", "LIMITED", "LLP", "P", "L", "THE", "AND", "&",
            "INDIA", "ENTERPRISES", "SOLUTIONS", "SYSTEMS", "TRADERS", "INFRA",
            "CONSORTIUM", "DIGITAL"}
    return {t for t in _norm(name).split(".") if t and t not in stop} or {""}


def compare_legal_name(doc_name: str | None, doc_source: str,
                       source_name: str | None, source_source: str) -> FieldComparison:
    """Fuzzy legal-name comparison tolerant of suffixes (Pvt/Ltd/LLP)."""
    a, b = _norm(doc_name), _norm(source_name)
    if not a or not b:
        result = CrossValidationResult.UNVERIFIABLE
        detail = "One side of the name comparison is missing."
    elif a == b:
        result = CrossValidationResult.MATCH
        detail = "Legal names match exactly."
    elif _name_tokens(a) & _name_tokens(b):
        result = CrossValidationResult.MINOR_MISMATCH
        detail = "Names share distinctive tokens but differ in form (suffix/spelling)."
    else:
        result = CrossValidationResult.MATERIAL_MISMATCH
        detail = "Legal names are entirely different."
    return FieldComparison(
        field_name="legal_name", result=result,
        value_a=doc_name, source_a=doc_source,
        value_b=source_name, source_b=source_source,
        method="TOKEN_OVERLAP", severity="MEDIUM",
        confidence=0.85, detail=detail,
    )


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    return None


def compare_validity(valid_upto: str | None, source: str, today: date | None = None) -> FieldComparison:
    """Check certificate validity dates (expiry detection, PRD FR-10)."""
    today = today or date.today()
    d = _parse_date(valid_upto)
    if not d:
        result = CrossValidationResult.UNVERIFIABLE
        detail = "No validity date available to check expiry."
    elif d >= today:
        result = CrossValidationResult.MATCH
        detail = f"Certificate valid until {d.isoformat()}."
    else:
        result = CrossValidationResult.EXPIRED
        detail = f"Certificate expired on {d.isoformat()}."
    return FieldComparison(
        field_name="valid_upto", result=result,
        value_a=valid_upto, source_a=source,
        value_b=d.isoformat() if d else None, source_b="DATE_CHECK",
        method="DATE_COMPARISON", severity="HIGH",
        confidence=1.0, detail=detail,
    )


def evaluate_comparisons(comparisons: list[FieldComparison]) -> tuple[str, str]:
    """Aggregate comparisons → (worst outcome, summary sentence)."""
    order = [
        CrossValidationResult.MISSING,
        CrossValidationResult.MATERIAL_MISMATCH,
        CrossValidationResult.EXPIRED,
        CrossValidationResult.UNVERIFIABLE,
        CrossValidationResult.MINOR_MISMATCH,
        CrossValidationResult.DUPLICATE,
        CrossValidationResult.MATCH,
    ]
    if not comparisons:
        return CrossValidationResult.UNVERIFIABLE.value, "No comparisons were possible."

    worst = min(comparisons, key=lambda c: order.index(c.result))
    summary = "; ".join(f"{c.field_name}: {c.detail}" for c in comparisons)
    return worst.result.value, summary
