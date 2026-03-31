import type { QueryRequest, QueryResponse } from "../../types/query";

const MOCK_DELAY_MS = 600;

/** Deterministic mock response for isolated frontend development. */
export async function postQueryMock(req: QueryRequest): Promise<QueryResponse> {
  await new Promise((r) => setTimeout(r, MOCK_DELAY_MS));

  const response: QueryResponse = {
    answer: `Here is a simulated answer for your question: "${req.query}". Please refer to the sources below for more details.`,
    sources: [
      {
        title: "How to reset iPension access",
        url: "https://example.atlassian.net/wiki/spaces/KMS/pages/12345",
        section: "Steps",
        doc_id: "12345",
        chunk_id: "12345#steps#1",
      },
      {
        title: "iPension FAQ",
        url: "https://example.atlassian.net/wiki/spaces/KMS/pages/67890",
        section: "Overview",
        doc_id: "67890",
        chunk_id: "67890#overview#1",
      },
    ],
    related_documents: [
      {
        page_id: "12345",
        title: "How to reset iPension access",
        url: "https://example.atlassian.net/wiki/spaces/KMS/pages/12345",
      },
      {
        page_id: "67890",
        title: "iPension FAQ",
        url: "https://example.atlassian.net/wiki/spaces/KMS/pages/67890",
      },
    ],
    debug: req.include_debug
      ? {
          normalized_query: req.query.toLowerCase(),
          selected_chunks: [
            {
              chunk_id: "12345#steps#1",
              doc_id: "12345",
              title: "How to reset iPension access",
              section: "Steps",
              content:
                "Step 1: Navigate to the iPension portal. Step 2: Click 'Forgot Password'. Step 3: Follow the email instructions.",
              url: "https://example.atlassian.net/wiki/spaces/KMS/pages/12345",
              tags: ["ipension", "access", "reset"],
              pipeline_version: 1,
              score: 12.3,
            },
          ],
        }
      : { normalized_query: "", selected_chunks: [] },
  };

  return response;
}
