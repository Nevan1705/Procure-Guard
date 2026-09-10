import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api/client'
import type { AuditEvent } from '../types'

export default function AuditReport() {
  const { bidId } = useParams()
  const id = Number(bidId)
  const [events, setEvents] = useState<AuditEvent[]>([])
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    try { setEvents(await api.bidAudit(id)) }
    catch (e) { setError(String(e)) }
  }, [id])
  useEffect(() => { load() }, [load])

  function download() {
    const blob = new Blob([JSON.stringify(events, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `bid-${id}-audit.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div>
      <h1>Audit trail — bid #{id}</h1>
      <p className="page-note">
        Every material step in this bid's life: who acted, when, and what changed. Events are
        append-only.
      </p>
      {error && <div className="err">{error}</div>}

      <button className="secondary" onClick={download} disabled={events.length === 0}>
        Export JSON
      </button>{' '}
      <Link to={`/bids/${id}`}><button className="secondary">Back to dashboard</button></Link>

      <div className="record">
        <table>
          <thead>
            <tr>
              <th>#</th><th>When</th><th>Actor</th><th>Event</th>
              <th>Entity</th><th>Correlation</th><th>Details</th>
            </tr>
          </thead>
          <tbody>
            {events.map(e => (
              <tr key={e.id}>
                <td className="mono">{e.id}</td>
                <td className="muted">{new Date(e.created_at).toLocaleString()}</td>
                <td>{e.actor_type}/{e.actor_id}</td>
                <td><strong>{e.event_type}</strong></td>
                <td className="mono">{e.entity_type}/{e.entity_id}</td>
                <td className="mono muted">{e.correlation_id ?? '—'}</td>
                <td>
                  {e.details && (
                    <details>
                      <summary className="mono">view</summary>
                      <pre>{JSON.stringify(e.details, null, 2)}</pre>
                    </details>
                  )}
                </td>
              </tr>
            ))}
            {events.length === 0 && (
              <tr><td colSpan={7} className="muted">
                Nothing recorded yet. Events appear as this bid moves through intake and
                verification.
              </td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
