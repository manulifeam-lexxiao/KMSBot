import type {
  HealthResponse,
  IndexStatusResponse,
  OperationAcceptedResponse,
  SyncStatusResponse,
} from "../../types/settings";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const msg =
      body && typeof body === "object" && "message" in body
        ? String(body.message)
        : `Request failed (${res.status})`;
    throw new Error(msg);
  }
  return (await res.json()) as T;
}

export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch(`${BASE_URL}/api/health`);
  return handleResponse<HealthResponse>(res);
}

export async function getSyncStatus(): Promise<SyncStatusResponse> {
  const res = await fetch(`${BASE_URL}/api/sync/status`);
  return handleResponse<SyncStatusResponse>(res);
}

export async function triggerFullSync(): Promise<OperationAcceptedResponse> {
  const res = await fetch(`${BASE_URL}/api/sync/full`, { method: "POST" });
  return handleResponse<OperationAcceptedResponse>(res);
}

export async function triggerIncrementalSync(): Promise<OperationAcceptedResponse> {
  const res = await fetch(`${BASE_URL}/api/sync/incremental`, {
    method: "POST",
  });
  return handleResponse<OperationAcceptedResponse>(res);
}

export async function getIndexStatus(): Promise<IndexStatusResponse> {
  const res = await fetch(`${BASE_URL}/api/index/status`);
  return handleResponse<IndexStatusResponse>(res);
}

export async function triggerIndexRebuild(): Promise<OperationAcceptedResponse> {
  const res = await fetch(`${BASE_URL}/api/index/rebuild`, { method: "POST" });
  return handleResponse<OperationAcceptedResponse>(res);
}
