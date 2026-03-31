import type { QueryRequest, QueryResponse } from "../../types/query";

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
