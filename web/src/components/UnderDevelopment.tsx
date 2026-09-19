/**
 * UnderDevelopment — placeholder for screens not yet implemented.
 *
 * Usage:
 *   <UnderDevelopment name="BR3 — Trending Products" owner="Khang" eta="W41" />
 */

interface Props {
  name: string;
  owner?: string;
  eta?: string;
}

export default function UnderDevelopment({ name, owner, eta }: Props) {
  return (
    <div className="under-dev">
      <div className="under-dev__icon">🚧</div>
      <h2 className="under-dev__title">{name}</h2>
      <p className="under-dev__msg">This screen is under development.</p>
      {(owner || eta) && (
        <p className="under-dev__meta">
          {owner && <span>Owner: <strong>{owner}</strong></span>}
          {owner && eta && '  ·  '}
          {eta && <span>ETA: <strong>{eta}</strong></span>}
        </p>
      )}
    </div>
  );
}
