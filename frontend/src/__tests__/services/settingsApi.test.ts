import { describe, it, expect, vi, afterEach } from "vitest";
import { getProvider, setProvider } from "../../services/api/settingsApi";

afterEach(() => vi.restoreAllMocks());

const makeRes = (body: unknown, ok = true, status = 200): Response =>
  ({ ok, status, json: () => Promise.resolve(body) }) as unknown as Response;

const azureStatus = {
  provider: "azure_openai" as const,
  available_providers: ["azure_openai", "github_models"] as const,
};

describe("getProvider", () => {
  it("returns current provider status", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue(makeRes(azureStatus));
    const result = await getProvider();
    expect(result.provider).toBe("azure_openai");
    expect(result.available_providers).toContain("github_models");
  });

  it("sends GET to /api/settings/provider", async () => {
    const fetchSpy = vi.spyOn(global, "fetch").mockResolvedValue(makeRes(azureStatus));
    await getProvider();
    const [url] = fetchSpy.mock.calls[0] as [string];
    expect(url).toContain("/api/settings/provider");
  });

  it("throws with message from body on error", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue(makeRes({ message: "Unauthorized" }, false, 401));
    await expect(getProvider()).rejects.toThrow("Unauthorized");
  });
});

describe("setProvider", () => {
  it("sends PATCH with provider in body", async () => {
    const fetchSpy = vi.spyOn(global, "fetch").mockResolvedValue(
      makeRes({
        provider: "github_models",
        available_providers: ["azure_openai", "github_models"],
      }),
    );
    const result = await setProvider("github_models");
    expect(result.provider).toBe("github_models");
    const [url, init] = fetchSpy.mock.calls[0] as [string, RequestInit];
    expect(url).toContain("/api/settings/provider");
    expect(init.method).toBe("PATCH");
    expect(JSON.parse(init.body as string)).toEqual({ provider: "github_models" });
  });

  it("throws on server error", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue(
      makeRes({ message: "Provider not configured" }, false, 422),
    );
    await expect(setProvider("github_models")).rejects.toThrow("Provider not configured");
  });
});
