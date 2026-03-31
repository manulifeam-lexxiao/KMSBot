import { useCallback, useRef, useState } from "react";
import type { ChatMessage, QueryRequest, QueryResponse } from "../types/query";
import { postQuery } from "../services/api/queryApi";
import { postQueryMock } from "../services/api/mock";

const useMock = import.meta.env.VITE_MOCK_API === "true";

let nextId = 1;
function makeId(): string {
  return `msg-${nextId++}-${Date.now()}`;
}

export interface UseQueryChat {
  messages: ChatMessage[];
  isLoading: boolean;
  sendMessage: (query: string) => void;
  clearMessages: () => void;
}

export function useQueryChat(includeDebug = false): UseQueryChat {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(
    (query: string) => {
      const trimmed = query.trim();
      if (!trimmed || isLoading) return;

      const userMsg: ChatMessage = {
        id: makeId(),
        role: "user",
        content: trimmed,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMsg]);
      setIsLoading(true);

      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      const req: QueryRequest = {
        query: trimmed,
        top_k: 5,
        include_debug: includeDebug,
      };

      const apiCall = useMock ? postQueryMock : postQuery;

      apiCall(req)
        .then((resp: QueryResponse) => {
          if (controller.signal.aborted) return;
          const assistantMsg: ChatMessage = {
            id: makeId(),
            role: "assistant",
            content: resp.answer,
            timestamp: new Date(),
            response: resp,
          };
          setMessages((prev) => [...prev, assistantMsg]);
        })
        .catch((err: unknown) => {
          if (controller.signal.aborted) return;
          const errorMessage = err instanceof Error ? err.message : "Unknown error";
          const errMsg: ChatMessage = {
            id: makeId(),
            role: "assistant",
            content: "Sorry, something went wrong.",
            timestamp: new Date(),
            error: errorMessage,
          };
          setMessages((prev) => [...prev, errMsg]);
        })
        .finally(() => {
          if (!controller.signal.aborted) {
            setIsLoading(false);
          }
        });
    },
    [isLoading, includeDebug],
  );

  const clearMessages = useCallback(() => {
    abortRef.current?.abort();
    setMessages([]);
    setIsLoading(false);
  }, []);

  return { messages, isLoading, sendMessage, clearMessages };
}
