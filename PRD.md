# PRD — ProcureGuard

## AI-Powered Integrated Bid Compliance Verification Platform for GeM Procurement

**Hackathon:** Smart India Hackathon 2026  
**Problem Statement ID:** SIH 26100  
**Problem Statement:** AI-Powered Integrated Bid Compliance Verification Platform for GeM Procurement  
**Theme:** Smart Automation  
**Category:** Software  
**Team:** Localhost 5173  
**Product:** ProcureGuard

---

## 1. Product Overview

ProcureGuard is an AI-powered decision-support platform for automating bidder compliance verification during Government e-Marketplace (GeM) procurement.

The platform ingests a tender and bidder submissions, extracts tender-specific eligibility and compliance requirements, processes supporting documents, verifies bidder information against authorized government/official data sources, cross-validates information, applies deterministic compliance rules, identifies risks and anomalies, and presents an explainable compliance assessment to the Procurement Officer.

The system does **not** make the final qualification/disqualification decision. The Procurement Officer remains the final decision-maker, while ProcureGuard provides evidence, verification states, risk indicators, recommendations, and an auditable trail.

### Core proposition

> **Automate repetitive verification, surface discrepancies early, preserve evidence, and keep the human officer in control.**

---

## 2. Problem Statement

Government procurement requires examination of multiple statutory, regulatory, eligibility, and tender-specific requirements. The verification process can involve bidder documents and information associated with:

- Udyam/MSME registration
- GST registration and return filing
- PAN and Income Tax compliance
- Make in India / local content requirements
- EPFO / ESIC compliance where applicable
- Startup India
- NSIC
- OEM authorization
- DigiLocker / document verification
- Blacklisting / debarment
- Other tender-specific statutory and eligibility requirements

The current process is document-intensive and may require cross-checking information across multiple portals and databases, increasing manual effort, evaluation time, and the possibility of inconsistencies or human error.

---

## 3. Product Goals

### Primary goals

1. Reduce manual effort in bidder compliance verification.
2. Automatically extract and structure tender-specific compliance requirements.
3. Extract relevant data from bidder documents using OCR and AI.
4. Verify bidder claims against authorized government/official sources where available.
5. Cross-validate information across documents and source systems.
6. Apply tender-specific and statutory compliance rules consistently.
7. Detect missing, expired, inconsistent, duplicate, suspicious, or unverifiable evidence.
8. Produce an explainable compliance score and risk level.
9. Generate actionable recommendations and clarification requests for officers.
10. Maintain a complete audit trail of checks, evidence, results, and officer decisions.
11. Preserve human control over the final qualification/disqualification decision.

### Target impact

The proposed solution aims to support the expected impact described in the submission:

- 60–80% reduction in verification effort
- Faster tender evaluation and award
- Improved compliance and transparency
- Reduced human errors and inconsistencies
- Better bidder screening and risk identification
- Standardized verification across CPSEs
- Complete auditability and traceability

These impact figures are **target outcomes**, not validated performance claims for the prototype.

---

## 4. Non-Goals

The first release will not:

- Automatically qualify or disqualify a bidder without officer review.
- Replace statutory authorities or official government portals.
- Treat an LLM response as authoritative proof of compliance.
- Circumvent authentication, access control, rate limits, or portal restrictions.
- Invent verification results when official data is unavailable.
- Provide legal determinations beyond configured procurement rules and available evidence.
- Assume unrestricted access to every government API.

Where an official integration is unavailable in the prototype, the platform should use clearly labelled mock/sandbox adapters, consistent with the submitted feasibility approach.

---

## 5. Users and Personas

### 5.1 Procurement Officer

**Primary user.** Reviews bids, verifies flagged cases, examines evidence, requests clarification, and makes the final qualification/disqualification decision.

**Needs:**
- Fast bid-level overview
- Clear compliance status
- Evidence behind every finding
- Visibility into missing or conflicting information
- Risk prioritization
- Ability to override/accept/review findings with reasons
- Audit-ready reports

### 5.2 Procurement Administrator

Configures tender templates, compliance rules, source connectors, user permissions, and system settings.

### 5.3 Compliance / Audit Reviewer

Reviews verification history, evidence, officer actions, overrides, timestamps, and generated reports.

### 5.4 System Integrator / Technical Administrator

Maintains portal adapters, API credentials, processing services, observability, and deployment configuration.

---

## 6. Primary User Journey

```text
Create/Import Tender
        ↓
Extract Tender Requirements
        ↓
Upload/Import Bidder Documents
        ↓
Classify Documents + OCR
        ↓
Extract Bidder Entities and Claims
        ↓
Resolve Bidder Identity
        ↓
Query Authorized Data Sources
        ↓
Cross-Validate Documents vs Sources
        ↓
Apply Tender-Specific Compliance Rules
        ↓
Detect Risks / Anomalies
        ↓
Generate Verification States + Evidence
        ↓
Calculate Compliance Score + Risk Level
        ↓
Generate Clarifications / Recommendations
        ↓
Procurement Officer Review
        ↓
Officer Decision + Reason
        ↓
Final Report + Immutable Audit Trail
```

---

## 7. Functional Requirements

## FR-01: Tender Intake

The system shall allow an authorized user to create a tender evaluation case.

### Inputs
- Tender reference / ID
- Tender title
- Tender document(s)
- Tender type/category where applicable
- Relevant dates
- Configurable compliance profile

### Requirements
- Store tender metadata.
- Store original tender documents.
- Track document versions.
- Associate all bidder submissions with the tender.
- Prevent accidental mixing of bidder data across tenders.

### Acceptance criteria
- A user can create a tender case and upload source files.
- Original source documents remain retrievable.
- Every subsequent verification result references the tender case.

---

## FR-02: AI Tender Requirement Analysis

The platform shall extract tender-specific eligibility, statutory, documentary, and commercial/compliance requirements from the tender documents.

### Extracted requirement model

Each requirement should contain:

- Requirement ID
- Requirement text
- Requirement category
- Applicability condition
- Required document/evidence type
- Source clause/page reference
- Mandatory/optional status
- Validation rule or rule family
- Effective date / validity condition where applicable
- Human-review requirement
- Extraction confidence

### Example categories
- Registration
- Tax compliance
- Financial/eligibility
- Local content / Make in India
- OEM authorization
- Statutory labour compliance
- Startup/MSME/NSIC benefit
- Blacklisting/debarment
- Tender-specific declarations

### Acceptance criteria
- Extracted requirements are displayed before bid verification begins.
- Every extracted requirement has source traceability to the tender.
- Low-confidence extraction is explicitly flagged for human review.

---

## FR-03: Bidder and Document Intake

The system shall allow multiple bidder documents to be uploaded and associated with a tender.

### Required capabilities
- Multi-file upload
- Supported common document formats
- Document metadata capture
- Document classification
- Duplicate detection
- File integrity checking
- Secure storage
- Version tracking

### Document categories may include
- PAN
- GST certificate / GST-related evidence
- Udyam/MSME certificate
- Income Tax-related evidence
- EPFO/ESIC evidence
- Startup India evidence
- NSIC evidence
- OEM authorization
- Make in India/local content declarations
- DigiLocker-issued documents
- Declarations/undertakings
- Other tender-specific evidence

---

## FR-04: Smart Document Processing

The platform shall use OCR and AI/NLP to process scanned and digital documents.

### Processing pipeline

1. File validation
2. Malware/security scan at ingestion boundary
3. PDF/image preprocessing
4. OCR where required
5. Document classification
6. Layout-aware extraction
7. Entity/value extraction
8. Field normalization
9. Confidence scoring
10. Evidence linking

### Fields to extract where present
- Legal entity name
- PAN
- GSTIN
- Udyam number
- CIN / MCA identifiers
- Registration dates
- Validity/expiry dates
- Addresses
- Authorized signatory
- OEM/manufacturer details
- Certificate/reference numbers
- Return/filing periods
- Local content declarations
- Other tender-relevant fields

### Acceptance criteria
- Every extracted field has source-document evidence.
- Low-confidence fields are reviewable.
- OCR errors do not silently become verified facts.

---

## FR-05: Entity Resolution / Bidder Identity Graph

The platform shall build a canonical bidder identity from identifiers appearing across submissions and verification sources.

### Core entities
- Bidder / legal entity
- PAN
- GST registration
- Udyam registration
- MCA entity / CIN
- OEM/manufacturer
- Tender
- Bid
- Document
- Verification check
- Official source record

### Relationships
Examples:

```text
Bidder ──has──> PAN
Bidder ──has──> GSTIN
Bidder ──has──> Udyam Registration
Bidder ──registered-with──> MCA Entity
Bidder ──authorized-by──> OEM
Bidder ──submits──> Document
Tender ──contains──> Requirement
Bid ──belongs-to──> Tender
Bid ──submitted-by──> Bidder
Verification ──uses──> Evidence
```

### Goal
Use linked identifiers to detect cross-document identity mismatches and suspicious relationships.

---

## FR-06: Government / Official Source Verification

The system shall support adapters for relevant government/official verification sources.

### Proposed source families

- GST / GSTN
- Udyam / MSME
- PAN / Income Tax-related verification
- MCA21
- Startup India
- NSIC
- EPFO
- ESIC
- DigiLocker / authorized document exchange
- Make in India / local content evidence
- BIS / DPIIT where applicable
- Blacklisting / debarment sources
- GeM-related sources

### Integration architecture

Each source shall be implemented behind a normalized adapter interface:

```text
VerificationService
 ├── GSTAdapter
 ├── UdyamAdapter
 ├── MCAAdapter
 ├── IncomeTaxAdapter
 ├── EPFOAdapter
 ├── ESICAdapter
 ├── StartupAdapter
 ├── NSICAdapter
 ├── DigiLockerAdapter
 └── BlacklistAdapter
```

### Source result model

Each adapter should return:

- Source name
- Query timestamp
- Query identifier/reference where available
- Subject identifier
- Retrieved fields
- Verification status
- Data freshness
- Error/status code
- Evidence pointer
- Source confidence / reliability metadata

### Critical rule
A missing official integration must result in **Unverifiable**, not **Verified**.

For the SIH prototype, mock APIs may be used where authorized live access is unavailable; mock responses must be visibly marked as simulated.

---

## FR-07: Cross-Validation Engine

The system shall compare values across bidder documents, tender claims, and official source results.

### Examples

- PAN on submitted document vs PAN associated with GST record
- Legal name across PAN/GST/Udyam/MCA
- Address consistency
- Registration number consistency
- Certificate validity dates
- OEM name vs bidder authorization
- Local content percentage vs tender threshold
- Filing period/return status where relevant
- Duplicate documents across submissions

### Result types
- Match
- Minor mismatch
- Material mismatch
- Missing
- Expired
- Duplicate
- Unverifiable

### Evidence
Every mismatch should include:

- Field under comparison
- Value A + source
- Value B + source
- Comparison method
- Severity
- Timestamp
- Confidence

---

## FR-08: Compliance Rule Engine

The platform shall convert extracted tender requirements into executable verification rules.

### Rule characteristics

A rule should support:

- Rule ID
- Rule name
- Requirement reference
- Applicability condition
- Inputs
- Operators
- Thresholds
- Evidence requirement
- Output state
- Severity
- Human-review requirement
- Version
- Effective date

### Example rule

```yaml
rule_id: GST_ACTIVE
requirement: "Bidder must have an active GST registration"
applicability: bidder_requires_gst == true
checks:
  - gst.source.status == "ACTIVE"
pass_state: VERIFIED
fail_state: NON_COMPLIANT
unknown_state: UNVERIFIABLE
severity: HIGH
```

### Rule priority

1. Tender-specific mandatory requirements
2. Applicable statutory requirements
3. Evidence validity requirements
4. Cross-document consistency requirements
5. Risk/anomaly signals

Rules must be versioned so that historic tender evaluations remain reproducible.

---

## FR-09: Four-State Verification Model

The proposed solution defines four primary verification states:

| State | Meaning |
|---|---|
| **Verified** | Evidence and available source information satisfy the configured requirement. |
| **Review** | Potential issue, ambiguity, low confidence, or discrepancy requires officer review. |
| **Non-Compliant** | Evidence indicates that the requirement is not satisfied. |
| **Unverifiable** | Required evidence/source information could not be reliably verified. |

The UI must never collapse **Unverifiable** into **Verified**.

---

## FR-10: Risk and Anomaly Detection

The system shall identify signals that deserve officer attention.

### Initial anomaly types

- Expired certificate
- Missing mandatory document
- Duplicate document
- OCR/extraction uncertainty
- Cross-document identity mismatch
- Official-source mismatch
- Suspiciously inconsistent dates
- Multiple identifiers mapping unexpectedly
- Conflicting OEM information
- Unverifiable government-source result

### Risk levels

Suggested normalized levels:

- Low
- Medium
- High
- Critical

Risk level is a decision-support signal and must not itself determine qualification.

---

## FR-11: Compliance Scoring

The platform shall calculate an overall compliance score for prioritization and decision support.

### Important design principle
The score should not hide mandatory failures.

Recommended architecture:

```text
Overall Result =
  Mandatory Compliance Gate
  + Weighted Compliance Score
  + Risk Adjustment
  + Uncertainty / Unverifiable Indicators
```

### Example scoring inputs

- Mandatory requirements satisfied
- Non-mandatory requirements satisfied
- Evidence completeness
- Source verification success
- Cross-validation consistency
- Document validity
- Anomaly severity
- Number of review-required findings
- Number of unverifiable findings

### Illustrative score bands

| Score | Suggested Risk | Interpretation |
|---:|---|---|
| 90–100 | Low | Strong evidence and consistency |
| 75–89 | Medium | Some issues/review items |
| 50–74 | High | Material gaps or inconsistencies |
| 0–49 | Critical | Significant non-compliance/evidence problems |

These bands are a prototype policy and should be configurable rather than hard-coded.

---

## FR-12: AI Recommendation Engine

The platform shall produce a recommendation for the Procurement Officer based on verified evidence and rule outcomes.

### Recommendation format

The engine should provide:

- Current compliance state
- Key supporting evidence
- Key failed requirements
- Key review items
- Unverifiable items
- Risk factors
- Suggested next action
- Clarification request where appropriate

### Example

```text
Recommendation: REVIEW
Reason:
- GST status verified.
- Udyam status verified.
- OEM authorization contains a name mismatch.
- Income-tax evidence could not be verified from an authorized source.
- Tender clause 4.2 requires clarification before final decision.
```

### LLM safety requirement
The recommendation generator must be grounded in structured verification results and evidence. The LLM must not independently invent compliance conclusions.

---

## FR-13: AI Clarification Generation

For missing or ambiguous requirements, the system shall generate a draft clarification request for officer review.

### Requirements
- Identify missing/ambiguous evidence.
- Reference the affected tender requirement.
- State what is required.
- Avoid asserting facts not supported by evidence.
- Allow officer editing before sending/exporting.

---

## FR-14: Procurement Compliance Dashboard

The dashboard shall provide a centralized view of bid compliance.

### Bid-level dashboard

Show:

- Bidder name
- Tender reference
- Overall compliance score
- Risk level
- Overall recommendation
- Verified count
- Review count
- Non-compliant count
- Unverifiable count
- Missing document count
- Expired document count
- Major discrepancies
- Pending officer actions

### Requirement-level view

Each requirement should show:

- Requirement text
- Status
- Evidence
- Verification source
- Rule applied
- Confidence
- Discrepancies
- Recommended action

---

## FR-15: Evidence and Explainability

Every material compliance result must be traceable.

### Evidence chain

```text
Result
  ↓
Rule
  ↓
Input Fields
  ↓
Source Record / Document
  ↓
Page / Region / Reference
  ↓
Timestamp + Verification Event
```

The UI should allow an officer to navigate from a result to its supporting evidence.

---

## FR-16: Human-in-the-Loop Decisioning

The Procurement Officer shall remain the final decision-maker.

### Officer actions

- Accept verification result
- Mark for review
- Override a result
- Request clarification
- Record reason
- Add notes
- Approve final qualification decision
- Reject/disqualify according to applicable procedure

### Override requirement
Any officer override should capture:

- User identity
- Previous state
- New state
- Reason
- Timestamp
- Optional note/evidence

---

## FR-17: Audit Trail

The system shall maintain an auditable record for each verification lifecycle.

### Audit events

- Tender created/updated
- Document uploaded/replaced
- OCR completed
- AI extraction completed
- Requirement created/edited
- Source queried
- Source response received
- Rule evaluated
- Result changed
- Risk generated
- Recommendation generated
- Clarification drafted
- Officer review performed
- Officer override performed
- Final decision recorded
- Report exported

### Audit properties

- Immutable event ID
- User/service identity
- Timestamp
- Event type
- Object/entity ID
- Before/after values where applicable
- Evidence reference
- Correlation ID

---

## FR-18: Reports and Export

The platform should produce an evaluation report containing:

- Tender details
- Bidder details
- Compliance summary
- Requirement-wise results
- Evidence references
- Risk assessment
- Missing/expired documents
- Discrepancies
- Recommendations
- Officer actions
- Final officer decision
- Audit metadata

The report should clearly distinguish **AI-generated findings** from **officer decisions**.

---

## 8. Non-Functional Requirements

### NFR-01: Security

- Encrypt data in transit and at rest.
- Enforce role-based access control.
- Isolate bidder data by tender and authorization boundary.
- Never expose source credentials to the frontend.
- Store secrets in a secret-management mechanism in production.
- Log security-sensitive actions.
- Support document access controls.

### NFR-02: Privacy

- Minimize storage of sensitive personal/business information.
- Provide controlled access to documents.
- Define retention and deletion policies.
- Avoid sending sensitive documents to external AI providers unless explicitly authorized and governed.

### NFR-03: Reliability

- Failed source queries must be represented explicitly.
- Partial integrations must not create false positive verification.
- Processing jobs should support retry and idempotency.

### NFR-04: Explainability

No final compliance state should be presented without an explanation and evidence reference.

### NFR-05: Reproducibility

A historical evaluation should be reproducible using:

- Tender version
- Rule version
- Source response/reference
- Model/version metadata where relevant
- Input document version
- Timestamp

### NFR-06: Scalability

The architecture should support asynchronous processing for large batches of bids and documents and be deployable in containerized infrastructure.

### NFR-07: Usability

The Procurement Officer should be able to identify the most important issues without reading every document manually.

---

## 9. Technical Architecture

### Proposed stack from submission

- **Frontend:** React
- **Backend:** FastAPI
- **Database:** PostgreSQL
- **OCR:** OCR service/library
- **AI:** LLM/NLP
- **Compliance:** Rules Engine
- **Integration:** REST APIs
- **Deployment:** Docker

### Recommended logical architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                      React Web Application                   │
│ Dashboard • Tender • Bidder • Evidence • Review • Reports   │
└─────────────────────────────┬────────────────────────────────┘
                              │ HTTPS/REST
┌─────────────────────────────▼────────────────────────────────┐
│                       FastAPI API Layer                      │
│ Auth • Tender • Bid • Document • Verification • Review      │
└──────┬──────────────┬──────────────┬──────────────┬─────────┘
       │              │              │              │
       ▼              ▼              ▼              ▼
 Document        AI/ML Pipeline   Rule Engine   Audit Service
 Service         OCR/Extraction   Compliance    Event Log
       │              │              │              │
       └──────────────┴──────┬───────┴──────────────┘
                             ▼
                       PostgreSQL
                             │
                             ▼
                    Evidence / Object Store
                             │
             ┌───────────────┴────────────────┐
             ▼                                ▼
      Source Adapter Layer              Report Service
             │
   ┌─────────┼─────────┬─────────┬──────────┐
   ▼         ▼         ▼         ▼          ▼
  GST      Udyam      MCA      IncomeTax   Other Sources
```

### Processing architecture

Long-running operations such as OCR, extraction, source verification, and bulk scoring should execute asynchronously through a job/queue abstraction in production.

---

## 10. Backend Service Boundaries

A prototype may start as a modular FastAPI application, while maintaining boundaries that can later be split into services.

### Modules

1. Authentication & Authorization
2. Tender Management
3. Bidder Management
4. Document Management
5. OCR & Extraction
6. Entity Resolution
7. Source Verification
8. Compliance Rule Engine
9. Risk Engine
10. Recommendation Engine
11. Review/Decision Management
12. Audit Trail
13. Reporting
14. Notifications / Clarifications

---

## 11. Suggested Data Model

### Tender

```text
id
reference_number
title
status
created_by
created_at
updated_at
version
```

### Requirement

```text
id
tender_id
code
category
description
applicability_rule
mandatory
source_reference
rule_version
extraction_confidence
status
```

### Bid

```text
id
tender_id
bidder_id
submission_reference
status
submitted_at
created_at
```

### Bidder

```text
id
legal_name
pan
cin
gstin
udyam_id
address
metadata
created_at
```

### Document

```text
id
bid_id
type
filename
storage_uri
hash
version
mime_type
ocr_status
classification_confidence
created_at
```

### ExtractedField

```text
id
document_id
field_name
field_value
normalized_value
confidence
page_number
bounding_box
evidence_text
```

### SourceVerification

```text
id
bidder_id
source_type
subject_identifier
request_reference
status
response_payload_reference
queried_at
freshness
```

### ComplianceCheck

```text
id
bid_id
requirement_id
state
score
severity
reason
rule_version
confidence
created_at
```

### Evidence

```text
id
check_id
type
source
reference
snapshot_uri
page_or_locator
timestamp
```

### ReviewAction

```text
id
bid_id
check_id
user_id
previous_state
new_state
action
reason
notes
created_at
```

### AuditEvent

```text
id
actor_type
actor_id
event_type
entity_type
entity_id
correlation_id
payload_hash
created_at
```

---

## 12. API Requirements

### Tender APIs

```http
POST   /api/tenders
GET    /api/tenders/{tender_id}
POST   /api/tenders/{tender_id}/documents
POST   /api/tenders/{tender_id}/analyze
GET    /api/tenders/{tender_id}/requirements
```

### Bid APIs

```http
POST   /api/tenders/{tender_id}/bids
GET    /api/bids/{bid_id}
POST   /api/bids/{bid_id}/documents
POST   /api/bids/{bid_id}/verify
GET    /api/bids/{bid_id}/dashboard
```

### Verification APIs

```http
POST /api/bids/{bid_id}/verifications/run
GET  /api/bids/{bid_id}/verifications
GET  /api/verifications/{verification_id}
```

### Review APIs

```http
POST /api/checks/{check_id}/review
POST /api/checks/{check_id}/override
POST /api/bids/{bid_id}/clarifications
POST /api/bids/{bid_id}/final-decision
```

### Audit APIs

```http
GET /api/bids/{bid_id}/audit
GET /api/tenders/{tender_id}/audit
```

---

## 13. Frontend Requirements

### Screen 1 — Tender List

- Search/filter tenders
- Tender status
- Number of bids
- Pending reviews
- Last verification activity

### Screen 2 — Tender Setup

- Upload tender documents
- View AI-extracted requirements
- Correct/edit requirements
- View extraction confidence
- Configure rule applicability

### Screen 3 — Bidder Intake

- Upload documents
- View document classification
- See extracted bidder identity
- Detect duplicate documents

### Screen 4 — Bidder Compliance Dashboard

Top-level cards:

- Compliance Score
- Risk Level
- Verified
- Review
- Non-Compliant
- Unverifiable

Additional sections:

- Critical findings
- Missing documents
- Expiring/expired documents
- Identity mismatches
- Source verification status
- Recommendations

### Screen 5 — Requirement Detail

- Tender clause
- Requirement description
- Result state
- Rule applied
- Extracted values
- Official-source values
- Side-by-side comparison
- Evidence viewer
- Review actions

### Screen 6 — Officer Review Queue

Prioritize:

1. Critical/high-risk findings
2. Mandatory non-compliance
3. Identity mismatches
4. Unverifiable mandatory checks
5. Low-confidence AI extraction
6. Other review items

### Screen 7 — Audit/Report

- Verification timeline
- Evidence references
- Officer actions
- Final decision
- Export/report generation

---

## 14. AI/ML Design Principles

### Principle 1 — AI extracts; rules decide compliance

LLMs/OCR should extract and interpret unstructured data. Deterministic rules should control formal compliance evaluation wherever possible.

### Principle 2 — Evidence grounding

Every AI-generated claim should point to source evidence.

### Principle 3 — Confidence-aware processing

Low-confidence extraction should trigger review rather than silent acceptance.

### Principle 4 — No hallucinated verification

An AI model must never fabricate a government source response, registration status, filing status, or document authenticity.

### Principle 5 — Human override with auditability

Officer decisions supersede automated suggestions only through a visible, logged action.

---

## 15. Compliance Evaluation Logic

A recommended evaluation sequence is:

```text
For each bidder:

1. Determine applicable requirements.
2. Check whether mandatory evidence exists.
3. Extract required fields from documents.
4. Verify relevant identifiers against authorized sources.
5. Cross-validate extracted and source values.
6. Evaluate tender-specific rules.
7. Detect expiry, duplicates and anomalies.
8. Assign a four-state result to each requirement.
9. Identify mandatory failures and unresolved reviews.
10. Calculate weighted score and risk level.
11. Generate evidence-grounded recommendation.
12. Present all findings to officer.
13. Store decision and audit events.
```

### Mandatory-gate principle

A bidder with a mandatory requirement in **Non-Compliant** state should not be represented as fully compliant merely because a weighted score is high.

Similarly, a bidder with mandatory requirements in **Unverifiable** state should be surfaced as requiring officer attention rather than being treated as compliant.

---

## 16. Mock Verification API Strategy for SIH Prototype

Because the proposal identifies limited access to government APIs, the SIH prototype should isolate real and simulated integrations behind the same interface.

### Example

```text
POST /mock/gst/verify
POST /mock/udyam/verify
POST /mock/mca/verify
POST /mock/incometax/verify
POST /mock/oem/verify
```

### Mock data requirements

Each mock source should include:

- Realistic but synthetic identifiers
- Active/inactive examples
- Matching/mismatching examples
- Expired examples
- Unavailable-source example
- Explicit `simulated: true` flag

### Demo benefit

The same bidder can demonstrate:

- Fully compliant case
- Missing evidence case
- Cross-document mismatch case
- Expired certificate case
- Unverifiable source case
- High-risk anomaly case

This makes the prototype deterministic and easy to demonstrate to judges.

---

## 17. Error Handling

The platform shall distinguish:

- Invalid document
- OCR failure
- Classification failure
- Extraction failure
- Source authentication failure
- Source timeout
- Source unavailable
- Rate-limit response
- Invalid identifier
- Rule configuration error
- Model error

### Error semantics

A technical failure must not be interpreted as non-compliance.

For example:

```text
GST API timeout
      ↓
GST status = UNVERIFIABLE
      ↓
Flag for review
```

not:

```text
GST API timeout
      ↓
GST status = NON-COMPLIANT
```

---

## 18. Observability and Operations

Track:

- API latency
- OCR processing time
- LLM latency/tokens where available
- Source adapter success/failure rate
- Verification job failures
- Queue depth
- Database errors
- Document processing failures
- Rule execution failures
- User review backlog

Every verification workflow should have a correlation ID spanning API, job, source adapter, rule execution, and audit records.

---

## 19. Security Threat Model

### Threats

- Unauthorized access to bidder documents
- Credential leakage
- Prompt injection inside uploaded documents
- Malicious files
- Data exfiltration through AI services
- Tampering with verification results
- Privilege escalation
- Audit-log manipulation
- Cross-tender data leakage

### Controls

- RBAC
- Strong authentication
- File scanning
- Sandboxed document processing
- Input/output validation
- LLM prompt isolation
- Strict tenant/tender authorization
- Signed/auditable result records where practical
- Secure secrets management
- Encryption
- Immutable or append-only audit architecture

### Prompt injection requirement

Tender and bidder documents are **untrusted content**. Extracted instructions inside a document must never override the system's policies, tool permissions, or compliance rules.

---

## 20. Performance Targets for Prototype

These are engineering targets for the SIH prototype and should be benchmarked rather than assumed.

| Area | Prototype target |
|---|---|
| Dashboard load | < 2 seconds for common case |
| API response for simple read | < 500 ms target |
| Document ingestion acknowledgement | < 2 seconds |
| OCR/extraction | Asynchronous; progress visible |
| Verification run | Asynchronous; status tracked |
| Audit event write | Near-real-time |
| Bulk bid processing | Queue-based |

The prototype should optimize perceived responsiveness by providing progress states rather than blocking the user on long-running AI/OCR jobs.

---

## 21. MVP Scope

### Must Have

- Tender upload
- AI-assisted tender requirement extraction
- Bidder document upload
- OCR + document classification
- Key bidder field extraction
- GST/Udyam/MCA-style mock verification adapters
- Cross-validation
- Rule engine
- Four-state verification
- Compliance score
- Risk level
- Explainable findings
- Officer review workflow
- Audit trail
- Dashboard
- Demo report

### Should Have

- Entity graph visualization
- AI clarification generation
- More source adapters
- Document duplicate detection
- Exportable compliance report
- Configurable scoring

### Could Have

- DigiLocker integration
- Real authorized integrations where available
- Advanced anomaly models
- Batch tender comparison
- Advanced analytics
- Historical bidder risk trends

### Won't Have in SIH MVP

- Autonomous qualification/disqualification
- Unapproved scraping or unauthorized portal access
- Production-grade integration with every listed government system
- Fully automated legal interpretation

---

## 22. MVP Demo Scenario

### Scenario A — Compliant bidder

1. Upload tender.
2. System extracts five to ten relevant requirements.
3. Upload bidder documents.
4. OCR/extraction identifies PAN/GST/Udyam/etc.
5. Mock official sources return matching active records.
6. All applicable mandatory checks become Verified.
7. Dashboard shows high score / low risk.
8. Officer reviews evidence.
9. Officer records final decision.
10. Audit report is generated.

### Scenario B — Mismatch bidder

1. Bidder provides a GST document with a legal-name mismatch.
2. GST source returns a different legal name.
3. Cross-validation marks the requirement Review or Non-Compliant depending on the configured rule.
4. Dashboard raises a high-risk discrepancy.
5. AI generates a clarification draft.
6. Officer reviews evidence and makes final decision.

### Scenario C — Unverifiable source

1. Required source is unavailable.
2. System marks the check Unverifiable.
3. Score/risk reflects unresolved uncertainty.
4. Officer is prompted to review.

---

## 23. Success Metrics

### Product metrics

- Percentage of tender requirements successfully extracted
- Document classification accuracy
- Key-field extraction accuracy
- Cross-validation detection rate
- Percentage of requirements with traceable evidence
- Percentage of automated checks completed without manual lookup
- Average number of officer actions per bid
- Average verification time per bid

### AI quality metrics

- OCR character/field accuracy
- Extraction precision/recall for critical identifiers
- Requirement extraction precision/recall
- False-positive discrepancy rate
- False-negative discrepancy rate
- Hallucination rate for generated explanations

### Operational metrics

- Source adapter availability
- Verification job success rate
- Mean processing time
- Error/retry rate
- Audit completeness

---

## 24. Acceptance Criteria

A release is MVP-complete when:

1. A tender can be uploaded and analyzed.
2. Requirements are extracted and traceable to the tender source.
3. Bidder documents can be uploaded and classified.
4. Key bidder identifiers can be extracted with confidence scores.
5. Verification adapters can return normalized source results.
6. The system can cross-validate at least several important fields.
7. Tender-specific rules can generate the four verification states.
8. Missing, expired, conflicting, and unverifiable evidence can be detected.
9. The dashboard displays score, risk, state counts, and critical findings.
10. Each finding exposes supporting evidence.
11. The officer can review and override findings with a reason.
12. Final qualification/disqualification remains an officer action.
13. Audit events are persisted for all material workflow steps.
14. A final report can be produced from the case.
15. Simulated APIs are clearly distinguished from real official integrations.

---

## 25. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Limited government API access | Adapter architecture + authorized APIs + clearly labelled mock APIs for prototype |
| Poor-quality scans | Image preprocessing + OCR + confidence thresholds + review queue |
| Different document formats | Flexible classifier and extraction schema |
| AI incorrect results | Grounded AI + deterministic rule engine + confidence + human review |
| Privacy/security concerns | RBAC, encryption, data minimization, secure processing |
| Changing tender rules | Versioned configurable rule engine |
| Source data inconsistency | Cross-validation + evidence comparison |
| Source unavailable | Unverifiable state, not non-compliant |
| Model hallucination | Structured inputs, evidence grounding, constrained output |
| Duplicate/malicious documents | Hashing, scanning, provenance checks |

The submission itself identifies limited government API access, poor-quality/scanned documents, different formats, AI errors, privacy/security concerns, and changing tender rules as key feasibility risks. fileciteturn0file0L108-L122

---

## 26. Development Roadmap

### Phase 1 — Foundation

- React application shell
- FastAPI backend
- PostgreSQL schema
- Authentication/RBAC
- Tender/bid/document entities
- Object storage interface

### Phase 2 — AI Document Pipeline

- OCR
- Document classification
- Structured field extraction
- Confidence/evidence capture

### Phase 3 — Tender Intelligence

- Tender parsing
- Requirement extraction
- Requirement editing UI
- Rule mapping

### Phase 4 — Verification Engine

- Adapter interface
- Mock GST/Udyam/MCA/etc.
- Cross-validation
- Four-state evaluation
- Scoring/risk

### Phase 5 — Officer Experience

- Compliance dashboard
- Evidence viewer
- Review queue
- Overrides
- AI clarification generation

### Phase 6 — Audit and Demo Hardening

- Full audit trail
- Reports
- Error states
- Security controls
- Demo datasets
- End-to-end benchmark

---

## 27. Suggested Team Workstreams

### Frontend

- Tender management UI
- Bidder dashboard
- Requirement detail
- Review queue
- Evidence viewer
- Reports

### Backend

- FastAPI APIs
- PostgreSQL models
- RBAC
- Workflow orchestration
- Audit service

### AI/ML

- OCR pipeline
- Document classification
- Requirement extraction
- Field extraction
- Evidence-grounded recommendation

### Rules/Compliance

- Requirement schema
- Rule DSL/configuration
- Four-state evaluator
- Scoring/risk engine

### Integrations

- Source adapter framework
- Mock source APIs
- Normalized source response schema
- Connector monitoring

### DevOps/Security

- Docker
- CI/CD
- Secrets
- Logging/monitoring
- Security testing

---

## 28. Source Basis and Traceability

This PRD is primarily derived from the submitted ProcureGuard SIH solution deck.

The deck identifies the proposed capabilities as AI tender analysis, OCR + AI document processing, source verification, cross-validation, a compliance engine, four-state verification, explainable results, risk/anomaly detection, an entity graph, AI clarifications, compliance scoring/reporting, and human-in-the-loop review. fileciteturn0file0L53-L64

The deck's proposed technical approach is tender analysis, document processing, data extraction, source verification, cross-validation, compliance checking, risk detection, human review, reporting/audit, with React, FastAPI, PostgreSQL, OCR, LLM/NLP, rules, REST APIs, and Docker. fileciteturn0file0L80-L92

The feasibility section explicitly proposes authorized APIs and mock APIs for the prototype, OCR/image preprocessing, flexible document classification/extraction, and combining AI with rule-based verification. fileciteturn0file0L112-L122

The submitted references include GeM, GST Portal, DigiLocker, API Setu/DigiLocker Data Exchange, and the NIST AI Risk Management Framework. fileciteturn0file0L159-L165

Where this PRD introduces engineering details not explicitly stated in the deck—such as endpoint shapes, schemas, scoring bands, service boundaries, acceptance criteria, threat controls, and roadmap items—those are **recommended implementation specifications**, not claims that they already exist in the proposed solution.

---

## 29. Open Questions for Product/Engineering Review

1. Which government/official integrations can be legally and technically accessed for the prototype?
2. Which tender rule families will be implemented first?
3. Which document types must be supported in the SIH demo?
4. What exact scoring policy should apply to mandatory vs non-mandatory requirements?
5. Which data retention period is acceptable for bidder documents?
6. Which LLM/OCR deployment model is permitted for sensitive procurement documents?
7. What official source constitutes authoritative evidence for each compliance category?
8. What procurement workflows or report formats need to be mirrored in the target deployment environment?

---

## 30. Definition of Done

A feature is considered done only when:

- It works through the intended user workflow.
- Inputs and outputs are validated.
- Failure states are represented explicitly.
- Security/access controls are applied.
- Evidence/source traceability exists where relevant.
- Audit events are generated for material actions.
- The feature is demonstrated with both positive and negative test cases.
- Documentation/API contracts are updated.

---

## 31. Guiding Product Principles

1. **Evidence over assertion.**
2. **Rules over free-form model judgment for compliance.**
3. **Unverifiable is not verified.**
4. **Every important result must be explainable.**
5. **The officer remains in control.**
6. **Every decision should be auditable.**
7. **Prototype integrations must be clearly distinguished from official production integrations.**

---

## Appendix A — Conceptual Verification Object

```json
{
  "bid_id": "BID-001",
  "requirement_id": "REQ-GST-001",
  "state": "VERIFIED",
  "score": 100,
  "risk": "LOW",
  "confidence": 0.98,
  "rule_version": "GST_ACTIVE@1.0",
  "evidence": [
    {
      "type": "DOCUMENT",
      "document_id": "DOC-123",
      "page": 1
    },
    {
      "type": "OFFICIAL_SOURCE",
      "source": "GST",
      "reference": "SRC-789"
    }
  ],
  "explanation": "Submitted GST identifier matches the verified source record and required status is active.",
  "verified_at": "2026-09-10T12:00:00Z"
}
```

## Appendix B — Conceptual Recommendation Object

```json
{
  "overall_state": "REVIEW",
  "compliance_score": 82,
  "risk_level": "MEDIUM",
  "summary": "Most mandatory requirements are supported, but two items require officer review.",
  "critical_findings": [
    "OEM authorization contains a legal-name mismatch.",
    "Income-tax verification is currently unverifiable."
  ],
  "next_actions": [
    "Review OEM authorization evidence.",
    "Request/perform authorized income-tax verification."
  ],
  "final_decision_authority": "PROCUREMENT_OFFICER"
}
```

---

**End of PRD**
