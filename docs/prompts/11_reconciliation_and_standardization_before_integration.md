# Prompt 11 - Reconciliation and Standardization Before Integration

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
You are given the outputs of multiple independently developed modules for the same KMS Bot POC. Different people or agents may have produced inconsistent naming, file placement, schema details, response models, config shapes, and duplicated functionality. Your job is to normalize and standardize the codebase before final integration.

What to do:
- inspect all module outputs
- compare them against the frozen contracts and repository governance from Prompt 01
- identify inconsistencies in:
  - directory structure
  - file placement
  - class and function naming
  - schema names and fields
  - API request and response models
  - config sections and variable names
  - registry schema usage
  - cleaned JSON usage
  - chunk JSON usage
  - search adapter contract usage
  - answer generator contract usage
  - frontend API consumption
- eliminate duplicate utilities and duplicate service definitions
- create a single standardized version of each overlapping concern
- refactor modules so that they align to one canonical project structure and one canonical set of contracts
- create a reconciliation report listing what was changed and why

Required output:
- cleaned and standardized file tree
- canonicalized schemas and contracts
- canonicalized config layout
- canonicalized service interfaces
- de-duplicated utilities
- migration notes for any renamed files or symbols
- unresolved conflict list if any issue cannot be automatically normalized

Constraints:
- do not introduce new business scope
- do not add unsupported features
- prioritize contract compliance and integration readiness over preserving every implementation detail from each contributor

Success criteria:
- after this prompt, the codebase should have one coherent structure and one coherent set of contracts
- the final integration prompt should be able to work on this normalized codebase rather than on raw divergent outputs
