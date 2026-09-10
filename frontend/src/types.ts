// Types mirroring backend schemas (app/schemas/api.py)

export type VerificationState = 'VERIFIED' | 'REVIEW' | 'NON_COMPLIANT' | 'UNVERIFIABLE'
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
export type OverallRecommendation = 'QUALIFY' | 'REVIEW' | 'DISQUALIFY'

export interface Tender {
  id: number
  reference_number: string
  title: string
  status: string
  created_at: string
  bid_count: number
}

export interface Requirement {
  id: number
  code: string
  category: string
  description: string
  mandatory: boolean
  source_reference: string | null
  extraction_confidence: number
  status: string | null
}

export interface Bid {
  id: number
  tender_id: number
  bidder_id: number
  bidder_name: string
  status: string
  submitted_at: string | null
  created_at: string
}

export interface DocumentOut {
  id: number
  type: string
  filename: string
  mime_type: string | null
  ocr_status: string | null
  classification_confidence: number
  created_at: string
}

export interface Check {
  id: number
  requirement_code: string
  requirement_description: string
  state: VerificationState
  severity: RiskLevel
  reason: string | null
  rule_version: string | null
  confidence: number
  mandatory: boolean
}

export interface Dashboard {
  bid_id: number
  bidder_name: string
  tender_reference: string
  compliance_score: number
  risk_level: RiskLevel
  overall_recommendation: OverallRecommendation
  counts: Record<VerificationState, number>
  missing_document_count: number
  expired_document_count: number
  checks: Check[]
  recommendation: {
    overall_state: string
    compliance_score: number
    risk_level: string
    summary: string
    critical_findings: string[]
    review_items: string[]
    unverifiable_items: string[]
    next_actions: string[]
    final_decision_authority: string
  } | null
}

export interface AuditEvent {
  id: number
  actor_type: string
  actor_id: string
  event_type: string
  entity_type: string
  entity_id: string
  correlation_id: string | null
  payload_hash?: string | null
  details: Record<string, unknown> | null
  created_at: string
}
