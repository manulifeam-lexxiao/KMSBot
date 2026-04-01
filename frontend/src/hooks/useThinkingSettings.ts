import { useCallback, useEffect, useRef, useState } from "react";
import type { ThinkingSettings } from "../types/settings";
import { getThinkingSettings, setThinkingSettings } from "../services/api/settingsApi";

export interface UseThinkingSettings {
  settings: ThinkingSettings | null;
  isLoading: boolean;
  isSaving: boolean;
  error: string | null;
  updateMaxArticles: (value: number) => Promise<void>;
}

export function useThinkingSettings(): UseThinkingSettings {
  const [settings, setSettings] = useState<ThinkingSettings | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    getThinkingSettings()
      .then((s) => {
        if (mountedRef.current) setSettings(s);
      })
      .catch((e: unknown) => {
        if (mountedRef.current)
          setError(e instanceof Error ? e.message : "Failed to load thinking settings");
      })
      .finally(() => {
        if (mountedRef.current) setIsLoading(false);
      });
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const updateMaxArticles = useCallback(async (value: number) => {
    setIsSaving(true);
    setError(null);
    try {
      const result = await setThinkingSettings({ thinking_max_articles: value });
      if (mountedRef.current) setSettings(result);
    } catch (e: unknown) {
      if (mountedRef.current)
        setError(e instanceof Error ? e.message : "Failed to update settings");
    } finally {
      if (mountedRef.current) setIsSaving(false);
    }
  }, []);

  return { settings, isLoading, isSaving, error, updateMaxArticles };
}
