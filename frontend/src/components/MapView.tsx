import "leaflet/dist/leaflet.css";
import { CircleMarker, MapContainer, Polygon, Polyline, Popup, TileLayer } from "react-leaflet";
import type { Alert, Telemetry, Zone } from "../types";

const SEVERITY_COLOR: Record<string, string> = {
  critical: "#dc2626",
  high: "#ea580c",
  medium: "#ca8a04",
  low: "#65a30d",
};

interface Props {
  dronePositions: Record<string, Telemetry>;
  droneTrails: Record<string, [number, number][]>;
  alerts: Alert[];
  zones: Zone[];
  center: [number, number];
}

export function MapView({ dronePositions, droneTrails, alerts, zones, center }: Props) {
  return (
    <MapContainer center={center} zoom={14} style={{ height: "100%", width: "100%" }}>
      <TileLayer
        attribution='&copy; OpenStreetMap contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {zones.map((zone) => (
        <Polygon
          key={zone.id}
          positions={zone.boundary}
          pathOptions={{ color: "#f59e0b", weight: 2, fillOpacity: 0.05, dashArray: "6 4" }}
        >
          <Popup>{zone.name}</Popup>
        </Polygon>
      ))}

      {Object.entries(droneTrails).map(([droneId, trail]) => (
        <Polyline key={droneId} positions={trail} pathOptions={{ color: "#2563eb", weight: 2 }} />
      ))}

      {Object.entries(dronePositions).map(([droneId, t]) => (
        <CircleMarker
          key={droneId}
          center={[t.lat, t.lon]}
          radius={8}
          pathOptions={{ color: "#2563eb", fillColor: "#3b82f6", fillOpacity: 1 }}
        >
          <Popup>
            <strong>{droneId}</strong>
            <br />
            Alt: {t.altitude_m.toFixed(0)} m
            <br />
            Heading: {t.heading_deg.toFixed(0)}°
            <br />
            Battery: {t.battery_pct.toFixed(0)}%
          </Popup>
        </CircleMarker>
      ))}

      {alerts
        .filter((a) => a.status === "open")
        .map((alert) => (
          <CircleMarker
            key={alert.id}
            center={[alert.lat, alert.lon]}
            radius={7}
            pathOptions={{
              color: SEVERITY_COLOR[alert.severity] ?? "#6b7280",
              fillColor: SEVERITY_COLOR[alert.severity] ?? "#6b7280",
              fillOpacity: 0.7,
            }}
          >
            <Popup>
              <strong>{alert.object_type}</strong> ({alert.severity})
              <br />
              from {alert.drone_id}
              <br />
              {new Date(alert.created_at).toLocaleTimeString()}
            </Popup>
          </CircleMarker>
        ))}
    </MapContainer>
  );
}
