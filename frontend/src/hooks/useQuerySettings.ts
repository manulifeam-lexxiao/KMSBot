import { useCallback, useState } from "react";
import type { QuerySettings } from "../types/settings";
import { getQuerySettings, setQuerySettings } from "../services/api/settingsApi";

export interface UseQuerySettings {
  settings: QuerySettings | null;
  isLoading: boolean;
  isSaving: boolean;
  error: string | null;
  updateQuerySettings: (updates: Partial<QuerySettings>) => Promise<void>;
}

export function useQuerySettings(): UseQuerySettings {
  const [settings, setSettings] = useState<QuerySettings | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [initialized, setInitialized] = useState(false);

  if (!initialized) {
    setInitialized(true);
    setIsLoading(true);
    getQuerySettings()
      .then((data) => {
        setSettings(data);
        setError(null);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Unknown error");
      })
      .finally(() => setIsLoading(false));
  }

  const updateQuerySettings = useCallback(async (updates: Partial<QuerySettings>) => {
    setIsSaving(true);
    setError(null);
    try {
      const updated = await setQuerySettings(updates);
      setSettings(updated);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setIsSaving(false);
    }
  }, []);

  return { settings, isLoading, isSaving, error, updateQuerySettings };
}
