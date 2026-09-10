# PLAN.md — ProcureGuard MVP Skeleton

Build plan for the SIH 2026 MVP of ProcureGuard, derived from `PRD.md`.
Status markers: `[x]` done · `[~]` in progress · `[ ]` pending.

---

## 1. Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Backend | FastAPI (modular monolith) | PRD stack; module boundaries kept so services can split later (PRD §10) |
| Database | SQLite via SQLAlchemy | Zero-setup local dev; models stay Postgres-compatible — swap `DATABASE_URL` later |
| Migrations | Skip for MVP | `Base.metadata.create_all()` is enough for the skeleton; add Alembic when Postgres lands |
| Frontend | React + TypeScript (Vite) | PRD stack + type-safe API contracts for the four-state model |
| OCR / LLM | Stubbed interfaces | Deterministic mock extraction now; plug real OCR/LLM behind the same interface later (PRD §14, §16) |
| Source adapters | Mock-only, same interface as real | PRD §16 — clearly labelled `simulated: true`, deterministic demo cases |
| Auth | Placeholder (no RBAC) | Skeleton phase; role fields exist on models, enforcement comes later |
| Async jobs | Synchronous, in-request | Queue abstraction deferred; pipeline steps are separate functions so they can move to a worker later |
| Package layout | Monorepo: `backend/` + `frontend/` | Simple to run for the hackathon demo |

---

## 2. Repository layout

```text
procureguard/
├── PLAN.md
├── PRD.md
├── README.md
├── backend/
│   ├── requirements.txt
│   ├── seed_demo.py            # loads demo tenders/bidders/documents (Scenarios A–C)
│   ├── app/
│   │   ├── main.py             # FastAPI app + router mounting + CORS
│   │   ├── core/
│   │   │   ├── config.py       # settings (DB URL, thresholds)
│   │   │   ├── enums.py        # VerificationState, RiskLevel, states per FR-09/FR-10
│   │   │   └── audit.py        # audit event recorder (FR-17)
│   │   ├── db/
│   │   │   ├── base.py         # SQLAlchemy Base + session
│   │   │   └── models.py       # PRD §11 data model
│   │   ├── schemas/            # Pydantic request/response models
│   │   ├── services/
│   │   │   ├── extraction.py   # stub OCR/classifier/field extractor (FR-04)
│   │   │   ├── adapters/       # source adapter interface + mocks (FR-06, §16)
│   │   │   ├── crossval.py     # cross-validation engine (FR-07)
│   │   │   ├── rules.py        # rule engine + built-in rules (FR-08)
│   │   │   ├── scoring.py      # four-state scoring + risk (FR-10, FR-11)
│   │   │   ├── recommendation.py  # evidence-grounded recommendation + clarification (FR-12, FR-13)
│   │   │   └── verification.py # orchestration pipeline (PRD §15 sequence)
│   │   └── api/
│   │       ├── router.py
│   │       ├── tenders.py      # FR-01, FR-02
│   │       ├── bids.py         # FR-03
│   │       ├── verification.py # FR-06..FR-11
│   │       ├── review.py       # FR-16
│   │       └── audit.py        # FR-17
│   └── tests/
│       └── test_mvp.py
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.ts          # proxies /api → backend :8000
    └── src/
        ├── main.tsx
        ├── App.tsx             # shell + routing (7 screens, PRD §13)
        ├── api/client.ts       # typed fetch client
        ├── types.ts            # mirrors backend schemas
        ├── components/         # StateBadge, ScoreCard, EvidencePanel
        └── pages/
            ├── TenderList.tsx        # Screen 1
            ├── TenderSetup.tsx       # Screen 2
            ├── BidderIntake.tsx      # Screen 3
            ├── BidDashboard.tsx      # Screen 4
            ├── RequirementDetail.tsx # Screen 5
            ├── ReviewQueue.tsx       # Screen 6
            └── AuditReport.tsx       # Screen 7
```

---

## 3. Data model (PRD §11)

Implemented as SQLAlchemy models: `Tender`, `Requirement`, `Bidder`, `Bid`,
`Document`, `ExtractedField`, `SourceVerification`, `ComplianceCheck`,
`Evidence`, `ReviewAction`, `AuditEvent`. Enums map to the PRD's four-state
model — **Unverifiable is never collapsed into Verified** (FR-09).

---

## 4. Build phases

### Phase 0 — Plan & skeleton `[x]`
- [x] PLAN.md with decisions and scope
- [x] Backend/folder structure

### Phase 1 — Backend foundation `[x]`
- [x] FastAPI app, settings, SQLAlchemy session (SQLite)
- [x] Core enums: VerificationState, RiskLevel, doc types, source types
- [x] All PRD §11 models with relationships
- [x] Audit event service (append-only)

### Phase 2 — Mock verification layer `[x]`
- [x] `SourceAdapter` interface returning normalized `SourceResult`
- [x] Mock GST / Udyam / MCA / OEM adapters driven by deterministic demo datasets
- [x] `simulated: true` flag on every mock response; unreachable-source case returns `UNAVAILABLE` → UNVERIFIABLE, never NON_COMPLIANT (PRD §17)

### Phase 3 — Intelligence services (stubbed AI) `[x]`
- [x] Extraction stub: deterministic filename/content-triggered field extraction with confidence + evidence text
- [x] Tender analyzer stub: keyword-driven requirement extraction with source clause refs
- [x] Cross-validation engine: name/PAN/GSTIN/date comparisons → Match / Minor / Material / Missing / Expired / Unverifiable
- [x] Rule engine: declarative rules per requirement category → four-state results
- [x] Scoring: mandatory gate + weighted score + risk adjustment (PRD FR-11)
- [x] Recommendation engine (template-based, evidence-grounded; LLM-pluggable later)
- [x] Clarification draft generator

### Phase 4 — API routes (PRD §12) `[x]`
- [x] Tenders: create, get, upload docs, analyze, list requirements
- [x] Bids: create, get, list, upload docs, dashboard
- [x] Verification: run, list, get
- [x] Review: review/override checks (reason captured), clarifications, final decision
- [x] Audit: per-bid and per-tender event streams
- [x] Mock source playground endpoints (`/api/mock/{source}/verify`)

### Phase 5 — Frontend (React + TS) `[x]`
- [x] Vite scaffold, typed API client, routing shell
- [x] Screen 1 Tender List · Screen 2 Tender Setup (+ bidder intake / doc upload)
- [x] Screen 4 Bid Dashboard (score/risk/state cards, findings, overrides, final decision)
- [x] Screen 6 Officer Review Queue (risk-sorted)
- [x] Screen 7 Audit/Report view (timeline + JSON export)
- [ ] Screen 5 Requirement Detail (side-by-side evidence viewer) — separate page; evidence summary lives on the dashboard for now

### Phase 6 — Demo data & tests `[x]`
- [x] `seed_demo.py`: 3 bids mapping to PRD §22 Scenarios A (compliant), B (mismatch), C (unverifiable source)
- [x] Backend pytest suite covering rule engine, scoring gate, cross-validation, unverifiable semantics (7 tests, all passing)
- [x] Frontend typecheck + production build pass
- [ ] Frontend smoke pass against seeded backend
- [ ] Docker compose (deferred until Postgres swap)

---

## 5. Verification pipeline (PRD §15)

```text
run_verification(bid):
  1. Load tender requirements (applicable ones)
  2. For each requirement → gather extracted fields (documents)
  3. Query mock source adapter for the requirement's identifier (or UNAVAILABLE)
  4. Cross-validate document values vs source values
  5. Evaluate rule → VERIFIED | REVIEW | NON_COMPLIANT | UNVERIFIABLE
  6. Attach evidence (document + source references) and explanation
  7. Persist ComplianceCheck + Evidence + SourceVerification
  8. Score: mandatory gate + weighted score + risk adjustment
  9. Generate recommendation + clarification drafts
 10. Emit audit events (correlation_id spans the whole run)
```

Error semantics: adapter failure/timeout/unavailable ⇒ `UNVERIFIABLE` + review flag,
**never** NON_COMPLIANT (PRD §17).

---

## 6. Definition of done for this skeleton

- [x] All 15 PRD §24 acceptance criteria have a code path (some via stubs/mocks)
- [x] pytest suite passes (7/7)
- [x] Seeded demo can walk all three PRD §22 scenarios end-to-end via API
- [ ] Frontend walks all three scenarios against the seeded backend

---

## 7. How to run

```bash
# Backend (terminal 1)
cd backend
pip install -r requirements.txt
python seed_demo.py        # creates procureguard.db with Scenarios A–C
uvicorn app.main:app --reload

# Frontend (terminal 2)
cd frontend
npm install
npm run dev                # http://localhost:5173 (proxies /api → :8000)
```

Demo logins/roles are not implemented yet — all officer actions are attributed to
`officer-demo`. Tests: `cd backend && python -m pytest tests/ -q`.
