import type {
  TokenUsageSummary,
  ThinkingSettings,
  QuerySettings,
  SearchProviderStatus,
  ConfluenceStatus,
} from "../../types/settings";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const msg =
      body && typeof body === "object" && "message" in body
        ? String(body.message)
        : `Request failed (${res.status})`;
    throw new Error(msg);
  }
  return (await res.json()) as T;
}

export type ProviderName = "azure_openai" | "github_models";

export interface ProviderStatus {
  provider: ProviderName;
  available_providers: ProviderName[];
}

export async function getProvider(): Promise<ProviderStatus> {
  const res = await fetch(`${BASE_URL}/api/settings/provider`);
  return handleResponse<ProviderStatus>(res);
}

export async function setProvider(provider: ProviderName): Promise<ProviderStatus> {
  const res = await fetch(`${BASE_URL}/api/settings/provider`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ provider }),
  });
  return handleResponse<ProviderStatus>(res);
}

export async function getTokenUsage(): Promise<TokenUsageSummary> {
  const res = await fetch(`${BASE_URL}/api/settings/token-usage`);
  return handleResponse<TokenUsageSummary>(res);
}

export async function getThinkingSettings(): Promise<ThinkingSettings> {
  const res = await fetch(`${BASE_URL}/api/settings/thinking`);
  return handleResponse<ThinkingSettings>(res);
}

export async function setThinkingSettings(settings: ThinkingSettings): Promise<ThinkingSettings> {
  const res = await fetch(`${BASE_URL}/api/settings/thinking`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(settings),
  });
  return handleResponse<ThinkingSettings>(res);
}

export async function getQuerySettings(): Promise<QuerySettings> {
  const res = await fetch(`${BASE_URL}/api/settings/query`);
  return handleResponse<QuerySettings>(res);
}

export async function setQuerySettings(updates: Partial<QuerySettings>): Promise<QuerySettings> {
  const res = await fetch(`${BASE_URL}/api/settings/query`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(updates),
  });
  return handleResponse<QuerySettings>(res);
}

export async function getSearchProvider(): Promise<SearchProviderStatus> {
  const res = await fetch(`${BASE_URL}/api/settings/search-provider`);
  return handleResponse<SearchProviderStatus>(res);
}

export async function setSearchProvider(
  provider: SearchProviderStatus["provider"],
): Promise<SearchProviderStatus> {
  const res = await fetch(`${BASE_URL}/api/settings/search-provider`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ provider }),
  });
  return handleResponse<SearchProviderStatus>(res);
}

export async function getConfluenceStatus(): Promise<ConfluenceStatus> {
  const res = await fetch(`${BASE_URL}/api/settings/confluence`);
  return handleResponse<ConfluenceStatus>(res);
}
