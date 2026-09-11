import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { SeverityBadge, formatINR } from "../components/ui";
import { api } from "../services/api";

export default function EventDetailPage() {
  const { eventId } = useParams();
  const [data, setData] = useState(null);
  const [action, setAction] = useState(null);

  useEffect(() => {
    api.event(eventId).then(setData);
  }, [eventId]);

  if (!data) return <div className="text-slate-400">Loading event...</div>;

  const event = data.event || {};
  const insight = data.insight || {};
  const risk = data.risk || {};
  const anomaly = data.anomaly || {};
  const decision = data.decision || {};
  const behavior = data.behavior || {};

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <Link to="/" className="text-xs text-accent">← Back to dashboard</Link>
          <h1 className="mt-1 text-2xl font-semibold">{event.event_id}</h1>
        </div>
        <button
          className="btn-primary"
          onClick={async () => {
            const result = await api.execute(event.event_id);
            setAction(result);
            setData(await api.event(eventId));
          }}
        >
          Execute Recommended Action
        </button>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Info title="Event metadata">
          <Row k="User" v={event.user_id} />
          <Row k="Amount" v={formatINR(event.transaction_amount)} />
          <Row k="Device" v={event.device_id} />
          <Row k="Location" v={event.location} />
          <Row k="Beneficiary" v={event.beneficiary} />
          <Row k="Source" v={event.source} />
        </Info>
        <Info title="Scores">
          <Row k="Anomaly" v={`${anomaly.anomaly_score ?? "—"} / 100`} />
          <Row k="Anomalous" v={anomaly.is_anomaly ? "TRUE" : "FALSE"} />
          <Row k="Risk" v={`${risk.risk_score ?? "—"} / 100`} />
          <div className="mt-2"><SeverityBadge value={risk.severity} /></div>
          <div className="mt-2"><SeverityBadge value={decision.decision} /></div>
        </Info>
        <Info title="Historical behavior">
          <Row k="Normal" v={behavior.normal_range} />
          <Row k="Current" v={behavior.current} />
          <Row k="Deviation" v={behavior.deviation} />
        </Info>
      </div>

      <div className="card p-4">
        <h3 className="mb-3 text-sm font-semibold">Pipeline timeline</h3>
        <div className="flex flex-col gap-2">
          {(data.timeline || []).map((step, i) => (
            <div key={i} className="flex items-center gap-3 text-sm">
              <div className="w-40 font-semibold text-accent">{step.stage}</div>
              <div className="text-slate-500">{step.at}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Info title="RevoralQ AI reasoning">
          <p className="text-sm leading-relaxed text-slate-200">{insight.summary}</p>
          <p className="mt-3 text-sm text-slate-400">{insight.why_it_happened}</p>
          <p className="mt-3 text-sm text-slate-300">{insight.risk_explanation}</p>
          <p className="mt-3 text-sm text-accent">{insight.recommended_action}</p>
          <div className="mt-2 text-xs text-slate-500">Confidence {insight.confidence} · Engine {insight.engine}</div>
        </Info>
        <Info title="Detected patterns">
          <ul className="list-disc pl-5 text-sm">
            {(insight.detected_patterns || []).map((p) => (
              <li key={p}>{p}</li>
            ))}
          </ul>
          <pre className="mt-4 overflow-auto rounded-lg bg-black/30 p-3 text-xs">{JSON.stringify(data.features, null, 2)}</pre>
        </Info>
        <Info title="Raw event">
          <pre className="overflow-auto text-xs">{JSON.stringify(data.raw_event, null, 2)}</pre>
        </Info>
        <Info title="Audit trail">
          <ul className="space-y-2 text-xs text-slate-300">
            {(data.audit || []).map((row) => (
              <li key={row.id}>
                {row.created_at} · {row.actor} · {row.action}
              </li>
            ))}
          </ul>
          {action ? <pre className="mt-3 text-xs">{JSON.stringify(action, null, 2)}</pre> : null}
        </Info>
      </div>
    </div>
  );
}

function Info({ title, children }) {
  return (
    <div className="card p-4">
      <h3 className="mb-3 text-sm font-semibold">{title}</h3>
      {children}
    </div>
  );
}

function Row({ k, v }) {
  return (
    <div className="flex justify-between gap-4 border-b border-white/5 py-1 text-sm">
      <span className="text-slate-500">{k}</span>
      <span className="font-mono text-slate-200">{v || "—"}</span>
    </div>
  );
}
