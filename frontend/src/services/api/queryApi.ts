import type { QueryRequest, QueryResponse, ThinkingEvent } from "../../types/query";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

export async function postQuery(req: QueryRequest): Promise<QueryResponse> {
  const res = await fetch(`${BASE_URL}/api/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const msg =
      body && typeof body === "object" && "message" in body
        ? String(body.message)
        : `Query failed (${res.status})`;
    throw new Error(msg);
  }

  return (await res.json()) as QueryResponse;
}

/**
 * THINKING 模式的 SSE 流式请求。
 * 每收到一个 SSE event 就调用 onEvent 回调。
 */
export async function postQueryStreaming(
  req: QueryRequest,
  onEvent: (event: ThinkingEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(`${BASE_URL}/api/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
    signal,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const msg =
      body && typeof body === "object" && "message" in body
        ? String(body.message)
        : `Query failed (${res.status})`;
    throw new Error(msg);
  }

  const reader = res.body?.getReader();
  if (!reader) throw new Error("No response body");

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed || !trimmed.startsWith("data: ")) continue;
      try {
        const event = JSON.parse(trimmed.slice(6)) as ThinkingEvent;
        onEvent(event);
      } catch {
        // 忽略无法解析的行
      }
    }
  }

  // 处理 buffer 中剩余的数据
  if (buffer.trim().startsWith("data: ")) {
    try {
      const event = JSON.parse(buffer.trim().slice(6)) as ThinkingEvent;
      onEvent(event);
    } catch {
      // 忽略
    }
  }
}
