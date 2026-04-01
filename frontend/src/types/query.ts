/** Matches OpenAPI QueryRequest */
export interface QueryRequest {
  query: string;
  top_k: number;
  include_debug: boolean;
  thinking: boolean;
}

/** SSE event emitted during THINKING mode streaming */
export interface ThinkingEvent {
  stage: "planning" | "searching" | "reading" | "summarizing" | "done";
  message?: string;
  articles_found?: number;
  reading?: number;
  current?: number;
  total?: number;
  /** Present only when stage === "done" */
  data?: QueryResponse;
}

/** Matches OpenAPI QuerySource */
export interface QuerySource {
  title: string;
  url: string;
  section: string;
  doc_id: string;
  chunk_id: string;
}

/** Matches OpenAPI RelatedDocument */
export interface RelatedDocument {
  page_id: string;
  title: string;
  url: string;
}

/** Matches OpenAPI SearchResultHit */
export interface SearchResultHit {
  chunk_id: string;
  doc_id: string;
  title: string;
  section: string;
  content: string;
  url: string;
  tags: string[];
  pipeline_version: number;
  score: number;
}

/** Matches OpenAPI QueryDebugInfo */
export interface QueryDebugInfo {
  normalized_query: string;
  selected_chunks: SearchResultHit[];
}

/** Matches OpenAPI QueryResponse */
export interface QueryResponse {
  answer: string;
  sources: QuerySource[];
  related_documents: RelatedDocument[];
  debug: QueryDebugInfo;
}

/** Matches OpenAPI ErrorResponse */
export interface ErrorResponse {
  error_code: string;
  message: string;
  details?: Record<string, unknown>;
}

/** Chat message for UI state */
export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  /** Present only for assistant messages */
  response?: QueryResponse;
  /** Present when the query failed */
  error?: string;
  /** Present during THINKING mode streaming */
  thinkingStage?: ThinkingEvent;
}
