# Local Data Layout

This directory stores only local runtime artifacts.

## Canonical Subdirectories

```text
data/raw/      raw Confluence payload snapshots
data/cleaned/  cleaned document JSON files
data/chunks/   per-document chunk arrays
data/sqlite/   SQLite database files
data/logs/     local log files
```

## File Naming Rules

- `data/raw/<page_id>.json`
- `data/cleaned/<doc_id>.json`
- `data/chunks/<doc_id>.json`
- `data/sqlite/kmsbot.db`
- `data/logs/<service>.log`

## Contract Rules

- `data/cleaned/<doc_id>.json` stores one cleaned document object matching `config/contracts/schemas/cleaned_document.schema.json`.
- `data/chunks/<doc_id>.json` stores a JSON array; every array item must match `config/contracts/schemas/chunk.schema.json`.
- SQLite registry authority is defined by `config/contracts/sqlite/001_registry.sql`.
