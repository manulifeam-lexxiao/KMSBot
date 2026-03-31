# KMS Bot POC 架构摘要（与新提示词一致）

## 核心范围
- 公共 Confluence KMS 空间
- POC / V1 不做 ACL
- Confluence 是唯一知识源
- FastAPI + React + SQLite + Local Files
- Azure AI Search 负责 BM25 检索
- Azure OpenAI 负责答案生成
- 一个统一 pipeline_version
- Prompt 放在后端文件，不放 Azure Portal / 前端设置
- 不做向量检索 / Hybrid / Rerank
- 不做指标平台 / 独立运维系统

## 关键模块
- Contract & Governance
- Backend Foundation
- Confluence Sync
- Cleaner / Parser
- Chunker
- Azure AI Search
- Query Orchestrator
- Azure OpenAI Answer Generator
- Frontend Chat UI
- Frontend Admin UI
- Reconciliation Before Integration
- Final Integration
