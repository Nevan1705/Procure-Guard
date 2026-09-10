"""Seed demo data covering PRD §22 Scenarios A, B, C.

Run from backend/:  python seed_demo.py
Creates procureguard.db with:
  - One tender (analyzed) with three bids:
      Bid 1 (Scenario A): compliant — all mandatory checks verified.
      Bid 2 (Scenario B): GST legal-name mismatch → review/non-compliant.
      Bid 3 (Scenario C): GST source unavailable → unverifiable.
"""
import io
import os

from fastapi import UploadFile

from app.core.config import UPLOAD_DIR
from app.db.base import Base, SessionLocal, engine
from app.db import models  # noqa: F401
from app.db.models import Bid, Document, Tender
from app.api.tenders import analyze_tender, create_tender, upload_tender_document
from app.api.bids import create_bid, upload_bid_document
from app.schemas.api import BidCreate, BidderCreate, TenderCreate
from app.services.verification import run_verification

# Synthetic filenames carry the identifier payload for the extraction stub.
COMPLIANT_DOCS = [
    "gst_certificate_27AAAPZ1234C1ZV_legalname=Acme Systems Pvt Ltd.txt",
    "pan_card_AAAPZ1234C.txt",
    "udyam_certificate_UDYAM-MH-01-0012345_legalname=Acme Systems Pvt Ltd.txt",
    "local_content_declaration_localcontent=85.txt",
]
MISMATCH_DOCS = [
    "gst_certificate_27AAIFM7712K1ZQ_legalname=Acme Systems Pvt Ltd.txt",
    "pan_card_AAAPZ1234C.txt",
]
UNVERIFIABLE_DOCS = [
    "gst_certificate_24AACCD9999P1Z2_legalname=Acme Systems Pvt Ltd.txt",
]


def _fake_upload(filename: str) -> UploadFile:
    """Build a minimal UploadFile-like object for direct endpoint calls."""
    return UploadFile(filename=filename, file=io.BytesIO(b"demo-content"))


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # A tender whose document text mentions the key requirement keywords.
    tender_text = (
        "Tender for supply of IT hardware.\n"
        "Clause 4.1: Bidders must have an active GST registration (GSTIN).\n"
        "Clause 4.2: Bidders must hold a valid Udyam/MSME registration.\n"
        "Clause 5.3: Valid PAN is mandatory.\n"
        "Clause 6.1: Make in India local content requirement applies.\n"
    )

    tender_out = create_tender(
        TenderCreate(reference_number="GeM/DEMO/2026/001",
                     title="Supply of IT hardware — GeM bid compliance demo"),
        db,
    )
    upload_tender_document(tender_out.id, _fake_upload("tender_document.txt"), db)
    # Write the corpus into the stored document so the analyzer has text.
    tender = db.get(Tender, tender_out.id)
    doc = db.query(Document).filter(Document.tender_id == tender.id).first()
    with open(doc.storage_uri, "w", encoding="utf-8") as f:
        f.write(tender_text)

    analysis = analyze_tender(tender.id, db)
    print(f"Tender {tender.id}: {analysis.requirements_extracted} requirements extracted")

    scenarios = [
        ("Scenario A — Compliant", "Acme Systems Pvt Ltd", COMPLIANT_DOCS),
        ("Scenario B — Mismatch", "Acme Systems Pvt Ltd", MISMATCH_DOCS),
        ("Scenario C — Unverifiable", "Acme Systems Pvt Ltd", UNVERIFIABLE_DOCS),
    ]

    for label, bidder_name, docs in scenarios:
        bid_out = create_bid(
            tender.id,
            BidCreate(
                bidder=BidderCreate(
                    legal_name=bidder_name,
                    pan="AAAPZ1234C",
                    gstin=docs[0].split("_")[2],
                    udyam_id="UDYAM-MH-01-0012345",
                ),
                submission_reference=label,
            ),
            db,
        )
        bid = db.get(Bid, bid_out.id)
        for doc_name in docs:
            upload_bid_document(bid.id, _fake_upload(doc_name), db)

        result = run_verification(db, bid)
        print(
            f"{label}: bid={bid.id} score={result['score']['score']} "
            f"risk={result['score']['risk_level']} "
            f"recommendation={result['recommendation']['overall_state']}"
        )

    db.close()
    print("Seed complete — procureguard.db ready.")


if __name__ == "__main__":
    seed()
