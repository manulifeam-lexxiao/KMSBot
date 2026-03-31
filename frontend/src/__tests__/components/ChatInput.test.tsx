import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ChatInput } from "../../features/chat/components/ChatInput";

describe("ChatInput", () => {
  it("renders text input and send button", () => {
    render(<ChatInput onSend={() => {}} disabled={false} />);
    expect(screen.getByPlaceholderText(/ask a question/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /send/i })).toBeInTheDocument();
  });

  it("calls onSend with trimmed value on form submit", () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} disabled={false} />);

    const input = screen.getByPlaceholderText(/ask a question/i);
    fireEvent.change(input, { target: { value: "  hello world  " } });
    fireEvent.submit(input.closest("form")!);

    expect(onSend).toHaveBeenCalledWith("hello world");
  });

  it("calls onSend when send button is clicked", () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} disabled={false} />);

    fireEvent.change(screen.getByPlaceholderText(/ask a question/i), {
      target: { value: "my question" },
    });
    fireEvent.click(screen.getByRole("button"));

    expect(onSend).toHaveBeenCalledWith("my question");
  });

  it("clears input after successful send", () => {
    render(<ChatInput onSend={() => {}} disabled={false} />);
    const input = screen.getByPlaceholderText(/ask a question/i);
    fireEvent.change(input, { target: { value: "hello" } });
    fireEvent.click(screen.getByRole("button"));
    expect(input).toHaveValue("");
  });

  it("does not call onSend for whitespace-only input", () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} disabled={false} />);

    const input = screen.getByPlaceholderText(/ask a question/i);
    fireEvent.change(input, { target: { value: "   " } });
    fireEvent.submit(input.closest("form")!);

    expect(onSend).not.toHaveBeenCalled();
  });

  it("does not call onSend for empty input", () => {
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} disabled={false} />);

    fireEvent.submit(screen.getByPlaceholderText(/ask a question/i).closest("form")!);

    expect(onSend).not.toHaveBeenCalled();
  });

  it("disables input and button when disabled=true", () => {
    render(<ChatInput onSend={() => {}} disabled={true} />);
    expect(screen.getByPlaceholderText(/ask a question/i)).toBeDisabled();
    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("button is disabled when input is empty even if not loading", () => {
    render(<ChatInput onSend={() => {}} disabled={false} />);
    // No text entered — button should be disabled
    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("button becomes enabled when input has content", () => {
    render(<ChatInput onSend={() => {}} disabled={false} />);
    fireEvent.change(screen.getByPlaceholderText(/ask a question/i), {
      target: { value: "hello" },
    });
    expect(screen.getByRole("button")).not.toBeDisabled();
  });
});
