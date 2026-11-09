import { useEffect, useState } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import {
  ArrowDownRight,
  ArrowUpRight,
  Calendar,
  Filter as FilterIcon,
  Minus,
  RefreshCw,
  Search,
} from 'lucide-react';
import type { ApiResponse, GmvRow } from '../types/api';
import QueryMeta from '../components/QueryMeta';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';

const REFRESH_MS = 10_000;
const MINUTE_MS = 60_000;
// The screen shows 60 minutes and compares them with the 60 before, which the
// API returns in the same response (up to 120 rows, one partition).
const CHART_MINUTES = 60;
// "vs previous" needs the response to reach back about two hours. Ten minutes of
// slack lets a quiet first few minutes pass; a tiny category (stationery: about
// 1,000 events in the month) shows "—" rather than comparing against a hole.
const HISTORY_MINUTES = 110;

// The demo replays this day: python ingestion/replayer.py --speed 60
// --start "2019-11-17 08:00:00" (15:00 in Vietnam), the day with the most purchases.
const DEMO_DATE = '2019-11-17';

// Silver's 14 category_l1 values, busiest first (measured 2026-09-30). 'all' is
// not a sum made here: the stream writes a total row per minute under it.
const CATEGORIES = [
  'electronics', 'unknown', 'appliances', 'computers', 'apparel', 'furniture', 'auto',
  'construction', 'kids', 'accessories', 'sport', 'medicine', 'country_yard', 'stationery',
];

// window_start is the Vietnam wall clock, "2019-11-17T15:04:00+07:00". Reading its
// first 19 characters as UTC gives numbers to do minute arithmetic on, and toISOString
// gives the same wall clock back, so the browser's own time zone never gets involved.
const toMs = (windowStart: string) => Date.parse(`${windowStart.slice(0, 19)}Z`);
const hhmm = (ms: number) => new Date(ms).toISOString().slice(11, 16);

const compact = new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 });
const money = new Intl.NumberFormat('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

interface Slot {
  minute: string;
  gmv: number;
  orders: number;
}

export default function BR1Page() {
  const [eventDate, setEventDate] = useState(DEMO_DATE);
  const [category, setCategory]   = useState('all');

  const [response, setResponse]   = useState<ApiResponse<GmvRow> | null>(null);
  const [error, setError]         = useState<string | null>(null);
  const [fetchedAt, setFetchedAt] = useState<number | null>(null);
  const [now, setNow]             = useState(() => Date.now());

  // The tab title matches the page title (as BR7Page does).
  useEffect(() => {
    const previousTitle = document.title;
    document.title = 'Real-time Operations';
    return () => { document.title = previousTitle; };
  }, []);

  // Fetch now and every 10 s. A filter change starts over: the old interval is
  // cleared and a request still in flight is aborted, so a late answer for the
  // previous filter never lands on screen.
  useEffect(() => {
    let controller: AbortController | null = null;
    const load = () => {
      controller?.abort();
      controller = new AbortController();
      const url = `${API_BASE}/api/br1/realtime?event_date=${eventDate}&category_l1=${encodeURIComponent(category)}`;
      fetch(url, { signal: controller.signal })
        .then(async r => {
          if (!r.ok) {
            // The API says what to run when Cassandra is down (HTTP 503).
            const body = await r.json().catch(() => null);
            throw new Error(body?.detail ?? `HTTP ${r.status}`);
          }
          return r.json() as Promise<ApiResponse<GmvRow>>;
        })
        .then(json => {
          setResponse(json);
          setError(null);
          setFetchedAt(Date.now());
        })
        .catch(e => {
          if (e.name !== 'AbortError') setError(e.message ?? String(e));
        });
    };
    setResponse(null);
    load();
    const timer = setInterval(load, REFRESH_MS);
    return () => {
      clearInterval(timer);
      controller?.abort();
    };
  }, [eventDate, category]);

  // Drives "Updated Ns ago".
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);

  const rows = response?.data ?? [];  // newest minute first, as Cassandra stores them

  // Every minute of the last hour gets a point. A minute with no row had no event
  // at all, so its GMV is honestly 0, not a gap to draw a line across.
  const newest = rows.length > 0 ? toMs(rows[0].window_start) : 0;
  const byMinute = new Map(rows.map(row => [toMs(row.window_start), row]));
  const slots: Slot[] = [];
  for (let i = CHART_MINUTES - 1; i >= 0; i--) {
    const t = newest - i * MINUTE_MS;
    const row = byMinute.get(t);
    slots.push({ minute: hhmm(t), gmv: row?.gmv ?? 0, orders: row?.order_count ?? 0 });
  }

  const hourStart = newest - (CHART_MINUTES - 1) * MINUTE_MS;
  const lastHour = rows.filter(row => toMs(row.window_start) >= hourStart);
  const hourBefore = rows.filter(row => toMs(row.window_start) < hourStart);
  const sum = (list: GmvRow[], pick: (row: GmvRow) => number) => list.reduce((acc, row) => acc + pick(row), 0);

  const gmv = sum(lastHour, row => row.gmv);
  const orders = sum(lastHour, row => row.order_count);
  const previousGmv = sum(hourBefore, row => row.gmv);
  const oldest = rows.length > 0 ? toMs(rows[rows.length - 1].window_start) : newest;
  const hasHistory = newest - oldest >= HISTORY_MINUTES * MINUTE_MS && previousGmv > 0;
  const change = hasHistory ? (gmv - previousGmv) / previousGmv : null;

  const ChangeIcon = change === null || change === 0 ? Minus : change > 0 ? ArrowUpRight : ArrowDownRight;
  const changeColor = change === null || change === 0
    ? 'var(--text-secondary)'
    : change > 0 ? 'var(--success-subtle)' : 'var(--danger-subtle)';

  const range = `${hhmm(hourStart)}–${hhmm(newest)}`;
  const previousRange = `${hhmm(hourStart - CHART_MINUTES * MINUTE_MS)}–${hhmm(hourStart - MINUTE_MS)}`;
  const categoryLabel = category === 'all' ? 'All categories' : category;

  return (
    <div className="page">
      {/* ── Page Header ─────────────────────────────────────── */}
      <div className="page-header">
        <div className="page-header__left">
          <div className="page-header__breadcrumb">
            <span>Modules</span>
            <span className="page-header__sep">/</span>
            <span className="page-header__current">BR1</span>
          </div>
          <h1 className="page-header__title">Real-time Operations</h1>
          <p className="page-header__description">
            Revenue and orders per minute from the live stream, against the hour before
          </p>
        </div>

        <div className="toolbar">
          <div className="toolbar__item">
            <Calendar size={13} strokeWidth={1.75} className="toolbar__icon" />
            <span className="toolbar__label">Date</span>
            <input
              type="date"
              className="toolbar__input"
              value={eventDate}
              min="2019-11-01"
              max="2019-11-30"
              onChange={e => e.target.value && setEventDate(e.target.value)}
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
              <option value="all">All categories</option>
              {CATEGORIES.map(name => (
                <option key={name} value={name}>{name}</option>
              ))}
            </select>
          </div>

          <div className="toolbar__sep" />

          <div className="toolbar__item">
            <RefreshCw size={13} strokeWidth={1.75} className="toolbar__icon" />
            <span className="toolbar__label">Updated</span>
            <span>
              {fetchedAt === null ? '—' : `${Math.max(0, Math.round((now - fetchedAt) / 1000))}s ago`}
            </span>
          </div>
        </div>
      </div>

      {/* ── Status Messages ─────────────────────────────────── */}
      {response === null && !error && (
        <div className="status-banner">
          <RefreshCw size={14} className="spin" />
          <span>Querying gmv_by_minute...</span>
        </div>
      )}

      {/* A failed refresh keeps the last good data on screen, under this banner. */}
      {error && (
        <div className="status-banner status-banner--error">
          <span>Failed to query real-time GMV: {error}</span>
        </div>
      )}

      {/* ── Empty State ─────────────────────────────────────── */}
      {response && rows.length === 0 && (
        <div className="empty-panel">
          <Search size={28} strokeWidth={1.5} className="empty-panel__icon" />
          <h3 className="empty-panel__title">No minutes yet</h3>
          <p className="empty-panel__desc">
            Nothing in gmv_by_minute for {eventDate} and {categoryLabel}. Is
            processing/streaming_gold.py running, and the replayer started after it?
          </p>
        </div>
      )}

      {/* ── Main Data View ──────────────────────────────────── */}
      {response && rows.length > 0 && (
        <div className="content-stack">
          <div className="kpi-ribbon">
            <div className="kpi-ribbon__cell">
              <span className="kpi-ribbon__label">GMV</span>
              <div className="kpi-ribbon__value">{compact.format(gmv)}</div>
              <span className="kpi-ribbon__hint">Last 60 min · {range}</span>
            </div>

            <div className="kpi-ribbon__cell">
              <span className="kpi-ribbon__label">Orders</span>
              <div className="kpi-ribbon__value">{orders.toLocaleString('en-US')}</div>
              <span className="kpi-ribbon__hint">Purchase events, last 60 min</span>
            </div>

            <div className="kpi-ribbon__cell">
              <span className="kpi-ribbon__label">AOV</span>
              <div className="kpi-ribbon__value">{orders > 0 ? money.format(gmv / orders) : '—'}</div>
              <span className="kpi-ribbon__hint">GMV per order</span>
            </div>

            <div className="kpi-ribbon__cell">
              <span className="kpi-ribbon__label">vs previous 60 min</span>
              <div className="kpi-ribbon__value kpi-ribbon__delta" style={{ color: changeColor }}>
                <ChangeIcon size={20} strokeWidth={2} aria-hidden="true" />
                {change === null ? '—' : `${change > 0 ? '+' : ''}${(change * 100).toFixed(1)}%`}
              </div>
              <span className="kpi-ribbon__hint">
                {change === null
                  ? 'Needs two hours of data'
                  : `GMV ${compact.format(previousGmv)} in ${previousRange}`}
              </span>
            </div>
          </div>

          <div className="panel">
            <div className="panel__header">
              <div className="panel__title-group">
                <h2 className="panel__title">GMV per minute, last 60 minutes</h2>
                <span className="panel__subtitle">
                  {eventDate} · {range} Vietnam time · {categoryLabel} · refreshes every 10 s
                </span>
              </div>
            </div>

            <div className="panel__chart">
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={slots} margin={{ top: 12, right: 24, left: 8, bottom: 4 }}>
                  <CartesianGrid strokeDasharray="2 2" stroke="rgba(255,255,255,0.06)" vertical={false} />
                  <XAxis
                    dataKey="minute"
                    interval={9}
                    axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
                    tickLine={false}
                    tick={{ fill: '#86868b', fontSize: 11, fontFamily: 'monospace' }}
                  />
                  <YAxis
                    width={56}
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: '#86868b', fontSize: 11, fontFamily: 'monospace' }}
                    tickFormatter={v => compact.format(v)}
                  />
                  <Tooltip
                    cursor={{ stroke: 'rgba(255,255,255,0.25)', strokeWidth: 1 }}
                    content={({ active, payload }) => {
                      if (!active || !payload || payload.length === 0) return null;
                      const slot = payload[0].payload as Slot;
                      return (
                        <div className="chart-tooltip">
                          <div className="chart-tooltip__title">{slot.minute}</div>
                          <div className="chart-tooltip__item">
                            <span className="chart-tooltip__label">GMV</span>
                            <span className="chart-tooltip__value font-mono">{money.format(slot.gmv)}</span>
                          </div>
                          <div className="chart-tooltip__item">
                            <span className="chart-tooltip__label">Orders</span>
                            <span className="chart-tooltip__value font-mono">{slot.orders}</span>
                          </div>
                        </div>
                      );
                    }}
                  />
                  {/* No animation: every 10 s refresh would otherwise redraw the
                      line from zero instead of just extending it. */}
                  <Line
                    type="linear"
                    dataKey="gmv"
                    stroke="var(--accent-apple)"
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4, stroke: 'var(--bg-surface)', strokeWidth: 2 }}
                    isAnimationActive={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* The same 60 minutes as numbers, newest first, for anyone who cannot hover. */}
            <details className="panel__details">
              <summary>Show the 60 minutes as a table</summary>
              <div className="panel__table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Minute</th>
                      <th>GMV</th>
                      <th>Orders</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[...slots].reverse().map(slot => (
                      <tr key={slot.minute}>
                        <td className="font-mono">{slot.minute}</td>
                        <td className="data-table__numeric font-mono">{money.format(slot.gmv)}</td>
                        <td className="data-table__numeric font-mono">{slot.orders}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </details>

            <div className="panel__footer">
              <QueryMeta meta={response.meta} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
