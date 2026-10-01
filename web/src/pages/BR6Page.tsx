import { useCallback, useEffect, useState } from 'react';
import {
  AlertTriangle,
  AlertCircle,
  CheckCircle2,
  Package,
  Filter as FilterIcon,
  RefreshCw,
  Search,
  Warehouse as WarehouseIcon,
} from 'lucide-react';
import type { ApiResponse, StockoutRow } from '../types/api';
import QueryMeta from '../components/QueryMeta';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';

// Warehouse labels matching DIM_WAREHOUSE_ROWS in serving/load_star_postgres.py.
const WAREHOUSE_NAMES: Record<number, string> = {
  1: 'WH-HAN (Hanoi)',
  2: 'WH-HCM (Ho Chi Minh)',
  3: 'WH-DAD (Da Nang)',
  4: 'WH-CTO (Can Tho)',
  5: 'WH-HPG (Hai Phong)',
};

// Urgency bands — matches SYSTEM_DESIGN.md and models.py docstring.
// days_to_stockout = 9999.0 means zero velocity (sentinel).
const SENTINEL = 9999.0;

function urgency(days: number): 'critical' | 'warning' | 'ok' | 'idle' {
  if (days >= SENTINEL) return 'idle';
  if (days < 3)         return 'critical';
  if (days < 7)         return 'warning';
  return 'ok';
}

function UrgencyBadge({ days }: { days: number }) {
  const level = urgency(days);
  const label =
    level === 'idle'     ? 'No sales'     :
    level === 'critical' ? `${days.toFixed(1)} d 🔴` :
    level === 'warning'  ? `${days.toFixed(1)} d 🟡` :
                           `${days.toFixed(1)} d ✅`;

  const classMap = {
    critical: 'badge badge--danger',
    warning:  'badge badge--warning',
    ok:       'badge badge--success',
    idle:     'badge badge--neutral',
  };

  return <span className={classMap[level]}>{label}</span>;
}

// KPI helper: count rows in each urgency band across all visible rows.
function computeKpis(rows: StockoutRow[]) {
  return rows.reduce(
    (acc, r) => {
      const u = urgency(r.days_to_stockout);
      acc[u] = (acc[u] ?? 0) + 1;
      return acc;
    },
    { critical: 0, warning: 0, ok: 0, idle: 0 } as Record<string, number>,
  );
}

export default function BR6Page() {
  const [warehouseFilter, setWarehouseFilter] = useState<string>('');   // '' = all
  const [maxDays, setMaxDays]                  = useState<string>('');   // '' = no limit
  const [inputMaxDays, setInputMaxDays]        = useState<string>('');   // controlled input

  const [response, setResponse]   = useState<ApiResponse<StockoutRow> | null>(null);
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState<string | null>(null);

  // Build query URL from current filter state.
  const buildUrl = useCallback(() => {
    const params = new URLSearchParams();
    if (warehouseFilter !== '') params.set('warehouse_id', warehouseFilter);
    if (maxDays !== '')         params.set('max_days',     maxDays);
    const qs = params.toString();
    return `${API_BASE}/api/br6/stockout${qs ? '?' + qs : ''}`;
  }, [warehouseFilter, maxDays]);

  // Fetch — no auto-refresh since this is batch data (written once by batch_gold.py).
  const fetchData = useCallback(() => {
    setLoading(true);
    setError(null);
    fetch(buildUrl())
      .then(async r => {
        if (!r.ok) {
          const body = await r.json().catch(() => null);
          throw new Error(body?.detail ?? `HTTP ${r.status}`);
        }
        return r.json() as Promise<ApiResponse<StockoutRow>>;
      })
      .then(json => {
        setResponse(json);
        setLoading(false);
      })
      .catch(e => {
        setError(e.message ?? String(e));
        setLoading(false);
      });
  }, [buildUrl]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const rows = response?.data ?? [];
  const kpis = computeKpis(rows);
  const warehouseLabel =
    warehouseFilter !== ''
      ? WAREHOUSE_NAMES[parseInt(warehouseFilter, 10)] ?? `Warehouse ${warehouseFilter}`
      : 'All warehouses';

  return (
    <div className="page">
      {/* ── Page Header ─────────────────────────────────────── */}
      <div className="page-header">
        <div className="page-header__left">
          <div className="page-header__breadcrumb">
            <span>Modules</span>
            <span className="page-header__sep">/</span>
            <span className="page-header__current">BR6</span>
          </div>
          <h1 className="page-header__title">Stockout Risk</h1>
          <p className="page-header__description">
            SKUs sorted by days until stockout, most urgent first. Powered by{' '}
            <code>stockout_risk</code> on Cassandra (batch, refreshed daily by{' '}
            <code>batch_gold.py</code>).
          </p>
        </div>

        {/* ── Toolbar ─────────────────────────────────────────── */}
        <div className="toolbar">
          <div className="toolbar__item">
            <WarehouseIcon size={13} strokeWidth={1.75} className="toolbar__icon" />
            <span className="toolbar__label">Warehouse</span>
            <select
              id="br6-warehouse-select"
              className="toolbar__select"
              value={warehouseFilter}
              onChange={e => setWarehouseFilter(e.target.value)}
            >
              <option value="">All warehouses</option>
              {Object.entries(WAREHOUSE_NAMES).map(([id, name]) => (
                <option key={id} value={id}>{name}</option>
              ))}
            </select>
          </div>

          <div className="toolbar__sep" />

          <div className="toolbar__item">
            <FilterIcon size={13} strokeWidth={1.75} className="toolbar__icon" />
            <span className="toolbar__label">Max days</span>
            <input
              id="br6-max-days-input"
              type="number"
              className="toolbar__input"
              placeholder="—"
              min="0"
              step="1"
              value={inputMaxDays}
              onChange={e => setInputMaxDays(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter') {
                  const v = parseFloat(inputMaxDays);
                  setMaxDays(isFinite(v) && v > 0 ? String(v) : '');
                }
              }}
            />
            <button
              id="br6-apply-filter-btn"
              className="toolbar__btn"
              onClick={() => {
                const v = parseFloat(inputMaxDays);
                setMaxDays(isFinite(v) && v > 0 ? String(v) : '');
              }}
            >
              Apply
            </button>
            {maxDays !== '' && (
              <button
                id="br6-clear-filter-btn"
                className="toolbar__btn toolbar__btn--ghost"
                onClick={() => { setInputMaxDays(''); setMaxDays(''); }}
              >
                ✕
              </button>
            )}
          </div>

          <div className="toolbar__sep" />

          <div className="toolbar__item">
            <RefreshCw
              size={13}
              strokeWidth={1.75}
              className={`toolbar__icon${loading ? ' spin' : ''}`}
            />
            <button
              id="br6-refresh-btn"
              className="toolbar__btn"
              onClick={fetchData}
              disabled={loading}
            >
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* ── Loading / Error banners ─────────────────────────── */}
      {loading && response === null && (
        <div className="status-banner">
          <RefreshCw size={14} className="spin" />
          <span>Querying stockout_risk…</span>
        </div>
      )}

      {error && (
        <div className="status-banner status-banner--error">
          <AlertCircle size={14} />
          <span>Failed to load: {error}</span>
        </div>
      )}

      {/* ── Empty state ─────────────────────────────────────── */}
      {response && rows.length === 0 && (
        <div className="empty-panel">
          <Search size={28} strokeWidth={1.5} className="empty-panel__icon" />
          <h3 className="empty-panel__title">No SKUs found</h3>
          <p className="empty-panel__desc">
            No stockout risk data for <strong>{warehouseLabel}</strong>
            {maxDays !== '' ? ` with max days ≤ ${maxDays}` : ''}.{' '}
            Run <code>python processing/batch_gold.py --br6</code> to populate
            Cassandra from <code>fact_inventory_daily</code>.
          </p>
        </div>
      )}

      {/* ── KPI ribbon + table ───────────────────────────────── */}
      {response && rows.length > 0 && (
        <div className="content-stack">
          {/* KPI ribbon */}
          <div className="kpi-ribbon">
            <div className="kpi-ribbon__cell">
              <span className="kpi-ribbon__label">Critical</span>
              <div
                className="kpi-ribbon__value"
                style={{ color: kpis.critical > 0 ? 'var(--danger-subtle)' : undefined }}
              >
                <AlertTriangle size={18} strokeWidth={2} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '6px' }} />
                {kpis.critical.toLocaleString()}
              </div>
              <span className="kpi-ribbon__hint">SKUs out in &lt; 3 days</span>
            </div>

            <div className="kpi-ribbon__cell">
              <span className="kpi-ribbon__label">Warning</span>
              <div
                className="kpi-ribbon__value"
                style={{ color: kpis.warning > 0 ? '#f5a623' : undefined }}
              >
                <AlertCircle size={18} strokeWidth={2} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '6px' }} />
                {kpis.warning.toLocaleString()}
              </div>
              <span className="kpi-ribbon__hint">SKUs out in 3–7 days</span>
            </div>

            <div className="kpi-ribbon__cell">
              <span className="kpi-ribbon__label">Healthy</span>
              <div className="kpi-ribbon__value">
                <CheckCircle2 size={18} strokeWidth={2} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '6px', color: 'var(--success-subtle)' }} />
                {kpis.ok.toLocaleString()}
              </div>
              <span className="kpi-ribbon__hint">SKUs with &gt; 7 days stock</span>
            </div>

            <div className="kpi-ribbon__cell">
              <span className="kpi-ribbon__label">Idle</span>
              <div className="kpi-ribbon__value">
                <Package size={18} strokeWidth={2} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '6px' }} />
                {kpis.idle.toLocaleString()}
              </div>
              <span className="kpi-ribbon__hint">No sales in last 7 days (sentinel 9999)</span>
            </div>
          </div>

          {/* Main table */}
          <div className="panel">
            <div className="panel__header">
              <div className="panel__title-group">
                <h2 className="panel__title">Stockout Risk — {warehouseLabel}</h2>
                <span className="panel__subtitle">
                  Most urgent SKUs first · {rows.length.toLocaleString()} rows
                  {maxDays !== '' ? ` · max days ≤ ${maxDays}` : ''}
                  {' '}· Cassandra <code>stockout_risk</code>
                </span>
              </div>
            </div>

            <div className="panel__table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Product ID</th>
                    <th>Warehouse</th>
                    <th>Days to Stockout</th>
                    <th className="data-table__numeric">Stock on Hand</th>
                    <th className="data-table__numeric">Velocity 7d (units/day)</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row, idx) => {
                    const level = urgency(row.days_to_stockout);
                    const rowClass =
                      level === 'critical' ? 'data-table__row--danger' :
                      level === 'warning'  ? 'data-table__row--warning' :
                      '';
                    return (
                      <tr key={`${row.warehouse_id}-${row.product_id}-${idx}`} className={rowClass}>
                        <td className="font-mono">{row.product_id}</td>
                        <td>{WAREHOUSE_NAMES[row.warehouse_id] ?? `WH-${row.warehouse_id}`}</td>
                        <td>
                          <UrgencyBadge days={row.days_to_stockout} />
                        </td>
                        <td className="data-table__numeric font-mono">
                          {row.stock_on_hand.toLocaleString()}
                        </td>
                        <td className="data-table__numeric font-mono">
                          {row.velocity_7d === 0
                            ? <span style={{ color: 'var(--text-secondary)' }}>0.0</span>
                            : row.velocity_7d.toFixed(2)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <div className="panel__footer">
              <QueryMeta meta={response.meta} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
