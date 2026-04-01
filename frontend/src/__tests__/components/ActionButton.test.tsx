import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ActionButton } from "../../features/settings/components/ActionButton";

describe("ActionButton", () => {
  it("renders button with provided label", () => {
    render(<ActionButton label="Full Sync" onClick={() => {}} />);
    expect(screen.getByRole("button", { name: "Full Sync" })).toBeInTheDocument();
  });

  it("calls onClick when clicked", () => {
    const onClick = vi.fn();
    render(<ActionButton label="Sync" onClick={onClick} />);
    fireEvent.click(screen.getByRole("button"));
    expect(onClick).toHaveBeenCalledOnce();
  });

  it("shows 'Running…' text when isRunning=true", () => {
    render(<ActionButton label="Sync" onClick={() => {}} isRunning />);
    expect(screen.getByRole("button")).toHaveTextContent("Running…");
  });

  it("disables button when isRunning=true", () => {
    render(<ActionButton label="Sync" onClick={() => {}} isRunning />);
    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("disables button when disabled=true", () => {
    render(<ActionButton label="Sync" onClick={() => {}} disabled />);
    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("does not call onClick when disabled", () => {
    const onClick = vi.fn();
    render(<ActionButton label="Sync" onClick={onClick} disabled />);
    fireEvent.click(screen.getByRole("button"));
    expect(onClick).not.toHaveBeenCalled();
  });

  it("displays lastError message", () => {
    render(<ActionButton label="Sync" onClick={() => {}} lastError="Something failed" />);
    expect(screen.getByText("Something failed")).toBeInTheDocument();
  });

  it("displays lastMessage when no error present", () => {
    render(<ActionButton label="Sync" onClick={() => {}} lastMessage="Operation accepted." />);
    expect(screen.getByText("Operation accepted.")).toBeInTheDocument();
  });

  it("shows error and hides lastMessage when both provided", () => {
    render(
      <ActionButton
        label="Sync"
        onClick={() => {}}
        lastError="Error occurred"
        lastMessage="Should not show"
      />,
    );
    expect(screen.getByText("Error occurred")).toBeInTheDocument();
    expect(screen.queryByText("Should not show")).not.toBeInTheDocument();
  });

  it("shows nothing extra when no error or message", () => {
    const { container } = render(<ActionButton label="Sync" onClick={() => {}} />);
    expect(container.querySelectorAll(".action-button__feedback")).toHaveLength(0);
  });
});
