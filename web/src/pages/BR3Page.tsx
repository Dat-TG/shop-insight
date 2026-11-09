import { useEffect, useState } from 'react';
import { ArrowDown, ArrowUp, Clock, Minus, Radio, RefreshCw, Search } from 'lucide-react';
import type { ApiResponse, QueryMeta as QueryMetaType, TrendingProductRow } from '../types/api';
import QueryMeta from '../components/QueryMeta';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';

const REFRESH_MS = 10_000;
const MINUTE_MS = 60_000;
const WINDOW_MINUTES = 15;

// window_start is the Vietnam wall clock, "2019-11-17T15:04:00+07:00". As in BR1,
// reading its first 19 characters as UTC gives numbers to do minute arithmetic on,
// and toISOString gives the same wall clock back, so the browser's own time zone
// never gets involved.
const toMs = (windowStart: string) => Date.parse(`${windowStart.slice(0, 19)}Z`);
const toParam = (ms: number) => `${new Date(ms).toISOString().slice(0, 19)}+07:00`;
const hhmm = (ms: number) => new Date(ms).toISOString().slice(11, 16);

interface Trending {
  rows: TrendingProductRow[];
  // Rank of each product in the window a minute earlier; null when that window has no rows.
  previousRanks: Map<number, number> | null;
  meta: QueryMetaType;
}

async function fetchWindow(windowStart: string | null, signal: AbortSignal) {
  // "+07:00" must be encoded, or the "+" arrives as a space.
  const query = windowStart === null ? '' : `?window_start=${encodeURIComponent(windowStart)}`;
  const response = await fetch(`${API_BASE}/api/br3/trending${query}`, { signal });
  if (!response.ok) {
    // The API says what to run when Cassandra is down (HTTP 503).
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `HTTP ${response.status}`);
  }
  return response.json() as Promise<ApiResponse<TrendingProductRow>>;
}

// The arrows compare each product's rank with its rank in the window a minute
// earlier, a partition of its own, asked for by window_start. The second call
// needs the first one's window_start, so they run one after the other, and the
// footer adds up both: their time, their partitions and their rows.
async function fetchTrending(windowStart: string | null, signal: AbortSignal): Promise<Trending> {
  const current = await fetchWindow(windowStart, signal);
  const metas = [current.meta];
  let previousRanks: Map<number, number> | null = null;
  if (current.data.length > 0) {
    const previous = await fetchWindow(toParam(toMs(current.data[0].window_start) - MINUTE_MS), signal);
    metas.push(previous.meta);
    if (previous.data.length > 0) {
      previousRanks = new Map(previous.data.map(row => [row.product_id, row.rank]));
    }
  }
  return {
    rows: current.data,
    previousRanks,
    meta: {
      ms: Math.round(metas.reduce((sum, meta) => sum + meta.ms, 0) * 10) / 10,
      warehouse: current.meta.warehouse,
      partitions: metas.reduce((sum, meta) => sum + meta.partitions, 0),
      rows: metas.reduce((sum, meta) => sum + meta.rows, 0),
    },
  };
}

// Places climbed since the window a minute earlier (negative: fell), null when
// the product was not in that top 20, undefined when there is nothing to compare with.
type Change = number | null | undefined;

function ChangeCell({ change }: { change: Change }) {
  if (change === undefined) return <span className="text-muted">—</span>;
  if (change === null) return <span className="rank-change rank-change--new">NEW</span>;
  if (change === 0) {
    return (
      <span className="rank-change rank-change--same" aria-label="same rank">
        <Minus size={13} strokeWidth={2} />
      </span>
    );
  }
  const up = change > 0;
  const Icon = up ? ArrowUp : ArrowDown;
  return (
    <span className={`rank-change rank-change--${up ? 'up' : 'down'}`} aria-label={`${up ? 'up' : 'down'} ${Math.abs(change)}`}>
      <Icon size={13} strokeWidth={2} />
      {Math.abs(change)}
    </span>
  );
}

export default function BR3Page() {
  // null: live, the newest window. Otherwise the window the user picked, "2019-11-17T15:00".
  const [picked, setPicked] = useState<string | null>(null);

  const [trending, setTrending]   = useState<Trending | null>(null);
  const [error, setError]         = useState<string | null>(null);
  const [fetchedAt, setFetchedAt] = useState<number | null>(null);
  const [now, setNow]             = useState(() => Date.now());

  // The tab title matches the page title (as BR7Page does).
  useEffect(() => {
    const previousTitle = document.title;
    document.title = 'Trending Products';
    return () => { document.title = previousTitle; };
  }, []);

  // Fetch now and every 10 s, in both modes: a picked window the stream has not
  // closed yet shows up once it has. A change of window starts over: the old
  // interval is cleared and a request still in flight is aborted, so a late
  // answer for the previous window never lands on screen.
  useEffect(() => {
    let controller: AbortController | null = null;
    const load = () => {
      controller?.abort();
      controller = new AbortController();
      fetchTrending(picked === null ? null : `${picked}:00+07:00`, controller.signal)
        .then(result => {
          setTrending(result);
          setError(null);
          setFetchedAt(Date.now());
        })
        .catch(e => {
          if (e.name !== 'AbortError') setError(e.message ?? String(e));
        });
    };
    setTrending(null);
    load();
    const timer = setInterval(load, REFRESH_MS);
    return () => {
      clearInterval(timer);
      controller?.abort();
    };
  }, [picked]);

  // Drives "Updated Ns ago".
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);

  const rows = trending?.rows ?? [];
  const previousRanks = trending?.previousRanks ?? null;
  const start = rows.length > 0 ? toMs(rows[0].window_start) : null;
  const range = start === null ? '' : `${hhmm(start)}–${hhmm(start + WINDOW_MINUTES * MINUTE_MS)}`;

  const changes: Change[] = rows.map(row => {
    if (previousRanks === null) return undefined;
    const before = previousRanks.get(row.product_id);
    return before === undefined ? null : before - row.rank;
  });
  const newcomers = changes.filter(change => change === null).length;
  const climbers = changes.filter(change => typeof change === 'number' && change > 0).length;
  const fallers = changes.filter(change => typeof change === 'number' && change < 0).length;
  const top = rows[0];

  return (
    <div className="page">
      {/* ── Page Header ─────────────────────────────────────── */}
      <div className="page-header">
        <div className="page-header__left">
          <div className="page-header__breadcrumb">
            <span>Modules</span>
            <span className="page-header__sep">/</span>
            <span className="page-header__current">BR3</span>
          </div>
          <h1 className="page-header__title">Trending Products</h1>
          <p className="page-header__description">
            Top 20 products by views in a 15-minute window that slides every minute, against the window a minute earlier
          </p>
        </div>

        <div className="toolbar">
          <div className="toolbar__item">
            <Clock size={13} strokeWidth={1.75} className="toolbar__icon" />
            <span className="toolbar__label">Window from</span>
            {/* Vietnam time, like the data: 1 Nov 07:00 to 1 Dec 06:59. */}
            <input
              type="datetime-local"
              className="toolbar__input"
              step={60}
              min="2019-11-01T07:00"
              max="2019-12-01T06:45"
              value={picked ?? ''}
              onChange={e => e.target.value && setPicked(e.target.value)}
            />
          </div>

          <div className="toolbar__sep" />

          <button
            type="button"
            className={`live-toggle${picked === null ? ' live-toggle--on' : ''}`}
            onClick={() => setPicked(null)}
            aria-pressed={picked === null}
          >
            <Radio size={13} strokeWidth={1.75} />
            Live
          </button>

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
      {trending === null && !error && (
        <div className="status-banner">
          <RefreshCw size={14} className="spin" />
          <span>Querying trending_products...</span>
        </div>
      )}

      {/* A failed refresh keeps the last good data on screen, under this banner. */}
      {error && (
        <div className="status-banner status-banner--error">
          <span>Failed to query trending products: {error}</span>
        </div>
      )}

      {/* ── Empty State ─────────────────────────────────────── */}
      {trending && rows.length === 0 && (
        <div className="empty-panel">
          <Search size={28} strokeWidth={1.5} className="empty-panel__icon" />
          <h3 className="empty-panel__title">No window yet</h3>
          <p className="empty-panel__desc">
            {picked === null
              ? 'Nothing in trending_products yet. A window lands there once the watermark closes it, 10 minutes of event time after it ends. Is processing/streaming_gold.py running, and the replayer started after it?'
              : `Nothing in trending_products for the window from ${picked.replace('T', ' ')}. It has not been replayed, or not closed yet.`}
          </p>
        </div>
      )}

      {/* ── Main Data View ──────────────────────────────────── */}
      {trending && rows.length > 0 && (
        <div className="content-stack">
          <div className="kpi-ribbon">
            <div className="kpi-ribbon__cell">
              <span className="kpi-ribbon__label">Window</span>
              <div className="kpi-ribbon__value">{range}</div>
              <span className="kpi-ribbon__hint">
                {rows[0].window_start.slice(0, 10)} · Vietnam time{picked === null ? ' · newest' : ''}
              </span>
            </div>

            <div className="kpi-ribbon__cell">
              <span className="kpi-ribbon__label">Top product</span>
              <div className="kpi-ribbon__value font-mono">{top.product_id}</div>
              <span className="kpi-ribbon__hint">
                {top.brand} · {top.category_l1} · {top.view_count.toLocaleString('en-US')} views
              </span>
            </div>

            <div className="kpi-ribbon__cell">
              <span className="kpi-ribbon__label">New in top 20</span>
              <div className="kpi-ribbon__value">{previousRanks === null ? '—' : newcomers}</div>
              <span className="kpi-ribbon__hint">Not in the window a minute earlier</span>
            </div>

            <div className="kpi-ribbon__cell">
              <span className="kpi-ribbon__label">Moved</span>
              <div className="kpi-ribbon__value">
                {previousRanks === null ? '—' : `${climbers} up · ${fallers} down`}
              </div>
              <span className="kpi-ribbon__hint">
                {previousRanks === null ? 'No window a minute earlier to compare with' : 'Against the window a minute earlier'}
              </span>
            </div>
          </div>

          <div className="panel">
            <div className="panel__header">
              <div className="panel__title-group">
                <h2 className="panel__title">Top {rows.length} by views, {range}</h2>
                <span className="panel__subtitle">
                  Ties go to more carts, then the lower product id · refreshes every 10 s · the footer
                  counts both calls, this window and the one a minute earlier
                </span>
              </div>
            </div>

            <div className="panel__table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Rank</th>
                    <th>Change</th>
                    <th>Product</th>
                    <th>Brand</th>
                    <th>Category</th>
                    <th>Views</th>
                    <th>Carts</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row, i) => (
                    <tr key={row.product_id}>
                      <td className="font-mono">{row.rank}</td>
                      <td><ChangeCell change={changes[i]} /></td>
                      <td className="font-mono">{row.product_id}</td>
                      <td>{row.brand}</td>
                      <td>{row.category_l1}</td>
                      <td className="data-table__numeric font-mono">{row.view_count.toLocaleString('en-US')}</td>
                      <td className="data-table__numeric font-mono">{row.cart_count.toLocaleString('en-US')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="panel__footer">
              <QueryMeta meta={trending.meta} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
