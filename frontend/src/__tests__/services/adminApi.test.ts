import { describe, it, expect, vi, afterEach } from "vitest";
import {
  getHealth,
  getSyncStatus,
  triggerFullSync,
  triggerIncrementalSync,
  getIndexStatus,
  triggerIndexRebuild,
} from "../../services/api/adminApi";

afterEach(() => vi.restoreAllMocks());

const makeRes = (body: unknown, ok = true, status = 200): Response =>
  ({ ok, status, json: () => Promise.resolve(body) }) as unknown as Response;

const healthData = {
  status: "ok",
  service: "kms-bot-backend",
  version: "0.1.0",
  timestamp: "2026-03-31T10:00:00Z",
  dependencies: { sqlite: "ok", azure_ai_search: "not_configured", azure_openai: "not_configured" },
};

const acceptedResponse = {
  job_id: "job-1",
  job_type: "full_sync",
  status: "accepted",
  requested_at: "2026-03-31T10:00:00Z",
  pipeline_version: 1,
  message: "Accepted.",
};

describe("getHealth", () => {
  it("returns health data on success", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue(makeRes(healthData));
    const result = await getHealth();
    expect(result.status).toBe("ok");
    expect(result.version).toBe("0.1.0");
  });

  it("throws with message from body on error", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue(makeRes({ message: "Service down" }, false, 503));
    await expect(getHealth()).rejects.toThrow("Service down");
  });

  it("throws generic message when body has no message field", async () => {
    vi.spyOn(global, "fetch").mockResolvedValue(makeRes({}, false, 500));
    await expect(getHealth()).rejects.toThrow("Request failed (500)");
  });
});

describe("triggerFullSync", () => {
  it("sends POST and returns accepted response", async () => {
    const fetchSpy = vi.spyOn(global, "fetch").mockResolvedValue(makeRes(acceptedResponse));
    const result = await triggerFullSync();
    expect(result.job_type).toBe("full_sync");
    const [url, init] = fetchSpy.mock.calls[0] as [string, RequestInit];
    expect(url).toContain("/api/sync/full");
    expect(init.method).toBe("POST");
  });
});

describe("triggerIncrementalSync", () => {
  it("sends POST to incremental endpoint", async () => {
    const fetchSpy = vi
      .spyOn(global, "fetch")
      .mockResolvedValue(makeRes({ ...acceptedResponse, job_type: "incremental_sync" }));
    await triggerIncrementalSync();
    const [url] = fetchSpy.mock.calls[0] as [string, RequestInit];
    expect(url).toContain("/api/sync/incremental");
  });
});

describe("getIndexStatus", () => {
  it("returns index status data", async () => {
    const data = {
      status: "success",
      current_job_id: null,
      pipeline_version: 1,
      last_started_at: null,
      last_finished_at: null,
      last_success_at: null,
      indexed_documents: 42,
      indexed_chunks: 187,
      error_message: null,
    };
    vi.spyOn(global, "fetch").mockResolvedValue(makeRes(data));
    const result = await getIndexStatus();
    expect(result.indexed_documents).toBe(42);
    expect(result.indexed_chunks).toBe(187);
  });
});

describe("getSyncStatus", () => {
  it("returns sync status data", async () => {
    const data = {
      status: "idle",
      mode: "none",
      current_job_id: null,
      pipeline_version: 1,
      last_started_at: null,
      last_finished_at: null,
      last_success_at: null,
      processed_pages: 10,
      changed_pages: 2,
      error_message: null,
    };
    vi.spyOn(global, "fetch").mockResolvedValue(makeRes(data));
    const result = await getSyncStatus();
    expect(result.processed_pages).toBe(10);
  });
});

describe("triggerIndexRebuild", () => {
  it("sends POST to index rebuild endpoint", async () => {
    const fetchSpy = vi
      .spyOn(global, "fetch")
      .mockResolvedValue(makeRes({ ...acceptedResponse, job_type: "index_rebuild" }));
    await triggerIndexRebuild();
    const [url, init] = fetchSpy.mock.calls[0] as [string, RequestInit];
    expect(url).toContain("/api/index/rebuild");
    expect(init.method).toBe("POST");
  });
});
