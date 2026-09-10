"""Stub OCR/extraction pipeline (PRD FR-04).

For the MVP this is a deterministic stand-in for a real OCR+LLM pipeline:
document type comes from the uploaded filename, and "extracted" fields are
derived from identifier patterns in the filename/optional text with fixed
confidence values. A real OCR/LLM implementation replaces
`extract_fields_from_document` without changing any caller.
"""
import re
from dataclasses import dataclass, field

from app.core.enums import DocumentType


@dataclass
class ExtractedFieldValue:
    field_name: str
    field_value: str
    normalized_value: str
    confidence: float
    page_number: int = 1
    evidence_text: str = ""
    bounding_box: str | None = None


@dataclass
class ExtractionOutput:
    document_type: DocumentType
    classification_confidence: float
    fields: list[ExtractedFieldValue] = field(default_factory=list)


# Filename hints → document type. Real pipeline: OCR → classifier.
_FILENAME_TYPE_HINTS: list[tuple[re.Pattern, DocumentType]] = [
    (re.compile(r"pan", re.I), DocumentType.PAN),
    (re.compile(r"gst", re.I), DocumentType.GST_CERTIFICATE),
    (re.compile(r"udyam|msme", re.I), DocumentType.UDYAM_CERTIFICATE),
    (re.compile(r"oem|authorization|authorisation", re.I), DocumentType.OEM_AUTHORIZATION),
    (re.compile(r"income.?tax|it-?return|itr", re.I), DocumentType.INCOME_TAX_EVIDENCE),
    (re.compile(r"local.?content|make.?in.?india", re.I), DocumentType.LOCAL_CONTENT_DECLARATION),
    (re.compile(r"declaration|undertaking", re.I), DocumentType.DECLARATION),
    (re.compile(r"epfo|esic", re.I), DocumentType.EPFO_ESIC),
    (re.compile(r"startup", re.I), DocumentType.STARTUP_INDIA),
    (re.compile(r"nsic", re.I), DocumentType.NSIC),
]

_PAN_RE = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")
_GSTIN_RE = re.compile(r"\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9A-Z]{3}\b")
_UDYAM_RE = re.compile(r"\bUDYAM-[A-Z]{2}-\d{2}-\d{7}\b", re.I)
_CIN_RE = re.compile(r"\b[LU]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}\b", re.I)


def classify_document(filename: str) -> tuple[DocumentType, float]:
    """Classify a document by filename keywords (stub for OCR classifier)."""
    for pattern, doc_type in _FILENAME_TYPE_HINTS:
        if pattern.search(filename):
            return doc_type, 0.92
    return DocumentType.OTHER, 0.60


def extract_fields_from_document(filename: str, text: str | None = None) -> ExtractionOutput:
    """Extract identifier fields deterministically.

    MVP strategy: scan the filename (and optional text) with identifier regexes.
    Real pipeline: OCR full text → LLM layout-aware extraction.
    """
    doc_type, cls_conf = classify_document(filename)
    corpus = " ".join([filename, text or ""])

    fields: list[ExtractedFieldValue] = []

    def add(field_name: str, value: str, confidence: float, evidence: str) -> None:
        if value and not any(f.field_name == field_name for f in fields):
            fields.append(
                ExtractedFieldValue(
                    field_name=field_name,
                    field_value=value,
                    normalized_value=value.strip().upper(),
                    confidence=confidence,
                    evidence_text=evidence,
                )
            )

    if m := _PAN_RE.search(corpus):
        add("pan", m.group(0), 0.95, f"Found PAN pattern in {filename}")
    if m := _GSTIN_RE.search(corpus):
        add("gstin", m.group(0), 0.95, f"Found GSTIN pattern in {filename}")
    if m := _UDYAM_RE.search(corpus):
        add("udyam_id", m.group(0).upper(), 0.90, f"Found Udyam number pattern in {filename}")
    if m := _CIN_RE.search(corpus):
        add("cin", m.group(0).upper(), 0.90, f"Found CIN pattern in {filename}")

    # Legal name heuristic: "legalname=<value>" payload in filename (demo hook).
    if m := re.search(r"legalname=([^_.]+(?:[ _][^_.]+)*)", filename, re.I):
        add("legal_name", m.group(1).replace("_", " ").strip(), 0.85, "Filename payload")

    # Local-content percentage: "localcontent=<n>" payload in filename (demo hook).
    if m := re.search(r"localcontent=(\d+(?:\.\d+)?)", filename, re.I):
        add("local_content_percent", m.group(1), 0.90, "Local-content declaration payload")

    return ExtractionOutput(
        document_type=doc_type,
        classification_confidence=cls_conf,
        fields=fields,
    )
