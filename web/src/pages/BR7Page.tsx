// BR7: frequently bought together. Same layout and shared classes as BR2Page.
// Owner: Nguyen. Calls GET /api/br7/anchors and GET /api/br7/affinity (serving/api/routers/br7.py).
import { useEffect, useState } from 'react';
import { Search, RefreshCw, ShoppingBag } from 'lucide-react';
import type { ApiResponse, AffinityRow } from '../types/api';
import QueryMeta from '../components/QueryMeta';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';

// The API adds three display fields on top of the frozen AffinityRow (see API_CONTRACT).
type RelatedRow = AffinityRow & {
  brand?: string | null;
  category_l1?: string | null;
  price?: number | null;
};
type Anchor = { product_id: number; partners: number };

export default function BR7Page() {
  const [input, setInput] = useState('');
  const [asked, setAsked] = useState<number | null>(null);
  const [response, setResponse] = useState<ApiResponse<RelatedRow> | null>(null);
  const [anchors, setAnchors] = useState<Anchor[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Offer ids that are known to work, so the screen never opens as a dead end.
  useEffect(() => {
    fetch(`${API_BASE}/api/br7/anchors`)
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json() as Promise<ApiResponse<Anchor>>;
      })
      .then(json => setAnchors(json.data))
      .catch(e => setError(String(e)));
  }, []);

  const search = (raw: string) => {
    const id = Number(raw.trim());
    if (!raw.trim() || !Number.isInteger(id) || id < 0) {
      setError('Enter a product id using digits only, for example 1004856.');
      return;
    }
    setLoading(true);
    setError(null);
    fetch(`${API_BASE}/api/br7/affinity?product_id=${id}`)
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json() as Promise<ApiResponse<RelatedRow>>;
      })
      .then(json => { setAsked(id); setResponse(json); })
      .catch(e => setError(String(e)))
      .finally(() => setLoading(false));
  };

  const pick = (id: number) => { setInput(String(id)); search(String(id)); };

  const rows = response?.data ?? [];
  const maxLift = rows.length ? Math.max(...rows.map(r => r.lift)) : 1;

  return (
    <div className="page">
      {/* ── Page Header ─────────────────────────────────────── */}
      <div className="page-header">
        <div className="page-header__left">
          <div className="page-header__breadcrumb">
            <span>Modules</span>
            <span className="page-header__sep">/</span>
            <span className="page-header__current">BR7</span>
          </div>
          <h1 className="page-header__title">Bought Together</h1>
          <p className="page-header__description">
            Products that shoppers purchased in the same session as an anchor product
          </p>
        </div>

        {/* ── Toolbar: product search ─────────────────────── */}
        <div className="toolbar">
          <div className="toolbar__item">
            <Search size={13} strokeWidth={1.75} className="toolbar__icon" />
            <span className="toolbar__label">Product ID</span>
            <input
              type="text"
              inputMode="numeric"
              className="toolbar__input"
              placeholder="1004856"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && search(input)}
            />
          </div>
          <div className="toolbar__sep" />
          <button className="br7-go" onClick={() => search(input)} disabled={loading}>
            Find related
          </button>
        </div>
      </div>

      <style>{css}</style>

      {/* Known-good ids */}
      {anchors.length > 0 && (
        <div className="br7-chips">
          <span className="br7-chips__label">Try</span>
          {anchors.map(a => (
            <button key={a.product_id} className="br7-chip" onClick={() => pick(a.product_id)}>
              {a.product_id}
            </button>
          ))}
        </div>
      )}

      {/* ── Status Messages ─────────────────────────────────── */}
      {loading && (
        <div className="status-banner">
          <RefreshCw size={14} className="spin" />
          <span>Synchronizing pipeline query...</span>
        </div>
      )}

      {error && (
        <div className="status-banner status-banner--error">
          <span>{error}</span>
        </div>
      )}

      {/* ── Before the first search ─────────────────────────── */}
      {!loading && !error && !response && (
        <div className="empty-panel">
          <ShoppingBag size={28} strokeWidth={1.5} className="empty-panel__icon" />
          <h3 className="empty-panel__title">Pick a product</h3>
          <p className="empty-panel__desc">
            Enter a product ID above, or choose one of the suggested IDs.
          </p>
        </div>
      )}

      {/* ── Empty State ─────────────────────────────────────── */}
      {!loading && !error && response && rows.length === 0 && (
        <div className="empty-panel">
          <Search size={28} strokeWidth={1.5} className="empty-panel__icon" />
          <h3 className="empty-panel__title">No Recommendations</h3>
          <p className="empty-panel__desc">
            Too few shoppers bought product {asked} together with other products.
            Pick one of the suggested IDs.
          </p>
        </div>
      )}

      {/* ── Results ─────────────────────────────────────────── */}
      {!loading && !error && response && rows.length > 0 && (
        <div className="content-stack">
          <div className="panel">
            <div className="panel__header">
              <div className="panel__title-group">
                <h2 className="panel__title">Frequently Bought With {asked}</h2>
                <span className="panel__subtitle">
                  Ranked by sessions bought together · lift above 1
                </span>
              </div>
            </div>

            <div className="panel__table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Product</th>
                    <th>Brand</th>
                    <th>Category</th>
                    <th>Price</th>
                    <th>Sessions Together</th>
                    <th>Lift</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map(r => (
                    <tr key={r.product_b}>
                      <td className="data-table__numeric font-mono text-emphasis">{r.product_b}</td>
                      <td className="text-secondary">{r.brand ?? 'unknown'}</td>
                      <td className="text-secondary">{r.category_l1 ?? 'unknown'}</td>
                      <td className="data-table__numeric font-mono text-secondary">
                        {r.price != null ? r.price.toFixed(2) : '—'}
                      </td>
                      <td className="data-table__numeric font-mono">{r.co_count.toLocaleString()}</td>
                      <td className="data-table__numeric font-mono text-emphasis">
                        <span
                          className="br7-bar"
                          style={{ width: `${Math.max((r.lift / maxLift) * 72, 3)}px` }}
                        />
                        {r.lift.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* ── Telemetry Footer ───────────────────────────── */}
            <div className="panel__footer">
              <QueryMeta meta={response.meta} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Only what the shared stylesheet does not already provide. Colours are BR2's:
// #0071e3 accent, #86868b secondary, #f5f5f7 text, white at low alpha for borders.
const css = `
.br7-go { padding: 5px 12px; font: inherit; font-size: 13px; font-weight: 500; color: #fff;
  background: #0071e3; border: 0; border-radius: 6px; cursor: pointer; }
.br7-go:disabled { opacity: .5; cursor: default; }
.br7-chips { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; margin: 0 0 16px; }
.br7-chips__label { color: #86868b; font-size: 12px; margin-right: 4px; }
.br7-chip { padding: 3px 10px; font: inherit; font-family: monospace; font-size: 12px; color: #f5f5f7;
  background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); border-radius: 999px; cursor: pointer; }
.br7-chip:hover { border-color: #0071e3; }
.br7-go:focus-visible, .br7-chip:focus-visible { outline: 2px solid #2997ff; outline-offset: 2px; }
.br7-bar { display: inline-block; height: 6px; margin-right: 8px; vertical-align: middle;
  background: #0071e3; border-radius: 3px; }
`;