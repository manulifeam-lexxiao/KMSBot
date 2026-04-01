import { useState } from "react";
import { useQueryChat } from "../../hooks/useQueryChat";
import { useDebugPreference } from "../../hooks/useDebugPreference";
import { MessageList } from "./components/MessageList";
import { ChatInput } from "./components/ChatInput";
import "./ChatPage.css";

export function ChatPage() {
  const { includeDebug, setIncludeDebug } = useDebugPreference();
  const [thinking, setThinking] = useState(false);
  const { messages, isLoading, sendMessage, clearMessages } = useQueryChat(includeDebug, thinking);

  return (
    <div className="chat-page">
      <header className="chat-page__header">
        <div className="chat-page__actions">
          <label className="chat-page__toggle chat-page__toggle--thinking">
            <input
              type="checkbox"
              checked={thinking}
              onChange={(e) => setThinking(e.target.checked)}
            />
            THINKING
          </label>
          <label className="chat-page__toggle">
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
