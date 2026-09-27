import { Clock, Database, Layers, Hash } from 'lucide-react';
import type { QueryMeta as QueryMetaType } from '../types/api';

interface Props {
  meta: QueryMetaType;
}

export default function QueryMeta({ meta }: Props) {
  return (
    <footer className="query-meta">
      <div className="query-meta__item">
        <Clock size={12} strokeWidth={1.75} />
        <span>{meta.ms} ms</span>
      </div>
      <span className="query-meta__sep">/</span>
      <div className="query-meta__item">
        <Database size={12} strokeWidth={1.75} />
        <span>{meta.warehouse}</span>
      </div>
      <span className="query-meta__sep">/</span>
      <div className="query-meta__item">
        <Layers size={12} strokeWidth={1.75} />
        <span>{meta.partitions} {meta.partitions === 1 ? 'partition' : 'partitions'}</span>
      </div>
      <span className="query-meta__sep">/</span>
      <div className="query-meta__item">
        <Hash size={12} strokeWidth={1.75} />
        <span>{meta.rows.toLocaleString()} rows</span>
      </div>
    </footer>
  );
}

