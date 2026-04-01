import { useCallback, useEffect, useRef, useState } from "react";
import type { TokenUsageSummary } from "../types/settings";
import { getTokenUsage } from "../services/api/settingsApi";

export interface UseTokenUsage {
  data: TokenUsageSummary | null;
  isLoading: boolean;
  error: string | null;
  refresh: () => void;
}

export function useTokenUsage(): UseTokenUsage {
  const [data, setData] = useState<TokenUsageSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const mountedRef = useRef(true);

  const load = useCallback(() => {
    setIsLoading(true);
    getTokenUsage()
      .then((d) => {
        if (mountedRef.current) {
          setData(d);
          setError(null);
        }
      })
      .catch((err: unknown) => {
        if (mountedRef.current)
          setError(err instanceof Error ? err.message : "Failed to load token usage");
      })
      .finally(() => {
        if (mountedRef.current) setIsLoading(false);
      });
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    load();
    return () => {
      mountedRef.current = false;
    };
  }, [load]);

  return { data, isLoading, error, refresh: load };
}
