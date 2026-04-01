import type { ReactNode } from "react";
import "./SettingsTabs.css";

export interface TabItem {
  id: string;
  label: string;
}

interface SettingsTabsProps {
  tabs: TabItem[];
  activeTab: string;
  onTabChange: (id: string) => void;
  children: ReactNode;
}

export function SettingsTabs({ tabs, activeTab, onTabChange, children }: SettingsTabsProps) {
  return (
    <div className="settings-tabs">
      <nav className="settings-tabs__nav" role="tablist">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            role="tab"
            type="button"
            aria-selected={activeTab === tab.id}
            className={`settings-tabs__tab${activeTab === tab.id ? " settings-tabs__tab--active" : ""}`}
            onClick={() => onTabChange(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>
      <div className="settings-tabs__content" role="tabpanel">
        {children}
      </div>
    </div>
  );
}
