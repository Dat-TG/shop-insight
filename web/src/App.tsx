/**
 * App — root component with NavBar (8 tabs) and React Router routes.
 *
 * Adding a new BR screen:
 *   1. Import its page:   import BR3Page from './pages/BR3Page'
 *   2. Ensure its tab exists in NAV_TABS (it already does for all 8 BRs)
 *   3. Add a <Route> in the <Routes> block below
 */

import { NavLink, Route, Routes } from 'react-router-dom';
import BR1Page from './pages/BR1Page';
import BR2Page from './pages/BR2Page';
import BR3Page from './pages/BR3Page';
import BR4Page from './pages/BR4Page';
import BR5Page from './pages/BR5Page';
import BR6Page from './pages/BR6Page';
import BR7Page from './pages/BR7Page';
import BR8Page from './pages/BR8Page';

const NAV_TABS = [
  { path: '/br1', label: 'BR1 — Real-time Ops' },
  { path: '/br2', label: 'BR2 — Conversion Funnel' },
  { path: '/br3', label: 'BR3 — Trending Products' },
  { path: '/br4', label: 'BR4 — RFM Segmentation' },
  { path: '/br5', label: 'BR5 — Abandoned Carts' },
  { path: '/br6', label: 'BR6 — Stockout Risk' },
  { path: '/br7', label: 'BR7 — Product Affinity' },
  { path: '/br8', label: 'BR8 — Order Velocity' },
] as const;

export default function App() {
  return (
    <div className="app">
      {/* ── Header ──────────────────────────────────────────── */}
      <header className="header">
        <span className="header__logo">🛍 ShopInsight</span>
        <span className="header__subtitle">Group 15 · CO5173 Data Engineering</span>
      </header>

      {/* ── Navigation ──────────────────────────────────────── */}
      <nav className="navbar">
        {NAV_TABS.map(tab => (
          <NavLink
            key={tab.path}
            to={tab.path}
            className={({ isActive }) =>
              ['navbar__tab', isActive ? 'navbar__tab--active' : ''].filter(Boolean).join(' ')
            }
          >
            {tab.label}
          </NavLink>
        ))}
      </nav>

      {/* ── Content ─────────────────────────────────────────── */}
      <main className="main">
        <Routes>
          <Route path="/"    element={<BR2Page />} />
          <Route path="/br1" element={<BR1Page />} />
          <Route path="/br2" element={<BR2Page />} />
          <Route path="/br3" element={<BR3Page />} />
          <Route path="/br4" element={<BR4Page />} />
          <Route path="/br5" element={<BR5Page />} />
          <Route path="/br6" element={<BR6Page />} />
          <Route path="/br7" element={<BR7Page />} />
          <Route path="/br8" element={<BR8Page />} />
        </Routes>
      </main>
    </div>
  );
}
