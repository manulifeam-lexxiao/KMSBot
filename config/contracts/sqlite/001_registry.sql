PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS document_registry (
    page_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    source_version INTEGER NOT NULL,
    last_updated TEXT NOT NULL,
    raw_hash TEXT NOT NULL,
    chunk_count INTEGER NOT NULL DEFAULT 0 CHECK (chunk_count >= 0),
    pipeline_version INTEGER NOT NULL CHECK (pipeline_version >= 1),
    index_status TEXT NOT NULL CHECK (
        index_status IN ('not_indexed', 'pending', 'indexed', 'stale', 'error')
    ),
    last_sync_time TEXT,
    last_index_time TEXT,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_document_registry_index_status
    ON document_registry (index_status);

CREATE INDEX IF NOT EXISTS idx_document_registry_last_updated
    ON document_registry (last_updated);

CREATE INDEX IF NOT EXISTS idx_document_registry_pipeline_version
    ON document_registry (pipeline_version);
