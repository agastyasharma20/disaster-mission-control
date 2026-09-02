import { useState } from "react";
import { api } from "../api";
import type { Announcement } from "../types";

interface Props {
  announcements: Announcement[];
  onCreated: (announcement: Announcement) => void;
}

export function AnnouncementLog({ announcements, onCreated }: Props) {
  const [text, setText] = useState("");
  const [zone, setZone] = useState("");

  async function submit() {
    if (!text.trim()) return;
    const created = (await api.createAnnouncement({ text, zone: zone || null })) as Announcement;
    onCreated(created);
    setText("");
  }

  return (
    <div className="panel">
      <h2>Announcement Log</h2>
      <div className="announcement-create">
        <input
          placeholder="Announcement text"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <input placeholder="Zone (optional)" value={zone} onChange={(e) => setZone(e.target.value)} />
        <button onClick={submit}>Log</button>
      </div>
      <div className="scroll-list">
        {announcements.map((a) => (
          <div key={a.id} className="announcement-card">
            <div>{a.text}</div>
            <div className="task-card-meta">
              {a.zone ?? "—"} · {new Date(a.timestamp).toLocaleTimeString()}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
