export type BackendStatus =
  | { state: "loading" }
  | { state: "success"; serviceName?: string }
  | { state: "error"; message?: string };

const statusCopy = {
  loading: {
    label: "Checking backend",
    detail: "Waiting for the health check."
  },
  success: {
    label: "Backend connected",
    detail: "Tavola API is ready."
  },
  error: {
    label: "Backend unavailable",
    detail: "Catalog, basket, and checkout data will reconnect here."
  }
} as const;

type BackendStatusPanelProps = {
  status: BackendStatus;
};

export function BackendStatusPanel({ status }: BackendStatusPanelProps) {
  const copy = statusCopy[status.state];
  const detail =
    status.state === "success" && status.serviceName
      ? `${status.serviceName} is ready.`
      : status.state === "error" && status.message
        ? status.message
        : copy.detail;
  const liveRegionRole = status.state === "error" ? "alert" : "status";

  return (
    <section
      aria-label="Backend status"
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
