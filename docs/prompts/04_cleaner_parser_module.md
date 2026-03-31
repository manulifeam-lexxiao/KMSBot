# Prompt 04 - Cleaner and Parser Module

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
Implement the Cleaner / Parser module that converts raw Confluence HTML / XHTML into the cleaned structured document JSON required by downstream chunking. This module must be able to operate independently on the raw artifacts produced by the sync module.

What to implement:
- parser service that loads raw Confluence page artifacts
- cleaning pipeline for HTML / XHTML
- heading extraction
- paragraph extraction
- ordered and unordered list handling
- simple table conversion into readable text
- basic code block preservation as text
- low-value noise removal
- cleaned JSON persistence

Required cleaned output shape:
- doc_id
- title
- sections[] with heading and content
- plain_text

Supported content matrix to implement:
- headings
- paragraphs
- bullet lists
- numbered lists
- simple tables
- basic code blocks

Explicitly out of scope:
- full Confluence macro compatibility
- OCR of images
- attachment parsing
- perfect rendering preservation

Constraints:
- keep the logic deterministic and rule-based
- do not couple directly to Azure AI Search or Azure OpenAI
- do not require the chunker to exist in order to run

Decoupling requirement:
- this module must accept raw file inputs and emit cleaned JSON outputs without depending on sync internals beyond the raw artifact contract
- define exactly what a downstream chunker can assume about the cleaned JSON

Include in your response:
- supported content matrix
- parser input contract
- parser output contract
- file naming and storage rules for cleaned artifacts
