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
