import { useState } from "react";
import type { QueryDebugInfo } from "../../../types/query";
import "./DebugPanel.css";

interface DebugPanelProps {
  debug: QueryDebugInfo;
}

export function DebugPanel({ debug }: DebugPanelProps) {
  const [open, setOpen] = useState(false);

  // Hide if there is nothing useful in debug
  if (!debug.normalized_query && debug.selected_chunks.length === 0) {
    return null;
  }

  return (
    <div className="debug-panel">
      <button
        type="button"
        className="debug-panel__toggle"
        onClick={() => setOpen((v) => !v)}
      >
        {open ? "▾ Hide debug" : "▸ Show debug"}
      </button>
      {open && (
        <pre className="debug-panel__content">
          {JSON.stringify(debug, null, 2)}
        </pre>
      )}
    </div>
  );
}
