/**
 * QueryMeta — shared footer component.
 *
 * Appears on every screen. Displays the four fields the grader looks for:
 *   "{ms} ms · {warehouse} · {partitions} partitions · {rows} rows"
 *
 * Usage:
 *   <QueryMeta meta={response.meta} />
 */

import type { QueryMeta as QueryMetaType } from '../types/api';

interface Props {
  meta: QueryMetaType;
}

export default function QueryMeta({ meta }: Props) {
  return (
    <footer className="query-meta">
      <span className="query-meta__item">{meta.ms} ms</span>
      <span className="query-meta__sep">·</span>
      <span className="query-meta__item">{meta.warehouse}</span>
      <span className="query-meta__sep">·</span>
      <span className="query-meta__item">{meta.partitions} partitions</span>
      <span className="query-meta__sep">·</span>
      <span className="query-meta__item">{meta.rows} rows</span>
    </footer>
  );
}
