import "./ActionButton.css";

interface ActionButtonProps {
  label: string;
  onClick: () => void;
  disabled?: boolean;
  isRunning?: boolean;
  lastError?: string | null;
  lastMessage?: string | null;
}

export function ActionButton({
  label,
  onClick,
  disabled,
  isRunning,
  lastError,
  lastMessage,
}: ActionButtonProps) {
  return (
    <div className="action-button-wrapper">
      <button
        type="button"
        className="action-button"
        onClick={onClick}
        disabled={disabled || isRunning}
      >
        {isRunning ? (
          <>
            <span className="action-button__spinner" aria-hidden="true">
              <span />
              <span />
              <span />
            </span>
            Running…
          </>
        ) : (
          label
        )}
      </button>
      {lastError && (
        <span className="action-button__feedback action-button__feedback--error">{lastError}</span>
      )}
      {!lastError && lastMessage && (
        <span className="action-button__feedback action-button__feedback--ok">{lastMessage}</span>
      )}
    </div>
  );
}
