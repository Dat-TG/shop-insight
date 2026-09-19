import { Terminal, ArrowUpRight } from 'lucide-react';

interface Props {
  name: string;
  owner?: string;
  eta?: string;
}

export default function UnderDevelopment({ name, owner, eta }: Props) {
  return (
    <div className="under-dev">
      <div className="under-dev__badge">
        <Terminal size={14} strokeWidth={1.75} />
        <span>Module in progress</span>
      </div>
      <h2 className="under-dev__title">{name}</h2>
      <p className="under-dev__msg">This analytical view is currently being provisioned for the pipeline.</p>
      {(owner || eta) && (
        <div className="under-dev__meta">
          {owner && (
            <span className="under-dev__tag">
              Owner: <strong>{owner}</strong>
            </span>
          )}
          {eta && (
            <span className="under-dev__tag">
              Target: <strong>{eta}</strong>
            </span>
          )}
        </div>
      )}
    </div>
  );
}

