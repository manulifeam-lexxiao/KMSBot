import type { QuerySource } from "../../../types/query";
import "./SourceList.css";

interface SourceListProps {
  sources: QuerySource[];
}

export function SourceList({ sources }: SourceListProps) {
  if (sources.length === 0) return null;

  return (
    <div className="source-list">
      <h4 className="source-list__title">Sources</h4>
      <ul className="source-list__items">
        {sources.map((s) => (
          <li key={s.chunk_id} className="source-list__item">
            <a href={s.url} target="_blank" rel="noopener noreferrer" className="source-list__link">
              {s.title}
            </a>
            <span className="source-list__section">§ {s.section}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
