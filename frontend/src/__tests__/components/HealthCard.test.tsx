import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { HealthCard } from "../../features/admin/components/HealthCard";
import type { HealthResponse } from "../../types/admin";

const healthData: HealthResponse = {
  status: "ok",
  service: "kms-bot-backend",
  version: "0.1.0",
  timestamp: "2026-03-31T10:00:00Z",
  dependencies: {
    sqlite: "ok",
    azure_ai_search: "not_configured",
    azure_openai: "not_configured",
  },
};

describe("HealthCard", () => {
  it("shows loading text when isLoading=true and no data", () => {
    render(<HealthCard data={null} error={null} isLoading={true} />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it("does not show loading text once data is available", () => {
    render(<HealthCard data={healthData} error={null} isLoading={true} />);
    expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
  });

  it("shows error message when error is provided", () => {
    render(<HealthCard data={null} error="Connection refused" isLoading={false} />);
    expect(screen.getByText("Connection refused")).toBeInTheDocument();
  });

  it("renders the version from data", () => {
    render(<HealthCard data={healthData} error={null} isLoading={false} />);
    expect(screen.getByText("0.1.0")).toBeInTheDocument();
  });

  it("renders all three dependency labels", () => {
    render(<HealthCard data={healthData} error={null} isLoading={false} />);
    expect(screen.getByText("SQLite")).toBeInTheDocument();
    expect(screen.getByText("Azure AI Search")).toBeInTheDocument();
    expect(screen.getByText("Azure OpenAI")).toBeInTheDocument();
  });

  it("renders status badges for ok and not_configured dependencies", () => {
    render(<HealthCard data={healthData} error={null} isLoading={false} />);
    // sqlite: ok — appears at least once
    const okBadges = screen.getAllByText("ok");
    expect(okBadges.length).toBeGreaterThanOrEqual(1);
    // azure_ai_search and azure_openai: not_configured — two badges
    const unconfigured = screen.getAllByText("not_configured");
    expect(unconfigured).toHaveLength(2);
  });

  it("shows degraded status badge when backend is degraded", () => {
    const degraded: HealthResponse = {
      ...healthData,
      status: "degraded",
      dependencies: { ...healthData.dependencies, azure_ai_search: "degraded" },
    };
    render(<HealthCard data={degraded} error={null} isLoading={false} />);
    expect(screen.getAllByText("degraded").length).toBeGreaterThanOrEqual(1);
  });

  it("renders nothing data-specific when data is null", () => {
    render(<HealthCard data={null} error={null} isLoading={false} />);
    expect(screen.queryByText("Version")).not.toBeInTheDocument();
    expect(screen.queryByText("SQLite")).not.toBeInTheDocument();
  });
});
