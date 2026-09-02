export interface Telemetry {
  id: string;
  drone_id: string;
  lat: number;
  lon: number;
  altitude_m: number;
  heading_deg: number;
  battery_pct: number;
  timestamp: string;
}

export interface Detection {
  id: string;
  drone_id: string;
  object_type: string;
  confidence: number;
  lat: number;
  lon: number;
  snapshot_url: string | null;
  timestamp: string;
}

export type Severity = "critical" | "high" | "medium" | "low";
export type AlertStatus = "open" | "acknowledged" | "resolved";

export interface Alert {
  id: string;
  detection_id: string | null;
  drone_id: string;
  object_type: string;
  severity: Severity;
  status: AlertStatus;
  lat: number;
  lon: number;
  created_at: string;
}

export type TaskType = "drop" | "rescue";
export type TaskStatus = "pending" | "dispatched" | "in_progress" | "completed" | "failed";

export interface Task {
  id: string;
  type: TaskType;
  target_lat: number;
  target_lon: number;
  assigned_team: string | null;
  priority: Severity;
  status: TaskStatus;
  linked_alert_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface Announcement {
  id: string;
  text: string;
  zone: string | null;
  made_by: string | null;
  timestamp: string;
}

export interface WsMessage<T = unknown> {
  type: "telemetry" | "detection" | "alert" | "alert_updated" | "task" | "task_updated" | "announcement";
  payload: T;
}
