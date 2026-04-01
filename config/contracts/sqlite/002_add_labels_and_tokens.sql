-- 002_add_labels_and_tokens.sql
-- 新增 labels 列到 document_registry + 创建 token_usage 表 + 创建 titles_fts 虚拟表

-- ---- document_registry: 新增 labels 列 ----
ALTER TABLE document_registry ADD COLUMN labels TEXT DEFAULT '[]';

-- ---- token_usage: LLM 调用 token 使用记录 ----
CREATE TABLE IF NOT EXISTS token_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    query TEXT NOT NULL,
    mode TEXT NOT NULL CHECK (mode IN ('standard', 'thinking')),
    provider TEXT NOT NULL,
    stage TEXT NOT NULL CHECK (stage IN ('planning', 'ranking', 'answering', 'summarizing')),
    prompt_tokens INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    model TEXT
);

CREATE INDEX IF NOT EXISTS idx_token_usage_timestamp ON token_usage (timestamp);
CREATE INDEX IF NOT EXISTS idx_token_usage_provider ON token_usage (provider);
CREATE INDEX IF NOT EXISTS idx_token_usage_mode ON token_usage (mode);

-- ---- titles_fts: L0 标题 + labels 快速搜索索引 ----
CREATE VIRTUAL TABLE IF NOT EXISTS titles_fts USING fts5(
    page_id UNINDEXED,
    title,
    labels,
    tokenize='unicode61 remove_diacritics 2'
);
