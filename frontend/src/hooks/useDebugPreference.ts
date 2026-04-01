import { useCallback, useState } from "react";

const STORAGE_KEY = "kmsbot:include_debug";

function readStored(): boolean {
  try {
    return localStorage.getItem(STORAGE_KEY) === "true";
  } catch {
    return false;
  }
}

export interface UseDebugPreference {
  includeDebug: boolean;
  setIncludeDebug: (value: boolean) => void;
}

export function useDebugPreference(): UseDebugPreference {
  const [includeDebug, setLocal] = useState<boolean>(readStored);

  const setIncludeDebug = useCallback((value: boolean) => {
    try {
      localStorage.setItem(STORAGE_KEY, String(value));
    } catch {
      // 忽略 localStorage 不可用的情况
    }
    setLocal(value);
  }, []);

  return { includeDebug, setIncludeDebug };
}
