/**
 * BR2Page — Conversion Funnel screen (fully implemented sample).
 *
 * Owner: Tin
 * API:   GET /api/br2/funnel?start_date&end_date&category_l1
 * Data:  web/fixtures/br2-funnel.json (W38); gold/funnel_daily/ via DuckDB (W40)
 *
 * This is the reference screen. Use it as a template for BR1–BR8:
 *   1. Fetch data with useEffect → useState pattern below
 *   2. Render your chart using Recharts
 *   3. Place <QueryMeta meta={data.meta} /> at the bottom of the card
 */

import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell,
  ResponsiveContainer,
} from 'recharts';
import type { ApiResponse, FunnelRow } from '../types/api';
import QueryMeta from '../components/QueryMeta';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';

const STEP_COLORS: Record<string, string> = {
  view:     '#6366f1',
  cart:     '#8b5cf6',
  purchase: '#a855f7',
};

const STEP_LABELS: Record<string, string> = {
  view:     '👁 View',
  cart:     '🛒 Cart',
  purchase: '💳 Purchase',
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

  // Fetch on mount and whenever filters change
  useEffect(() => { fetchFunnel(); }, [startDate, endDate, category]); // eslint-disable-line react-hooks/exhaustive-deps

  const chartData = (response?.data ?? []).map(row => ({
    ...row,
    label: STEP_LABELS[row.step] ?? row.step,
    pct: `${(row.conversion_rate * 100).toFixed(1)}%`,
  }));

  return (
    <div className="page">
      {/* ── Filters ──────────────────────────────────────────── */}
      <div className="filters">
        <label className="filter-group">
          <span>Start date</span>
          <input
            type="date" value={startDate} min="2019-11-01" max="2019-11-30"
            onChange={e => setStartDate(e.target.value)}
          />
        </label>
        <label className="filter-group">
          <span>End date</span>
          <input
            type="date" value={endDate} min="2019-11-01" max="2019-11-30"
            onChange={e => setEndDate(e.target.value)}
          />
        </label>
        <label className="filter-group">
          <span>Category</span>
          <select value={category} onChange={e => setCategory(e.target.value)}>
            <option value="all">All</option>
            <option value="electronics">Electronics</option>
            <option value="appliances">Appliances</option>
            <option value="computers">Computers</option>
            <option value="furniture">Furniture</option>
          </select>
        </label>
      </div>

      {/* ── Status ───────────────────────────────────────────── */}
      {loading && <p className="status-msg">Loading…</p>}
      {error   && <p className="status-msg status-msg--error">Error: {error}</p>}

      {/* ── Empty state ──────────────────────────────────────── */}
      {!loading && !error && response && response.data.length === 0 && (
        <div className="empty-state">
          <span>🔍</span>
          <p>No data for the selected filters.</p>
        </div>
      )}

      {/* ── Chart card ───────────────────────────────────────── */}
      {!loading && !error && response && response.data.length > 0 && (
        <div className="card">
          <h2 className="card__title">Conversion Funnel</h2>
          <p className="card__subtitle">
            {startDate} → {endDate}
            {category !== 'all' && ` · ${category}`}
          </p>

          <ResponsiveContainer width="100%" height={280}>
            <BarChart
              data={chartData}
              layout="vertical"
              margin={{ top: 8, right: 48, left: 80, bottom: 8 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis type="number" tick={{ fill: '#94a3b8', fontSize: 12 }}
                tickFormatter={v => v.toLocaleString()} />
              <YAxis type="category" dataKey="label" tick={{ fill: '#e2e8f0', fontSize: 13 }} />
              <Tooltip
                contentStyle={{ background: '#1e293b', border: 'none', borderRadius: 8 }}
                labelStyle={{ color: '#e2e8f0' }}
                formatter={(value: number, _name: string, entry) => [
                  `${value.toLocaleString()} (${entry.payload.pct} of views)`,
                  'Count',
                ]}
              />
              <Bar dataKey="count" radius={[0, 6, 6, 0]}>
                {chartData.map(row => (
                  <Cell key={row.step} fill={STEP_COLORS[row.step] ?? '#6366f1'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>

          {/* ── Conversion table ─────────────────────────────── */}
          <table className="data-table">
            <thead>
              <tr>
                <th>Step</th>
                <th>Events</th>
                <th>Sessions</th>
                <th>Conv. rate</th>
              </tr>
            </thead>
            <tbody>
              {response.data.map(row => (
                <tr key={row.step}>
                  <td style={{ color: STEP_COLORS[row.step] }}>
                    {STEP_LABELS[row.step] ?? row.step}
                  </td>
                  <td>{row.count.toLocaleString()}</td>
                  <td>{row.session_count.toLocaleString()}</td>
                  <td>{(row.conversion_rate * 100).toFixed(2)}%</td>
                </tr>
              ))}
            </tbody>
          </table>

          <QueryMeta meta={response.meta} />
        </div>
      )}
    </div>
  );
}
