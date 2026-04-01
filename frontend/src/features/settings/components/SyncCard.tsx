import type { SyncStatusResponse } from "../../../types/settings";
import type { ActionState } from "../settingsTypes";
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

export function SyncCard({ data, error, isLoading, fullSync, incrementalSync }: SyncCardProps) {
  const isBusy = data?.status === "running" || fullSync.isRunning || incrementalSync.isRunning;

  const progressPct =
    data && data.changed_pages > 0
      ? Math.min(Math.round((data.processed_pages / data.changed_pages) * 100), 100)
      : null;

  return (
    <section className="settings-card">
      {isBusy && (
        <div className="settings-card__progress">
          <div className="settings-card__progress-bar" />
        </div>
      )}
      {isBusy && (
        <div className="settings-card__progress settings-card__progress--bottom">
          {progressPct !== null ? (
            <>
              <div
                className="settings-card__progress-bar settings-card__progress-bar--determinate"
                style={{ width: `${progressPct}%` }}
              />
              <span className="settings-card__progress-label">{progressPct}%</span>
            </>
          ) : (
            <div className="settings-card__progress-bar" />
          )}
        </div>
      )}
      <h2 className="settings-card__title">Sync</h2>
      {isLoading && !data && <p className="settings-card__loading">Loading…</p>}
      {error && <p className="settings-card__error">{error}</p>}
      {data && (
        <div className="settings-card__body">
          <div className="settings-card__row">
            <span className="settings-card__label">Status</span>
            <StatusBadge status={data.status} />
          </div>
          <div className="settings-card__row">
            <span className="settings-card__label">Mode</span>
            <span>{data.mode}</span>
          </div>
          <div className="settings-card__row">
            <span className="settings-card__label">Pipeline Version</span>
            <span>{data.pipeline_version}</span>
          </div>
          <div className="settings-card__row">
            <span className="settings-card__label">Processed Pages</span>
            <span>{data.processed_pages}</span>
          </div>
          <div className="settings-card__row">
            <span className="settings-card__label">Changed Pages</span>
            <span>{data.changed_pages}</span>
          </div>
          <div className="settings-card__row">
            <span className="settings-card__label">Last Started</span>
            <span>{fmtTime(data.last_started_at)}</span>
          </div>
          <div className="settings-card__row">
            <span className="settings-card__label">Last Finished</span>
            <span>{fmtTime(data.last_finished_at)}</span>
          </div>
          <div className="settings-card__row">
            <span className="settings-card__label">Last Success</span>
            <span>{fmtTime(data.last_success_at)}</span>
          </div>
          {data.error_message && (
            <div className="settings-card__row">
              <span className="settings-card__label">Error</span>
              <span className="settings-card__error-text">{data.error_message}</span>
            </div>
          )}
        </div>
      )}
      <div className="settings-card__actions">
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
