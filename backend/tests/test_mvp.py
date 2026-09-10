"""MVP test suite covering adapters, cross-validation, scoring gate, rules, and API workflow."""
import io

import pytest
from fastapi import UploadFile
from fastapi.testclient import TestClient

from app.main import app
from app.db.base import Base, SessionLocal, engine
from app.db import models  # noqa: F401


@pytest.fixture()
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)


def _upload(filename: str) -> UploadFile:
    return UploadFile(filename=filename, file=io.BytesIO(b"test"))


# ---------------------------------------------------------------- unit tests

def test_mock_gst_active_and_unavailable():
    from app.services.adapters import get_adapter
    from app.core.enums import SourceType, SourceStatus

    gst = get_adapter(SourceType.GST)
    active = gst.verify("27AAAPZ1234C1ZV")
    assert active.status == SourceStatus.ACTIVE.value
    assert active.simulated is True
    assert active.fields["legal_name"] == "Acme Systems Pvt Ltd"

    unavailable = gst.verify("24AACCD9999P1Z2")
    assert unavailable.status == SourceStatus.UNAVAILABLE.value
    assert unavailable.error is not None


def test_crossval_name_match_and_mismatch():
    from app.services.crossval import compare_legal_name
    from app.core.enums import CrossValidationResult

    assert compare_legal_name("Acme Systems Pvt Ltd", "DOC",
                              "Acme Systems Pvt Ltd", "GST").result == CrossValidationResult.MATCH
    assert compare_legal_name("Acme Systems Pvt Ltd", "DOC",
                              "Meridian Infra Consortium LLP", "GST"
                              ).result == CrossValidationResult.MATERIAL_MISMATCH


def test_scoring_mandatory_gate_blocks_high_score():
    """A high weighted score must not hide a mandatory NON_COMPLIANT (PRD FR-11)."""
    from types import SimpleNamespace
    from app.services.scoring import compute_compliance_score
    from app.core.enums import VerificationState, RiskLevel

    req = SimpleNamespace(mandatory=True, code="REQ-GST")
    checks = [
        SimpleNamespace(requirement=req, state=VerificationState.NON_COMPLIANT,
                        score=0.0, severity=RiskLevel.HIGH),
        SimpleNamespace(requirement=SimpleNamespace(mandatory=False, code="REQ-X"),
                        state=VerificationState.VERIFIED, score=100.0,
                        severity=RiskLevel.LOW),
        SimpleNamespace(requirement=SimpleNamespace(mandatory=False, code="REQ-Y"),
                        state=VerificationState.VERIFIED, score=100.0,
                        severity=RiskLevel.LOW),
    ]
    result = compute_compliance_score(checks)
    assert result.mandatory_gate_failed is True
    assert result.risk_level == RiskLevel.CRITICAL
    assert result.score < 100.0


def test_scoring_unverifiable_mandatory_is_not_compliant():
    """Mandatory UNVERIFIABLE must surface as needing attention, not compliant (PRD FR-09)."""
    from types import SimpleNamespace
    from app.services.scoring import compute_compliance_score
    from app.core.enums import VerificationState, RiskLevel

    req = SimpleNamespace(mandatory=True, code="REQ-GST")
    checks = [
        SimpleNamespace(requirement=req, state=VerificationState.UNVERIFIABLE,
                        score=40.0, severity=RiskLevel.HIGH),
        SimpleNamespace(requirement=SimpleNamespace(mandatory=False, code="REQ-X"),
                        state=VerificationState.VERIFIED, score=100.0,
                        severity=RiskLevel.LOW),
    ]
    result = compute_compliance_score(checks)
    assert result.mandatory_gate_uncertain is True
    assert result.risk_level == RiskLevel.HIGH


def test_rule_engine_unavailable_source_maps_to_unverifiable():
    """Adapter failure ⇒ UNVERIFIABLE, never NON_COMPLIANT (PRD §17)."""
    from app.services.rules import RuleEngine
    from app.services.adapters.base import SourceResult
    from app.core.enums import SourceStatus, VerificationState
    from types import SimpleNamespace

    req = SimpleNamespace(code="REQ-GST-001",
                          category=SimpleNamespace(value="REGISTRATION"),
                          mandatory=True)
    source = SourceResult(source="GST", subject_identifier="X",
                          status=SourceStatus.UNAVAILABLE.value, error="timeout")
    out = RuleEngine().evaluate(req, {}, source)
    assert out.state == VerificationState.UNVERIFIABLE


# ---------------------------------------------------------------- API workflow

def test_full_workflow_scenarios(client):
    """End-to-end: tender → analyze → bids → verify → dashboard (PRD §22)."""
    # Health
    assert client.get("/api/health").json()["status"] == "ok"

    # Create tender (title carries the requirement keywords)
    r = client.post("/api/tenders", json={
        "reference_number": "GeM/TEST/2026/001",
        "title": ("Supply of laptops. Clause 4.1 requires active GST registration. "
                  "Clause 4.2 requires valid Udyam MSME registration. "
                  "Clause 5.1 requires PAN. Clause 7.2 OEM authorization needed."),
    })
    assert r.status_code == 201, r.text
    tender_id = r.json()["id"]

    # Analyze requirements
    r = client.post(f"/api/tenders/{tender_id}/analyze")
    assert r.status_code == 200, r.text
    extracted = r.json()["requirements"]
    assert len(extracted) >= 3

    # Three bids for the three scenarios
    def make_bid(gstin: str):
        r = client.post(f"/api/tenders/{tender_id}/bids", json={
            "bidder": {"legal_name": "Acme Systems Pvt Ltd", "pan": "AAAPZ1234C",
                       "gstin": gstin, "udyam_id": "UDYAM-MH-01-0012345"},
            "submission_reference": "test",
        })
        assert r.status_code == 201, r.text
        return r.json()["id"]

    bid_a = make_bid("27AAAPZ1234C1ZV")   # compliant
    bid_b = make_bid("27AAIFM7712K1ZQ")   # mismatch
    bid_c = make_bid("24AACCD9999P1Z2")   # unavailable source

    # Upload documents (filenames carry the extraction payload)
    for bid, gst_doc in [
        (bid_a, "gst_certificate_27AAAPZ1234C1ZV_legalname=Acme Systems Pvt Ltd.txt"),
        (bid_b, "gst_certificate_27AAIFM7712K1ZQ_legalname=Acme Systems Pvt Ltd.txt"),
        (bid_c, "gst_certificate_24AACCD9999P1Z2_legalname=Acme Systems Pvt Ltd.txt"),
        (bid_a, "udyam_certificate_UDYAM-MH-01-0012345_legalname=Acme Systems Pvt Ltd.txt"),
    ]:
        r = client.post(f"/api/bids/{bid}/documents",
                        files={"file": (gst_doc, io.BytesIO(b"demo"), "text/plain")})
        assert r.status_code == 201, r.text

    # Run verification
    results = {}
    for bid in (bid_a, bid_b, bid_c):
        r = client.post(f"/api/bids/{bid}/verify")
        assert r.status_code == 200, r.text
        results[bid] = r.json()

    # Scenario A: compliant
    a = results[bid_a]
    assert a["score"]["risk_level"] == "LOW"
    assert a["recommendation"]["overall_state"] == "QUALIFY"
    assert all(c["state"] in ("VERIFIED",) for c in a["checks"])

    # Scenario B: mismatch surfaces (review or non-compliant, never silent)
    b = results[bid_b]
    states = {c["state"] for c in b["checks"]}
    assert states & {"REVIEW", "NON_COMPLIANT"}
    assert b["score"]["risk_level"] in ("MEDIUM", "HIGH", "CRITICAL")

    # Scenario C: unverifiable, NOT non-compliant (PRD §17)
    c = results[bid_c]
    assert any(ch["state"] == "UNVERIFIABLE" for ch in c["checks"])
    assert not any(ch["state"] == "NON_COMPLIANT" for ch in c["checks"])

    # Dashboard reflects the four states
    r = client.get(f"/api/bids/{bid_a}/dashboard")
    assert r.status_code == 200
    dash = r.json()
    assert dash["counts"]["VERIFIED"] >= 1
    assert dash["compliance_score"] >= 75

    # Officer override with reason (PRD FR-16)
    check_id = dash["checks"][0]["id"]
    r = client.post(f"/api/checks/{check_id}/override", json={
        "action": "OVERRIDE",
        "new_state": "REVIEW",
        "reason": "Signature on GST certificate needs manual verification.",
    })
    assert r.status_code == 200

    # Final decision remains an officer action
    r = client.post(f"/api/bids/{bid_a}/final-decision", json={
        "decision": "QUALIFIED", "reason": "All mandatory requirements verified."})
    assert r.status_code == 200

    # Audit trail exists (PRD FR-17)
    r = client.get(f"/api/bids/{bid_a}/audit")
    assert r.status_code == 200
    events = r.json()
    types = {e["event_type"] for e in events}
    assert "VERIFICATION_STARTED" in types
    assert "RULE_EVALUATED" in types
    assert "OFFICER_OVERRIDE" in types
    assert "FINAL_DECISION" in types


def test_mock_verify_endpoint(client):
    r = client.get("/api/mock/gst/verify", params={"identifier": "27AAAPZ1234C1ZV"})
    assert r.status_code == 200
    body = r.json()
    assert body["simulated"] is True
    assert body["status"] == "ACTIVE"
