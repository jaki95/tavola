export type BackendStatus =
  | { state: "loading" }
  | { state: "success"; serviceName?: string }
  | { state: "error"; message?: string };

const statusCopy = {
  loading: {
    label: "Checking service",
    detail: "Waiting for the health check."
  },
  success: {
    label: "Service ready",
    detail: "Tavola API ready."
  },
  error: {
    label: "Service unavailable",
    detail: "Catalog and basket data will reconnect here."
  }
} as const;

type BackendStatusPanelProps = {
  status: BackendStatus;
};

export function BackendStatusPanel({ status }: BackendStatusPanelProps) {
  const copy = statusCopy[status.state];
  const detail =
    status.state === "success" && status.serviceName
      ? `${status.serviceName} ready.`
      : status.state === "error" && status.message
        ? status.message
        : copy.detail;
  const liveRegionRole = status.state === "error" ? "alert" : "status";

  return (
    <section
      aria-label="Service status"
      className={`status-panel status-panel--${status.state}`}
      role={liveRegionRole}
    >
      <span aria-hidden="true" className="status-panel__signal" />
      <div>
        <p className="status-panel__label">{copy.label}</p>
        <p className="status-panel__detail">{detail}</p>
      </div>
    </section>
  );
}
