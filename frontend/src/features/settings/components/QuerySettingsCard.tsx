import { useState } from "react";
import { useQuerySettings } from "../../../hooks/useQuerySettings";

export function QuerySettingsCard() {
  const { settings, isLoading, isSaving, error, updateQuerySettings } = useQuerySettings();
  const [localTopK, setLocalTopK] = useState("");
  const [localMaxChunks, setLocalMaxChunks] = useState("");
  const [localThreshold, setLocalThreshold] = useState("");
  const [initialized, setInitialized] = useState(false);

  if (settings && !initialized) {
    setLocalTopK(String(settings.top_k));
    setLocalMaxChunks(String(settings.max_chunks_per_doc));
    setLocalThreshold(String(settings.similarity_threshold));
    setInitialized(true);
  }

  const isDirty =
    settings != null &&
    (localTopK !== String(settings.top_k) ||
      localMaxChunks !== String(settings.max_chunks_per_doc) ||
      localThreshold !== String(settings.similarity_threshold));

  const handleSave = () => {
    if (!settings) return;
    const top_k = parseInt(localTopK, 10);
    const max_chunks_per_doc = parseInt(localMaxChunks, 10);
    const similarity_threshold = parseFloat(localThreshold);
    if (
      isNaN(top_k) ||
      top_k < 1 ||
      top_k > 10 ||
      isNaN(max_chunks_per_doc) ||
      max_chunks_per_doc < 1 ||
      max_chunks_per_doc > 10 ||
      isNaN(similarity_threshold) ||
      similarity_threshold < 0 ||
      similarity_threshold > 1
    )
      return;
    void updateQuerySettings({ top_k, max_chunks_per_doc, similarity_threshold });
  };

  return (
    <div className="card animate-in">
      <div className="card__header">
        <h2 className="card__title">Query Settings</h2>
      </div>
      <div className="card__body">
        {isLoading && <p className="card__placeholder">Loading...</p>}
        {error && <p className="card__error">{error}</p>}
        {settings && (
          <div className="thinking-settings">
            <div className="thinking-settings__field">
              <label className="thinking-settings__label" htmlFor="qs-top-k">
                Top K Results
              </label>
              <div className="thinking-settings__input-group">
                <input
                  id="qs-top-k"
                  type="number"
                  className="thinking-settings__input"
                  min={1}
                  max={10}
                  value={localTopK}
                  onChange={(e) => setLocalTopK(e.target.value)}
                />
              </div>
              <p className="thinking-settings__hint">每次查询返回的最大匹配结果数量 (1-10)</p>
            </div>

            <div className="thinking-settings__field">
              <label className="thinking-settings__label" htmlFor="qs-max-chunks">
                Max Chunks per Doc
              </label>
              <div className="thinking-settings__input-group">
                <input
                  id="qs-max-chunks"
                  type="number"
                  className="thinking-settings__input"
                  min={1}
                  max={10}
                  value={localMaxChunks}
                  onChange={(e) => setLocalMaxChunks(e.target.value)}
                />
              </div>
              <p className="thinking-settings__hint">同一文档最多保留的 chunk 数量 (1-10)</p>
            </div>

            <div className="thinking-settings__field">
              <label className="thinking-settings__label" htmlFor="qs-threshold">
                Similarity Threshold
              </label>
              <div className="thinking-settings__input-group">
                <input
                  id="qs-threshold"
                  type="number"
                  className="thinking-settings__input"
                  min={0}
                  max={1}
                  step={0.05}
                  value={localThreshold}
                  onChange={(e) => setLocalThreshold(e.target.value)}
                />
                <button
                  type="button"
                  className="thinking-settings__save"
                  onClick={handleSave}
                  disabled={isSaving || !isDirty}
                >
                  {isSaving ? "Saving..." : "Save"}
                </button>
              </div>
              <p className="thinking-settings__hint">近义 chunk 去重阈值 (0.0-1.0)</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
