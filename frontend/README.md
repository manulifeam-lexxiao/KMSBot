# KMS Bot Frontend

React + TypeScript chat UI for the KMS Bot POC.

## Quick Start

```bash
npm install
npm run dev          # dev server on http://localhost:5173
npm run build        # production build → dist/
```

### Mock mode (no backend required)

Create a `.env` file:

```env
VITE_MOCK_API=true
```

Then `npm run dev` serves the UI with deterministic mock responses.

## Structure

```text
frontend/
  index.html
  vite.config.ts
  src/
    main.tsx                       # entry
    App.tsx                        # root component
    index.css                      # global reset
    types/
      query.ts                     # API contract types
    services/
      api/
        queryApi.ts                # POST /api/query call
        mock.ts                    # mock response for dev
    hooks/
      useQueryChat.ts              # chat state + API hook
    features/
      chat/
        ChatPage.tsx               # page shell
        ChatPage.css
        components/
          MessageList.tsx           # scrollable message list
          MessageList.css
          ChatInput.tsx             # text input + send button
          ChatInput.css
          AnswerMessage.tsx         # assistant bubble wrapper
          AnswerMessage.css
          SourceList.tsx            # citation chips
          SourceList.css
          RelatedDocuments.tsx      # related page links
          RelatedDocuments.css
          DebugPanel.tsx            # collapsible debug JSON
          DebugPanel.css
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
