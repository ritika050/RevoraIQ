import { useEffect, useState } from "react";
import { api } from "../services/api";

export default function AdminPage() {
  const [status, setStatus] = useState(null);
  useEffect(() => {
    api.admin().then(setStatus);
    const t = setInterval(() => api.admin().then(setStatus), 4000);
    return () => clearInterval(t);
  }, []);

  const items = [
    ["System health", status?.system],
    ["API status", status?.api],
    ["Database status", status?.database],
    ["Event processor", status?.event_processor],
    ["AI engine", status?.ai_engine],
    ["Last processed event", status?.last_processed_event],
    ["Total events processed", status?.total_events_processed],
    ["Failed events", status?.failed_events],
  ];

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-semibold">Admin / System</h1>
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {items.map(([label, value]) => (
          <div key={label} className="card p-4">
            <div className="text-xs uppercase tracking-widest text-slate-500">{label}</div>
            <div className="mt-2 font-mono text-lg text-white">{value ?? "—"}</div>
          </div>
        ))}
      </div>
      <div className="card p-4">
        <h3 className="mb-2 text-sm font-semibold">Queue status</h3>
        <pre className="text-xs text-slate-300">{JSON.stringify(status?.queue || {}, null, 2)}</pre>
      </div>
    </div>
  );
}
