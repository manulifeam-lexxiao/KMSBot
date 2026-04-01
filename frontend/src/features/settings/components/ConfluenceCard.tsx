import type { ConfluenceStatus } from "../../../types/settings";
import { StatusBadge } from "./StatusBadge";

interface ConfluenceCardProps {
  data: ConfluenceStatus | null;
  error: string | null;
  isLoading: boolean;
}

export function ConfluenceCard({ data, error, isLoading }: ConfluenceCardProps) {
  return (
    <section className="settings-card">
      <h2 className="settings-card__title">Confluence</h2>
      {isLoading && !data && <p className="settings-card__loading">Loading…</p>}
      {error && <p className="settings-card__error">{error}</p>}
      {data && (
        <div className="settings-card__body">
          <div className="settings-card__row">
            <span className="settings-card__label">Connectivity</span>
            <StatusBadge status={data.connectivity} />
          </div>
          {data.configured ? (
            <>
              <div className="settings-card__row">
                <span className="settings-card__label">Base URL</span>
                <span>{data.base_url}</span>
              </div>
              <div className="settings-card__row">
                <span className="settings-card__label">Space Key</span>
                <span>{data.space_key}</span>
              </div>
              <div className="settings-card__row">
                <span className="settings-card__label">Page Limit</span>
                <span>{data.page_limit}</span>
              </div>
              {data.error_detail && (
                <div className="settings-card__row">
                  <span className="settings-card__label">Error</span>
                  <span className="settings-card__error-text">{data.error_detail}</span>
                </div>
              )}
            </>
          ) : (
            <div className="settings-card__row">
              <span className="settings-card__label" style={{ minWidth: "unset" }}>
                请在 config/app.yaml 中配置 confluence 连接信息
              </span>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
