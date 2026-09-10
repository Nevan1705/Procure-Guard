import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import type { Bid, DocumentOut, Requirement, Tender } from '../types'

export default function TenderSetup() {
  const { tenderId } = useParams()
  const navigate = useNavigate()
  const id = Number(tenderId)

  const [tender, setTender] = useState<Tender | null>(null)
  const [requirements, setRequirements] = useState<Requirement[]>([])
  const [bids, setBids] = useState<Bid[]>([])
  const [error, setError] = useState('')

  const [bidderName, setBidderName] = useState('')
  const [gstin, setGstin] = useState('')
  const [pan, setPan] = useState('')
  const [udyamId, setUdyamId] = useState('')
  const fileInput = useRef<HTMLInputElement>(null)
  const [activeBid, setActiveBid] = useState<Bid | null>(null)
  const [docs, setDocs] = useState<DocumentOut[]>([])

  const loadBidDocs = useCallback(async (bidId: number) => {
    try { setDocs(await api.listBidDocuments(bidId)) } catch (e) { setError(String(e)) }
  }, [])

  const load = useCallback(async () => {
    try {
      const t = await api.getTender(id)
      setTender(t)
      setRequirements(await api.listRequirements(id))
      // Refresh the bids table without a dedicated list endpoint.
      const all = await api.listBids()
      setBids(all.filter(b => b.tender_id === id))
    } catch (e) { setError(String(e)) }
  }, [id])

  useEffect(() => { load() }, [load])

  async function createBid() {
    if (!bidderName || !gstin) return
    try {
      const bid = await api.createBid(id,
        { legal_name: bidderName, gstin, pan: pan || null, udyam_id: udyamId || null },
        `Web intake ${new Date().toISOString().slice(0, 10)}`)
      setBids(b => [...b, bid])
      setActiveBid(bid)
      setBidderName(''); setGstin(''); setPan(''); setUdyamId('')
    } catch (e) { setError(String(e)) }
  }

  async function upload(file: File) {
    if (!activeBid || !file) return
    try {
      await api.uploadBidDocument(activeBid.id, file)
      await loadBidDocs(activeBid.id)
    } catch (e) { setError(String(e)) }
  }

  async function runVerification(bid: Bid) {
    try {
      await api.runVerification(bid.id)
      navigate(`/bids/${bid.id}`)
    } catch (e) { setError(String(e)) }
  }

  return (
    <div>
      <h1>{tender ? `File ${tender.reference_number}` : 'Opening file…'}</h1>
      {tender && <p className="page-note">{tender.title}</p>}
      {error && <div className="err">{error}</div>}

      <div className="record">
        <h2>Requirements extracted from the tender</h2>
        <p className="page-note" style={{ marginBottom: 12 }}>
          Pulled from the tender document with a source clause for each. Low-confidence extracts
          are flagged for your review.
        </p>
        <table>
          <thead>
            <tr>
              <th>Code</th><th>Category</th><th>Requirement</th>
              <th>Mandatory</th><th>Source</th><th>Confidence</th>
            </tr>
          </thead>
          <tbody>
            {requirements.map(r => (
              <tr key={r.id}>
                <td className="mono">{r.code}</td>
                <td>{r.category}</td>
                <td>{r.description}</td>
                <td>{r.mandatory ? 'Yes' : 'No'}</td>
                <td className="muted">{r.source_reference}</td>
                <td>{(r.extraction_confidence * 100).toFixed(0)}%</td>
              </tr>
            ))}
            {requirements.length === 0 && (
              <tr><td colSpan={6} className="muted">
                Nothing extracted yet — upload a tender document and run analysis.
              </td></tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="record">
        <h2>Add a bidder</h2>
        <div className="grid cols-3">
          <div>
            <label htmlFor="bidder-name">Legal name</label>
            <input id="bidder-name" value={bidderName}
                   onChange={e => setBidderName(e.target.value)} />
          </div>
          <div>
            <label htmlFor="bidder-gstin">GSTIN</label>
            <input id="bidder-gstin" value={gstin} className="mono"
                   onChange={e => setGstin(e.target.value)} />
          </div>
          <div>
            <label htmlFor="bidder-pan">PAN</label>
            <input id="bidder-pan" value={pan} className="mono"
                   onChange={e => setPan(e.target.value)} />
          </div>
          <div>
            <label htmlFor="bidder-udyam">Udyam ID</label>
            <input id="bidder-udyam" value={udyamId} className="mono"
                   onChange={e => setUdyamId(e.target.value)} />
          </div>
          <div style={{ alignSelf: 'end' }}>
            <button onClick={createBid} disabled={!bidderName || !gstin}>Add bidder</button>
          </div>
        </div>
      </div>

      <div className="record">
        <h2>Bids on this file</h2>
        <table>
          <thead>
            <tr><th>Bid</th><th>Bidder</th><th>Status</th><th>Actions</th></tr>
          </thead>
          <tbody>
            {bids.map(b => (
              <tr key={b.id}>
                <td className="mono">#{b.id}</td>
                <td>{b.bidder_name}</td>
                <td>{b.status}</td>
                <td>
                  <button className="secondary"
                          onClick={() => { setActiveBid(b); loadBidDocs(b.id) }}>
                    Select
                  </button>{' '}
                  <button onClick={() => runVerification(b)}>Verify</button>
                </td>
              </tr>
            ))}
            {bids.length === 0 && (
              <tr><td colSpan={4} className="muted">
                No bids yet. Add a bidder above, or open the seeded demo files from the tender
                list.
              </td></tr>
            )}
          </tbody>
        </table>
      </div>

      {activeBid && (
        <div className="record">
          <h2>Documents — bid #{activeBid.id}, {activeBid.bidder_name}</h2>
          <input type="file" ref={fileInput} style={{ display: 'none' }}
                 onChange={e => e.target.files?.[0] && upload(e.target.files[0])} />
          <button className="secondary" onClick={() => fileInput.current?.click()}>
            Upload document
          </button>
          <table style={{ marginTop: 12 }}>
            <thead>
              <tr><th>File</th><th>Classified as</th><th>OCR</th><th>Confidence</th></tr>
            </thead>
            <tbody>
              {docs.map(d => (
                <tr key={d.id}>
                  <td className="mono">{d.filename}</td>
                  <td>{d.type}</td>
                  <td className="muted">{d.ocr_status}</td>
                  <td>{(d.classification_confidence * 100).toFixed(0)}%</td>
                </tr>
              ))}
              {docs.length === 0 && (
                <tr><td colSpan={4} className="muted">
                  No documents yet. The stub classifier reads filename keywords
                  (gst, pan, udyam, oem, localcontent=NN).
                </td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
