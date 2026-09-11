import { useEffect, useState } from "react";
import AlertPanel from "../components/AlertPanel";
import Charts from "../components/Charts";
import EventTable from "../components/EventTable";
import PipelineTracker from "../components/PipelineTracker";
import { MetricCard } from "../components/ui";
import { api } from "../services/api";

export default function Dashboard({ pipeline, onBusy }) {
  const [metrics, setMetrics] = useState(null);
  const [events, setEvents] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [busy, setBusy] = useState("");
  const [actionLog, setActionLog] = useState(null);

  async function refresh() {
    const [m, e, a] = await Promise.all([api.metrics(), api.events(), api.alerts()]);
    setMetrics(m);
    setEvents(e);
    setAlerts(a.filter((x) => x.status === "open"));
  }

  useEffect(() => {
    refresh().catch(console.error);
  }, [pipeline.tick]);

  async function run(label, fn) {
    setBusy(label);
    onBusy?.(true);
    try {
      const result = await fn();
      if (result?.action || result?.results) {
        const last = result.action || result.results?.[result.results.length - 1]?.action;
        if (last) setActionLog(last);
      }
      await refresh();
    } finally {
      setBusy("");
      onBusy?.(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-end">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">RevoralQ Intelligence Dashboard</h1>
          <p className="mt-1 text-slate-400">Ingest, detect, explain, decide, and act — in real time.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button className="btn-ghost" disabled={!!busy} onClick={() => run("normal", () => api.generate("normal"))}>
            Generate Normal Event
          </button>
          <button className="btn-ghost" disabled={!!busy} onClick={() => run("suspicious", () => api.generate("suspicious"))}>
            Generate Suspicious Event
          </button>
          <button className="btn-ghost" disabled={!!busy} onClick={() => run("burst", () => api.generate("burst"))}>
            Generate Burst of Events
          </button>
          <button className="btn-ghost" disabled={!!busy} onClick={() => run("scenario", () => api.scenario())}>
            Run Demo Scenario
          </button>
          <button className="btn-primary" disabled={!!busy} onClick={() => run("demo", () => api.demo())}>
            DEMO MODE
          </button>
        </div>
      </div>

      <PipelineTracker stage={pipeline.stage} message={pipeline.message} />

      {pipeline.demoMessage ? (
        <div className="rounded-xl border border-accent/30 bg-accent/10 px-4 py-3 text-sm text-accent">
          {pipeline.demoMessage}
        </div>
      ) : null}

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-6">
        <MetricCard label="Total Events" value={metrics?.total_events ?? "—"} />
        <MetricCard label="Events / Minute" value={metrics?.events_per_minute ?? "—"} />
        <MetricCard label="Anomalies Detected" value={metrics?.anomalies_detected ?? "—"} />
        <MetricCard label="High Risk Events" value={metrics?.high_risk_events ?? "—"} />
        <MetricCard label="Critical Events" value={metrics?.critical_events ?? "—"} />
        <MetricCard label="Actions Triggered" value={metrics?.actions_triggered ?? "—"} />
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <div className="xl:col-span-2 card p-4">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold">Live event feed</h2>
            <span className="text-xs text-slate-500">{busy ? `Working: ${busy}` : "Streaming"}</span>
          </div>
          <EventTable rows={events.slice(0, 18)} />
        </div>
        <div className="space-y-4">
          <AlertPanel
            alerts={alerts}
            onExecute={async (id) => {
              const result = await api.execute(id);
              setActionLog(result);
              await refresh();
            }}
            onDismiss={async (id) => {
              await api.dismiss(id);
              await refresh();
            }}
          />
          {actionLog ? (
            <div className="card p-4 font-mono text-xs text-slate-300">
              <div className="mb-2 text-sm font-semibold text-white">ACTION EXECUTED</div>
              <pre className="whitespace-pre-wrap">{JSON.stringify(actionLog, null, 2)}</pre>
            </div>
          ) : null}
        </div>
      </div>

      <Charts charts={metrics?.charts} />
    </div>
  );
}
