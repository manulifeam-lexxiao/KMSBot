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
    search_backend?: string;
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

/** Token usage daily breakdown */
export interface TokenUsageDaily {
  date: string;
  prompt_tokens: number;
  completion_tokens: number;
  requests: number;
}

/** Token usage per-provider or per-mode breakdown */
export interface TokenUsageBreakdown {
  prompt_tokens: number;
  completion_tokens: number;
  requests: number;
}

/** Token usage summary from backend */
export interface TokenUsageSummary {
  total_prompt_tokens: number;
  total_completion_tokens: number;
  total_tokens: number;
  total_requests: number;
  daily: TokenUsageDaily[];
  by_provider: Record<string, TokenUsageBreakdown>;
  by_mode: Record<string, TokenUsageBreakdown>;
}

/** THINKING mode settings */
export interface ThinkingSettings {
  thinking_max_articles: number;
}

/** Query settings */
export interface QuerySettings {
  top_k: number;
  max_chunks_per_doc: number;
  similarity_threshold: number;
}

/** Search provider status */
export interface SearchProviderStatus {
  provider: "sqlite_fts5" | "azure_ai_search";
  available_providers: string[];
  azure_configured: boolean;
}

/** Confluence connectivity status */
export interface ConfluenceStatus {
  configured: boolean;
  base_url: string | null;
  space_key: string | null;
  page_limit: number | null;
  connectivity: "ok" | "error" | "not_configured";
  error_detail: string | null;
}
