import type { SyncStatusResponse } from "../../../types/admin";
import type { ActionState } from "../adminTypes";
import { StatusBadge } from "./StatusBadge";
import { ActionButton } from "./ActionButton";
import "./Card.css";

interface SyncCardProps {
  data: SyncStatusResponse | null;
  error: string | null;
  isLoading: boolean;
  fullSync: ActionState;
  incrementalSync: ActionState;
}

function fmtTime(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString();
}

export function SyncCard({
  data,
  error,
  isLoading,
  fullSync,
  incrementalSync,
}: SyncCardProps) {
  const isBusy =
    data?.status === "running" ||
    fullSync.isRunning ||
    incrementalSync.isRunning;

  return (
    <section className="admin-card">
      <h2 className="admin-card__title">Sync</h2>
      {isLoading && !data && <p className="admin-card__loading">Loading…</p>}
      {error && <p className="admin-card__error">{error}</p>}
      {data && (
        <div className="admin-card__body">
          <div className="admin-card__row">
            <span className="admin-card__label">Status</span>
            <StatusBadge status={data.status} />
          </div>
          <div className="admin-card__row">
            <span className="admin-card__label">Mode</span>
            <span>{data.mode}</span>
          </div>
          <div className="admin-card__row">
            <span className="admin-card__label">Pipeline Version</span>
            <span>{data.pipeline_version}</span>
          </div>
          <div className="admin-card__row">
            <span className="admin-card__label">Processed Pages</span>
            <span>{data.processed_pages}</span>
          </div>
          <div className="admin-card__row">
            <span className="admin-card__label">Changed Pages</span>
            <span>{data.changed_pages}</span>
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
              <span className="admin-card__error-text">
                {data.error_message}
              </span>
            </div>
          )}
        </div>
      )}
      <div className="admin-card__actions">
        <ActionButton
          label="Full Sync"
          onClick={fullSync.trigger}
          disabled={isBusy}
          isRunning={fullSync.isRunning}
          lastError={fullSync.lastError}
          lastMessage={fullSync.lastResult?.message ?? null}
        />
        <ActionButton
          label="Incremental Sync"
          onClick={incrementalSync.trigger}
          disabled={isBusy}
          isRunning={incrementalSync.isRunning}
          lastError={incrementalSync.lastError}
          lastMessage={incrementalSync.lastResult?.message ?? null}
        />
      </div>
    </section>
  );
}
