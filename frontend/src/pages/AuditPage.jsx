import { useEffect, useState } from "react";
import { api } from "../services/api";

export default function AuditPage() {
  const [rows, setRows] = useState([]);
  useEffect(() => {
    api.audit().then(setRows);
  }, []);
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Audit logs</h1>
      <div className="card overflow-x-auto p-4">
        <table className="min-w-full text-left text-sm">
          <thead className="text-xs uppercase text-slate-500">
            <tr>
              <th className="px-3 py-2">Time</th>
              <th className="px-3 py-2">Actor</th>
              <th className="px-3 py-2">Action</th>
              <th className="px-3 py-2">Event</th>
              <th className="px-3 py-2">Details</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id} className="border-t border-white/5">
                <td className="px-3 py-2 font-mono text-xs text-slate-400">{row.created_at}</td>
                <td className="px-3 py-2">{row.actor}</td>
                <td className="px-3 py-2">{row.action}</td>
                <td className="px-3 py-2 font-mono text-accent">{row.event_id || "—"}</td>
                <td className="px-3 py-2 text-xs text-slate-400">{row.details}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
