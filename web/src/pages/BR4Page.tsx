import { Fragment, useEffect, useState } from 'react';
import type { CSSProperties } from 'react';
import { Calendar, Filter as FilterIcon, RefreshCw, Search, Users } from 'lucide-react';
import type { ApiResponse, QueryMeta as QueryMetaType, RfmRow, RfmSegment } from '../types/api';
import QueryMeta from '../components/QueryMeta';

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';
const SCORES = [1, 2, 3, 4, 5];
const SEGMENTS: RfmSegment[] = [
  'champion',
  'loyal',
  'promising',
  'needs_attention',
  'at_risk',
  'hibernating',
  'no_purchase',
];

type SegmentFilter = 'all' | RfmSegment;

interface Cell {
  r: number;
  f: number;
}

interface Heatmap {
  cells: Map<string, number>;
  segments: Map<string, number>;
  meta: QueryMetaType;
}

function cellKey(r: number | null, f: number | null) {
  return `${r}-${f}`;
}

function segmentLabel(segment: string) {
  return segment
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

function formatMoney(value: number) {
  return value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function orDash(value: number | string | null) {
  return value === null ? '—' : value.toLocaleString();
}

async function fetchSegments(params: Record<string, string | number>): Promise<ApiResponse<RfmRow>> {
  const query = new URLSearchParams(Object.entries(params).map(([key, value]) => [key, String(value)]));
  const response = await fetch(`${API_BASE}/api/br4/segments?${query}`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json() as Promise<ApiResponse<RfmRow>>;
}

function buildHeatmap(responses: ApiResponse<RfmRow>[]): Heatmap {
  const cells = new Map<string, number>();
  const segments = new Map<string, number>();
  for (const row of responses.flatMap(response => response.data)) {
    const key = cellKey(row.r_score, row.f_score);
    cells.set(key, (cells.get(key) ?? 0) + 1);
    segments.set(row.segment, (segments.get(row.segment) ?? 0) + 1);
  }
  const metas = responses.map(response => response.meta);
  return {
    cells,
    segments,
    meta: {
      ms: Math.max(...metas.map(meta => meta.ms)),
      warehouse: metas[0].warehouse,
      partitions: Math.max(...metas.map(meta => meta.partitions)),
      rows: metas.reduce((sum, meta) => sum + meta.rows, 0),
    },
  };
}

export default function BR4Page() {
  const [snapshotDate, setSnapshotDate] = useState('2019-11-30');
  const [segment, setSegment] = useState<SegmentFilter>('all');
  const [heatmap, setHeatmap] = useState<Heatmap | null>(null);
  const [selected, setSelected] = useState<Cell | null>(null);
  const [cellRows, setCellRows] = useState<ApiResponse<RfmRow> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    setSelected(null);
    Promise.all(SCORES.map(r => fetchSegments({ snapshot_date: snapshotDate, segment, r_score: r })))
      .then(responses => {
        if (active) setHeatmap(buildHeatmap(responses));
      })
      .catch(e => {
        if (active) setError(String(e));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [snapshotDate, segment]);

  useEffect(() => {
    setCellRows(null);
    if (!selected) return;
    let active = true;
    fetchSegments({ snapshot_date: snapshotDate, segment, r_score: selected.r, f_score: selected.f })
      .then(response => {
        if (active) setCellRows(response);
      })
      .catch(e => {
        if (active) setError(String(e));
      });
    return () => {
      active = false;
    };
  }, [selected, snapshotDate, segment]);

  const cellCounts = heatmap ? [...heatmap.cells.values()] : [];
  const scoredCustomers = cellCounts.reduce((sum, count) => sum + count, 0);
  const largestCell = Math.max(0, ...cellCounts);
  const selectedCount = selected && heatmap ? heatmap.cells.get(cellKey(selected.r, selected.f)) ?? 0 : null;
  const footerMeta = selected && cellRows ? cellRows.meta : heatmap?.meta;

  return (
    <div className="page">
      <div className="page-header">
        <div className="page-header__left">
          <div className="page-header__breadcrumb">
            <span>Modules</span>
            <span className="page-header__sep">/</span>
            <span className="page-header__current">BR4</span>
          </div>
          <h1 className="page-header__title">RFM Segments</h1>
          <p className="page-header__description">
            Customers scored by recency, frequency and monetary value to decide which segment deserves ad spend
          </p>
        </div>

        <div className="toolbar">
          <div className="toolbar__item">
            <Calendar size={13} strokeWidth={1.75} className="toolbar__icon" />
            <span className="toolbar__label">Snapshot</span>
            <input
              type="date"
              className="toolbar__input"
              value={snapshotDate}
              min="2019-11-01"
              max="2019-11-30"
              onChange={e => setSnapshotDate(e.target.value)}
            />
          </div>

          <div className="toolbar__sep" />

          <div className="toolbar__item">
            <FilterIcon size={13} strokeWidth={1.75} className="toolbar__icon" />
            <span className="toolbar__label">Segment</span>
            <select
              className="toolbar__select"
              value={segment}
              onChange={e => setSegment(e.target.value as SegmentFilter)}
            >
              <option value="all">All Segments</option>
              {SEGMENTS.map(name => (
                <option key={name} value={name}>
                  {segmentLabel(name)}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {loading && (
        <div className="status-banner">
          <RefreshCw size={14} className="spin" />
          <span>Loading RFM snapshot...</span>
        </div>
      )}

      {error && (
        <div className="status-banner status-banner--error">
          <span>Failed to query RFM segments: {error}</span>
        </div>
      )}

      {!loading && !error && heatmap && scoredCustomers === 0 && (
        <div className="empty-panel">
          <Search size={28} strokeWidth={1.5} className="empty-panel__icon" />
          <h3 className="empty-panel__title">No Scored Customers</h3>
          <p className="empty-panel__desc">
            {segment === 'no_purchase'
              ? 'Customers who never purchased have no recency or frequency score, so they are not placed on the heatmap.'
              : `No RFM snapshot is stored for ${snapshotDate}. Segments are built for 2019-11-30.`}
          </p>
        </div>
      )}

      {!loading && !error && heatmap && scoredCustomers > 0 && (
        <div className="content-stack">
          <div className="kpi-ribbon">
            <div className="kpi-ribbon__cell">
              <span className="kpi-ribbon__label">Scored Customers</span>
              <div className="kpi-ribbon__value">{scoredCustomers.toLocaleString()}</div>
              <span className="kpi-ribbon__hint">Purchased at least once</span>
            </div>
            <div className="kpi-ribbon__cell">
              <span className="kpi-ribbon__label">Champions</span>
              <div className="kpi-ribbon__value">{(heatmap.segments.get('champion') ?? 0).toLocaleString()}</div>
              <span className="kpi-ribbon__hint">Recent and frequent buyers</span>
            </div>
            <div className="kpi-ribbon__cell">
              <span className="kpi-ribbon__label">At Risk</span>
              <div className="kpi-ribbon__value">{(heatmap.segments.get('at_risk') ?? 0).toLocaleString()}</div>
              <span className="kpi-ribbon__hint">Frequent buyers gone quiet</span>
            </div>
            <div className="kpi-ribbon__cell">
              <span className="kpi-ribbon__label">Selected Cell</span>
              <div className="kpi-ribbon__value">{selectedCount === null ? '—' : selectedCount.toLocaleString()}</div>
              <span className="kpi-ribbon__hint">
                {selected ? `R${selected.r} · F${selected.f}` : 'Click a cell to list its customers'}
              </span>
            </div>
          </div>

          <div className="panel">
            <div className="panel__header">
              <div className="panel__title-group">
                <h2 className="panel__title">Recency × Frequency</h2>
                <span className="panel__subtitle">
                  {snapshotDate} · {segment === 'all' ? 'All Segments' : segmentLabel(segment)}
                </span>
              </div>
            </div>

            <div className="heatmap">
              <div className="heatmap__grid">
                {[...SCORES].reverse().map(r => (
                  <Fragment key={r}>
                    <span className="heatmap__axis">R{r}</span>
                    {SCORES.map(f => {
                      const count = heatmap.cells.get(cellKey(r, f)) ?? 0;
                      const isSelected = selected?.r === r && selected?.f === f;
                      return (
                        <button
                          key={f}
                          type="button"
                          className={['heatmap__cell', isSelected ? 'heatmap__cell--selected' : ''].filter(Boolean).join(' ')}
                          style={{ '--heat': largestCell ? count / largestCell : 0 } as CSSProperties}
                          aria-label={`R${r} F${f}: ${count} customers`}
                          aria-pressed={isSelected}
                          onClick={() => setSelected({ r, f })}
                        >
                          <span className="heatmap__count">{count.toLocaleString()}</span>
                        </button>
                      );
                    })}
                  </Fragment>
                ))}
                <span />
                {SCORES.map(f => (
                  <span key={f} className="heatmap__axis">
                    F{f}
                  </span>
                ))}
              </div>
              <div className="heatmap__legend">
                <span>Rows: recency score, 5 = most recent. Columns: frequency score, 5 = most frequent.</span>
                <span>Recency is taken from the snapshot that set each customer's current segment.</span>
              </div>
            </div>

            {selected && (
              <div className="panel__table-wrapper">
                {!cellRows && (
                  <div className="status-banner">
                    <RefreshCw size={14} className="spin" />
                    <span>
                      Loading customers in R{selected.r} · F{selected.f}...
                    </span>
                  </div>
                )}
                {cellRows && cellRows.data.length === 0 && (
                  <div className="empty-panel">
                    <Users size={28} strokeWidth={1.5} className="empty-panel__icon" />
                    <h3 className="empty-panel__title">No Customers in This Cell</h3>
                    <p className="empty-panel__desc">
                      No customer has recency score {selected.r} and frequency score {selected.f} for this filter.
                    </p>
                  </div>
                )}
                {cellRows && cellRows.data.length > 0 && (
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>User ID</th>
                        <th>Segment</th>
                        <th>Recency (days)</th>
                        <th>Frequency</th>
                        <th>Monetary</th>
                        <th>RFM Cell</th>
                      </tr>
                    </thead>
                    <tbody>
                      {cellRows.data.map(row => (
                        <tr key={row.user_id}>
                          <td className="font-mono">{row.user_id}</td>
                          <td>{segmentLabel(row.segment)}</td>
                          <td className="data-table__numeric font-mono">{orDash(row.recency_days)}</td>
                          <td className="data-table__numeric font-mono">{row.frequency.toLocaleString()}</td>
                          <td className="data-table__numeric font-mono text-emphasis">{formatMoney(row.monetary)}</td>
                          <td className="data-table__numeric font-mono text-secondary">{orDash(row.rfm_cell)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            )}

            {footerMeta && (
              <div className="panel__footer">
                <QueryMeta meta={footerMeta} />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
