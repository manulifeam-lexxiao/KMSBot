# Prompt 08 - Azure OpenAI Answer Generator

You are implementing part of a POC internal KMS Bot system.

Business context:
- The system is a POC / V1 intelligent Q&A system for a public Confluence KMS space
- The Confluence KMS space is a cross-team public knowledge space
- There is no ACL / permission filtering requirement in V1
- Confluence is the only source of truth
- The goal is to sync knowledge from Confluence, process it, index it, retrieve relevant chunks, and generate answers with citations

Architecture constraints:
- Frontend: React + TypeScript
- Backend: Python 3.11+, FastAPI, Pydantic
- Local storage: files + SQLite
- Search: Azure AI Search
- LLM: Azure OpenAI
- Deployment: Docker
- One unified pipeline_version field is used for reprocessing control
- Business strategy must live in the backend, not in Azure Portal settings
- Prompts must be stored in backend prompt template files, not in frontend settings
- No advanced agent workflow
- No vector search / hybrid search / reranking in POC
- No metrics platform and no separate operations platform in POC
- Keep the implementation simple, modular, debuggable, and easy to integrate

Required API family for the final system:
- POST /api/sync/full
- POST /api/sync/incremental
- GET  /api/sync/status
- POST /api/index/rebuild
- GET  /api/index/status
- POST /api/query
- GET  /api/health

Required data contracts for the final system:
Registry table fields:
- page_id
- title
- source_version
- last_updated
- raw_hash
- chunk_count
- pipeline_version
- index_status
- last_sync_time
- last_index_time
- error_message

Cleaned document JSON shape:
{
  "doc_id": "12345",
  "title": "How to reset iPension access",
  "sections": [
    {"heading": "Overview", "content": "..."},
    {"heading": "Steps", "content": "..."}
  ],
  "plain_text": "..."
}

Chunk JSON shape:
{
  "chunk_id": "12345#steps#1",
  "doc_id": "12345",
  "title": "How to reset iPension access",
  "section": "Steps",
  "content": "Step 1 ... Step 2 ...",
  "url": "...",
  "tags": ["ipension", "access", "reset"],
  "pipeline_version": 1
}

Query API target response shape:
{
  "answer": "...",
  "sources": [
    {
      "title": "How to reset iPension access",
      "url": "...",
      "section": "Steps",
      "doc_id": "12345",
      "chunk_id": "12345#steps#1"
    }
  ],
  "related_documents": [
    {
      "page_id": "12345",
      "title": "...",
      "url": "..."
    }
  ],
  "debug": {
    "normalized_query": "...",
    "selected_chunks": []
  }
}

General coding rules:
- Keep code modular and easy to integrate
- Do not introduce unnecessary frameworks
- Do not implement ACL logic
- Do not implement unsupported future features
- Add minimal error handling and debug-friendly logging
- Make outputs runnable locally
- If a dependency is not implemented yet, use a clean interface or mock placeholder instead of inventing hidden coupling
- Preserve a clean separation between sync, parse, chunk, search, answer, API, frontend, and integration concerns

Always produce in your response:
1. file tree changes
2. full code files
3. config changes
4. explicit input/output contract of this module
5. integration notes
6. acceptance checklist


Task:
Implement the answer generator module that consumes assembled context plus the original user question and returns an answer grounded only in the provided context. This module must store prompt templates in backend files and must be independently testable with mocked retrieval inputs.

What to implement:
- Azure OpenAI client wrapper
- answer generator service
- prompt template loading from files
- system prompt template for standard mode
- optional debug prompt template or debug output mode
- answer grounding rules
- fallback behavior when the answer is not found in context
- final answer payload mapping aligned with the frozen Query API contract

Prompt rules that must be enforced:
- answer strictly from provided context
- do not use outside knowledge
- if not found, say "Not found in the knowledge base"
- always cite source title or URL in the answer text if your final response style includes inline references

Constraints:
- no agent workflow
- no tool calling from the model
- do not place prompt management in frontend settings
- do not make this module depend on Confluence or parser internals

Decoupling requirement:
- this module must accept a clearly defined retrieval package from the orchestrator and return a clearly defined answer payload
- it must be possible to develop and test this module entirely with mocked context inputs

Include in your response:
- prompt file list
- answer generator input contract
- answer generator output contract
- fallback rules
