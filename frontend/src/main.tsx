import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import App from './App'
import TenderList from './pages/TenderList'
import TenderSetup from './pages/TenderSetup'
import BidDashboard from './pages/BidDashboard'
import ReviewQueue from './pages/ReviewQueue'
import AuditReport from './pages/AuditReport'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />}>
          <Route index element={<TenderList />} />
          <Route path="tenders/:tenderId" element={<TenderSetup />} />
          <Route path="bids/:bidId" element={<BidDashboard />} />
          <Route path="review" element={<ReviewQueue />} />
          <Route path="bids/:bidId/audit" element={<AuditReport />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
)
