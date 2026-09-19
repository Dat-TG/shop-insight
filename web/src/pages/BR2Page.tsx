import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell,
  ResponsiveContainer,
} from 'recharts';
import {
  Eye,
  ShoppingCart,
  CreditCard,
  Search,
  Calendar,
  Filter as FilterIcon,
  RefreshCw,
} from 'lucide-react';
import type { ApiResponse, FunnelRow } from '../types/api';
import QueryMeta from '../components/QueryMeta';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';

// Apple-inspired restrained color scheme for data steps (Monochrome / Apple Blue / Slate)
const STEP_CONFIG: Record<string, { label: string; icon: typeof Eye; color: string; tint: string }> = {
  view: {
    label: 'View',
    icon: Eye,
    color: '#0071e3', // Apple Blue
    tint: 'rgba(0, 113, 227, 0.1)',
  },
  cart: {
    label: 'Cart',
    icon: ShoppingCart,
    color: '#2997ff', // Apple Light Blue
    tint: 'rgba(41, 151, 255, 0.1)',
  },
  purchase: {
    label: 'Purchase',
    icon: CreditCard,
    color: '#30d158', // Apple Mint/Green (subdued)
    tint: 'rgba(48, 209, 88, 0.1)',
  },
};

export default function BR2Page() {
  const [startDate, setStartDate] = useState('2019-11-01');
  const [endDate, setEndDate]     = useState('2019-11-30');
  const [category, setCategory]   = useState('all');

  const [response, setResponse] = useState<ApiResponse<FunnelRow> | null>(null);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState<string | null>(null);

  const fetchFunnel = () => {
    setLoading(true);
    setError(null);
    const url = `${API_BASE}/api/br2/funnel?start_date=${startDate}&end_date=${endDate}&category_l1=${category}`;
    fetch(url)
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json() as Promise<ApiResponse<FunnelRow>>;
      })
      .then(json => setResponse(json))
      .catch(e => setError(String(e)))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchFunnel(); }, [startDate, endDate, category]); // eslint-disable-line react-hooks/exhaustive-deps

  const dataRows = response?.data ?? [];

  const viewCount = dataRows.find(r => r.step === 'view')?.count ?? 0;
  const cartCount = dataRows.find(r => r.step === 'cart')?.count ?? 0;
  const purchaseCount = dataRows.find(r => r.step === 'purchase')?.count ?? 0;

  const viewToCartPct = viewCount > 0 ? ((cartCount / viewCount) * 100).toFixed(2) : '0.00';
  const cartToPurchasePct = cartCount > 0 ? ((purchaseCount / cartCount) * 100).toFixed(2) : '0.00';
  const overallConvPct = viewCount > 0 ? ((purchaseCount / viewCount) * 100).toFixed(2) : '0.00';

  const chartData = dataRows.map(row => {
    const config = STEP_CONFIG[row.step] ?? { label: row.step, color: '#86868b' };
    return {
      ...row,
      displayName: config.label,
      pctOfViews: `${(row.conversion_rate * 100).toFixed(2)}%`,
    };
  });

  return (
    <div className="page">
      {/* ── Page Header ─────────────────────────────────────── */}
      <div className="page-header">
        <div className="page-header__left">
          <div className="page-header__breadcrumb">
            <span>Modules</span>
            <span className="page-header__sep">/</span>
            <span className="page-header__current">BR2</span>
          </div>
          <h1 className="page-header__title">Conversion Funnel</h1>
          <p className="page-header__description">
            Analysis of customer progression and drop-off from item impression to checkout
          </p>
        </div>

        {/* ── Toolbar / Filter Bar (Apple-style inline controls) ── */}
        <div className="toolbar">
          <div className="toolbar__item">
            <Calendar size={13} strokeWidth={1.75} className="toolbar__icon" />
            <span className="toolbar__label">From</span>
            <input
              type="date"
              className="toolbar__input"
              value={startDate}
              min="2019-11-01"
              max="2019-11-30"
              onChange={e => setStartDate(e.target.value)}
            />
          </div>

          <div className="toolbar__sep" />

          <div className="toolbar__item">
            <span className="toolbar__label">To</span>
            <input
              type="date"
              className="toolbar__input"
              value={endDate}
              min="2019-11-01"
              max="2019-11-30"
              onChange={e => setEndDate(e.target.value)}
            />
          </div>

          <div className="toolbar__sep" />

          <div className="toolbar__item">
            <FilterIcon size={13} strokeWidth={1.75} className="toolbar__icon" />
            <span className="toolbar__label">Category</span>
            <select
              className="toolbar__select"
              value={category}
              onChange={e => setCategory(e.target.value)}
            >
              <option value="all">All Categories</option>
              <option value="electronics">Electronics</option>
              <option value="appliances">Appliances</option>
              <option value="computers">Computers</option>
              <option value="furniture">Furniture</option>
            </select>
          </div>
        </div>
      </div>

      {/* ── Status Messages ─────────────────────────────────── */}
      {loading && (
        <div className="status-banner">
          <RefreshCw size={14} className="spin" />
          <span>Synchronizing pipeline query...</span>
        </div>
      )}

      {error && (
        <div className="status-banner status-banner--error">
          <span>Failed to query funnel data: {error}</span>
        </div>
      )}

      {/* ── Empty State ─────────────────────────────────────── */}
      {!loading && !error && response && dataRows.length === 0 && (
        <div className="empty-panel">
          <Search size={28} strokeWidth={1.5} className="empty-panel__icon" />
          <h3 className="empty-panel__title">No Events Recorded</h3>
          <p className="empty-panel__desc">
            No funnel records matched your selected date range and category filter.
          </p>
        </div>
      )}

      {/* ── Main Data View ──────────────────────────────────── */}
      {!loading && !error && response && dataRows.length > 0 && (
        <div className="content-stack">
          {/* ── Minimalist KPI Ribbon (Single unified strip of 4 cells) ── */}
          <div className="kpi-ribbon">
            <div className="kpi-ribbon__cell">
              <span className="kpi-ribbon__label">Total Views</span>
              <div className="kpi-ribbon__value">{viewCount.toLocaleString()}</div>
              <span className="kpi-ribbon__hint">100% Top of Funnel</span>
            </div>

            <div className="kpi-ribbon__cell">
              <span className="kpi-ribbon__label">Cart Additions</span>
              <div className="kpi-ribbon__value">{cartCount.toLocaleString()}</div>
              <span className="kpi-ribbon__hint">{viewToCartPct}% view-to-cart</span>
            </div>

            <div className="kpi-ribbon__cell">
              <span className="kpi-ribbon__label">Purchases</span>
              <div className="kpi-ribbon__value">{purchaseCount.toLocaleString()}</div>
              <span className="kpi-ribbon__hint">{cartToPurchasePct}% cart-to-buy</span>
            </div>

            <div className="kpi-ribbon__cell">
              <span className="kpi-ribbon__label">Overall Conversion</span>
              <div className="kpi-ribbon__value">{overallConvPct}%</div>
              <span className="kpi-ribbon__hint">End-to-end efficiency</span>
            </div>
          </div>

          {/* ── Main Panel: Chart & Detailed Table ─────────────── */}
          <div className="panel">
            <div className="panel__header">
              <div className="panel__title-group">
                <h2 className="panel__title">Funnel Progression Flow</h2>
                <span className="panel__subtitle">
                  {startDate} — {endDate} · {category === 'all' ? 'All Catalog Segments' : category}
                </span>
              </div>
            </div>

            {/* Recharts Bar Visualization */}
            <div className="panel__chart">
              <ResponsiveContainer width="100%" height={230}>
                <BarChart
                  data={chartData}
                  layout="vertical"
                  margin={{ top: 12, right: 36, left: 60, bottom: 8 }}
                >
                  <CartesianGrid strokeDasharray="2 2" stroke="rgba(255,255,255,0.06)" horizontal={false} />
                  <XAxis
                    type="number"
                    axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
                    tickLine={false}
                    tick={{ fill: '#86868b', fontSize: 11, fontFamily: 'monospace' }}
                    tickFormatter={v => v.toLocaleString()}
                  />
                  <YAxis
                    type="category"
                    dataKey="displayName"
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: '#f5f5f7', fontSize: 13, fontWeight: 500 }}
                  />
                  <Tooltip
                    cursor={{ fill: 'rgba(255,255,255,0.03)' }}
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload;
                        return (
                          <div className="chart-tooltip">
                            <div className="chart-tooltip__title">{data.displayName} Stage</div>
                            <div className="chart-tooltip__item">
                              <span className="chart-tooltip__label">Volume:</span>
                              <span className="chart-tooltip__value font-mono">
                                {data.count.toLocaleString()}
                              </span>
                            </div>
                            <div className="chart-tooltip__item">
                              <span className="chart-tooltip__label">Retention:</span>
                              <span className="chart-tooltip__value font-mono">
                                {data.pctOfViews}
                              </span>
                            </div>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Bar dataKey="count" radius={[0, 4, 4, 0]} barSize={26}>
                    {chartData.map(row => (
                      <Cell
                        key={row.step}
                        fill={STEP_CONFIG[row.step]?.color ?? '#0071e3'}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* ── Table: Precise Step Breakdown ──────────────── */}
            <div className="panel__table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Funnel Stage</th>
                    <th>Events Count</th>
                    <th>Unique Sessions</th>
                    <th>Stage Retention</th>
                    <th>Drop-off</th>
                  </tr>
                </thead>
                <tbody>
                  {dataRows.map((row, idx) => {
                    const stepCfg = STEP_CONFIG[row.step];
                    const StepIcon = stepCfg?.icon ?? Eye;
                    const prevCount = idx > 0 ? dataRows[idx - 1].count : row.count;
                    const dropOffPct = idx === 0
                      ? '0.00%'
                      : `${(((prevCount - row.count) / prevCount) * 100).toFixed(2)}%`;

                    return (
                      <tr key={row.step}>
                        <td className="data-table__stage-cell">
                          <span
                            className="data-table__step-indicator"
                            style={{ backgroundColor: stepCfg?.color ?? '#86868b' }}
                          />
                          <StepIcon size={14} strokeWidth={1.75} className="data-table__step-icon" />
                          <span className="data-table__step-name">{stepCfg?.label ?? row.step}</span>
                        </td>
                        <td className="data-table__numeric font-mono">
                          {row.count.toLocaleString()}
                        </td>
                        <td className="data-table__numeric font-mono text-secondary">
                          {row.session_count.toLocaleString()}
                        </td>
                        <td className="data-table__numeric font-mono text-emphasis">
                          {(row.conversion_rate * 100).toFixed(2)}%
                        </td>
                        <td className="data-table__numeric font-mono text-muted">
                          {idx === 0 ? '—' : `-${dropOffPct}`}
                        </td>
                      </tr>
                    );
                  })}
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

