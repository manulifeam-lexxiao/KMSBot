# Frontend Skeleton

This directory is reserved for the React + TypeScript frontend.

## Canonical Structure

```text
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
```

## Placement Rules

- `app/` owns app bootstrap, router, and global providers.
- `components/` owns reusable UI that is not tied to one screen.
- `features/chat/` owns chat-only UI and state.
- `features/admin/` owns sync, index, and health UI.
- `hooks/` owns reusable frontend hooks.
- `services/api/` is the only place allowed to call backend HTTP endpoints.
- `types/` owns shared frontend types derived from the frozen API contract.

## Naming Rules

- components: `PascalCase.tsx`
- hooks: `useSomething.ts`
- API clients: `queryApi.ts`, `syncApi.ts`, `healthApi.ts`
- feature folders: lower case by business capability

## Dependency Rules

- Frontend must not call Confluence, Azure AI Search, or Azure OpenAI directly.
- Frontend must not store runtime prompt text.
- Frontend renders backend response contracts; it does not reconstruct answer strategy locally.
