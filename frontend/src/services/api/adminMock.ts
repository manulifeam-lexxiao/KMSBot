import type {
  HealthResponse,
  IndexStatusResponse,
  OperationAcceptedResponse,
  SyncStatusResponse,
} from "../../types/admin";

const MOCK_DELAY_MS = 400;

function delay(ms = MOCK_DELAY_MS): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}

export async function getHealthMock(): Promise<HealthResponse> {
  await delay();
  return {
    status: "ok",
    service: "kms-bot-backend",
    version: "0.1.0",
    timestamp: new Date().toISOString(),
    dependencies: {
      sqlite: "ok",
      azure_ai_search: "not_configured",
      azure_openai: "not_configured",
    },
  };
}

export async function getSyncStatusMock(): Promise<SyncStatusResponse> {
  await delay();
  return {
    status: "idle",
    mode: "none",
    current_job_id: null,
    pipeline_version: 1,
    last_started_at: "2026-03-30T10:00:00Z",
    last_finished_at: "2026-03-30T10:02:30Z",
    last_success_at: "2026-03-30T10:02:30Z",
    processed_pages: 42,
    changed_pages: 5,
    error_message: null,
  };
}

export async function triggerFullSyncMock(): Promise<OperationAcceptedResponse> {
  await delay(600);
  return {
    job_id: `sync-full-mock-${Date.now()}`,
    job_type: "full_sync",
    status: "accepted",
    requested_at: new Date().toISOString(),
    pipeline_version: 1,
    message: "Full sync request accepted.",
  };
}

export async function triggerIncrementalSyncMock(): Promise<OperationAcceptedResponse> {
  await delay(600);
  return {
    job_id: `sync-incremental-mock-${Date.now()}`,
    job_type: "incremental_sync",
    status: "accepted",
    requested_at: new Date().toISOString(),
    pipeline_version: 1,
    message: "Incremental sync request accepted.",
  };
}

export async function getIndexStatusMock(): Promise<IndexStatusResponse> {
  await delay();
  return {
    status: "success",
    current_job_id: null,
    pipeline_version: 1,
    last_started_at: "2026-03-30T10:05:00Z",
    last_finished_at: "2026-03-30T10:06:15Z",
    last_success_at: "2026-03-30T10:06:15Z",
    indexed_documents: 42,
    indexed_chunks: 187,
    error_message: null,
  };
}

export async function triggerIndexRebuildMock(): Promise<OperationAcceptedResponse> {
  await delay(600);
  return {
    job_id: `index-rebuild-mock-${Date.now()}`,
    job_type: "index_rebuild",
    status: "accepted",
    requested_at: new Date().toISOString(),
    pipeline_version: 1,
    message: "Index rebuild request accepted.",
  };
}
