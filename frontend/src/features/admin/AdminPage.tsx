import { useAdmin } from "../../hooks/useAdmin";
import { HealthCard } from "./components/HealthCard";
import { SyncCard } from "./components/SyncCard";
import { IndexCard } from "./components/IndexCard";
import { ProviderSelector } from "./ProviderSelector";
import "./AdminPage.css";

export function AdminPage() {
  const {
    health,
    syncStatus,
    indexStatus,
    fullSync,
    incrementalSync,
    indexRebuild,
  } = useAdmin();

  return (
    <div className="admin-page">
      <header className="admin-page__header">
        <h1 className="admin-page__title">Administration</h1>
      </header>

      <div className="admin-page__grid">
        <div className="card animate-in">
          <div className="card__header">
            <h2 className="card__title">AI Provider</h2>
          </div>
          <div className="card__body">
            <ProviderSelector />
          </div>
        </div>

        <HealthCard
          data={health.data}
          error={health.error}
          isLoading={health.isLoading}
        />
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
