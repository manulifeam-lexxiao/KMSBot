import type { HealthResponse } from "../../../types/settings";
import { StatusBadge } from "./StatusBadge";
import "./Card.css";

interface HealthCardProps {
  data: HealthResponse | null;
  error: string | null;
  isLoading: boolean;
}

export function HealthCard({ data, error, isLoading }: HealthCardProps) {
  return (
    <section className="settings-card">
      <h2 className="settings-card__title">Health</h2>
      {isLoading && !data && <p className="settings-card__loading">Loading…</p>}
      {error && <p className="settings-card__error">{error}</p>}
      {data && (
        <div className="settings-card__body">
          <div className="settings-card__row">
            <span className="settings-card__label">Status</span>
            <StatusBadge status={data.status} />
          </div>
          <div className="settings-card__row">
            <span className="settings-card__label">Version</span>
            <span>{data.version}</span>
          </div>
          <div className="settings-card__row">
            <span className="settings-card__label">Timestamp</span>
            <span>{new Date(data.timestamp).toLocaleString()}</span>
          </div>
          <div className="settings-card__row">
            <span className="settings-card__label">SQLite</span>
            <StatusBadge status={data.dependencies.sqlite} />
          </div>
          <div className="settings-card__row">
            <span className="settings-card__label">
              {data.dependencies.search_backend === "sqlite_fts5"
                ? "SQLite FTS5"
                : "Azure AI Search"}
            </span>
            <StatusBadge status={data.dependencies.azure_ai_search} />
          </div>
          <div className="settings-card__row">
            <span className="settings-card__label">Azure OpenAI</span>
            <StatusBadge status={data.dependencies.azure_openai} />
          </div>
        </div>
      )}
    </section>
  );
}
