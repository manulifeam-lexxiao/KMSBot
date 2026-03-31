import { describe, it, expect, vi, afterEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { useProvider } from "../../hooks/useProvider";
import * as settingsApi from "../../services/api/settingsApi";

vi.mock("../../services/api/settingsApi");

afterEach(() => vi.restoreAllMocks());

const azureStatus = {
  provider: "azure_openai" as const,
  available_providers: ["azure_openai" as const, "github_models" as const],
};

const githubStatus = {
  provider: "github_models" as const,
  available_providers: ["azure_openai" as const, "github_models" as const],
};

describe("useProvider", () => {
  it("starts loading and resolves with provider status", async () => {
    vi.mocked(settingsApi.getProvider).mockResolvedValue(azureStatus);
    const { result } = renderHook(() => useProvider());

    expect(result.current.isLoading).toBe(true);
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.status?.provider).toBe("azure_openai");
    expect(result.current.error).toBeNull();
  });

  it("sets error when initial load fails", async () => {
    vi.mocked(settingsApi.getProvider).mockRejectedValue(new Error("Server unavailable"));
    const { result } = renderHook(() => useProvider());

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.error).toBe("Server unavailable");
    expect(result.current.status).toBeNull();
  });

  it("uses generic error message for non-Error rejections", async () => {
    vi.mocked(settingsApi.getProvider).mockRejectedValue("plain string error");
    const { result } = renderHook(() => useProvider());

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.error).toBe("Failed to load provider");
  });

  it("switches provider and updates status", async () => {
    vi.mocked(settingsApi.getProvider).mockResolvedValue(azureStatus);
    vi.mocked(settingsApi.setProvider).mockResolvedValue(githubStatus);

    const { result } = renderHook(() => useProvider());
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(() => result.current.switchProvider("github_models"));

    expect(result.current.status?.provider).toBe("github_models");
    expect(vi.mocked(settingsApi.setProvider)).toHaveBeenCalledWith("github_models");
  });

  it("sets error when switchProvider fails", async () => {
    vi.mocked(settingsApi.getProvider).mockResolvedValue(azureStatus);
    vi.mocked(settingsApi.setProvider).mockRejectedValue(new Error("Switch failed"));

    const { result } = renderHook(() => useProvider());
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(() => result.current.switchProvider("github_models"));

    expect(result.current.error).toBe("Switch failed");
    // Status should remain unchanged
    expect(result.current.status?.provider).toBe("azure_openai");
  });

  it("clears previous error before switching", async () => {
    vi.mocked(settingsApi.getProvider).mockResolvedValue(azureStatus);
    vi.mocked(settingsApi.setProvider)
      .mockRejectedValueOnce(new Error("First failure"))
      .mockResolvedValueOnce(githubStatus);

    const { result } = renderHook(() => useProvider());
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    // First switch fails
    await act(() => result.current.switchProvider("github_models"));
    expect(result.current.error).toBe("First failure");

    // Second switch succeeds — error should clear
    await act(() => result.current.switchProvider("github_models"));
    expect(result.current.error).toBeNull();
  });

  it("sets isSwitching to false after switch completes", async () => {
    vi.mocked(settingsApi.getProvider).mockResolvedValue(azureStatus);
    vi.mocked(settingsApi.setProvider).mockResolvedValue(githubStatus);

    const { result } = renderHook(() => useProvider());
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    await act(() => result.current.switchProvider("github_models"));

    expect(result.current.isSwitching).toBe(false);
  });
});
