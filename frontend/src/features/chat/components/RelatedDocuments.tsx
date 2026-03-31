import type { RelatedDocument } from "../../../types/query";
import "./RelatedDocuments.css";

interface RelatedDocumentsProps {
  documents: RelatedDocument[];
}

export function RelatedDocuments({ documents }: RelatedDocumentsProps) {
  if (documents.length === 0) return null;

  return (
    <div className="related-docs">
      <h4 className="related-docs__title">Related Documents</h4>
      <ul className="related-docs__items">
        {documents.map((d) => (
          <li key={d.page_id} className="related-docs__item">
            <a
              href={d.url}
              target="_blank"
              rel="noopener noreferrer"
              className="related-docs__link"
            >
              {d.title}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}
