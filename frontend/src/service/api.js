const API = "/api";

async function request(path, options = {}) {
  const res = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json();
}

export const api = {
  health: () => request("/health"),
  metrics: () => request("/metrics"),
  events: (params = {}) => {
    const q = new URLSearchParams(
      Object.fromEntries(Object.entries(params).filter(([, v]) => v !== "" && v != null))
    ).toString();
    return request(`/events${q ? `?${q}` : ""}`);
  },
  event: (id) => request(`/events/${id}`),
  alerts: () => request("/alerts"),
  audit: () => request("/audit-logs"),
  profile: (userId) => request(`/users/${userId}/profile`),
  admin: () => request("/admin/status"),
  generate: (mode) => request("/events/generate", { method: "POST", body: JSON.stringify({ mode, user_id: "USR-102" }) }),
  demo: () => request("/demo/run", { method: "POST" }),
  scenario: () => request("/demo/scenario", { method: "POST" }),
  execute: (eventId) => request(`/actions/${eventId}/execute`, { method: "POST", body: JSON.stringify({}) }),
  dismiss: (eventId) => request(`/alerts/${eventId}/dismiss`, { method: "POST" }),
};

export function connectStream(onEvent) {
  const source = new EventSource(`${API}/stream`);
  ["pipeline", "event", "alert", "metrics", "demo", "action", "ready"].forEach((type) => {
    source.addEventListener(type, (e) => {
      try {
        onEvent(type, JSON.parse(e.data || "{}"));
      } catch {
        onEvent(type, {});
      }
    });
  });
  return source;
}
