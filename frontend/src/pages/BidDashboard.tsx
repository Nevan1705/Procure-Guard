import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { REC_STAMP, RiskBadge, RISK_STAMP, STATE_STAMP, StateBadge } from '../components/badges'
import type { Dashboard, VerificationState } from '../types'

const STATES: VerificationState[] = ['VERIFIED', 'REVIEW', 'NON_COMPLIANT', 'UNVERIFIABLE']

const TALLY_CLS: Record<VerificationState, string> = {
  VERIFIED: 'ink-verified',
  REVIEW: 'ink-review',
  NON_COMPLIANT: 'ink-failed',
  UNVERIFIABLE: 'ink-unverifiable',
}

export default function BidDashboard() {
  const { bidId } = useParams()
  const id = Number(bidId)
  const [dash, setDash] = useState<Dashboard | null>(null)
  const [error, setError] = useState('')
  const [reason, setReason] = useState('')

  const load = useCallback(async () => {
    try { setDash(await api.getDashboard(id)) }
    catch (e) { setError(String(e)) }
  }, [id])
  useEffect(() => { load() }, [load])

  async function override(checkId: number, newState: string) {
    const why = reason.trim() || 'Officer override from dashboard'
    try {
      await api.overrideCheck(checkId, newState, why)
      setReason('')
      await load()
    } catch (e) { setError(String(e)) }
  }

  async function finalDecision(d: 'QUALIFIED' | 'DISQUALIFIED') {
    if (!reason.trim()) { setError('A reason is required to record a final decision.'); return }
    try {
      await api.finalDecision(id, d, reason.trim())
      setReason('')
      await load()
    } catch (e) { setError(String(e)) }
  }

  if (error && !dash) {
    return (
      <div>
        <h1>Bid file</h1>
        <div className="err">{error}</div>
      </div>
    )
  }
  if (!dash) return <p className="muted">Opening the file…</p>

  const rec = dash.recommendation

  return (
    <div>
      <h1>Bid #{dash.bid_id} — {dash.bidder_name}</h1>
      <p className="page-note">Tender <span className="mono">{dash.tender_reference}</span></p>
      {error && <div className="err">{error}</div>}

      {rec && (
        <div className="verdict-band">
          <div className="ledger">
            <span className="ledger-figure">{dash.compliance_score.toFixed(0)}</span>
            <span className="ledger-caption">Compliance score, of 100</span>
          </div>
          <div className="verdict-stamps">
            <span className={`stamp stamp-big stamp-land ${RISK_STAMP[dash.risk_level]}`}>
              {dash.risk_level} risk
            </span>
            <span
              className={`stamp stamp-big stamp-land stamp-land-2 ${REC_STAMP[dash.overall_recommendation] ?? ''}`}
            >
              {dash.overall_recommendation}
            </span>
          </div>
          <div className="state-tally">
            {STATES.map(s => (
              <div key={s}>
                <span className={`tally-fig ${TALLY_CLS[s]}`}>{dash.counts[s] ?? 0}</span>
                <span className="tally-lbl">{STATE_STAMP[s].label}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {rec && (
        <div className="record">
          <h2>Assessment</h2>
          <p style={{ maxWidth: '68ch', margin: '0 0 12px' }}>{rec.summary}</p>
          {rec.critical_findings.length > 0 && (
            <>
              <h2>Critical findings</h2>
              {rec.critical_findings.map((f, i) => <div className="finding" key={i}>{f}</div>)}
            </>
          )}
          {rec.unverifiable_items.length > 0 && (
            <>
              <h2>Could not be verified</h2>
              {rec.unverifiable_items.map((f, i) => <div className="finding" key={i}>{f}</div>)}
            </>
          )}
          {rec.review_items.length > 0 && (
            <>
              <h2>Needs review</h2>
              {rec.review_items.map((f, i) => <div className="finding" key={i}>{f}</div>)}
            </>
          )}
          {rec.next_actions.length > 0 && (
            <>
              <h2>Next steps</h2>
              <ul style={{ margin: '0 0 12px', paddingLeft: 20 }}>
                {rec.next_actions.map((a, i) => <li key={i}>{a}</li>)}
              </ul>
            </>
          )}
          <p className="muted">
            {dash.missing_document_count} document(s) missing · {dash.expired_document_count} expired
          </p>
        </div>
      )}

      <div className="record">
        <h2>Requirement results</h2>
        <label htmlFor="override-reason">
          Reason for officer actions — recorded in the audit trail
        </label>
        <textarea
          id="override-reason"
          value={reason}
          onChange={e => setReason(e.target.value)}
          placeholder="e.g. Signature on the certificate needs manual verification"
        />
        <table style={{ marginTop: 12 }}>
          <thead>
            <tr>
              <th>Requirement</th><th>Mandatory</th><th>Result</th><th>Severity</th>
              <th>Reason</th><th>Rule</th><th>Confidence</th><th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {dash.checks.map(c => (
              <tr key={c.id}>
                <td>
                  <strong className="mono">{c.requirement_code}</strong>
                  <div className="muted">{c.requirement_description}</div>
                </td>
                <td>{c.mandatory ? 'Yes' : 'No'}</td>
                <td><StateBadge state={c.state} /></td>
                <td><RiskBadge level={c.severity} /></td>
                <td className="muted">{c.reason}</td>
                <td className="mono">{c.rule_version}</td>
                <td>{(c.confidence * 100).toFixed(0)}%</td>
                <td>
                  <button className="secondary" onClick={() => override(c.id, 'VERIFIED')}>Accept</button>{' '}
                  <button className="secondary" onClick={() => override(c.id, 'NON_COMPLIANT')}>Fail</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="record">
        <h2>Final decision</h2>
        <p className="page-note" style={{ marginBottom: 12 }}>
          The system recommends; you decide. Your decision and reason are written to the audit
          trail.
        </p>
        <button onClick={() => finalDecision('QUALIFIED')}>Qualify bid</button>{' '}
        <button className="danger" onClick={() => finalDecision('DISQUALIFIED')}>Disqualify bid</button>{' '}
        <Link to={`/bids/${id}/audit`} style={{ display: 'inline-block', marginLeft: 4 }}>
          <button className="secondary">View audit trail</button>
        </Link>
      </div>
    </div>
  )
}
