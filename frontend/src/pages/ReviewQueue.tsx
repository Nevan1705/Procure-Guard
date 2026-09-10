import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { RISK_STAMP } from '../components/badges'
import type { Bid, Dashboard } from '../types'

interface Row {
  bid: Bid
  dash: Dashboard | null
  error?: string
}

// Review queue priority (PRD FR-14 / Screen 6): risk first, then recommendation,
// then score. The dashboard endpoint supplies all three.
const RISK_ORDER: Record<string, number> = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 }
const REC_ORDER: Record<string, number> = { DISQUALIFY: 0, REVIEW: 1, QUALIFY: 2 }

export default function ReviewQueue() {
  const [rows, setRows] = useState<Row[]>([])
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const load = useCallback(async () => {
    try {
      const bids = await api.listBids()
      const results = await Promise.all(
        bids.map(async (bid): Promise<Row> => {
          try {
            return { bid, dash: await api.getDashboard(bid.id) }
          } catch (e) {
            return { bid, dash: null, error: String(e) }
          }
        }),
      )
      results.sort((a, b) => {
        const ra = RISK_ORDER[a.dash?.risk_level ?? 'LOW'] ?? 3
        const rb = RISK_ORDER[b.dash?.risk_level ?? 'LOW'] ?? 3
        if (ra !== rb) return ra - rb
        const ca = REC_ORDER[a.dash?.overall_recommendation ?? 'REVIEW'] ?? 1
        const cb = REC_ORDER[b.dash?.overall_recommendation ?? 'REVIEW'] ?? 1
        if (ca !== cb) return ca - cb
        return (a.dash?.compliance_score ?? 100) - (b.dash?.compliance_score ?? 100)
      })
      setRows(results)
      setError('')
    } catch (e) {
      setError(String(e))
    }
  }, [])

  useEffect(() => { load() }, [load])

  return (
    <div>
      <h1>Review queue</h1>
      <p className="page-note">
        Bids most worth your attention first: highest risk, then weakest recommendation, then
        lowest score. Unverified bids wait at the bottom.
      </p>
      {error && <div className="err">{error}</div>}

      <div className="record">
        <table>
          <thead>
            <tr>
              <th>Bid</th><th>Bidder</th><th>Tender</th><th>Status</th>
              <th>Score</th><th>Risk</th><th>Recommendation</th><th>Results</th><th></th>
            </tr>
          </thead>
          <tbody>
            {rows.map(({ bid, dash, error: err }) => (
              <tr key={bid.id} className="clickable"
                  onClick={() => dash && navigate(`/bids/${bid.id}`)}>
                <td className="mono">#{bid.id}</td>
                <td>{bid.bidder_name}</td>
                <td className="mono">{dash ? dash.tender_reference : bid.tender_id}</td>
                <td>{bid.status}</td>
                {dash ? (
                  <>
                    <td>{dash.compliance_score.toFixed(0)}</td>
                    <td><span className={`stamp ${RISK_STAMP[dash.risk_level]}`}>{dash.risk_level}</span></td>
                    <td><strong>{dash.overall_recommendation}</strong></td>
                    <td className="muted">
                      V{dash.counts.VERIFIED ?? 0} · R{dash.counts.REVIEW ?? 0} ·
                      N{dash.counts.NON_COMPLIANT ?? 0} · U{dash.counts.UNVERIFIABLE ?? 0}
                    </td>
                    <td><button className="secondary">Open</button></td>
                  </>
                ) : (
                  <td colSpan={5} className="muted">{err ?? 'Not verified yet'}</td>
                )}
              </tr>
            ))}
            {rows.length === 0 && (
              <tr><td colSpan={9} className="muted">
                The queue is empty. Bids appear here once tenders are seeded and verified.
              </td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
