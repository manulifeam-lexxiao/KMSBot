import { useSettings } from "../../hooks/useSettings";
import { HealthCard } from "./components/HealthCard";
import { SyncCard } from "./components/SyncCard";
import { IndexCard } from "./components/IndexCard";
import { TokenUsageCard } from "./components/TokenUsageCard";
import { ThinkingSettingsCard } from "./components/ThinkingSettingsCard";
import { ProviderSelector } from "./ProviderSelector";
import "./SettingsPage.css";
import "./components/SettingsCards.css";

export function SettingsPage() {
  const { health, syncStatus, indexStatus, fullSync, incrementalSync, indexRebuild } =
    useSettings();

  return (
    <div className="settings-page">
      <header className="settings-page__header">
        <h1 className="settings-page__title">Settings</h1>
      </header>

      <div className="settings-page__grid">
        <div className="card animate-in">
          <div className="card__header">
            <h2 className="card__title">AI Provider</h2>
          </div>
          <div className="card__body">
            <ProviderSelector />
          </div>
        </div>

        <ThinkingSettingsCard />
        <TokenUsageCard />

        <HealthCard data={health.data} error={health.error} isLoading={health.isLoading} />
        <SyncCard
          data={syncStatus.data}
          error={syncStatus.error}
          isLoading={syncStatus.isLoading}
          fullSync={fullSync}
          incrementalSync={incrementalSync}
        />
        <IndexCard
          data={indexStatus.data}
          error={indexStatus.error}
          isLoading={indexStatus.isLoading}
          indexRebuild={indexRebuild}
        />
      </div>
    </div>
  );
}
