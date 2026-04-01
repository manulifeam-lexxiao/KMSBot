import type { ThinkingEvent } from "../../../types/query";
import "./ThinkingProgress.css";

interface ThinkingProgressProps {
  event: ThinkingEvent;
}

const STAGE_LABELS: Record<ThinkingEvent["stage"], string> = {
  planning: "分析中",
  searching: "搜索中",
  reading: "阅读中",
  summarizing: "总结中",
  done: "完成",
};

const STAGE_ORDER: ThinkingEvent["stage"][] = ["planning", "searching", "reading", "summarizing"];

export function ThinkingProgress({ event }: ThinkingProgressProps) {
  const currentIdx = STAGE_ORDER.indexOf(event.stage);

  return (
    <div className="thinking-progress">
      <div className="thinking-progress__stages">
        {STAGE_ORDER.map((stage, idx) => {
          let status: "done" | "active" | "pending" = "pending";
          if (idx < currentIdx) status = "done";
          else if (idx === currentIdx) status = "active";

          return (
            <div
              key={stage}
              className={`thinking-progress__stage thinking-progress__stage--${status}`}
            >
              <span className="thinking-progress__dot" />
              <span className="thinking-progress__label">{STAGE_LABELS[stage]}</span>
            </div>
          );
        })}
      </div>

      <p className="thinking-progress__message">{event.message}</p>

      {event.stage === "reading" && event.total != null && event.current != null && (
        <div className="thinking-progress__bar-wrap">
          <div
            className="thinking-progress__bar"
            style={{ width: `${(event.current / event.total) * 100}%` }}
          />
        </div>
      )}
    </div>
  );
}
