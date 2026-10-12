import { useEffect, useState } from 'react';
import { Calendar, Megaphone, RefreshCw, Search, SlidersHorizontal } from 'lucide-react';
import type { ApiResponse, AbandonedCartRow } from '../types/api';
import QueryMeta from '../components/QueryMeta';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';

const REFRESH_MS = 10_000;
// A whole day can hold up to about 18,300 abandoned carts (15 Nov); the demo replay of
// 17 Nov from 15:00 holds at most 3,965. The table draws the highest 200;
// the cards and the campaign always count every cart the filter lets through.
const MAX_ROWS = 200;

// The demo replays this day: python ingestion/replayer.py --speed 60
// --start "2019-11-17 08:00:00" (15:00 in Vietnam).
const DEMO_DATE = '2019-11-17';

const compact = new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 });
const money = new Intl.NumberFormat('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

// last_event_at is the Vietnam wall clock, "2019-11-17T15:04:00+07:00": read the clock off the text.
const hhmm = (iso: string) => iso.slice(11, 16);

export default function BR5Page() {
  const [eventDate, setEventDate] = useState(DEMO_DATE);
  const [minValueText, setMinValueText] = useState('0');
  const minValue = Math.max(0, Number(minValueText) || 0);

  const [response, setResponse]   = useState<ApiResponse<AbandonedCartRow> | null>(null);
  const [error, setError]         = useState<string | null>(null);
  const [fetchedAt, setFetchedAt] = useState<number | null>(null);
  const [now, setNow]             = useState(() => Date.now());
  const [notice, setNotice]       = useState<string | null>(null);

  // Fetch now and every 10 s. A filter change starts over: the old interval is
  // cleared and a request still in flight is aborted, so a late answer for the
  // previous filter never lands on screen.
  useEffect(() => {
    let controller: AbortController | null = null;
    const load = () => {
      controller?.abort();
      controller = new AbortController();
      const url = `${API_BASE}/api/br5/carts?event_date=${eventDate}&min_value=${minValue}`;
      fetch(url, { signal: controller.signal })
        .then(async r => {
          if (!r.ok) {
            // The API says what to run when Cassandra is down (HTTP 503).
            const body = await r.json().catch(() => null);
            throw new Error(body?.detail ?? `HTTP ${r.status}`);
          }
          return r.json() as Promise<ApiResponse<AbandonedCartRow>>;
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
    setNotice(null);
    load();
    const timer = setInterval(load, REFRESH_MS);
    return () => {
      clearInterval(timer);
      controller?.abort();
    };
  }, [eventDate, minValue]);

  // Drives "Updated Ns ago".
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);

  const rows = response?.data ?? [];  // highest cart value first: the API sorted them
  const totalValue = rows.reduce((acc, cart) => acc + cart.cart_value, 0);
  const average = rows.length > 0 ? totalValue / rows.length : 0;

  const createCampaign = () => {
    // Simulated: nothing is sent anywhere.
    setNotice(
      `Đã tạo chiến dịch nhắc lại cho ${rows.length.toLocaleString('en-US')} giỏ hàng, ` +
      `tổng giá trị ${money.format(totalValue)}. Đây chỉ là mô phỏng, không có tin nhắn nào được gửi.`
    );
  };

  return (
    <div className="page">
      {/* ── Page Header ─────────────────────────────────────── */}
      <div className="page-header">
        <div className="page-header__left">
          <div className="page-header__breadcrumb">
            <span>Modules</span>
            <span className="page-header__sep">/</span>
            <span className="page-header__current">BR5</span>
          </div>
          <h1 className="page-header__title">Abandoned Carts</h1>
          <p className="page-header__description">
            Sessions that added to cart and did not buy within 30 minutes, highest value first
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
              max="2019-12-01"
              onChange={e => e.target.value && setEventDate(e.target.value)}
            />
          </div>

          <div className="toolbar__sep" />

          <div className="toolbar__item">
            <SlidersHorizontal size={13} strokeWidth={1.75} className="toolbar__icon" />
            <span className="toolbar__label">Min value</span>
            <input
              type="number"
              className="toolbar__input"
              value={minValueText}
              min={0}
              step={50}
              onChange={e => setMinValueText(e.target.value)}
            />
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
          <span>Querying abandoned_carts...</span>
        </div>
      )}

      {/* A failed refresh keeps the last good data on screen, under this banner. */}
      {error && (
        <div className="status-banner status-banner--error">
          <span>Failed to query abandoned carts: {error}</span>
        </div>
      )}

      {/* ── Empty State ─────────────────────────────────────── */}
      {response && rows.length === 0 && (
        <div className="empty-panel">
          <Search size={28} strokeWidth={1.5} className="empty-panel__icon" />
          <h3 className="empty-panel__title">No abandoned carts yet</h3>
          <p className="empty-panel__desc">
            Nothing in abandoned_carts for {eventDate} with a value of at least {money.format(minValue)}.
            A cart appears about 40 minutes of event time after the session's last event, which
            is about 40 seconds at replay speed 60. Is processing/streaming_gold.py running,
            and the replayer started after it?
          </p>
        </div>
      )}

      {/* ── Main Data View ──────────────────────────────────── */}
      {response && rows.length > 0 && (
        <div className="content-stack">
          <div className="kpi-ribbon">
            <div className="kpi-ribbon__cell">
              <span className="kpi-ribbon__label">Abandoned carts</span>
              <div className="kpi-ribbon__value">{rows.length.toLocaleString('en-US')}</div>
              <span className="kpi-ribbon__hint">{eventDate}, value ≥ {money.format(minValue)}</span>
            </div>

            <div className="kpi-ribbon__cell">
              <span className="kpi-ribbon__label">Value at stake</span>
              <div className="kpi-ribbon__value">{compact.format(totalValue)}</div>
              <span className="kpi-ribbon__hint">Sum of cart values</span>
            </div>

            <div className="kpi-ribbon__cell">
              <span className="kpi-ribbon__label">Average cart</span>
              <div className="kpi-ribbon__value">{money.format(average)}</div>
              <span className="kpi-ribbon__hint">Value per cart</span>
            </div>

            <div className="kpi-ribbon__cell">
              <span className="kpi-ribbon__label">Largest cart</span>
              <div className="kpi-ribbon__value">{money.format(rows[0].cart_value)}</div>
              <span className="kpi-ribbon__hint">{rows[0].item_count} items</span>
            </div>
          </div>

          <div className="panel">
            <div className="panel__header">
              <div className="panel__title-group">
                <h2 className="panel__title">Carts to win back</h2>
                <span className="panel__subtitle">
                  {eventDate} · Vietnam time · highest value first · refreshes every 10 s
                </span>
              </div>
              <button type="button" className="toolbar__item" onClick={createCampaign}>
                <Megaphone size={13} strokeWidth={1.75} className="toolbar__icon" />
                <span>Tạo chiến dịch nhắc lại</span>
              </button>
            </div>

            {notice && (
              <div className="status-banner" role="status">
                <Megaphone size={14} />
                <span>{notice}</span>
              </div>
            )}

            <div className="panel__table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Session</th>
                    <th>User</th>
                    <th>Items</th>
                    <th>Cart value</th>
                    <th>Last activity</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.slice(0, MAX_ROWS).map(cart => (
                    <tr key={cart.user_session}>
                      <td className="font-mono" title={cart.user_session}>{cart.user_session.slice(0, 8)}…</td>
                      <td className="font-mono">{cart.user_id}</td>
                      <td className="data-table__numeric font-mono">{cart.item_count}</td>
                      <td className="data-table__numeric font-mono">{money.format(cart.cart_value)}</td>
                      <td className="font-mono">{hhmm(cart.last_event_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {rows.length > MAX_ROWS && (
              <span className="panel__subtitle">
                Showing the {MAX_ROWS} highest of {rows.length.toLocaleString('en-US')} carts.
              </span>
            )}

            <div className="panel__footer">
              <QueryMeta meta={response.meta} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
