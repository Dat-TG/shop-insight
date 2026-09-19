import { NavLink, Route, Routes } from 'react-router-dom';
import {
  Activity,
  Filter,
  Flame,
  Users,
  ShoppingCart,
  AlertCircle,
  GitFork,
  Zap,
  Layers,
} from 'lucide-react';
import BR1Page from './pages/BR1Page';
import BR2Page from './pages/BR2Page';
import BR3Page from './pages/BR3Page';
import BR4Page from './pages/BR4Page';
import BR5Page from './pages/BR5Page';
import BR6Page from './pages/BR6Page';
import BR7Page from './pages/BR7Page';
import BR8Page from './pages/BR8Page';

const NAV_TABS = [
  { path: '/br1', label: 'Real-time Ops', id: 'BR1', icon: Activity },
  { path: '/br2', label: 'Conversion Funnel', id: 'BR2', icon: Filter },
  { path: '/br3', label: 'Trending Products', id: 'BR3', icon: Flame },
  { path: '/br4', label: 'RFM Segments', id: 'BR4', icon: Users },
  { path: '/br5', label: 'Abandoned Carts', id: 'BR5', icon: ShoppingCart },
  { path: '/br6', label: 'Stockout Risk', id: 'BR6', icon: AlertCircle },
  { path: '/br7', label: 'Product Affinity', id: 'BR7', icon: GitFork },
  { path: '/br8', label: 'Order Velocity', id: 'BR8', icon: Zap },
] as const;

export default function App() {
  return (
    <div className="app">
      {/* ── Minimalist Apple-like Top Bar ──────────────────── */}
      <header className="header">
        <div className="header__brand">
          <div className="header__icon-box">
            <Layers size={18} strokeWidth={2} />
          </div>
          <div className="header__titles">
            <span className="header__title">ShopInsight</span>
            <span className="header__badge">Data Platform</span>
          </div>
        </div>

        {/* ── Segmented Navigation Control ─────────────────── */}
        <nav className="navbar" aria-label="Module Navigation">
          <div className="navbar__segmented">
            {NAV_TABS.map(tab => {
              const Icon = tab.icon;
              return (
                <NavLink
                  key={tab.path}
                  to={tab.path}
                  className={({ isActive }) =>
                    ['navbar__tab', isActive ? 'navbar__tab--active' : ''].filter(Boolean).join(' ')
                  }
                >
                  <Icon size={14} strokeWidth={1.75} className="navbar__icon" />
                  <span className="navbar__id">{tab.id}</span>
                  <span className="navbar__label">{tab.label}</span>
                </NavLink>
              );
            })}
          </div>
        </nav>

        <div className="header__meta">
          <span className="header__status-dot" />
          <span className="header__meta-text">CO5173 · Team 15</span>
        </div>
      </header>

      {/* ── Main Content Area ──────────────────────────────── */}
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

