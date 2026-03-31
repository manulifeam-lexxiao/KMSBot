import type { HealthResponse } from "../../../types/admin";
import { StatusBadge } from "./StatusBadge";
import "./Card.css";

interface HealthCardProps {
  data: HealthResponse | null;
  error: string | null;
  isLoading: boolean;
}

export function HealthCard({ data, error, isLoading }: HealthCardProps) {
  return (
    <section className="admin-card">
      <h2 className="admin-card__title">Health</h2>
      {isLoading && !data && <p className="admin-card__loading">Loading…</p>}
      {error && <p className="admin-card__error">{error}</p>}
      {data && (
        <div className="admin-card__body">
          <div className="admin-card__row">
            <span className="admin-card__label">Status</span>
            <StatusBadge status={data.status} />
          </div>
          <div className="admin-card__row">
            <span className="admin-card__label">Version</span>
            <span>{data.version}</span>
          </div>
          <div className="admin-card__row">
            <span className="admin-card__label">Timestamp</span>
            <span>{new Date(data.timestamp).toLocaleString()}</span>
          </div>
          <div className="admin-card__row">
            <span className="admin-card__label">SQLite</span>
            <StatusBadge status={data.dependencies.sqlite} />
          </div>
          <div className="admin-card__row">
            <span className="admin-card__label">
              {data.dependencies.search_backend === "sqlite_fts5"
                ? "SQLite FTS5"
                : "Azure AI Search"}
            </span>
            <StatusBadge status={data.dependencies.azure_ai_search} />
          </div>
          <div className="admin-card__row">
            <span className="admin-card__label">Azure OpenAI</span>
            <StatusBadge status={data.dependencies.azure_openai} />
          </div>
        </div>
      )}
    </section>
  );
}
