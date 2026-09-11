import { Link } from "react-router-dom";

export default function AlertPanel({ alerts, onExecute, onDismiss }) {
  if (!alerts?.length) {
    return (
      <div className="card p-4 text-sm text-slate-400">
        No open high-risk alerts. The incident panel populates when risk is HIGH or CRITICAL.
      </div>
    );
  }
  return (
    <div className="space-y-3">
      {alerts.map((alert) => (
        <div key={alert.id || alert.event_id} className="card border-rose-500/30 p-4">
          <div className="text-sm font-semibold text-rose-300">🚨 {alert.title || "CRITICAL RISK DETECTED"}</div>
          <div className="mt-2 grid gap-1 text-sm text-slate-300">
            <div>User: {alert.user_id}</div>
            <div>Risk Score: {alert.risk_score}</div>
          </div>
          <ul className="mt-2 list-disc pl-5 text-sm text-slate-300">
            {(alert.reasons || []).map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
          <div className="mt-3 rounded-lg bg-black/20 p-3 text-sm text-slate-200">
            <div className="text-xs uppercase tracking-wide text-slate-500">AI Recommendation</div>
            {alert.recommended_action || alert.message}
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            <button className="btn-danger" onClick={() => onExecute(alert.event_id)}>
              Execute Action
            </button>
            <Link className="btn-ghost" to={`/events/${alert.event_id}`}>
              View Details
            </Link>
            <button className="btn-ghost" onClick={() => onDismiss(alert.event_id)}>
              Dismiss
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
