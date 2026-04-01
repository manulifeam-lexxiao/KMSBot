import { useTokenUsage } from "../../../hooks/useTokenUsage";

export function TokenUsageCard() {
  const { data, isLoading, error, refresh } = useTokenUsage();

  return (
    <div className="card animate-in">
      <div className="card__header">
        <h2 className="card__title">Token Usage</h2>
        <button type="button" className="card__action" onClick={refresh} disabled={isLoading}>
          Refresh
        </button>
      </div>
      <div className="card__body">
        {isLoading && <p className="card__placeholder">Loading...</p>}
        {error && <p className="card__error">{error}</p>}
        {data && (
          <div className="token-usage">
            <div className="token-usage__summary">
              <div className="token-usage__stat">
                <span className="token-usage__label">Total Tokens</span>
                <span className="token-usage__value">{data.total_tokens.toLocaleString()}</span>
              </div>
              <div className="token-usage__stat">
                <span className="token-usage__label">Prompt</span>
                <span className="token-usage__value">
                  {data.total_prompt_tokens.toLocaleString()}
                </span>
              </div>
              <div className="token-usage__stat">
                <span className="token-usage__label">Completion</span>
                <span className="token-usage__value">
                  {data.total_completion_tokens.toLocaleString()}
                </span>
              </div>
              <div className="token-usage__stat">
                <span className="token-usage__label">Requests</span>
                <span className="token-usage__value">{data.total_requests.toLocaleString()}</span>
              </div>
            </div>

            {Object.keys(data.by_provider).length > 0 && (
              <div className="token-usage__section">
                <h3 className="token-usage__section-title">By Provider</h3>
                {Object.entries(data.by_provider).map(([provider, stats]) => (
                  <div key={provider} className="token-usage__row">
                    <span className="token-usage__row-label">{provider}</span>
                    <span className="token-usage__row-value">
                      {(stats.prompt_tokens + stats.completion_tokens).toLocaleString()} tokens (
                      {stats.requests} req)
                    </span>
                  </div>
                ))}
              </div>
            )}

            {Object.keys(data.by_mode).length > 0 && (
              <div className="token-usage__section">
                <h3 className="token-usage__section-title">By Mode</h3>
                {Object.entries(data.by_mode).map(([mode, stats]) => (
                  <div key={mode} className="token-usage__row">
                    <span className="token-usage__row-label">{mode}</span>
                    <span className="token-usage__row-value">
                      {(stats.prompt_tokens + stats.completion_tokens).toLocaleString()} tokens (
                      {stats.requests} req)
                    </span>
                  </div>
                ))}
              </div>
            )}

            {data.daily.length > 0 && (
              <div className="token-usage__section">
                <h3 className="token-usage__section-title">Recent Daily</h3>
                {data.daily.slice(0, 7).map((day) => (
                  <div key={day.date} className="token-usage__row">
                    <span className="token-usage__row-label">{day.date}</span>
                    <span className="token-usage__row-value">
                      {(day.prompt_tokens + day.completion_tokens).toLocaleString()} tokens (
                      {day.requests} req)
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
