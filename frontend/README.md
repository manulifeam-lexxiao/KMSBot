# 前端（Frontend）

React 18 + TypeScript 前端应用，提供问答聊天界面与管理后台（同步触发、索引状态、设置管理）。

## 快速启动

```bash
npm install
npm run dev          # 开发服务器，访问 http://localhost:5173
npm run build        # 生产构建，输出到 dist/
npm run test         # 运行单元测试
```

### 纯前端 Mock 模式（无需后端）

创建 `.env` 文件：

```env
VITE_MOCK_API=true
```

然后执行 `npm run dev`，前端将使用本地确定性 Mock 响应，无需启动后端。

## 目录结构

```text
frontend/
  index.html
  vite.config.ts
  vitest.config.ts
  src/
    main.tsx                        # 应用入口
    App.tsx                         # 根组件与路由
    index.css                       # 全局样式重置
    app/                            # 应用引导、全局 Provider
    components/                     # 跨页面复用组件
    types/
      query.ts                      # 问答 API 契约类型
      admin.ts                      # 管理后台契约类型
    services/
      api/
        queryApi.ts                 # POST /api/query
        syncApi.ts                  # POST /api/sync、/api/index
        healthApi.ts                # GET /api/health
        settingsApi.ts              # GET/PUT /api/settings
        mock.ts                     # 开发用 Mock 响应
    hooks/
      useQueryChat.ts               # 聊天状态 + API Hook
      useAdmin.ts                   # 管理后台状态 Hook
      useProvider.ts                # 提供商选择 Hook
    features/
      chat/
        ChatPage.tsx                # 聊天主页面
        components/
          MessageList.tsx           # 消息列表
          ChatInput.tsx             # 输入框与发送按钮
          AnswerMessage.tsx         # 助手回答气泡
          SourceList.tsx            # 引用来源标签
          RelatedDocuments.tsx      # 相关文档链接
          DebugPanel.tsx            # 可折叠调试 JSON 面板
      admin/
        AdminPage.tsx               # 管理后台主页面
        ProviderSelector.tsx        # 答案提供商切换
```

## 开发规范

- `services/api/` 是唯一允许调用后端 HTTP 接口的位置。
- `types/` 中的类型必须与 `config/contracts/openapi.yaml` 保持一致。
- 前端不得直接调用 Confluence、Azure AI Search 或 Azure OpenAI。
- 前端不得存储或硬编码运行时提示词文本。
- 组件文件：`PascalCase.tsx`；Hook 文件：`useSomething.ts`；API 客户端：`queryApi.ts`。
- Frontend renders backend response contracts; it does not reconstruct answer strategy locally.
