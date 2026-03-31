import type { QueryResponse } from "../../../types/query";
import { SourceList } from "./SourceList";
import { RelatedDocuments } from "./RelatedDocuments";
import { DebugPanel } from "./DebugPanel";
import "./AnswerMessage.css";

interface AnswerMessageProps {
  content: string;
  response?: QueryResponse;
  error?: string;
}

export function AnswerMessage({ content, response, error }: AnswerMessageProps) {
  return (
    <div className="answer-message">
      <div className="answer-message__text">{content}</div>

      {error && <div className="answer-message__error">Error: {error}</div>}

      {response && (
        <>
          <SourceList sources={response.sources} />
          <RelatedDocuments documents={response.related_documents} />
          <DebugPanel debug={response.debug} />
        </>
      )}
    </div>
  );
}
