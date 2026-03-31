import { useState } from "react";
import { useQueryChat } from "../../hooks/useQueryChat";
import { MessageList } from "./components/MessageList";
import { ChatInput } from "./components/ChatInput";
import "./ChatPage.css";

export function ChatPage() {
  const [includeDebug, setIncludeDebug] = useState(false);
  const { messages, isLoading, sendMessage, clearMessages } = useQueryChat(includeDebug);

  return (
    <div className="chat-page">
      <header className="chat-page__header">
        <h1 className="chat-page__title">KMS Bot</h1>
        <div className="chat-page__actions">
          <label className="chat-page__debug-toggle">
            <input
              type="checkbox"
              checked={includeDebug}
              onChange={(e) => setIncludeDebug(e.target.checked)}
            />
            Debug
          </label>
          <button
            type="button"
            className="chat-page__clear"
            onClick={clearMessages}
            disabled={messages.length === 0}
          >
            Clear
          </button>
        </div>
      </header>

      <MessageList messages={messages} isLoading={isLoading} />
      <ChatInput onSend={sendMessage} disabled={isLoading} />
    </div>
  );
}
