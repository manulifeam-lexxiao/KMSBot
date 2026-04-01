import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { ProviderSelector } from "../../features/settings/ProviderSelector";
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

describe("ProviderSelector", () => {
  it("shows skeleton loaders while loading", () => {
    vi.mocked(settingsApi.getProvider).mockReturnValue(new Promise(() => {})); // never resolves
    render(<ProviderSelector />);
    expect(document.querySelectorAll(".provider-selector__skeleton")).toHaveLength(2);
  });

  it("renders both provider option buttons after load", async () => {
    vi.mocked(settingsApi.getProvider).mockResolvedValue(azureStatus);
    render(<ProviderSelector />);
    await waitFor(() => screen.getByText("Azure OpenAI"));
    expect(screen.getByText("GitHub Models")).toBeInTheDocument();
  });

  it("shows 'Active' badge on the current provider", async () => {
    vi.mocked(settingsApi.getProvider).mockResolvedValue(azureStatus);
    render(<ProviderSelector />);
    await waitFor(() => screen.getByText("Active"));
    // The active badge should be inside the Azure OpenAI button
    const activeBadge = screen.getByText("Active");
    expect(activeBadge.closest("button")).toHaveTextContent("Azure OpenAI");
  });

  it("active provider button is disabled", async () => {
    vi.mocked(settingsApi.getProvider).mockResolvedValue(azureStatus);
    render(<ProviderSelector />);
    await waitFor(() => screen.getByText("Active"));
    const buttons = screen.getAllByRole("button");
    const activeButton = buttons.find((b) => b.classList.contains("provider-option--active"))!;
    expect(activeButton).toBeDisabled();
  });

  it("clicking inactive provider calls setProvider", async () => {
    vi.mocked(settingsApi.getProvider).mockResolvedValue(azureStatus);
    vi.mocked(settingsApi.setProvider).mockResolvedValue(githubStatus);
    render(<ProviderSelector />);
    await waitFor(() => screen.getByText("GitHub Models"));

    const buttons = screen.getAllByRole("button");
    const githubButton = buttons.find((b) => b.textContent?.includes("GitHub Models"))!;
    fireEvent.click(githubButton);

    await waitFor(() =>
      expect(vi.mocked(settingsApi.setProvider)).toHaveBeenCalledWith("github_models"),
    );
  });

  it("updates active badge after switching provider", async () => {
    vi.mocked(settingsApi.getProvider).mockResolvedValue(azureStatus);
    vi.mocked(settingsApi.setProvider).mockResolvedValue(githubStatus);
    render(<ProviderSelector />);
    await waitFor(() => screen.getByText("Active"));

    const buttons = screen.getAllByRole("button");
    const githubButton = buttons.find((b) => b.textContent?.includes("GitHub Models"))!;
    fireEvent.click(githubButton);

    await waitFor(() => {
      const activeBadge = screen.getByText("Active");
      expect(activeBadge.closest("button")).toHaveTextContent("GitHub Models");
    });
  });

  it("shows error message when initial load fails", async () => {
    vi.mocked(settingsApi.getProvider).mockRejectedValue(new Error("Service unavailable"));
    render(<ProviderSelector />);
    await waitFor(() => screen.getByText("Service unavailable"));
    expect(screen.getByText("Service unavailable")).toBeInTheDocument();
  });

  it("shows 'Switching provider…' text while switching", async () => {
    vi.mocked(settingsApi.getProvider).mockResolvedValue(azureStatus);

    let resolveSwitchFn!: (v: typeof githubStatus) => void;
    vi.mocked(settingsApi.setProvider).mockReturnValue(
      new Promise((res) => {
        resolveSwitchFn = res;
      }),
    );

    render(<ProviderSelector />);
    await waitFor(() => screen.getByText("GitHub Models"));

    const buttons = screen.getAllByRole("button");
    const githubButton = buttons.find((b) => b.textContent?.includes("GitHub Models"))!;
    fireEvent.click(githubButton);

    await waitFor(() => screen.getByText("Switching provider…"));
    expect(screen.getByText("Switching provider…")).toBeInTheDocument();

    // Resolve to clean up
    resolveSwitchFn(githubStatus);
  });
});
