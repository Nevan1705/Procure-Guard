// Typed API client — all calls go through /api (proxied by Vite in dev).

import type {
  AuditEvent,
  Bid,
  Dashboard,
  DocumentOut,
  Requirement,
  Tender,
} from '../types'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init)
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`${res.status} ${res.statusText}: ${text}`)
  }
  return res.json() as Promise<T>
}

function jsonInit(method: string, body: unknown): RequestInit {
  return {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }
}

// ------------------------------------------------------------------ tenders

export const api = {
  listTenders: () => request<Tender[]>('/api/tenders'),
  getTender: (id: number) => request<Tender>(`/api/tenders/${id}`),
  createTender: (reference_number: string, title: string) =>
    request<Tender>('/api/tenders', jsonInit('POST', { reference_number, title })),
  analyzeTender: (id: number) =>
    request<{ tender_id: number; requirements_extracted: number; requirements: Requirement[] }>(
      `/api/tenders/${id}/analyze`, { method: 'POST' }),
  listRequirements: (id: number) => request<Requirement[]>(`/api/tenders/${id}/requirements`),

  // ------------------------------------------------------------------ bids
  listBids: () => request<Bid[]>('/api/bids'),
  createBid: (tenderId: number, bidder: Record<string, unknown>, submission_reference?: string) =>
    request<Bid>(`/api/tenders/${tenderId}/bids`,
      jsonInit('POST', { bidder, submission_reference })),
  getBid: (id: number) => request<Bid>(`/api/bids/${id}`),
  uploadBidDocument: (bidId: number, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return request<DocumentOut>(`/api/bids/${bidId}/documents`, { method: 'POST', body: form })
  },
  listBidDocuments: (bidId: number) => request<DocumentOut[]>(`/api/bids/${bidId}/documents`),
  getDashboard: (bidId: number) => request<Dashboard>(`/api/bids/${bidId}/dashboard`),

  // ----------------------------------------------------------- verification
  runVerification: (bidId: number) =>
    request<Record<string, unknown>>(`/api/bids/${bidId}/verify`, { method: 'POST' }),

  // ----------------------------------------------------------------- review
  overrideCheck: (checkId: number, newState: string, reason: string) =>
    request<Record<string, unknown>>(`/api/checks/${checkId}/override`,
      jsonInit('POST', { action: 'OVERRIDE', new_state: newState, reason })),
  reviewCheck: (checkId: number, action: string, reason: string) =>
    request<Record<string, unknown>>(`/api/checks/${checkId}/review`,
      jsonInit('POST', { action, reason })),
  finalDecision: (bidId: number, decision: string, reason: string) =>
    request<Record<string, unknown>>(`/api/bids/${bidId}/final-decision`,
      jsonInit('POST', { decision, reason })),

  // ------------------------------------------------------------------ audit
  bidAudit: (bidId: number) => request<AuditEvent[]>(`/api/bids/${bidId}/audit`),
  tenderAudit: (tenderId: number) => request<AuditEvent[]>(`/api/tenders/${tenderId}/audit`),
}
