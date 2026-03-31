import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { StatusBadge } from "../../features/admin/components/StatusBadge";

describe("StatusBadge", () => {
  it("renders the status text", () => {
    render(<StatusBadge status="ok" />);
    expect(screen.getByText("ok")).toBeInTheDocument();
  });

  it.each([
    ["ok", "status-badge--ok"],
    ["success", "status-badge--ok"],
    ["idle", "status-badge--idle"],
    ["not_configured", "status-badge--idle"],
    ["running", "status-badge--running"],
    ["degraded", "status-badge--degraded"],
    ["error", "status-badge--error"],
  ])("applies class %s -> %s", (status, expectedClass) => {
    render(<StatusBadge status={status} />);
    expect(screen.getByText(status)).toHaveClass(expectedClass);
  });

  it("falls back to idle class for an unknown status", () => {
    render(<StatusBadge status="whatever" />);
    expect(screen.getByText("whatever")).toHaveClass("status-badge--idle");
  });
});
