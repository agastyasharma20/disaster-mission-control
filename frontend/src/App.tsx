import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import { AlertFeed } from "./components/AlertFeed";
import { AnnouncementLog } from "./components/AnnouncementLog";
import { MapView } from "./components/MapView";
import { TaskBoard } from "./components/TaskBoard";
import { VideoPanel } from "./components/VideoPanel";
import { useWebSocket } from "./hooks/useWebSocket";
import type { Alert, Announcement, Detection, Task, Telemetry, WsMessage } from "./types";

const DEFAULT_CENTER: [number, number] = [22.7196, 75.8577]; // Indore, MP
const TRAIL_LENGTH = 200;

export default function App() {
  const [dronePositions, setDronePositions] = useState<Record<string, Telemetry>>({});
  const [droneTrails, setDroneTrails] = useState<Record<string, [number, number][]>>({});
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [latestDetection, setLatestDetection] = useState<Detection | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    api.alerts().then((r) => setAlerts(r as Alert[]));
    api.tasks().then((r) => setTasks(r as Task[]));
    api.announcements().then((r) => setAnnouncements(r as Announcement[]));
  }, []);

  const handleMessage = useCallback((msg: WsMessage) => {
    setConnected(true);
    switch (msg.type) {
      case "telemetry": {
        const t = msg.payload as Telemetry;
        setDronePositions((prev) => ({ ...prev, [t.drone_id]: t }));
        setDroneTrails((prev) => {
          const trail = [...(prev[t.drone_id] ?? []), [t.lat, t.lon] as [number, number]];
          return { ...prev, [t.drone_id]: trail.slice(-TRAIL_LENGTH) };
        });
        break;
      }
      case "detection":
        setLatestDetection(msg.payload as Detection);
        break;
      case "alert":
        setAlerts((prev) => [msg.payload as Alert, ...prev]);
        break;
      case "alert_updated": {
        const updated = msg.payload as Alert;
        setAlerts((prev) => prev.map((a) => (a.id === updated.id ? updated : a)));
        break;
      }
      case "task":
        setTasks((prev) => [msg.payload as Task, ...prev]);
        break;
      case "task_updated": {
        const updated = msg.payload as Task;
        setTasks((prev) => prev.map((t) => (t.id === updated.id ? updated : t)));
        break;
      }
      case "announcement":
        setAnnouncements((prev) => [msg.payload as Announcement, ...prev]);
        break;
    }
  }, []);

  useWebSocket(handleMessage);

  const droneIds = Object.keys(dronePositions);
  const mapCenter = droneIds.length > 0 ? [dronePositions[droneIds[0]].lat, dronePositions[droneIds[0]].lon] as [number, number] : DEFAULT_CENTER;

  return (
    <div className="app">
      <header className="app-header">
        <h1>Disaster Mission Control</h1>
        <span className={`ws-status ${connected ? "connected" : "disconnected"}`}>
          {connected ? "● live" : "○ connecting…"}
        </span>
      </header>

      <div className="app-body">
        <div className="map-pane">
          <MapView
            dronePositions={dronePositions}
            droneTrails={droneTrails}
            alerts={alerts}
            center={mapCenter}
          />
        </div>

        <div className="side-pane">
          <VideoPanel droneId={droneIds[0] ?? null} latestDetection={latestDetection} />
          <AlertFeed
            alerts={alerts}
            onUpdated={(updated) => setAlerts((prev) => prev.map((a) => (a.id === updated.id ? updated : a)))}
          />
        </div>
      </div>

      <div className="bottom-pane">
        <TaskBoard
          tasks={tasks}
          alerts={alerts}
          onCreated={(task) => setTasks((prev) => [task, ...prev])}
          onUpdated={(updated) => setTasks((prev) => prev.map((t) => (t.id === updated.id ? updated : t)))}
        />
        <AnnouncementLog
          announcements={announcements}
          onCreated={(a) => setAnnouncements((prev) => [a, ...prev])}
        />
      </div>
    </div>
  );
}
