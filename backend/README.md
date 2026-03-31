# Backend Skeleton

This directory is reserved for the Python 3.11+ FastAPI backend.

## Canonical Package Root

```text
backend/src/kms_bot/
```

## Canonical Structure

```text
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
```

## Placement Rules

- `api/routes/` owns HTTP request and response wiring only.
- `core/` owns startup, config loading, logging, exception handling, and dependency wiring.
- `db/` owns SQLite bootstrap and connection lifecycle.
- `repositories/` owns persistence adapters.
- `schemas/` owns Pydantic request, response, and DTO models.
- `services/` owns shared orchestration abstractions and interfaces.
- `modules/*` owns feature-specific implementation details.

## Naming Rules

- module files: `snake_case.py`
- router files: `sync.py`, `index.py`, `query.py`, `health.py`
- service classes: `SomethingService`
- repository classes: `SomethingRepository`
- request models: `SomethingRequest`
- response models: `SomethingResponse`

## Dependency Rules

- Router code must not contain parsing, chunking, search, or answer logic.
- Module code must not depend on frontend code.
- Search and answer modules must communicate through explicit contracts, not SDK objects.
