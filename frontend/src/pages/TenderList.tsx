import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import type { Tender } from '../types'

export default function TenderList() {
  const [tenders, setTenders] = useState<Tender[]>([])
  const [error, setError] = useState('')
  const [ref, setRef] = useState('')
  const [title, setTitle] = useState('')
  const navigate = useNavigate()

  async function load() {
    try { setTenders(await api.listTenders()) }
    catch (e) { setError(String(e)) }
  }
  useEffect(() => { load() }, [])

  async function create() {
    if (!ref || !title) return
    try {
      const t = await api.createTender(ref, title)
      setRef(''); setTitle('')
      await api.analyzeTender(t.id)
      navigate(`/tenders/${t.id}`)
    } catch (e) { setError(String(e)) }
  }

  return (
    <div>
      <h1>Tender files</h1>
      <p className="page-note">
        Each tender holds its own requirements and bids. Files stay separate from intake through
        decision.
      </p>
      {error && <div className="err">{error}</div>}

      <div className="record">
        <h2>Open a new file</h2>
        <div className="grid cols-3">
          <div>
            <label htmlFor="tender-ref">Reference number</label>
            <input id="tender-ref" value={ref} onChange={e => setRef(e.target.value)}
                   placeholder="GeM/2026/…" />
          </div>
          <div>
            <label htmlFor="tender-title">Title</label>
            <input id="tender-title" value={title} onChange={e => setTitle(e.target.value)}
                   placeholder="Supply of IT hardware…" />
          </div>
          <div style={{ alignSelf: 'end' }}>
            <button onClick={create} disabled={!ref || !title}>Create and analyze</button>
          </div>
        </div>
      </div>

      <div className="record">
        <table>
          <thead>
            <tr>
              <th>Reference</th><th>Title</th><th>Status</th><th>Bids</th><th>Opened</th>
            </tr>
          </thead>
          <tbody>
            {tenders.map(t => (
              <tr key={t.id} className="clickable" onClick={() => navigate(`/tenders/${t.id}`)}>
                <td className="mono">{t.reference_number}</td>
                <td>{t.title}</td>
                <td>{t.status}</td>
                <td>{t.bid_count}</td>
                <td className="muted">{new Date(t.created_at).toLocaleDateString()}</td>
              </tr>
            ))}
            {tenders.length === 0 && (
              <tr><td colSpan={5} className="muted">
                No files yet. Enter a reference number above to open the first one.
              </td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
