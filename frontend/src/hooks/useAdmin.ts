import { useCallback, useEffect, useRef, useState } from "react";
import type {
  HealthResponse,
  IndexStatusResponse,
  OperationAcceptedResponse,
  SyncStatusResponse,
} from "../types/admin";
import * as realApi from "../services/api/adminApi";
import * as mockApi from "../services/api/adminMock";

const useMock = import.meta.env.VITE_MOCK_API === "true";

const api = {
  getHealth: useMock ? mockApi.getHealthMock : realApi.getHealth,
  getSyncStatus: useMock ? mockApi.getSyncStatusMock : realApi.getSyncStatus,
  triggerFullSync: useMock ? mockApi.triggerFullSyncMock : realApi.triggerFullSync,
  triggerIncrementalSync: useMock
    ? mockApi.triggerIncrementalSyncMock
    : realApi.triggerIncrementalSync,
  getIndexStatus: useMock ? mockApi.getIndexStatusMock : realApi.getIndexStatus,
  triggerIndexRebuild: useMock ? mockApi.triggerIndexRebuildMock : realApi.triggerIndexRebuild,
};

/* ------------------------------------------------------------------ */
/*  Generic polling hook                                               */
/* ------------------------------------------------------------------ */

interface PollState<T> {
  data: T | null;
  error: string | null;
  isLoading: boolean;
  refresh: () => void;
}

function usePoll<T>(fetcher: () => Promise<T>, intervalMs = 10_000): PollState<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const mountedRef = useRef(true);

  const load = useCallback(() => {
    setIsLoading(true);
    fetcher()
      .then((d) => {
        if (mountedRef.current) {
          setData(d);
          setError(null);
        }
      })
      .catch((err: unknown) => {
        if (mountedRef.current) {
          setError(err instanceof Error ? err.message : "Unknown error");
        }
      })
      .finally(() => {
        if (mountedRef.current) setIsLoading(false);
      });
  }, [fetcher]);

  useEffect(() => {
    mountedRef.current = true;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
    const id = setInterval(load, intervalMs);
    return () => {
      mountedRef.current = false;
      clearInterval(id);
    };
  }, [load, intervalMs]);

  return { data, error, isLoading, refresh: load };
}

/* ------------------------------------------------------------------ */
/*  Action hook (fire-once operations like sync / rebuild)             */
/* ------------------------------------------------------------------ */

interface ActionState {
  isRunning: boolean;
  lastResult: OperationAcceptedResponse | null;
  lastError: string | null;
  trigger: () => void;
}

function useAction(
  action: () => Promise<OperationAcceptedResponse>,
  onSuccess?: () => void,
): ActionState {
  const [isRunning, setIsRunning] = useState(false);
  const [lastResult, setLastResult] = useState<OperationAcceptedResponse | null>(null);
  const [lastError, setLastError] = useState<string | null>(null);

  const trigger = useCallback(() => {
    if (isRunning) return;
    setIsRunning(true);
    setLastError(null);
    action()
      .then((resp) => {
        setLastResult(resp);
        onSuccess?.();
      })
      .catch((err: unknown) => {
        setLastError(err instanceof Error ? err.message : "Unknown error");
      })
      .finally(() => setIsRunning(false));
  }, [isRunning, action, onSuccess]);

  return { isRunning, lastResult, lastError, trigger };
}

/* ------------------------------------------------------------------ */
/*  Public composite hook                                              */
/* ------------------------------------------------------------------ */

export interface UseAdmin {
  health: PollState<HealthResponse>;
  syncStatus: PollState<SyncStatusResponse>;
  indexStatus: PollState<IndexStatusResponse>;
  fullSync: ActionState;
  incrementalSync: ActionState;
  indexRebuild: ActionState;
}

export function useAdmin(): UseAdmin {
  const health = usePoll(api.getHealth, 15_000);
  const syncStatus = usePoll(api.getSyncStatus, 8_000);
  const indexStatus = usePoll(api.getIndexStatus, 8_000);

  const fullSync = useAction(api.triggerFullSync, syncStatus.refresh);
  const incrementalSync = useAction(api.triggerIncrementalSync, syncStatus.refresh);
  const indexRebuild = useAction(api.triggerIndexRebuild, indexStatus.refresh);

  return {
    health,
    syncStatus,
    indexStatus,
    fullSync,
    incrementalSync,
    indexRebuild,
  };
}
