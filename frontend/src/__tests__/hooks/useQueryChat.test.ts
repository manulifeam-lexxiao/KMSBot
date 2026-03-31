import { describe, it, expect, vi, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useQueryChat } from "../../hooks/useQueryChat";
import * as queryApi from "../../services/api/queryApi";

vi.mock("../../services/api/queryApi");

afterEach(() => vi.clearAllMocks());

const mockResponse = {
  answer: "The answer is 42.",
  sources: [
    {
      title: "Source Doc",
      url: "https://example.com/1",
      section: "Overview",
      doc_id: "doc1",
      chunk_id: "doc1#1",
    },
  ],
  related_documents: [],
  debug: { normalized_query: "test query", selected_chunks: [] },
};

describe("useQueryChat", () => {
  it("starts with empty messages and not loading", () => {
    const { result } = renderHook(() => useQueryChat());
    expect(result.current.messages).toEqual([]);
    expect(result.current.isLoading).toBe(false);
  });

  it("appends a user message immediately after sendMessage", async () => {
    vi.mocked(queryApi.postQuery).mockResolvedValue(mockResponse);
    const { result } = renderHook(() => useQueryChat());

    await act(async () => result.current.sendMessage("hello world"));

    expect(result.current.messages[0].role).toBe("user");
    expect(result.current.messages[0].content).toBe("hello world");
  });

  it("appends an assistant message after API resolves", async () => {
    vi.mocked(queryApi.postQuery).mockResolvedValue(mockResponse);
    const { result } = renderHook(() => useQueryChat());

    await act(async () => result.current.sendMessage("hello"));

    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[1].role).toBe("assistant");
    expect(result.current.messages[1].content).toBe("The answer is 42.");
    expect(result.current.messages[1].response?.sources).toHaveLength(1);
  });

  it("trims the query before sending", async () => {
    vi.mocked(queryApi.postQuery).mockResolvedValue(mockResponse);
    const { result } = renderHook(() => useQueryChat());

    await act(async () => result.current.sendMessage("  trimmed query  "));

    expect(result.current.messages[0].content).toBe("trimmed query");
    expect(vi.mocked(queryApi.postQuery).mock.calls[0]?.[0].query).toBe("trimmed query");
  });

  it("does not call the API for whitespace-only input", async () => {
    const spy = vi.mocked(queryApi.postQuery);
    const { result } = renderHook(() => useQueryChat());

    act(() => result.current.sendMessage("   "));

    expect(spy).not.toHaveBeenCalled();
    expect(result.current.messages).toEqual([]);
  });

  it("does not call the API for empty string", async () => {
    const spy = vi.mocked(queryApi.postQuery);
    const { result } = renderHook(() => useQueryChat());

    act(() => result.current.sendMessage(""));

    expect(spy).not.toHaveBeenCalled();
  });

  it("appends error assistant message when API rejects", async () => {
    vi.mocked(queryApi.postQuery).mockRejectedValue(new Error("Network timeout"));
    const { result } = renderHook(() => useQueryChat());

    await act(async () => result.current.sendMessage("hello"));

    expect(result.current.messages).toHaveLength(2);
    const errMsg = result.current.messages[1];
    expect(errMsg.role).toBe("assistant");
    expect(errMsg.error).toBe("Network timeout");
    expect(errMsg.content).toBe("Sorry, something went wrong.");
  });

  it("sends include_debug flag to API when enabled", async () => {
    vi.mocked(queryApi.postQuery).mockResolvedValue(mockResponse);
    const { result } = renderHook(() => useQueryChat(true));

    await act(async () => result.current.sendMessage("debug query"));

    expect(vi.mocked(queryApi.postQuery).mock.calls[0]?.[0].include_debug).toBe(true);
  });

  it("clears all messages on clearMessages", async () => {
    vi.mocked(queryApi.postQuery).mockResolvedValue(mockResponse);
    const { result } = renderHook(() => useQueryChat());

    await act(async () => result.current.sendMessage("hello"));
    expect(result.current.messages).toHaveLength(2);

    act(() => result.current.clearMessages());
    expect(result.current.messages).toEqual([]);
    expect(result.current.isLoading).toBe(false);
  });

  it("sets isLoading to false after API resolves", async () => {
    vi.mocked(queryApi.postQuery).mockResolvedValue(mockResponse);
    const { result } = renderHook(() => useQueryChat());

    await act(async () => result.current.sendMessage("hello"));

    expect(result.current.isLoading).toBe(false);
  });
});
