import type { Detection } from "../types";

interface Props {
  droneId: string | null;
  streamUrl?: string;
  latestDetection: Detection | null;
}

/**
 * Placeholder video panel (Section 4.7). Real drone video is an RTSP/WebRTC
 * feed (Section 4.1) -- wire `streamUrl` up to a player (e.g. an
 * MSE/WebRTC bridge) once a live feed exists. Until then this shows the
 * most recent AI detection as a stand-in for "what the drone is seeing".
 */
export function VideoPanel({ droneId, streamUrl, latestDetection }: Props) {
  return (
    <div className="panel video-panel">
      <h2>Live Feed {droneId ? `— ${droneId}` : ""}</h2>
      <div className="video-frame">
        {streamUrl ? (
          <video src={streamUrl} autoPlay muted controls />
        ) : (
          <div className="video-placeholder">No live stream configured (simulated drone).</div>
        )}
      </div>
      {latestDetection && (
        <div className="video-detection">
          Last detection: <strong>{latestDetection.object_type}</strong>{" "}
          ({Math.round(latestDetection.confidence * 100)}%)
        </div>
      )}
    </div>
  );
}
