import { useCallback, useEffect, useRef, useState } from "react";
import {
  getProvider,
  setProvider,
  type ProviderName,
  type ProviderStatus,
} from "../services/api/settingsApi";

interface UseProviderState {
  status: ProviderStatus | null;
  isLoading: boolean;
  isSwitching: boolean;
  error: string | null;
  switchProvider: (provider: ProviderName) => Promise<void>;
}

export function useProvider(): UseProviderState {
  const [status, setStatus] = useState<ProviderStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSwitching, setIsSwitching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    getProvider()
      .then((s) => {
        if (mountedRef.current) setStatus(s);
      })
      .catch((e: unknown) => {
        if (mountedRef.current)
          setError(e instanceof Error ? e.message : "Failed to load provider");
      })
      .finally(() => {
        if (mountedRef.current) setIsLoading(false);
      });
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const switchProvider = useCallback(async (provider: ProviderName) => {
    setIsSwitching(true);
    setError(null);
    try {
      const result = await setProvider(provider);
      if (mountedRef.current) setStatus(result);
    } catch (e: unknown) {
      if (mountedRef.current)
        setError(e instanceof Error ? e.message : "Failed to switch provider");
    } finally {
      if (mountedRef.current) setIsSwitching(false);
    }
  }, []);

  return { status, isLoading, isSwitching, error, switchProvider };
}
