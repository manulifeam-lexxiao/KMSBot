import { useProvider } from "../../hooks/useProvider";
import type { ProviderName } from "../../services/api/settingsApi";
import "./ProviderSelector.css";

const PROVIDER_META: Record<ProviderName, { label: string; desc: string }> = {
  azure_openai: {
    label: "Azure OpenAI",
    desc: "Enterprise-grade deployment via Azure. Requires endpoint & API key.",
  },
  github_models: {
    label: "GitHub Models",
    desc: "OpenAI-compatible API via GitHub. Requires a GitHub PAT.",
  },
};

export function ProviderSelector() {
  const { status, isLoading, isSwitching, error, switchProvider } = useProvider();

  if (isLoading) {
    return (
      <div className="provider-selector provider-selector--loading">
        <span className="provider-selector__skeleton" />
        <span className="provider-selector__skeleton" />
      </div>
    );
  }

  return (
    <div className="provider-selector">
      {error && <p className="provider-selector__error">{error}</p>}
      <div className="provider-selector__options">
        {(["azure_openai", "github_models"] as ProviderName[]).map((name) => {
          const meta = PROVIDER_META[name];
          const isActive = status?.provider === name;
          return (
            <button
              key={name}
              type="button"
              className={`provider-option${isActive ? " provider-option--active" : ""}`}
              onClick={() => switchProvider(name)}
              disabled={isSwitching || isActive}
            >
              <div className="provider-option__header">
                <span className="provider-option__name">{meta.label}</span>
                {isActive && (
                  <span className="provider-option__badge">Active</span>
                )}
              </div>
              <p className="provider-option__desc">{meta.desc}</p>
            </button>
          );
        })}
      </div>
      {isSwitching && (
        <p className="provider-selector__status">Switching provider…</p>
      )}
    </div>
  );
}
