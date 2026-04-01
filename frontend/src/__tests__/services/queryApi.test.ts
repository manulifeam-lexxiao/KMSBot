import { describe, it, expect, vi, afterEach } from "vitest";
import { postQuery } from "../../services/api/queryApi";

afterEach(() => vi.restoreAllMocks());

const makeRes = (body: unknown, ok = true, status = 200): Response =>
  ({ ok, status, json: () => Promise.resolve(body) }) as unknown as Response;

const okPayload = {
  answer: "test answer",
  sources: [],
  related_documents: [],
  debug: { normalized_query: "hello", selected_chunks: [] },
};

describe("postQuery", () => {
  it("returns the parsed response body on success", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue(makeRes(okPayload));
    const result = await postQuery({
      query: "hello",
      top_k: 5,
      include_debug: false,
      thinking: false,
    });
    expect(result.answer).toBe("test answer");
    expect(result.sources).toEqual([]);
  });

  it("sends POST to /api/query with JSON body", async () => {
    const fetchSpy = vi.spyOn(global, "fetch").mockResolvedValue(makeRes(okPayload));
    await postQuery({ query: "hello", top_k: 3, include_debug: true, thinking: false });
    const [url, init] = fetchSpy.mock.calls[0] as [string, RequestInit];
    expect(url).toContain("/api/query");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body as string)).toMatchObject({ query: "hello", top_k: 3 });
  });

  it("throws error with message from response body when not ok", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue(
      makeRes({ message: "Bad request from server" }, false, 400),
    );
    await expect(
      postQuery({ query: "hello", top_k: 5, include_debug: false, thinking: false }),
    ).rejects.toThrow("Bad request from server");
  });

  it("throws generic message when body has no message field", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue(makeRes({ error: "unknown" }, false, 500));
    await expect(
      postQuery({ query: "hello", top_k: 5, include_debug: false, thinking: false }),
    ).rejects.toThrow("Query failed (500)");
  });

  it("throws when fetch itself rejects (network failure)", async () => {
    vi.spyOn(global, "fetch").mockRejectedValue(new Error("Network error"));
    await expect(
      postQuery({ query: "hello", top_k: 5, include_debug: false, thinking: false }),
    ).rejects.toThrow("Network error");
  });
});
