export const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";
export const WS_URL = import.meta.env.VITE_WS_URL ?? "ws://localhost:8000/ws/dashboard";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    throw new Error(`${init?.method ?? "GET"} ${path} failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  alerts: () => request("/api/alerts"),
  tasks: () => request("/api/tasks"),
  announcements: () => request("/api/announcements"),
  zones: () => request("/api/zones"),
  createTask: (body: unknown) => request("/api/tasks", { method: "POST", body: JSON.stringify(body) }),
  updateTask: (id: string, body: unknown) =>
    request(`/api/tasks/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  updateAlert: (id: string, body: unknown) =>
    request(`/api/alerts/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  createAnnouncement: (body: unknown) =>
    request("/api/announcements", { method: "POST", body: JSON.stringify(body) }),
};
