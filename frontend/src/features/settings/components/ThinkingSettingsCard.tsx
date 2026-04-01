import { useState } from "react";
import { useThinkingSettings } from "../../../hooks/useThinkingSettings";

export function ThinkingSettingsCard() {
  const { settings, isLoading, isSaving, error, updateMaxArticles } = useThinkingSettings();
  const [localValue, setLocalValue] = useState<string>("");
  const [initialized, setInitialized] = useState(false);

  // 初始化本地值
  if (settings && !initialized) {
    setLocalValue(String(settings.thinking_max_articles));
    setInitialized(true);
  }

  const handleSave = () => {
    const num = parseInt(localValue, 10);
    if (isNaN(num) || num < 1 || num > 50) return;
    void updateMaxArticles(num);
  };

  const isDirty = settings != null && localValue !== String(settings.thinking_max_articles);

  return (
    <div className="card animate-in">
      <div className="card__header">
        <h2 className="card__title">THINKING Mode</h2>
      </div>
      <div className="card__body">
        {isLoading && <p className="card__placeholder">Loading...</p>}
        {error && <p className="card__error">{error}</p>}
        {settings && (
          <div className="thinking-settings">
            <div className="thinking-settings__field">
              <label className="thinking-settings__label" htmlFor="thinking-max-articles">
                Max Articles per Query
              </label>
              <div className="thinking-settings__input-group">
                <input
                  id="thinking-max-articles"
                  type="number"
                  className="thinking-settings__input"
                  min={1}
                  max={50}
                  value={localValue}
                  onChange={(e) => setLocalValue(e.target.value)}
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
              <p className="thinking-settings__hint">
                THINKING 模式下每次查询最多深度阅读的文章数量 (1-50)
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
