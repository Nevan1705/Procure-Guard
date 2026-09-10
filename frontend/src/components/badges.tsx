import type { RiskLevel, VerificationState } from '../types'

// Four-state ink (PRD FR-09): Unverifiable is washed grey — never green,
// so it can never read as a good outcome.
export const STATE_STAMP: Record<VerificationState, { cls: string; label: string }> = {
  VERIFIED: { cls: 'stamp--verified', label: 'Verified' },
  REVIEW: { cls: 'stamp--review', label: 'Review' },
  NON_COMPLIANT: { cls: 'stamp--failed', label: 'Non-compliant' },
  UNVERIFIABLE: { cls: 'stamp--unverifiable', label: 'Unverifiable' },
}

export const RISK_STAMP: Record<RiskLevel, string> = {
  LOW: 'stamp--verified',
  MEDIUM: 'stamp--review',
  HIGH: 'stamp--high',
  CRITICAL: 'stamp--failed',
}

export const REC_STAMP: Record<string, string> = {
  QUALIFY: 'stamp--verified',
  REVIEW: 'stamp--review',
  DISQUALIFY: 'stamp--failed',
}

export function StateBadge({ state }: { state: VerificationState }) {
  const s = STATE_STAMP[state]
  return <span className={`stamp ${s.cls}`}>{s.label}</span>
}

export function RiskBadge({ level }: { level: RiskLevel }) {
  return <span className={`stamp ${RISK_STAMP[level]}`}>{level}</span>
}
