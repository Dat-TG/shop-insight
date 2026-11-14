import { Fragment, useEffect, useState } from 'react';
import {
  AlertTriangle,
  Calendar,
  ChevronDown,
  ChevronRight,
  Filter as FilterIcon,
  RefreshCw,
  ShieldAlert,
  User,
} from 'lucide-react';
import type { ApiResponse, VelocityAlertRow } from '../types/api';
import QueryMeta from '../components/QueryMeta';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';

const REFRESH_MS = 10_000;
const DEMO_DATE = '2019-11-17';
// A full day holds up to ~11,000 (window, user) rows. The severity counts use all
// of them; the table renders only the newest MAX_ROWS, as BR5 does.
const MAX_ROWS = 200;

const SEVERITY_CONFIG = {
  high:   { label: 'High',   color: '#ff3b30', bg: 'rgba(255,59,48,0.12)',  badge: 'badge badge--danger'  },
  medium: { label: 'Medium', color: '#ff9f0a', bg: 'rgba(255,159,10,0.10)', badge: 'badge badge--warning' },
  low:    { label: 'Low',    color: '#30d158', bg: 'rgba(48,209,88,0.08)',  badge: 'badge badge--success' },
} as const;

// 'flagged' (the default) hides low alerts in the table: low is a single purchase in
// five minutes, ordinary behaviour, and 94% of a day's alerts. It asks the API for
// every severity, so the cards still count all three levels.
const SEVERITY_OPTIONS = ['flagged', 'all', 'high', 'medium', 'low'];
const SEVERITY_LABELS: Record<string, string> = {
  flagged: 'Medium + High', all: 'All Severities', high: 'High', medium: 'Medium', low: 'Low',
};

// window_start is Vietnam wall clock with +07:00. Read first 19 chars as UTC for
// arithmetic; toISOString gives the same wall clock back.
const toMs = (s: string) => Date.parse(`${s.slice(0, 19)}Z`);
const hhmm = (ms: number) => new Date(ms).toISOString().slice(11, 16);

const money = new Intl.NumberFormat('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export default function BR8Page() {
  const [eventDate, setEventDate] = useState(DEMO_DATE);
  const [severity, setSeverity]   = useState('flagged');
  const [expandedKey, setExpandedKey] = useState<string | null>(null);

  const [response, setResponse]   = useState<ApiResponse<VelocityAlertRow> | null>(null);
  const [error, setError]         = useState<string | null>(null);
  const [fetchedAt, setFetchedAt] = useState<number | null>(null);
  const [now, setNow]             = useState(() => Date.now());

  // The tab title matches the page title (as BR7Page does).
  useEffect(() => {
    const previousTitle = document.title;
    document.title = 'Risk Alerts';
    return () => { document.title = previousTitle; };
  }, []);

  // Tick the "X s ago" label every second.
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);

  // Fetch now and every 10 s, as BR5Page does. A tick keeps the table (and the
  // expanded alert) on screen until the new answer arrives, and a failed tick keeps
  // the last good data under the error banner. Only a filter change clears it: the
  // old interval is cleared and a request still in flight is aborted, so a late
  // answer for the previous filter never lands on screen.
  useEffect(() => {
    let controller: AbortController | null = null;
    const load = () => {
      controller?.abort();
      controller = new AbortController();
      const params = new URLSearchParams({
        event_date: eventDate,
        severity: severity === 'flagged' ? 'all' : severity,
      });
      fetch(`${API_BASE}/api/br8/alerts?${params}`, { signal: controller.signal })
        .then(async r => {
          if (!r.ok) {
            const body = await r.json().catch(() => null);
            throw new Error(body?.detail ?? `HTTP ${r.status}`);
          }
          return r.json() as Promise<ApiResponse<VelocityAlertRow>>;
        })
        .then(json => { setResponse(json); setError(null); setFetchedAt(Date.now()); })
        .catch(e => { if (e.name !== 'AbortError') setError(e.message ?? String(e)); });
    };
    setResponse(null);
    setError(null);
    load();
    const id = setInterval(load, REFRESH_MS);
    return () => { clearInterval(id); controller?.abort(); };
  }, [eventDate, severity]);

  const rows = response?.data ?? [];
  const highCount   = rows.filter(r => r.severity === 'high').length;
  const mediumCount = rows.filter(r => r.severity === 'medium').length;
  const lowCount    = rows.filter(r => r.severity === 'low').length;
  const shown = severity === 'flagged' ? rows.filter(r => r.severity !== 'low') : rows;
  const secsAgo = fetchedAt ? Math.round((now - fetchedAt) / 1000) : null;

  return (
    <div className="page">
      {/* ── Page Header ─────────────────────────────────────── */}
      <div className="page-header">
        <div className="page-header__left">
          <div className="page-header__breadcrumb">
            <span>Modules</span>
            <span className="page-header__sep">/</span>
            <span className="page-header__current">BR8</span>
          </div>
          <h1 className="page-header__title">Risk Alerts</h1>
          <p className="page-header__description">
            Users placing an abnormally high number of orders in a 5-minute window
          </p>
        </div>

        {/* ── Toolbar ─────────────────────────────────────────── */}
        <div className="toolbar">
          <div className="toolbar__item">
            <Calendar size={13} strokeWidth={1.75} className="toolbar__icon" />
            <span className="toolbar__label">Date</span>
            <input
              type="date"
              id="br8-date-input"
              className="toolbar__input"
              value={eventDate}
              onChange={e => setEventDate(e.target.value)}
            />
          </div>
          <div className="toolbar__sep" />
          <div className="toolbar__item">
            <FilterIcon size={13} strokeWidth={1.75} className="toolbar__icon" />
            <span className="toolbar__label">Severity</span>
            <select
              id="br8-severity-select"
              className="toolbar__select"
              value={severity}
              onChange={e => setSeverity(e.target.value)}
            >
              {SEVERITY_OPTIONS.map(s => (
                <option key={s} value={s}>{SEVERITY_LABELS[s]}</option>
              ))}
            </select>
          </div>
          <div className="toolbar__sep" />
          <div className="toolbar__item toolbar__item--muted">
            <RefreshCw size={12} strokeWidth={1.75} className={response === null && !error ? 'spin' : ''} />
            <span className="toolbar__label">
              {secsAgo === null ? 'Loading…' : `Updated ${secsAgo}s ago`}
            </span>
          </div>
        </div>
      </div>

      {/* ── Status Messages ─────────────────────────────────── */}
      {response === null && !error && (
        <div className="status-banner">
          <RefreshCw size={14} className="spin" />
          <span>Querying Cassandra order_velocity_alerts…</span>
        </div>
      )}
      {/* A failed refresh keeps the last good data on screen, under this banner. */}
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
            <ShieldAlert size={18} />
            <span className="br8-summary__count">{highCount}</span>
            <span className="br8-summary__label">High</span>
          </div>
          <div className="br8-summary__card br8-summary__card--medium">
            <AlertTriangle size={18} />
            <span className="br8-summary__count">{mediumCount}</span>
            <span className="br8-summary__label">Medium</span>
          </div>
          <div className="br8-summary__card br8-summary__card--low">
            <User size={18} />
            <span className="br8-summary__count">{lowCount}</span>
            <span className="br8-summary__label">Low</span>
          </div>
          <div className="br8-summary__card">
            <span className="br8-summary__count">{rows.length}</span>
            <span className="br8-summary__label">Total Alerts</span>
          </div>
        </div>
      )}

      {/* ── Empty State ─────────────────────────────────────── */}
      {response && shown.length === 0 && (
        <div className="empty-panel">
          <ShieldAlert size={28} strokeWidth={1.5} className="empty-panel__icon" />
          <h3 className="empty-panel__title">No Alerts</h3>
          <p className="empty-panel__desc">
            No order velocity alerts found for {eventDate}
            {severity !== 'all' ? ` with severity "${SEVERITY_LABELS[severity]}"` : ''}.
            Try a different date or severity filter.
          </p>
        </div>
      )}

      {/* ── Alert Table ─────────────────────────────────────── */}
      {response && shown.length > 0 && (
        <div className="content-stack">
          <div className="panel">
            <div className="panel__header">
              <div className="panel__title-group">
                <h2 className="panel__title">Alert Timeline — {eventDate}</h2>
                <span className="panel__subtitle">
                  Newest window first · orders per user in fixed 5-minute windows
                  {severity === 'flagged' && lowCount > 0
                    ? ` · ${lowCount.toLocaleString('en-US')} low alerts (1 order) hidden`
                    : ''}
                </span>
              </div>
            </div>
            <div className="panel__table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th style={{ width: '28px', textAlign: 'center' }}></th>
                    <th>Window</th>
                    <th>User ID</th>
                    <th>Orders</th>
                    <th>Total Value</th>
                    <th>Severity</th>
                  </tr>
                </thead>
                <tbody>
                  {shown.slice(0, MAX_ROWS).map(row => {
                    const sev = SEVERITY_CONFIG[row.severity as keyof typeof SEVERITY_CONFIG];
                    // Unique within a day: the table key is ((event_date), window_start, user_id).
                    // No index in it, so the expanded alert stays put when a refresh adds rows.
                    const rowKey = `${row.window_start}-${row.user_id}`;
                    const isExpanded = expandedKey === rowKey;
                    const rowClass = `${row.severity === 'high'
                      ? 'data-table__row--danger'
                      : row.severity === 'medium'
                        ? 'data-table__row--warning'
                        : ''} data-table__row--clickable`;
                    return (
                      <Fragment key={rowKey}>
                        <tr
                          className={rowClass}
                          onClick={() => setExpandedKey(isExpanded ? null : rowKey)}
                          title="Click to view alert details"
                        >
                          <td style={{ textAlign: 'center', cursor: 'pointer', paddingRight: 0 }}>
                            {isExpanded ? (
                              <ChevronDown size={14} className="text-secondary" />
                            ) : (
                              <ChevronRight size={14} className="text-secondary" />
                            )}
                          </td>
                          <td className="font-mono text-secondary">{hhmm(toMs(row.window_start))}</td>
                          <td className="data-table__numeric font-mono text-emphasis">{row.user_id}</td>
                          <td className="data-table__numeric font-mono">{row.order_count}</td>
                          <td className="data-table__numeric font-mono">${money.format(row.total_value)}</td>
                          <td>
                            <span className={sev?.badge ?? 'badge'}>
                              {sev?.label ?? row.severity}
                            </span>
                          </td>
                        </tr>
                        {isExpanded && (
                          <tr className="data-table__expand-row">
                            <td colSpan={6}>
                              <div className="br8-alert-detail">
                                <div className="br8-alert-detail__header">
                                  <strong>Alert Details · User #{row.user_id}</strong>
                                  <span className="text-secondary font-mono">
                                    Window: {hhmm(toMs(row.window_start))} – {hhmm(toMs(row.window_start) + 5 * 60 * 1000)} (5-min burst)
                                  </span>
                                </div>
                                <div className="br8-alert-detail__stats">
                                  <div className="br8-alert-detail__stat">
                                    <span className="br8-alert-detail__label">Orders in Window</span>
                                    <span className="br8-alert-detail__value">{row.order_count} orders</span>
                                  </div>
                                  <div className="br8-alert-detail__stat">
                                    <span className="br8-alert-detail__label">Total Transaction Value</span>
                                    <span className="br8-alert-detail__value">${money.format(row.total_value)}</span>
                                  </div>
                                  <div className="br8-alert-detail__stat">
                                    <span className="br8-alert-detail__label">Average Order Value</span>
                                    <span className="br8-alert-detail__value">${money.format(row.total_value / Math.max(row.order_count, 1))}</span>
                                  </div>
                                  <div className="br8-alert-detail__stat">
                                    <span className="br8-alert-detail__label">Alert Severity</span>
                                    <span className="br8-alert-detail__value">{sev?.label ?? row.severity}</span>
                                  </div>
                                </div>
                                <div className="br8-alert-detail__note">
                                  {row.severity === 'high' && (
                                    <span>⚠️ <strong>Critical velocity spike (≥4 orders in 5 min):</strong> User initiated rapid repeated orders exceeding automated thresholds. Flagged for fraud prevention review.</span>
                                  )}
                                  {row.severity === 'medium' && (
                                    <span>⚡ <strong>Elevated purchasing activity (2–3 orders in 5 min):</strong> Velocity moderately above normal baseline. Monitored for bulk re-ordering or automated purchasing.</span>
                                  )}
                                  {row.severity === 'low' && (
                                    <span>✓ <strong>Standard purchasing velocity (1 order in 5 min):</strong> Order volume is within normal consumer behavior.</span>
                                  )}
                                </div>
                              </div>
                            </td>
                          </tr>
                        )}
                      </Fragment>
                    );
                  })}
                </tbody>
              </table>
            </div>
            {shown.length > MAX_ROWS && (
              <span className="panel__subtitle">
                Showing the {MAX_ROWS} newest of {shown.length.toLocaleString('en-US')} alerts. The counts above include all of them.
              </span>
            )}
            <div className="panel__footer">
              {response && <QueryMeta meta={response.meta} />}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
