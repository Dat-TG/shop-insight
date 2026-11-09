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
import type { ApiResponse, FunnelRow, QueryMeta as QueryMetaType } from '../types/api';
import QueryMeta from '../components/QueryMeta';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';

// funnel_daily holds 31 session start dates (Vietnam time). 1 Dec is the last
// seven hours of 30 Nov UTC, so it is a partial day; the default range leaves it out.
const FIRST_DAY = '2019-11-01';
const LAST_DAY = '2019-12-01';
// The source file has almost no purchase between 15 Nov 01:09 and 16 Nov 15:32
// Vietnam time (SYSTEM_DESIGN 3.1). It is in the data, not a pipeline bug.
const HOLE_DAY = '2019-11-15';

// Silver's 14 category_l1 values, busiest first, copied from BR1Page. 'all' is a
// stored row in funnel_daily, not a sum made here.
const CATEGORIES = [
  'electronics', 'unknown', 'appliances', 'computers', 'apparel', 'furniture', 'auto',
  'construction', 'kids', 'accessories', 'sport', 'medicine', 'country_yard', 'stationery',
];

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

// A rate with a zero denominator is "—", never NaN: a small category on one day
// can have sessions that viewed and none that reached the cart.
function pct(numerator: number, denominator: number) {
  return denominator > 0 ? `${((numerator / denominator) * 100).toFixed(2)}%` : '—';
}

function sessionsAt(rows: FunnelRow[], step: FunnelRow['step']) {
  return rows.find(r => r.step === step)?.session_count ?? 0;
}

async function fetchFunnel(
  startDate: string, endDate: string, category: string, signal: AbortSignal,
): Promise<ApiResponse<FunnelRow>> {
  const query = new URLSearchParams({ start_date: startDate, end_date: endDate, category_l1: category });
  const r = await fetch(`${API_BASE}/api/br2/funnel?${query}`, { signal });
  if (!r.ok) {
    const body = await r.json().catch(() => null);
    throw new Error(body?.detail ?? `HTTP ${r.status}`);
  }
  return r.json() as Promise<ApiResponse<FunnelRow>>;
}

interface CategoryFunnel {
  category: string;
  rows: FunnelRow[];
}

interface CategoryTable {
  entries: CategoryFunnel[];
  meta: QueryMetaType;
}

// One request per category, as BR4 builds its heatmap: the contract returns the
// three steps of one category, so the table is 15 calls to the same endpoint. The
// footer shows the slowest call, the most partitions any call read, and all rows.
function buildCategoryTable(responses: ApiResponse<FunnelRow>[], categories: string[]): CategoryTable {
  const entries = responses.map((response, i) => ({ category: categories[i], rows: response.data }));
  const [all, ...rest] = entries;
  rest.sort((a, b) => sessionsAt(b.rows, 'view') - sessionsAt(a.rows, 'view'));
  const metas = responses.map(response => response.meta);
  return {
    entries: [all, ...rest],
    meta: {
      ms: Math.max(...metas.map(meta => meta.ms)),
      warehouse: metas[0].warehouse,
      partitions: Math.max(...metas.map(meta => meta.partitions)),
      rows: metas.reduce((sum, meta) => sum + meta.rows, 0),
    },
  };
}

export default function BR2Page() {
  const [startDate, setStartDate] = useState(FIRST_DAY);
  const [endDate, setEndDate]     = useState('2019-11-30');
  const [category, setCategory]   = useState('all');

  const [response, setResponse] = useState<ApiResponse<FunnelRow> | null>(null);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState<string | null>(null);

  const [byCategory, setByCategory]     = useState<CategoryTable | null>(null);
  const [categoryError, setCategoryError] = useState<string | null>(null);

  // The tab title matches the page title (as BR7Page does).
  useEffect(() => {
    const previousTitle = document.title;
    document.title = 'Conversion Funnel';
    return () => { document.title = previousTitle; };
  }, []);

  // The funnel for the selected category. A filter change aborts a request still
  // in flight, so a late answer for the previous filter never lands on screen.
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    fetchFunnel(startDate, endDate, category, controller.signal)
      .then(json => {
        setResponse(json);
        setLoading(false);
      })
      .catch(e => {
        if (e.name === 'AbortError') return;
        setError(e.message ?? String(e));
        setLoading(false);
      });
    return () => controller.abort();
  }, [startDate, endDate, category]);

  // The by-category table depends on the dates only.
  useEffect(() => {
    const controller = new AbortController();
    const categories = ['all', ...CATEGORIES];
    setByCategory(null);
    setCategoryError(null);
    Promise.all(categories.map(c => fetchFunnel(startDate, endDate, c, controller.signal)))
      .then(responses => setByCategory(buildCategoryTable(responses, categories)))
      .catch(e => {
        if (e.name !== 'AbortError') setCategoryError(e.message ?? String(e));
      });
    return () => controller.abort();
  }, [startDate, endDate]);

  const dataRows = response?.data ?? [];

  // Sessions, not events, drive every rate: a session counts at every step up to
  // the furthest it reached, so the bars always decrease. Event counts do not:
  // on 1-7 Nov the file has more purchase events than cart events.
  const viewSessions = sessionsAt(dataRows, 'view');
  const cartSessions = sessionsAt(dataRows, 'cart');
  const purchaseSessions = sessionsAt(dataRows, 'purchase');

  const coversHole = startDate <= HOLE_DAY && HOLE_DAY <= endDate;

  const chartData = dataRows.map(row => {
    const config = STEP_CONFIG[row.step] ?? { label: row.step, color: '#86868b' };
    return {
      ...row,
      displayName: config.label,
      pctOfSessions: `${(row.conversion_rate * 100).toFixed(2)}%`,
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
            Sessions that reached view, cart and purchase, by the day the session started (Vietnam time)
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
              min={FIRST_DAY}
              max={LAST_DAY}
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
              min={FIRST_DAY}
              max={LAST_DAY}
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
              {CATEGORIES.map(c => (
                <option key={c} value={c}>{c}</option>
              ))}
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
          <h3 className="empty-panel__title">No Sessions Recorded</h3>
          <p className="empty-panel__desc">
            No session started in this date range and category. funnel_daily holds
            sessions that started from {FIRST_DAY} to {LAST_DAY}.
          </p>
          <div className="panel__footer">
            <QueryMeta meta={response.meta} />
          </div>
        </div>
      )}

      {/* ── Main Data View ──────────────────────────────────── */}
      {!loading && !error && response && dataRows.length > 0 && (
        <div className="content-stack">
          {/* ── Minimalist KPI Ribbon (Single unified strip of 4 cells) ── */}
          <div className="kpi-ribbon">
            <div className="kpi-ribbon__cell">
              <span className="kpi-ribbon__label">Sessions</span>
              <div className="kpi-ribbon__value">{viewSessions.toLocaleString()}</div>
              <span className="kpi-ribbon__hint">100% Top of Funnel</span>
            </div>

            <div className="kpi-ribbon__cell">
              <span className="kpi-ribbon__label">Reached Cart</span>
              <div className="kpi-ribbon__value">{cartSessions.toLocaleString()}</div>
              <span className="kpi-ribbon__hint">{pct(cartSessions, viewSessions)} view-to-cart</span>
            </div>

            <div className="kpi-ribbon__cell">
              <span className="kpi-ribbon__label">Purchased</span>
              <div className="kpi-ribbon__value">{purchaseSessions.toLocaleString()}</div>
              <span className="kpi-ribbon__hint">{pct(purchaseSessions, cartSessions)} cart-to-buy</span>
            </div>

            <div className="kpi-ribbon__cell">
              <span className="kpi-ribbon__label">Overall Conversion</span>
              <div className="kpi-ribbon__value">{pct(purchaseSessions, viewSessions)}</div>
              <span className="kpi-ribbon__hint">Purchased / sessions</span>
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
                              <span className="chart-tooltip__label">Sessions:</span>
                              <span className="chart-tooltip__value font-mono">
                                {data.session_count.toLocaleString()}
                              </span>
                            </div>
                            <div className="chart-tooltip__item">
                              <span className="chart-tooltip__label">Events:</span>
                              <span className="chart-tooltip__value font-mono">
                                {data.count.toLocaleString()}
                              </span>
                            </div>
                            <div className="chart-tooltip__item">
                              <span className="chart-tooltip__label">Of sessions:</span>
                              <span className="chart-tooltip__value font-mono">
                                {data.pctOfSessions}
                              </span>
                            </div>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Bar dataKey="session_count" radius={[0, 4, 4, 0]} barSize={26} isAnimationActive={false}>
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
                    <th>Sessions</th>
                    <th>Events</th>
                    <th>Of Sessions</th>
                    <th>Drop-off</th>
                  </tr>
                </thead>
                <tbody>
                  {dataRows.map((row, idx) => {
                    const stepCfg = STEP_CONFIG[row.step];
                    const StepIcon = stepCfg?.icon ?? Eye;
                    const previous = idx > 0 ? dataRows[idx - 1].session_count : 0;
                    const dropOff = previous > 0
                      ? `-${(((previous - row.session_count) / previous) * 100).toFixed(2)}%`
                      : '—';

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
                        <td className="data-table__numeric font-mono text-emphasis">
                          {row.session_count.toLocaleString()}
                        </td>
                        <td className="data-table__numeric font-mono text-secondary">
                          {row.count.toLocaleString()}
                        </td>
                        <td className="data-table__numeric font-mono">
                          {(row.conversion_rate * 100).toFixed(2)}%
                        </td>
                        <td className="data-table__numeric font-mono text-muted">
                          {dropOff}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <p className="panel__note">
              A session counts at every step up to the furthest one it reached, so a
              purchase with no cart event still counts as reaching the cart. Events are
              shown for reference.
              {coversHole && (
                <> The source file has almost no purchase from 15 Nov 01:09 to 16 Nov 15:32
                  (Vietnam time), so 15 Nov converts at almost zero.</>
              )}
            </p>

            {/* ── Telemetry Footer ───────────────────────────── */}
            <div className="panel__footer">
              <QueryMeta meta={response.meta} />
            </div>
          </div>
        </div>
      )}

      {/* ── By-category conversion table ───────────────────── */}
      {categoryError && (
        <div className="status-banner status-banner--error">
          <span>Failed to query the category table: {categoryError}</span>
        </div>
      )}

      {byCategory && (
        <div className="panel">
          <div className="panel__header">
            <div className="panel__title-group">
              <h2 className="panel__title">Conversion by Category</h2>
              <span className="panel__subtitle">
                {startDate} — {endDate} · select a row to filter the funnel
              </span>
            </div>
          </div>

          <div className="panel__table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Category</th>
                  <th>Sessions</th>
                  <th>Reached Cart</th>
                  <th>Purchased</th>
                  <th>View → Cart</th>
                  <th>Cart → Purchase</th>
                </tr>
              </thead>
              <tbody>
                {byCategory.entries.map(entry => {
                  const views = sessionsAt(entry.rows, 'view');
                  const carts = sessionsAt(entry.rows, 'cart');
                  const purchases = sessionsAt(entry.rows, 'purchase');
                  const selected = entry.category === category;
                  return (
                    <tr key={entry.category} className={selected ? 'data-table__row--selected' : undefined}>
                      <td>
                        <button
                          type="button"
                          className="category-button"
                          aria-pressed={selected}
                          onClick={() => setCategory(entry.category)}
                        >
                          {entry.category === 'all' ? 'All Categories' : entry.category}
                        </button>
                      </td>
                      <td className="font-mono text-emphasis">{entry.rows.length ? views.toLocaleString() : '—'}</td>
                      <td className="font-mono">{entry.rows.length ? carts.toLocaleString() : '—'}</td>
                      <td className="font-mono">{entry.rows.length ? purchases.toLocaleString() : '—'}</td>
                      <td className="font-mono">{pct(carts, views)}</td>
                      <td className="font-mono">{pct(purchases, carts)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <p className="panel__note">
            A session that touches two categories counts in both, at the step it reached
            in each, so the category rows do not add up to All Categories.
          </p>

          <div className="panel__footer">
            <QueryMeta meta={byCategory.meta} />
          </div>
        </div>
      )}
    </div>
  );
}
