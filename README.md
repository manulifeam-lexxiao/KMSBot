# KMS Bot POC Repository

This repository is the contract-first baseline for the KMS Bot POC / V1.

At this stage, the repository intentionally freezes structure, naming, ownership, and machine-readable contracts before any business module is implemented.

## Authoritative Files

Use the following authority order when files overlap:

1. `config/contracts/openapi.yaml`
2. `config/contracts/sqlite/001_registry.sql`
3. `config/contracts/schemas/*.schema.json`
4. `docs/CONTRACT_FREEZE_AND_REPOSITORY_GOVERNANCE.md`
5. `config/app.example.yaml`
6. `README.md`

Notes:

- `docs/prompts/` contains human implementation prompts and planning inputs.
- `prompts/` is reserved for runtime backend prompt templates.
- Prompt 11 may standardize implementation drift, but it must not silently replace frozen contracts without an explicit contract update.

## Repository Layout

```text
backend/   Python backend package, interfaces, modules, and API layer
frontend/  React + TypeScript application code
config/    YAML config baseline plus contract artifacts
data/      Local runtime data only (raw, cleaned, chunks, sqlite, logs)
docker/    Dockerfiles, compose files, and runtime container assets
docs/      Design docs and human implementation prompts
prompts/   Runtime LLM prompt templates loaded by the backend
```

## Working Rules

- Keep business strategy in backend code and backend prompt template files.
- Do not store runtime prompts in frontend settings or Azure Portal.
- Do not implement ACL, vector search, hybrid search, reranking, or advanced agent workflows in POC / V1.
- Use a single `pipeline_version` field to drive reprocessing compatibility.
- Keep generated artifacts out of source directories; write them only under `data/`.

## Branching

Use short-lived feature branches from `main`.

Branch naming rule:

```text
<type>/pNN-<scope>
```

Examples:

- `chore/p01-contract-freeze`
- `feature/p02-backend-foundation`
- `feature/p03-confluence-sync`
- `feature/p09-frontend-chat-ui`

## Next Steps

1. Prompt 02 implements the backend runtime baseline using the frozen contracts in `config/contracts/`.
2. Prompts 03-10 implement modules inside their assigned directories without redefining contracts.
3. Prompt 11 reconciles implementation drift while preserving contract authority.
