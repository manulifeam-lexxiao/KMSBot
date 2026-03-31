import "./StatusBadge.css";

interface StatusBadgeProps {
  status: string;
}

const STATUS_CLASS: Record<string, string> = {
  ok: "status-badge--ok",
  success: "status-badge--ok",
  idle: "status-badge--idle",
  running: "status-badge--running",
  degraded: "status-badge--degraded",
  error: "status-badge--error",
  not_configured: "status-badge--idle",
};

export function StatusBadge({ status }: StatusBadgeProps) {
  const cls = STATUS_CLASS[status] ?? "status-badge--idle";
  return <span className={`status-badge ${cls}`}>{status}</span>;
}
