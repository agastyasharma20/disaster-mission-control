import { api } from "../api";
import type { Alert } from "../types";

const SEVERITY_CLASS: Record<string, string> = {
  critical: "sev-critical",
  high: "sev-high",
  medium: "sev-medium",
  low: "sev-low",
};

interface Props {
  alerts: Alert[];
  onUpdated: (alert: Alert) => void;
}

export function AlertFeed({ alerts, onUpdated }: Props) {
  async function acknowledge(alert: Alert) {
    const updated = (await api.updateAlert(alert.id, { status: "acknowledged" })) as Alert;
    onUpdated(updated);
  }

  return (
    <div className="panel">
      <h2>Alerts</h2>
      <div className="scroll-list">
        {alerts.length === 0 && <p className="empty">No alerts yet.</p>}
        {alerts.map((alert) => (
          <div key={alert.id} className={`alert-card ${SEVERITY_CLASS[alert.severity] ?? ""}`}>
            <div className="alert-card-header">
              <span className="badge">{alert.severity}</span>
              <span>{alert.object_type}</span>
            </div>
            <div className="alert-card-meta">
              {alert.drone_id} &middot; {new Date(alert.created_at).toLocaleTimeString()} &middot; {alert.status}
            </div>
            {alert.status === "open" && (
              <button onClick={() => acknowledge(alert)}>Acknowledge</button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
