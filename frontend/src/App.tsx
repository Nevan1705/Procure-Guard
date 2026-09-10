import { NavLink, Outlet } from 'react-router-dom'
import './App.css'

export default function App() {
  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="file-tab">File</span>
          <span className="brand-name">ProcureGuard</span>
          <span className="brand-sub">GeM bid compliance · SIH 2026</span>
        </div>
        <nav>
          <NavLink to="/">Tenders</NavLink>
          <NavLink to="/review">Review queue</NavLink>
        </nav>
      </header>
      <main className="content">
        <Outlet />
      </main>
      <footer className="foot">
        Decision support only — the Procurement Officer makes the final call. Mock source data is
        labelled <code>simulated</code>.
      </footer>
    </div>
  )
}
