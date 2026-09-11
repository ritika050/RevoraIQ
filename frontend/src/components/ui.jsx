export function SeverityBadge({ value }) {
  const key = String(value || "n/a").toUpperCase();
  const styles = {
    LOW: "bg-emerald-500/15 text-emerald-300 border-emerald-400/30",
    MEDIUM: "bg-amber-500/15 text-amber-300 border-amber-400/30",
    HIGH: "bg-orange-500/20 text-orange-300 border-orange-400/30",
    CRITICAL: "bg-rose-500/20 text-rose-300 border-rose-400/40",
    YES: "bg-rose-500/20 text-rose-300 border-rose-400/30",
    NO: "bg-slate-500/20 text-slate-300 border-white/10",
    BLOCK: "bg-rose-500/20 text-rose-200 border-rose-400/30",
    FLAG: "bg-orange-500/20 text-orange-200 border-orange-400/30",
    MONITOR: "bg-amber-500/15 text-amber-200 border-amber-400/30",
    ALLOW: "bg-emerald-500/15 text-emerald-200 border-emerald-400/30",
    ACTIONED: "bg-cyan-500/15 text-cyan-200 border-cyan-400/30",
  };
  return (
    <span className={`chip border ${styles[key] || "bg-white/10 text-slate-300 border-white/10"}`}>
      {key}
    </span>
  );
}

export function MetricCard({ label, value, hint }) {
  return (
    <div className="card p-4">
      <div className="text-xs uppercase tracking-[0.18em] text-slate-400">{label}</div>
      <div className="mt-2 font-mono text-3xl font-semibold text-white">{value}</div>
      {hint ? <div className="mt-1 text-xs text-slate-500">{hint}</div> : null}
    </div>
  );
}

export function formatINR(amount) {
  if (amount == null) return "—";
  return `₹${Number(amount).toLocaleString("en-IN")}`;
}

export function formatTime(ts) {
  if (!ts) return "—";
  try {
    return new Date(ts).toLocaleTimeString();
  } catch {
    return ts;
  }
}
