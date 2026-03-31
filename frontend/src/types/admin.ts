/** Matches OpenAPI DependencyStatus */
export type DependencyStatus = "ok" | "degraded" | "error" | "not_configured";

/** Matches OpenAPI HealthResponse */
export interface HealthResponse {
  status: "ok" | "degraded" | "error";
  service: "kms-bot-backend";
  version: string;
  timestamp: string;
  dependencies: {
    sqlite: DependencyStatus;
    azure_ai_search: DependencyStatus;
    azure_openai: DependencyStatus;
  };
}

/** Matches OpenAPI OperationAcceptedResponse */
export interface OperationAcceptedResponse {
  job_id: string;
  job_type: "full_sync" | "incremental_sync" | "index_rebuild";
  status: "accepted";
  requested_at: string;
  pipeline_version: number;
  message: string;
}

/** Matches OpenAPI SyncStatusResponse */
export interface SyncStatusResponse {
  status: "idle" | "running" | "success" | "error";
  mode: "none" | "full" | "incremental";
  current_job_id: string | null;
  pipeline_version: number;
  last_started_at: string | null;
  last_finished_at: string | null;
  last_success_at: string | null;
  processed_pages: number;
  changed_pages: number;
  error_message: string | null;
}

/** Matches OpenAPI IndexStatusResponse */
export interface IndexStatusResponse {
  status: "idle" | "running" | "success" | "error";
  current_job_id: string | null;
  pipeline_version: number;
  last_started_at: string | null;
  last_finished_at: string | null;
  last_success_at: string | null;
  indexed_documents: number;
  indexed_chunks: number;
  error_message: string | null;
}
