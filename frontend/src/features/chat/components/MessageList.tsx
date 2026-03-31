import { useEffect, useRef } from "react";
import type { ChatMessage } from "../../../types/query";
import { AnswerMessage } from "./AnswerMessage";
import "./MessageList.css";

interface MessageListProps {
  messages: ChatMessage[];
  isLoading: boolean;
}

export function MessageList({ messages, isLoading }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="message-list message-list--empty">
        <p className="message-list__placeholder">
          Ask a question about our knowledge base to get started.
        </p>
      </div>
    );
  }

  return (
    <div className="message-list">
      {messages.map((msg) => (
        <div key={msg.id} className={`message-list__bubble message-list__bubble--${msg.role}`}>
          {msg.role === "user" ? (
            <div className="message-list__user-text">{msg.content}</div>
          ) : (
            <AnswerMessage content={msg.content} response={msg.response} error={msg.error} />
          )}
        </div>
      ))}

      {isLoading && (
        <div className="message-list__bubble message-list__bubble--assistant">
          <div className="message-list__loading">
            <span className="message-list__dot" />
            <span className="message-list__dot" />
            <span className="message-list__dot" />
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
