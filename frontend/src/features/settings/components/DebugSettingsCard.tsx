import { useDebugPreference } from "../../../hooks/useDebugPreference";
import "./DebugSettingsCard.css";

export function DebugSettingsCard() {
  const { includeDebug, setIncludeDebug } = useDebugPreference();

  return (
    <div className="card animate-in">
      <div className="card__header">
        <h2 className="card__title">Debug Mode</h2>
      </div>
      <div className="card__body">
        <div className="debug-settings">
          <label className="debug-settings__toggle">
            <div className="debug-settings__switch-wrap">
              <input
                type="checkbox"
                className="debug-settings__input"
                checked={includeDebug}
                onChange={(e) => setIncludeDebug(e.target.checked)}
              />
              <span className="debug-settings__switch" />
            </div>
            <div className="debug-settings__text">
              <span className="debug-settings__label">Include Debug Info</span>
              <span className="debug-settings__hint">
                查询响应将包含来源文档和检索过程的调试信息
              </span>
            </div>
          </label>
        </div>
      </div>
    </div>
  );
}
