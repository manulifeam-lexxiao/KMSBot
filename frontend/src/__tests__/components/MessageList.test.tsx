import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MessageList } from "../../features/chat/components/MessageList";
import type { ChatMessage } from "../../types/query";

function makeMsg(
  role: "user" | "assistant",
  content: string,
  extra?: Partial<ChatMessage>,
): ChatMessage {
  return {
    id: `${role}-${content}`,
    role,
    content,
    timestamp: new Date("2026-03-31T10:00:00Z"),
    ...extra,
  };
}

describe("MessageList", () => {
  it("shows placeholder when there are no messages and not loading", () => {
    render(<MessageList messages={[]} isLoading={false} />);
    expect(screen.getByText(/ask a question/i)).toBeInTheDocument();
  });

  it("does not show placeholder while loading (even with no messages)", () => {
    render(<MessageList messages={[]} isLoading={true} />);
    expect(screen.queryByText(/ask a question/i)).not.toBeInTheDocument();
  });

  it("renders a user message", () => {
    render(<MessageList messages={[makeMsg("user", "What is KMSBot?")]} isLoading={false} />);
    expect(screen.getByText("What is KMSBot?")).toBeInTheDocument();
  });

  it("renders an assistant message", () => {
    render(
      <MessageList
        messages={[makeMsg("assistant", "KMSBot is a knowledge base assistant.")]}
        isLoading={false}
      />,
    );
    expect(screen.getByText("KMSBot is a knowledge base assistant.")).toBeInTheDocument();
  });

  it("renders multiple messages in sequence", () => {
    const messages = [
      makeMsg("user", "Hello"),
      makeMsg("assistant", "Hi there!"),
      makeMsg("user", "How are you?"),
    ];
    render(<MessageList messages={messages} isLoading={false} />);
    expect(screen.getByText("Hello")).toBeInTheDocument();
    expect(screen.getByText("Hi there!")).toBeInTheDocument();
    expect(screen.getByText("How are you?")).toBeInTheDocument();
  });

  it("shows exactly three loading dots when isLoading=true", () => {
    render(<MessageList messages={[]} isLoading={true} />);
    expect(document.querySelectorAll(".message-list__dot")).toHaveLength(3);
  });

  it("shows loading dots even when messages already exist", () => {
    render(<MessageList messages={[makeMsg("user", "Hello")]} isLoading={true} />);
    expect(document.querySelectorAll(".message-list__dot")).toHaveLength(3);
  });

  it("assigns correct CSS class to user bubble", () => {
    render(<MessageList messages={[makeMsg("user", "User msg")]} isLoading={false} />);
    const bubble = screen.getByText("User msg").closest(".message-list__bubble");
    expect(bubble).toHaveClass("message-list__bubble--user");
  });

  it("assigns correct CSS class to assistant bubble", () => {
    render(<MessageList messages={[makeMsg("assistant", "Bot reply")]} isLoading={false} />);
    const bubble = screen.getByText("Bot reply").closest(".message-list__bubble");
    expect(bubble).toHaveClass("message-list__bubble--assistant");
  });

  it("renders assistant error content when message has error field", () => {
    const msg = makeMsg("assistant", "Sorry, something went wrong.", { error: "Timeout" });
    render(<MessageList messages={[msg]} isLoading={false} />);
    expect(screen.getByText(/sorry/i)).toBeInTheDocument();
    expect(screen.getByText(/timeout/i)).toBeInTheDocument();
  });
});
