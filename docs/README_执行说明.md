# KMS Bot 新提示词执行说明（中文）

## 1. 这套提示词的设计目标

这是一套面向多人并行开发的 KMS Bot POC 提示词集合，目标是：

- 尽量提升模块间解耦程度
- 尽量减少不同人输出结果之间的直接耦合
- 先冻结契约，再分工实现
- 在最终集成前增加一次“统一清理 / 归一化 / 修正差异”的中间步骤

## 2. 提示词列表

1. 01_contract_freeze_and_repo_governance.md
2. 02_backend_foundation_and_runtime_baseline.md
3. 03_confluence_sync_module.md
4. 04_cleaner_parser_module.md
5. 05_chunker_normalizer_module.md
6. 06_azure_ai_search_module.md
7. 07_query_orchestrator_and_context_assembly.md
8. 08_azure_openai_answer_generator.md
9. 09_frontend_chat_ui.md
10. 10_frontend_admin_settings_ui.md
11. 11_reconciliation_and_standardization_before_integration.md
12. 12_final_integration_docker_runbook.md

## 3. 推荐执行顺序

### 阶段 A：冻结契约与底座（必须先做）
1. Prompt 01 - Contract Freeze and Repository Governance
2. Prompt 02 - Backend Foundation and Runtime Baseline

### 阶段 B：模块开发（可并行）
3. Prompt 03 - Confluence Sync Module
4. Prompt 04 - Cleaner and Parser Module
5. Prompt 05 - Chunker and Normalizer Module
6. Prompt 06 - Azure AI Search Module
7. Prompt 07 - Query Orchestrator and Context Assembly
8. Prompt 08 - Azure OpenAI Answer Generator
9. Prompt 09 - Frontend Chat UI
10. Prompt 10 - Frontend Admin and Settings UI

### 阶段 C：统一清理（必须在最终集成前执行）
11. Prompt 11 - Reconciliation and Standardization Before Integration

### 阶段 D：最终集成
12. Prompt 12 - Final Integration, Docker, and Runbook

## 4. 这套提示词最多支持几个人分工

### 最推荐的总人数安排：10 人
- 1 人：契约 / 架构 Owner（负责 Prompt 01）
- 1 人：平台 / 后端底座 Owner（负责 Prompt 02）
- 1 人：Prompt 03
- 1 人：Prompt 04
- 1 人：Prompt 05
- 1 人：Prompt 06
- 1 人：Prompt 07
- 1 人：Prompt 08
- 1 人：Prompt 09
- 1 人：Prompt 10

之后由架构 Owner 或集成人负责：
- Prompt 11
- Prompt 12

### 峰值并行人数：8 人
在 Prompt 01 和 Prompt 02 完成后，Prompt 03~10 最多可以 8 个人并行执行。

## 5. 为什么这样拆最稳

- Prompt 01 先把契约、目录、命名、Schema、接口全部冻结
- Prompt 02 先把 FastAPI 底座、配置加载、日志、数据库初始化统一
- Prompt 03~10 都尽量围绕固定输入输出契约独立实现
- Prompt 11 专门处理不同人跑出来的差异、重复、命名不一致、目录不一致、Config 不一致
- Prompt 12 只负责“标准化之后”的最终集成，不承担大规模修复任务

## 6. 关键注意事项

- 绝对不要跳过 Prompt 01
- 绝对不要跳过 Prompt 11
- 不要让 Prompt 12 去兜底解决前面所有差异
- 各模块开发者必须以 Prompt 01 冻结出的契约为唯一基线
- 如果多人输出中出现冲突，以 Prompt 01 的契约和 Prompt 11 的统一结果为准
