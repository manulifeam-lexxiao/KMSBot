# KMS Bot Contract Freeze and Repository Governance

## 1. Purpose

This document is the authoritative human-readable baseline for the KMS Bot POC / V1 repository.

Its purpose is to freeze:

- repository structure
- naming conventions
- canonical file placement
- backend and frontend package boundaries
- config structure
- runtime prompt placement
- local data layout
- API contracts
- module input / output boundaries
- multi-person branch and ownership rules

This document must not be used to add business features. It only defines how later module implementations are allowed to fit together.

## 2. Authority Order

When multiple files overlap, apply this authority order:

1. `config/contracts/openapi.yaml`
2. `config/contracts/sqlite/001_registry.sql`
3. `config/contracts/schemas/*.schema.json`
4. `docs/CONTRACT_FREEZE_AND_REPOSITORY_GOVERNANCE.md`
5. `config/app.example.yaml`
6. `README.md`
7. later implementation files

Interpretation rules:

- `docs/prompts/` is for human implementation prompts only.
- `prompts/` is for runtime backend prompt template files only.
- Later prompts may implement modules, but they may not silently redefine frozen contracts.
- Prompt 11 may standardize implementation drift; it is not allowed to invent new contracts without updating the authority files above.

## 3. Final Repository Directory Structure

```text
KMSBot/
  backend/
    src/
      kms_bot/
        api/
          routes/
        core/
        db/
        repositories/
        schemas/
        services/
        modules/
          sync/
          parser/
          chunker/
          search/
          query/
          answer/
  frontend/
    src/
      app/
      components/
      features/
        chat/
        admin/
      hooks/
      services/
        api/
      types/
  config/
    app.example.yaml
    contracts/
      openapi.yaml
      sqlite/
        001_registry.sql
      schemas/
        cleaned_document.schema.json
        chunk.schema.json
        search_result_adapter.schema.json
        answer_generator_input.schema.json
  data/
    raw/
    cleaned/
    chunks/
    sqlite/
    logs/
  docker/
  docs/
    CONTRACT_FREEZE_AND_REPOSITORY_GOVERNANCE.md
    prompts/
  prompts/
    query_answering/
    query_rewrite/
  .env.example
  .gitignore
  README.md
```

## 4. Naming Conventions

### 4.1 Backend Python

| Area | Rule | Example |
| --- | --- | --- |
| package name | lower snake case | `kms_bot` |
| module file | lower snake case | `query_service.py` |
| router file | endpoint-family name | `query.py`, `sync.py` |
| service class | PascalCase + `Service` | `QueryService` |
| repository class | PascalCase + `Repository` | `RegistryRepository` |
| schema file | lower snake case by domain | `query.py`, `sync.py` |
| Pydantic request model | PascalCase + `Request` | `QueryRequest` |
| Pydantic response model | PascalCase + `Response` | `QueryResponse` |
| record / DTO model | PascalCase noun | `SearchResultHit` |
| module-local interface file | `ports.py` | `modules/search/ports.py` |

Rules:

- Use `snake_case` for files and modules.
- Keep HTTP concerns in `api/routes/` and schema models in `schemas/`.
- Keep orchestration or business logic out of router files.
- Keep external service wrappers behind explicit interfaces or service classes.

### 4.2 Frontend React + TypeScript

| Area | Rule | Example |
| --- | --- | --- |
| React component file | PascalCase `.tsx` | `ChatPanel.tsx` |
| hook file | `use` + PascalCase `.ts` | `useQueryHistory.ts` |
| feature folder | lower case | `chat`, `admin` |
| API client file | lower camel case + `Api.ts` | `queryApi.ts` |
| shared type file | lower snake case or domain file | `query.ts`, `sync.ts` |
| utility file | lower camel case | `formatCitation.ts` |

Rules:

- Put screen-specific code under `features/`.
- Put reusable presentational components under `components/`.
- Put backend HTTP access only under `services/api/`.
- Do not place prompt text, search logic, or answer composition logic in frontend code.

### 4.3 Config and Contract Files

| Area | Rule | Example |
| --- | --- | --- |
| environment example | `.env.example` | `.env.example` |
| YAML config file | lower case with dot-separated suffix | `app.example.yaml` |
| OpenAPI contract | fixed filename | `openapi.yaml` |
| JSON schema | lower snake case + `.schema.json` | `chunk.schema.json` |
| SQL schema | numeric prefix + descriptive name | `001_registry.sql` |

## 5. Canonical File Placement Rules

| Concern | Canonical location | Must not live in |
| --- | --- | --- |
| FastAPI routers | `backend/src/kms_bot/api/routes/` | `modules/`, `frontend/` |
| app startup, config, logging | `backend/src/kms_bot/core/` | `modules/`, `frontend/` |
| DB bootstrap and connection | `backend/src/kms_bot/db/` | `services/`, `frontend/` |
| persistence classes | `backend/src/kms_bot/repositories/` | `api/routes/`, `frontend/` |
| Pydantic HTTP / domain schemas | `backend/src/kms_bot/schemas/` | `frontend/`, `data/` |
| module business logic | `backend/src/kms_bot/modules/<module>/` | `api/routes/`, `frontend/` |
| cross-module orchestration abstractions | `backend/src/kms_bot/services/` | `frontend/` |
| frontend app bootstrapping | `frontend/src/app/` | `backend/` |
| reusable UI | `frontend/src/components/` | `backend/` |
| feature-specific UI | `frontend/src/features/chat/`, `frontend/src/features/admin/` | `backend/` |
| frontend hooks | `frontend/src/hooks/` | `backend/` |
| frontend API clients | `frontend/src/services/api/` | `components/`, `backend/` |
| runtime prompt templates | `prompts/<capability>/` | `frontend/`, `docs/prompts/` |
| human design docs | `docs/` | `backend/`, `prompts/` |
| generated runtime data | `data/` | `backend/`, `frontend/`, `config/` |

## 6. Canonical Backend Package Structure

### `backend/src/kms_bot/api/`

- FastAPI route registration and HTTP-only request handling.
- One route file per endpoint family.
- Allowed dependency direction: router -> service / module interface -> schema.

### `backend/src/kms_bot/core/`

- app factory
- config loader
- logging setup
- exception mapping
- dependency wiring

### `backend/src/kms_bot/db/`

- SQLite connection bootstrap
- session / connection management
- schema initialization hooks

### `backend/src/kms_bot/repositories/`

- registry persistence
- file-based persistence helpers
- no HTTP handling
- no Azure or Confluence client logic

### `backend/src/kms_bot/schemas/`

- Pydantic models mirroring frozen API and module contracts
- request / response DTOs
- no DB access
- no service calls

### `backend/src/kms_bot/services/`

- application-level orchestration abstractions
- dependency injection facades
- shared interfaces used by multiple modules

### `backend/src/kms_bot/modules/`

Each module owns its internal implementation only:

- `sync/`
- `parser/`
- `chunker/`
- `search/`
- `query/`
- `answer/`

Rule:

- Modules may depend on `core/`, `db/`, `repositories/`, `schemas/`, and explicit interfaces.
- Modules must not import frontend code or reach into another module's private internals.

## 7. Canonical Frontend Package Structure

### `frontend/src/app/`

- app shell
- router setup
- providers

### `frontend/src/components/`

- reusable shared UI only

### `frontend/src/features/chat/`

- query input
- answer display
- citation display
- chat-specific state only

### `frontend/src/features/admin/`

- sync controls
- index controls
- health / status display
- admin-specific state only

### `frontend/src/hooks/`

- reusable frontend hooks
- no direct business logic beyond UI state and API composition

### `frontend/src/services/api/`

- only place where frontend performs backend HTTP calls
- request and response shapes must follow `config/contracts/openapi.yaml`

### `frontend/src/types/`

- shared frontend domain types derived from frozen API contracts

## 8. Canonical Config Structure

The POC uses a single YAML config file with env override support.

Required top-level sections:

- `app`
- `server`
- `logging`
- `storage`
- `database`
- `confluence`
- `search`
- `answer`
- `query`
- `prompts`

Rules:

- YAML provides baseline defaults.
- environment variables override YAML values.
- secrets must not be hardcoded in source files.
- Azure-specific business strategy must not be hidden in Azure Portal configuration.
- frontend must not be the source of truth for backend runtime configuration.

## 9. Canonical Prompt File Placement Rule

Runtime prompt templates must follow this rule:

```text
prompts/<capability>/<template_name>.md
```

Examples:

- `prompts/query_answering/default.md`
- `prompts/query_rewrite/default.md`

Rules:

- Only backend code loads runtime prompt templates.
- `docs/prompts/` must never be used as runtime prompt input.
- Frontend settings must not store prompt body text.
- Prompt selection logic belongs to backend code and backend config only.

## 10. Canonical Data Directory Structure

Generated runtime artifacts must stay under `data/`.

| Directory | Purpose | Canonical file naming |
| --- | --- | --- |
| `data/raw/` | raw Confluence payload snapshots | `<page_id>.json` |
| `data/cleaned/` | cleaned document JSON files | `<doc_id>.json` |
| `data/chunks/` | chunk output files | `<doc_id>.json` containing an array of chunk objects |
| `data/sqlite/` | local SQLite database | `kmsbot.db` |
| `data/logs/` | local debug logs | `<service>.log` |

Rules:

- Files under `data/` are runtime artifacts, not authoritative source files.
- The per-object JSON shape is frozen by the machine-readable schema files under `config/contracts/schemas/`.
- Registry metadata authority lives in SQLite using the schema in `config/contracts/sqlite/001_registry.sql`.

## 11. Frozen API Contract Definitions

The machine-readable authority is `config/contracts/openapi.yaml`.

Frozen endpoint families:

| Method | Path | Purpose | Response style |
| --- | --- | --- | --- |
| `POST` | `/api/sync/full` | trigger full sync | asynchronous acceptance |
| `POST` | `/api/sync/incremental` | trigger incremental sync | asynchronous acceptance |
| `GET` | `/api/sync/status` | inspect sync status | current status snapshot |
| `POST` | `/api/index/rebuild` | trigger index rebuild | asynchronous acceptance |
| `GET` | `/api/index/status` | inspect index status | current status snapshot |
| `POST` | `/api/query` | submit a user query | answer + citations |
| `GET` | `/api/health` | service health | health snapshot |

Key frozen rules:

- Trigger endpoints return `202 Accepted` with job metadata.
- Status endpoints return `200 OK` with the latest known state.
- `/api/query` is the only frontend endpoint allowed to return answer content.
- Frontend must not call Azure AI Search or Azure OpenAI directly.

## 12. Exact Registry Schema Definition

The exact registry schema is frozen in `config/contracts/sqlite/001_registry.sql`.

Table name:

- `document_registry`

Frozen columns:

- `page_id`
- `title`
- `source_version`
- `last_updated`
- `raw_hash`
- `chunk_count`
- `pipeline_version`
- `index_status`
- `last_sync_time`
- `last_index_time`
- `error_message`

V1 rule:

- Do not add extra registry columns without an explicit contract update.

## 13. Exact JSON Schema Contracts

Machine-readable schema authority:

- cleaned document: `config/contracts/schemas/cleaned_document.schema.json`
- chunk: `config/contracts/schemas/chunk.schema.json`
- search result adapter: `config/contracts/schemas/search_result_adapter.schema.json`
- answer generator input: `config/contracts/schemas/answer_generator_input.schema.json`

These files freeze the JSON object shapes used across independently implemented modules.

## 14. Search Result Adapter Contract

The `search` module must adapt Azure AI Search responses into the frozen `SearchResultHit` shape before returning to `query` orchestration.

Allowed output fields:

- `chunk_id`
- `doc_id`
- `title`
- `section`
- `content`
- `url`
- `tags`
- `pipeline_version`
- `score`

Rules:

- Output must be sorted by descending `score`.
- Output must not leak Azure SDK response objects beyond the search module boundary.
- Query orchestration must depend only on the adapted contract, not on Azure Search SDK types.

## 15. Answer Generator Input Contract

The `answer` module input is frozen by `config/contracts/schemas/answer_generator_input.schema.json`.

Required input fields:

- `query`
- `normalized_query`
- `prompt_template_path`
- `selected_chunks`
- `include_debug`

Rules:

- The answer module receives already selected chunks; it must not run search itself.
- The answer module may load prompt files from `prompts/`, but it must not read frontend state files.
- Query orchestration owns chunk selection; answer generation owns answer synthesis and source mapping.

## 16. Frontend-to-Backend API Contract

The frontend may only call backend APIs through `frontend/src/services/api/`.

Frozen rules:

- frontend request and response types must mirror `config/contracts/openapi.yaml`
- chat UI may call `/api/query` and `/api/health`
- admin UI may call `/api/sync/full`, `/api/sync/incremental`, `/api/sync/status`, `/api/index/rebuild`, `/api/index/status`, and `/api/health`
- frontend must not call Confluence, Azure AI Search, or Azure OpenAI directly
- frontend must not reconstruct citations from raw chunks on its own; it must render the backend response contract

## 17. Module Boundaries, Allowed Inputs and Outputs, and Mocking Rules

| Module | Allowed inputs | Required outputs | Must not depend on | Mocking allowed during module development |
| --- | --- | --- | --- | --- |
| Sync | config, Confluence client interface, registry repository, current `pipeline_version` | raw files in `data/raw/`, registry upserts | parser internals, chunker, search, answer, frontend | mock Confluence client and file store |
| Parser | raw file payloads from `data/raw/` | cleaned document files matching `cleaned_document.schema.json` | Confluence HTTP client, chunker, search, answer, frontend | raw JSON fixtures |
| Chunker | cleaned document files, current `pipeline_version` | chunk arrays matching `chunk.schema.json`, registry `chunk_count` update | Confluence, Azure SDKs, answer, frontend | cleaned JSON fixtures |
| Search | chunk files or chunk DTOs, search config | adapted `SearchResultHit` records, index status updates | answer internals, frontend, parser internals | mock Azure AI Search client |
| Query orchestrator | `QueryRequest`, search adapter output, answer service interface | `QueryResponse` | Confluence sync logic, parser internals, frontend internals | mock search and answer services |
| Answer | answer generator input contract, prompt file path | answer text plus mapped source records for `QueryResponse` | Azure Search client, frontend, raw data files | mock Azure OpenAI client and prompt loader |
| Backend API layer | HTTP requests, service interfaces, schema models | HTTP responses matching OpenAPI contract | raw filesystem traversal, Azure SDK calls in router functions | mock services via dependency injection |
| Frontend chat | query response contract | UI state and HTTP requests only | prompt text, Azure SDKs, Confluence client | mock backend API client |
| Frontend admin | status and trigger endpoint contracts | UI state and HTTP requests only | backend internals, direct DB/file access | mock backend API client |

## 18. Branch, Merge, and Ownership Guidance

### 18.1 Protected Branches

- `main` is protected and releasable.
- All prompt owners work from short-lived feature branches.

### 18.2 Feature Branch Naming

Use:

```text
<type>/pNN-<scope>
```

Allowed `type` values:

- `feature`
- `chore`
- `docs`
- `fix`

Examples:

- `feature/p04-cleaner-parser`
- `feature/p06-azure-search`
- `feature/p10-frontend-admin-ui`

### 18.3 Ownership by Scope

| Owner scope | Primary files / directories |
| --- | --- |
| Prompt 01 owner | `docs/CONTRACT_FREEZE_AND_REPOSITORY_GOVERNANCE.md`, `config/contracts/**`, `config/app.example.yaml`, root governance files |
| Prompt 02 owner | `backend/src/kms_bot/core/`, `api/`, `db/`, shared service interfaces |
| Prompt 03 owner | `backend/src/kms_bot/modules/sync/` |
| Prompt 04 owner | `backend/src/kms_bot/modules/parser/` |
| Prompt 05 owner | `backend/src/kms_bot/modules/chunker/` |
| Prompt 06 owner | `backend/src/kms_bot/modules/search/` |
| Prompt 07 owner | `backend/src/kms_bot/modules/query/` |
| Prompt 08 owner | `backend/src/kms_bot/modules/answer/`, `prompts/` runtime templates |
| Prompt 09 owner | `frontend/src/features/chat/` |
| Prompt 10 owner | `frontend/src/features/admin/` |
| Prompt 11 owner | cross-module standardization, no silent contract redefinition |
| Prompt 12 owner | integration, Docker, runbook, no contract bypass |

### 18.4 Merge Rules

- A module branch should normally modify only its owned directories plus tests and wiring points.
- Any PR that touches `config/contracts/**` or this document requires review by the Prompt 01 owner.
- Any PR that changes shared backend foundation files requires review by the Prompt 02 owner.
- If overlapping generated content conflicts, frozen contract files win over implementation convenience.
- Prompt 12 must not be used as a catch-all place to redefine data contracts or rename directories ad hoc.

## 19. Acceptance Criteria for This Contract Freeze

This repository baseline is considered complete when:

1. the directory structure exists
2. the authority order is explicit
3. API contracts are machine-readable
4. registry and JSON schemas are machine-readable
5. backend and frontend placement rules are frozen
6. runtime prompt placement is distinct from `docs/prompts/`
7. module boundaries, forbidden dependencies, and mocking rules are explicit
8. branch naming and ownership rules are explicit
