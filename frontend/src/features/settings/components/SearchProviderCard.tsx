import { useSearchProvider } from "../../../hooks/useSearchProvider";

const PROVIDER_META: Record<string, { label: string; desc: string }> = {
  sqlite_fts5: {
    label: "SQLite FTS5",
    desc: "本地全文检索，无需外部依赖。适合开发和小规模部署。",
  },
  azure_ai_search: {
    label: "Azure AI Search",
    desc: "Azure 云端向量语义检索。需要配置 endpoint 和 API key。",
  },
};

export function SearchProviderCard() {
  const { status, isLoading, isSwitching, error, switchProvider } = useSearchProvider();

  if (isLoading) {
    return (
      <div className="card animate-in">
        <div className="card__header">
          <h2 className="card__title">Search Provider</h2>
        </div>
        <div className="card__body">
          <div className="provider-selector provider-selector--loading">
            <span className="provider-selector__skeleton" />
            <span className="provider-selector__skeleton" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="card animate-in">
      <div className="card__header">
        <h2 className="card__title">Search Provider</h2>
      </div>
      <div className="card__body">
        {error && <p className="provider-selector__error">{error}</p>}
        <div className="provider-selector__options">
          {(["sqlite_fts5", "azure_ai_search"] as const).map((name) => {
            const meta = PROVIDER_META[name]!;
            const isActive = status?.provider === name;
            const isDisabled =
              isSwitching || isActive || (name === "azure_ai_search" && !status?.azure_configured);
            return (
              <button
                key={name}
                type="button"
                className={`provider-option${isActive ? " provider-option--active" : ""}`}
                onClick={() => switchProvider(name)}
                disabled={isDisabled}
                title={
                  name === "azure_ai_search" && !status?.azure_configured
                    ? "Azure AI Search 未配置"
                    : undefined
                }
              >
                <div className="provider-option__header">
                  <span className="provider-option__name">{meta.label}</span>
                  {isActive && <span className="provider-option__badge">Active</span>}
                  {name === "azure_ai_search" && !status?.azure_configured && (
                    <span className="provider-option__badge provider-option__badge--warn">
                      未配置
                    </span>
                  )}
                </div>
                <p className="provider-option__desc">{meta.desc}</p>
              </button>
            );
          })}
        </div>
        {isSwitching && <p className="provider-selector__status">Switching provider…</p>}
      </div>
    </div>
  );
}
