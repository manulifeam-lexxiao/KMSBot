import { useCallback, useState } from "react";
import type { SearchProviderStatus } from "../types/settings";
import { getSearchProvider, setSearchProvider } from "../services/api/settingsApi";

export interface UseSearchProvider {
  status: SearchProviderStatus | null;
  isLoading: boolean;
  isSwitching: boolean;
  error: string | null;
  switchProvider: (provider: SearchProviderStatus["provider"]) => Promise<void>;
}

export function useSearchProvider(): UseSearchProvider {
  const [status, setStatus] = useState<SearchProviderStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSwitching, setIsSwitching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [initialized, setInitialized] = useState(false);

  if (!initialized) {
    setInitialized(true);
    setIsLoading(true);
    getSearchProvider()
      .then((data) => {
        setStatus(data);
        setError(null);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Unknown error");
      })
      .finally(() => setIsLoading(false));
  }

  const switchProvider = useCallback(async (provider: SearchProviderStatus["provider"]) => {
    setIsSwitching(true);
    setError(null);
    try {
      const updated = await setSearchProvider(provider);
      setStatus(updated);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setIsSwitching(false);
    }
  }, []);

  return { status, isLoading, isSwitching, error, switchProvider };
}
