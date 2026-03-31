# 本地运行时数据

本目录仅存放运行时生成的本地数据文件，**不提交到版本控制**（已在 `.gitignore` 中排除具体内容）。

## 子目录说明

| 目录 | 内容 |
|------|------|
| `data/raw/` | 从 Confluence 拉取的原始页面快照 |
| `data/cleaned/` | 经过 HTML 清洗和结构化解析后的文档 JSON |
| `data/chunks/` | 按文档分块后的 chunk 数组 JSON |
| `data/sqlite/` | SQLite 数据库文件（`kmsbot.db`）|
| `data/logs/` | 本地运行日志 |

## 文件命名规则

- `data/raw/<page_id>.json`
- `data/cleaned/<doc_id>.json`
- `data/chunks/<doc_id>.json`
- `data/sqlite/kmsbot.db`
- `data/logs/<service>.log`

## Schema 约束

- `data/cleaned/<doc_id>.json` 的结构须符合 `config/contracts/schemas/cleaned_document.schema.json`。
- `data/chunks/<doc_id>.json` 是 JSON 数组，每个元素须符合 `config/contracts/schemas/chunk.schema.json`。
- SQLite 数据库结构由 `config/contracts/sqlite/001_registry.sql` 定义。
