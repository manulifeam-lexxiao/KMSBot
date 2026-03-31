import type { IndexStatusResponse } from "../../../types/admin";
import type { ActionState } from "../adminTypes";
import { StatusBadge } from "./StatusBadge";
import { ActionButton } from "./ActionButton";
import "./Card.css";

interface IndexCardProps {
  data: IndexStatusResponse | null;
  error: string | null;
  isLoading: boolean;
  indexRebuild: ActionState;
}

function fmtTime(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString();
}

export function IndexCard({ data, error, isLoading, indexRebuild }: IndexCardProps) {
  const isBusy = data?.status === "running" || indexRebuild.isRunning;

  return (
    <section className="admin-card">
      <h2 className="admin-card__title">Index</h2>
      {isLoading && !data && <p className="admin-card__loading">Loading…</p>}
      {error && <p className="admin-card__error">{error}</p>}
      {data && (
        <div className="admin-card__body">
          <div className="admin-card__row">
            <span className="admin-card__label">Status</span>
            <StatusBadge status={data.status} />
          </div>
          <div className="admin-card__row">
            <span className="admin-card__label">Pipeline Version</span>
            <span>{data.pipeline_version}</span>
          </div>
          <div className="admin-card__row">
            <span className="admin-card__label">Indexed Documents</span>
            <span>{data.indexed_documents}</span>
          </div>
          <div className="admin-card__row">
            <span className="admin-card__label">Indexed Chunks</span>
            <span>{data.indexed_chunks}</span>
          </div>
          <div className="admin-card__row">
            <span className="admin-card__label">Last Started</span>
            <span>{fmtTime(data.last_started_at)}</span>
          </div>
          <div className="admin-card__row">
            <span className="admin-card__label">Last Finished</span>
            <span>{fmtTime(data.last_finished_at)}</span>
          </div>
          <div className="admin-card__row">
            <span className="admin-card__label">Last Success</span>
            <span>{fmtTime(data.last_success_at)}</span>
          </div>
          {data.error_message && (
            <div className="admin-card__row">
              <span className="admin-card__label">Error</span>
              <span className="admin-card__error-text">{data.error_message}</span>
            </div>
          )}
        </div>
      )}
      <div className="admin-card__actions">
        <ActionButton
          label="Rebuild Index"
          onClick={indexRebuild.trigger}
          disabled={isBusy}
          isRunning={indexRebuild.isRunning}
          lastError={indexRebuild.lastError}
          lastMessage={indexRebuild.lastResult?.message ?? null}
        />
      </div>
    </section>
  );
}
