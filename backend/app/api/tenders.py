"""Tender APIs (PRD FR-01, FR-02) with stubbed AI requirement analysis."""
import hashlib
import os
import re

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.audit import record_audit_event
from app.core.config import UPLOAD_DIR, LOW_CONFIDENCE_THRESHOLD
from app.core.enums import DocumentType, RequirementCategory, TenderStatus
from app.db.base import get_db
from app.db.models import Document, Requirement, Tender
from app.schemas.api import (
    DocumentOut,
    TenderAnalyzeResult,
    TenderCreate,
    TenderOut,
)

router = APIRouter(prefix="/api/tenders", tags=["tenders"])

# Keyword → category extraction rules for the analyzer stub.
_KEYWORD_RULES: list[tuple[re.Pattern, RequirementCategory, str]] = [
    (re.compile(r"gst(?:in)?\b|goods and services tax", re.I),
     RequirementCategory.REGISTRATION, "Bidder must have an active GST registration."),
    (re.compile(r"udyam|msme", re.I),
     RequirementCategory.STARTUP_MSME_BENEFIT, "Bidder must hold a valid Udyam (MSME) registration."),
    (re.compile(r"pan\b|permanent account number", re.I),
     RequirementCategory.REGISTRATION, "Bidder must submit a valid PAN."),
    (re.compile(r"make in india|local content", re.I),
     RequirementCategory.LOCAL_CONTENT, "Bidder must meet the minimum local-content percentage."),
    (re.compile(r"oem|original equipment manufacturer|authorization|authorisation", re.I),
     RequirementCategory.OEM_AUTHORIZATION, "Bidder must provide OEM authorization for quoted products."),
    (re.compile(r"income.?tax|itr|it return", re.I),
     RequirementCategory.TAX_COMPLIANCE, "Bidder must demonstrate income-tax return filing compliance."),
    (re.compile(r"blacklist|debar", re.I),
     RequirementCategory.BLACKLISTING, "Bidder must not be blacklisted or debarred by any authority."),
    (re.compile(r"epf|esic|labour|provident", re.I),
     RequirementCategory.LABOUR_COMPLIANCE, "Bidder must comply with applicable EPFO/ESIC obligations."),
    (re.compile(r"turnover|financial years?|annual report", re.I),
     RequirementCategory.FINANCIAL_ELIGIBILITY, "Bidder must meet the turnover/financial eligibility criteria."),
    (re.compile(r"declar|undertak", re.I),
     RequirementCategory.DECLARATION, "Bidder must submit the tender-specific declaration/undertaking."),
]


def _save_upload(upload: UploadFile, prefix: str) -> tuple[str, str]:
    """Persist an upload to disk; return (stored filename, sha256 hash)."""
    target_dir = os.path.join(UPLOAD_DIR, "tenders")
    os.makedirs(target_dir, exist_ok=True)
    safe_name = f"{prefix}_{upload.filename}".replace("/", "_").replace("\\", "_")
    path = os.path.join(target_dir, safe_name)
    content = upload.file.read()
    with open(path, "wb") as f:
        f.write(content)
    digest = hashlib.sha256(content).hexdigest()
    return safe_name, digest


@router.post("", response_model=TenderOut, status_code=201)
def create_tender(payload: TenderCreate, db: Session = Depends(get_db)):
    tender = Tender(
        reference_number=payload.reference_number,
        title=payload.title,
        status=TenderStatus.DRAFT,
        created_by="officer-demo",
    )
    db.add(tender)
    db.commit()
    record_audit_event(db, "TENDER_CREATED", "tender", tender.id,
                       details={"reference": tender.reference_number})
    db.commit()
    return TenderOut(
        id=tender.id,
        reference_number=tender.reference_number,
        title=tender.title,
        status=tender.status,
        created_at=tender.created_at,
        bid_count=0,
    )


@router.get("", response_model=list[TenderOut])
def list_tenders(db: Session = Depends(get_db)):
    tenders = db.query(Tender).order_by(Tender.created_at.desc()).all()
    return [
        TenderOut(
            id=t.id, reference_number=t.reference_number, title=t.title,
            status=t.status, created_at=t.created_at, bid_count=len(t.bids),
        )
        for t in tenders
    ]


@router.get("/{tender_id}", response_model=TenderOut)
def get_tender(tender_id: int, db: Session = Depends(get_db)):
    tender = db.get(Tender, tender_id)
    if not tender:
        raise HTTPException(404, "Tender not found")
    return TenderOut(
        id=tender.id, reference_number=tender.reference_number, title=tender.title,
        status=tender.status, created_at=tender.created_at, bid_count=len(tender.bids),
    )


@router.post("/{tender_id}/documents", response_model=DocumentOut, status_code=201)
def upload_tender_document(tender_id: int, file: UploadFile, db: Session = Depends(get_db)):
    tender = db.get(Tender, tender_id)
    if not tender:
        raise HTTPException(404, "Tender not found")

    safe_name, digest = _save_upload(file, f"tender{tender_id}")
    doc = Document(
        tender_id=tender_id,
        type=DocumentType.OTHER,
        filename=file.filename or safe_name,
        storage_uri=f"{UPLOAD_DIR}/tenders/{safe_name}",
        hash=digest,
        mime_type=file.content_type,
        ocr_status="PENDING",
    )
    db.add(doc)
    db.commit()
    record_audit_event(db, "DOCUMENT_UPLOADED", "tender", tender_id,
                       details={"document_id": doc.id, "filename": doc.filename})
    db.commit()
    return doc


@router.post("/{tender_id}/analyze", response_model=TenderAnalyzeResult)
def analyze_tender(tender_id: int, db: Session = Depends(get_db)):
    """Stub AI tender analysis (PRD FR-02).

    MVP: keyword-driven requirement extraction from the tender documents' text
    (or the title when no documents yet). A real LLM pipeline replaces the
    extraction core; the requirement model and API stay identical.
    """
    tender = db.get(Tender, tender_id)
    if not tender:
        raise HTTPException(404, "Tender not found")

    corpus_parts = [tender.title]
    for doc in tender.documents:
        try:
            with open(doc.storage_uri, "r", encoding="utf-8", errors="ignore") as f:
                corpus_parts.append(f.read())
        except OSError:
            continue
    corpus = "\n".join(corpus_parts)

    # Remove stale requirements on re-analysis (versioned in a later phase).
    tender.requirements.clear()

    extracted: list[dict] = []
    seq = 0
    for pattern, category, description in _KEYWORD_RULES:
        matches = list(pattern.finditer(corpus))
        if not matches:
            continue
        seq += 1
        first = matches[0]
        clause_ref = _guess_clause_ref(corpus, first.start())
        low_confidence = len(matches) == 1 and len(first.group(0)) < 8
        req = Requirement(
            tender_id=tender.id,
            code=f"REQ-{category.value[:8]}-{seq:03d}",
            category=category,
            description=description,
            mandatory=category != RequirementCategory.DECLARATION,
            source_reference=clause_ref,
            rule_version=f"{category.value}@1.0",
            extraction_confidence=0.62 if low_confidence else 0.88,
            status="ACTIVE" if not low_confidence else "NEEDS_REVIEW",
        )
        db.add(req)
        extracted.append({
            "code": req.code,
            "category": category.value,
            "description": description,
            "mandatory": req.mandatory,
            "source_reference": clause_ref,
            "extraction_confidence": req.extraction_confidence,
            "status": req.status,
        })

    tender.status = TenderStatus.ANALYZED
    record_audit_event(db, "TENDER_ANALYZED", "tender", tender.id,
                       details={"requirements": len(extracted)})
    db.commit()

    return TenderAnalyzeResult(
        tender_id=tender.id,
        requirements_extracted=len(extracted),
        requirements=extracted,
    )


@router.get("/{tender_id}/requirements")
def list_requirements(tender_id: int, db: Session = Depends(get_db)):
    tender = db.get(Tender, tender_id)
    if not tender:
        raise HTTPException(404, "Tender not found")
    return [
        {
            "id": r.id,
            "code": r.code,
            "category": r.category.value,
            "description": r.description,
            "mandatory": r.mandatory,
            "source_reference": r.source_reference,
            "extraction_confidence": r.extraction_confidence,
            "status": r.status,
        }
        for r in tender.requirements
    ]


def _guess_clause_ref(corpus: str, pos: int) -> str:
    """Heuristic clause reference: nearest 'Clause N' or 'Section N' before match."""
    window = corpus[max(0, pos - 300):pos]
    m = list(re.finditer(r"(?:Clause|Section)\s+(\d+(?:\.\d+)?)", window, re.I))
    return f"Clause {m[-1].group(1)}" if m else "Reference pending manual tagging"
