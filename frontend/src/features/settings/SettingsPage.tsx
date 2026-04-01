import { useState } from "react";
import { useSettings } from "../../hooks/useSettings";
import { HealthCard } from "./components/HealthCard";
import { SyncCard } from "./components/SyncCard";
import { IndexCard } from "./components/IndexCard";
import { TokenUsageCard } from "./components/TokenUsageCard";
import { ThinkingSettingsCard } from "./components/ThinkingSettingsCard";
import { DebugSettingsCard } from "./components/DebugSettingsCard";
import { QuerySettingsCard } from "./components/QuerySettingsCard";
import { SearchProviderCard } from "./components/SearchProviderCard";
import { ConfluenceCard } from "./components/ConfluenceCard";
import { SettingsTabs } from "./components/SettingsTabs";
import { ProviderSelector } from "./ProviderSelector";
import "./SettingsPage.css";
import "./components/SettingsCards.css";

const TABS = [
  { id: "ai", label: "AI 模型" },
  { id: "query", label: "查询" },
  { id: "data", label: "数据" },
  { id: "system", label: "系统" },
];

export function SettingsPage() {
  const [activeTab, setActiveTab] = useState("ai");
  const {
    health,
    syncStatus,
    indexStatus,
    confluenceStatus,
    fullSync,
    incrementalSync,
    indexRebuild,
  } = useSettings();

  return (
    <div className="settings-page">
      <header className="settings-page__header">
        <h1 className="settings-page__title">Settings</h1>
      </header>

      <SettingsTabs tabs={TABS} activeTab={activeTab} onTabChange={setActiveTab}>
        {activeTab === "ai" && (
          <>
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
          </>
        )}

        {activeTab === "query" && (
          <>
            <DebugSettingsCard />
            <QuerySettingsCard />
            <SearchProviderCard />
          </>
        )}

        {activeTab === "data" && (
          <>
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
            <ConfluenceCard
              data={confluenceStatus.data}
              error={confluenceStatus.error}
              isLoading={confluenceStatus.isLoading}
            />
          </>
        )}

        {activeTab === "system" && (
          <HealthCard data={health.data} error={health.error} isLoading={health.isLoading} />
        )}
      </SettingsTabs>
    </div>
  );
}
