import { Link } from "react-router-dom";
import { formatINR, formatTime, SeverityBadge } from "./ui";

export default function EventTable({ rows, onSelect }) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-left text-sm">
        <thead className="text-xs uppercase tracking-wider text-slate-500">
          <tr>
            {["Time", "Event ID", "User", "Source", "Amount", "Anomaly", "Risk", "Severity", "Decision", "Status"].map(
              (h) => (
                <th key={h} className="px-3 py-2 font-medium">
                  {h}
                </th>
              )
            )}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={row.event_id}
              className="cursor-pointer border-t border-white/5 hover:bg-white/5"
              onClick={() => onSelect?.(row.event_id)}
            >
              <td className="px-3 py-2 font-mono text-xs text-slate-400">{formatTime(row.created_at)}</td>
              <td className="px-3 py-2 font-mono text-accent">
                <Link to={`/events/${row.event_id}`}>{row.event_id}</Link>
              </td>
              <td className="px-3 py-2">{row.user_id}</td>
              <td className="px-3 py-2 capitalize">{row.source}</td>
              <td className="px-3 py-2 font-mono">{formatINR(row.transaction_amount)}</td>
              <td className="px-3 py-2">
                <SeverityBadge value={row.anomaly ? "YES" : "NO"} />
              </td>
              <td className="px-3 py-2 font-mono">{row.risk_score ?? "—"}</td>
              <td className="px-3 py-2">
                <SeverityBadge value={row.severity} />
              </td>
              <td className="px-3 py-2">
                <SeverityBadge value={row.decision} />
              </td>
              <td className="px-3 py-2 uppercase text-xs text-slate-400">{row.status}</td>
            </tr>
          ))}
          {!rows.length ? (
            <tr>
              <td colSpan={10} className="px-3 py-8 text-center text-slate-500">
                No events yet. Generate one or run Demo Mode.
              </td>
            </tr>
          ) : null}
        </tbody>
      </table>
    </div>
  );
}
