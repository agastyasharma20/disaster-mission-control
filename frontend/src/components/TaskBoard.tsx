import { useState } from "react";
import { api } from "../api";
import type { Alert, Task, TaskStatus } from "../types";

const COLUMNS: TaskStatus[] = ["pending", "dispatched", "in_progress", "completed", "failed"];

const NEXT_STATUS: Partial<Record<TaskStatus, TaskStatus>> = {
  pending: "dispatched",
  dispatched: "in_progress",
  in_progress: "completed",
};

interface Props {
  tasks: Task[];
  alerts: Alert[];
  onCreated: (task: Task) => void;
  onUpdated: (task: Task) => void;
}

export function TaskBoard({ tasks, alerts, onCreated, onUpdated }: Props) {
  const [type, setType] = useState<"drop" | "rescue">("drop");
  const [alertId, setAlertId] = useState<string>("");

  const openAlerts = alerts.filter((a) => a.status !== "resolved");

  async function createFromAlert() {
    const alert = openAlerts.find((a) => a.id === alertId);
    if (!alert) return;
    const task = (await api.createTask({
      type,
      target_lat: alert.lat,
      target_lon: alert.lon,
      priority: alert.severity,
      linked_alert_id: alert.id,
    })) as Task;
    onCreated(task);
  }

  async function advance(task: Task) {
    const next = NEXT_STATUS[task.status];
    if (!next) return;
    const updated = (await api.updateTask(task.id, { status: next })) as Task;
    onUpdated(updated);
  }

  return (
    <div className="panel">
      <h2>Logistics &amp; Rescue Tasks</h2>

      <div className="task-create">
        <select value={type} onChange={(e) => setType(e.target.value as "drop" | "rescue")}>
          <option value="drop">Drop</option>
          <option value="rescue">Rescue</option>
        </select>
        <select value={alertId} onChange={(e) => setAlertId(e.target.value)}>
          <option value="">Select alert…</option>
          {openAlerts.map((a) => (
            <option key={a.id} value={a.id}>
              {a.object_type} ({a.severity}) — {a.drone_id}
            </option>
          ))}
        </select>
        <button disabled={!alertId} onClick={createFromAlert}>
          Create task
        </button>
      </div>

      <div className="task-columns">
        {COLUMNS.map((status) => (
          <div key={status} className="task-column">
            <h3>{status.replace("_", " ")}</h3>
            {tasks
              .filter((t) => t.status === status)
              .map((task) => (
                <div key={task.id} className="task-card">
                  <div>
                    <strong>{task.type}</strong> · {task.priority}
                  </div>
                  <div className="task-card-meta">
                    {task.target_lat.toFixed(4)}, {task.target_lon.toFixed(4)}
                  </div>
                  {task.assigned_team && <div className="task-card-meta">Team: {task.assigned_team}</div>}
                  {NEXT_STATUS[task.status] && (
                    <button onClick={() => advance(task)}>Mark {NEXT_STATUS[task.status]}</button>
                  )}
                </div>
              ))}
          </div>
        ))}
      </div>
    </div>
  );
}
