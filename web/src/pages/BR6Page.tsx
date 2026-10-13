import { useEffect, useState } from 'react';
import {
  AlertTriangle,
  Filter as FilterIcon,
  RefreshCw,
  Warehouse,
} from 'lucide-react';
import type { ApiResponse, StockoutRow } from '../types/api';
import QueryMeta from '../components/QueryMeta';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';

// Row colour thresholds (matching SYSTEM_DESIGN.md §9 + data-table__row-- CSS classes
// added in index.css by Tín).
const CRITICAL_DAYS = 3;   // red  — days_to_stockout < 3
const WARNING_DAYS  = 7;   // amber — days_to_stockout < 7
const SENTINEL      = 9999; // means velocity = 0, no recent sales

const WAREHOUSES = [1, 2, 3, 4, 5];

const round2 = (v: number) => Math.round(v * 100) / 100;

function daysLabel(days: number): string {
  if (days >= SENTINEL) return '∞ (no sales)';
  return `${round2(days)} d`;
}

function rowUrgency(days: number): string {
  if (days < CRITICAL_DAYS) return 'data-table__row--danger';
  if (days < WARNING_DAYS)  return 'data-table__row--warning';
  return '';
}

function badgeClass(days: number): string {
  if (days >= SENTINEL) return 'badge badge--neutral';
  if (days < CRITICAL_DAYS) return 'badge badge--danger';
  if (days < WARNING_DAYS)  return 'badge badge--warning';
  return 'badge badge--success';
}

export default function BR6Page() {
  const [warehouseId, setWarehouseId] = useState<string>('all');
  const [maxDays, setMaxDays]         = useState<string>('');

  const [response, setResponse] = useState<ApiResponse<StockoutRow> | null>(null);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState<string | null>(null);

  const fetchData = () => {
    setLoading(true);
    setError(null);
    const params = new URLSearchParams();
    if (warehouseId !== 'all') params.set('warehouse_id', warehouseId);
    if (maxDays !== '') params.set('max_days', maxDays);
    fetch(`${API_BASE}/api/br6/stockout?${params}`)
      .then(async r => {
        if (!r.ok) {
          const body = await r.json().catch(() => null);
          throw new Error(body?.detail ?? `HTTP ${r.status}`);
        }
        return r.json() as Promise<ApiResponse<StockoutRow>>;
      })
      .then(json => setResponse(json))
      .catch(e => setError(String(e)))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); }, [warehouseId, maxDays]); // eslint-disable-line react-hooks/exhaustive-deps

  const rows = response?.data ?? [];
  const criticalCount = rows.filter(r => r.days_to_stockout < CRITICAL_DAYS).length;
  const warningCount  = rows.filter(r => r.days_to_stockout >= CRITICAL_DAYS && r.days_to_stockout < WARNING_DAYS).length;
  const noSalesCount  = rows.filter(r => r.days_to_stockout >= SENTINEL).length;

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
          <h1 className="page-header__title">Inventory Alerts</h1>
          <p className="page-header__description">
            SKUs by days until stockout at current velocity — red under 3 days
          </p>
        </div>

        {/* ── Toolbar ─────────────────────────────────────────── */}
        <div className="toolbar">
          <div className="toolbar__item">
            <Warehouse size={13} strokeWidth={1.75} className="toolbar__icon" />
            <span className="toolbar__label">Warehouse</span>
            <select
              id="br6-warehouse-select"
              className="toolbar__select"
              value={warehouseId}
              onChange={e => setWarehouseId(e.target.value)}
            >
              <option value="all">All Warehouses</option>
              {WAREHOUSES.map(id => (
                <option key={id} value={String(id)}>Warehouse {id}</option>
              ))}
            </select>
          </div>
          <div className="toolbar__sep" />
          <div className="toolbar__item">
            <FilterIcon size={13} strokeWidth={1.75} className="toolbar__icon" />
            <span className="toolbar__label">Max Days</span>
            <input
              type="number"
              id="br6-maxdays-input"
              className="toolbar__input"
              style={{ width: 72 }}
              placeholder="e.g. 7"
              min={1}
              step={1}
              value={maxDays}
              onChange={e => setMaxDays(e.target.value)}
            />
          </div>
          <div className="toolbar__sep" />
          <button
            className="toolbar__btn"
            onClick={fetchData}
            disabled={loading}
            id="br6-refresh-btn"
            title="Refresh"
          >
            <RefreshCw size={13} strokeWidth={1.75} className={loading ? 'spin' : ''} />
          </button>
        </div>
      </div>

      {/* ── Status Messages ─────────────────────────────────── */}
      {loading && !response && (
        <div className="status-banner">
          <RefreshCw size={14} className="spin" />
          <span>Querying Cassandra stockout_risk…</span>
        </div>
      )}
      {error && (
        <div className="status-banner status-banner--error">
          <AlertTriangle size={14} />
          <span>{error}</span>
        </div>
      )}

      {/* ── Summary Cards ────────────────────────────────────── */}
      {response && (
        <div className="br8-summary">
          <div className="br8-summary__card br8-summary__card--high">
            <AlertTriangle size={18} />
            <span className="br8-summary__count">{criticalCount}</span>
            <span className="br8-summary__label">Critical (&lt;3 d)</span>
          </div>
          <div className="br8-summary__card br8-summary__card--medium">
            <AlertTriangle size={18} />
            <span className="br8-summary__count">{warningCount}</span>
            <span className="br8-summary__label">Low Stock (3–7 d)</span>
          </div>
          <div className="br8-summary__card">
            <Warehouse size={18} />
            <span className="br8-summary__count">{noSalesCount}</span>
            <span className="br8-summary__label">No Sales</span>
          </div>
          <div className="br8-summary__card">
            <span className="br8-summary__count">{rows.length}</span>
            <span className="br8-summary__label">Total SKUs</span>
          </div>
        </div>
      )}

      {/* ── Empty State ─────────────────────────────────────── */}
      {!loading && !error && response && rows.length === 0 && (
        <div className="empty-panel">
          <Warehouse size={28} strokeWidth={1.5} className="empty-panel__icon" />
          <h3 className="empty-panel__title">No SKUs Found</h3>
          <p className="empty-panel__desc">
            No stock data for the selected filters. Try a different warehouse or
            remove the max-days filter. The batch job must have run at least once.
          </p>
        </div>
      )}

      {/* ── SKU Table ───────────────────────────────────────── */}
      {!loading && !error && response && rows.length > 0 && (
        <div className="content-stack">
          <div className="panel">
            <div className="panel__header">
              <div className="panel__title-group">
                <h2 className="panel__title">Stockout Risk — Most Urgent First</h2>
                <span className="panel__subtitle">
                  Sorted by days_to_stockout ASC · ∞ = zero velocity last 7 days
                </span>
              </div>
            </div>
            <div className="panel__table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Warehouse</th>
                    <th>Product ID</th>
                    <th>Days to Stockout</th>
                    <th>Stock on Hand</th>
                    <th>Velocity 7d</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row, i) => (
                    <tr key={`${row.warehouse_id}-${row.product_id}-${i}`} className={rowUrgency(row.days_to_stockout)}>
                      <td className="font-mono text-secondary">W{row.warehouse_id}</td>
                      <td className="data-table__numeric font-mono text-emphasis">{row.product_id}</td>
                      <td className="data-table__numeric font-mono">
                        {daysLabel(row.days_to_stockout)}
                      </td>
                      <td className="data-table__numeric font-mono">{row.stock_on_hand.toLocaleString()}</td>
                      <td className="data-table__numeric font-mono">
                        {row.velocity_7d === 0 ? '—' : row.velocity_7d.toFixed(2)}
                      </td>
                      <td>
                        <span className={badgeClass(row.days_to_stockout)}>
                          {row.days_to_stockout >= SENTINEL
                            ? 'No Sales'
                            : row.days_to_stockout < CRITICAL_DAYS
                              ? 'Critical'
                              : row.days_to_stockout < WARNING_DAYS
                                ? 'Low Stock'
                                : 'OK'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="panel__footer">
              {response && <QueryMeta meta={response.meta} />}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
