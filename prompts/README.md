# Runtime Prompt Templates

This directory is reserved for backend runtime prompt template files.

## Canonical Rule

```text
prompts/<capability>/<template_name>.md
```

Examples:

- `prompts/query_answering/default.md`
- `prompts/query_rewrite/default.md`

## Governance Rules

- Only backend code may load files from this directory.
- `docs/prompts/` is not a runtime prompt directory.
- Frontend settings must not become a prompt store.
- Prompt body text will be implemented later; this step freezes only placement and ownership.
