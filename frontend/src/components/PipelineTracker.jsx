const STAGES = [
  "EVENT",
  "VALIDATED",
  "PROCESSED",
  "ANOMALY DETECTED",
  "RISK SCORED",
  "AI ANALYZED",
  "DECISION",
  "ACTION",
];

const STAGE_MAP = {
  ingesting: 0,
  validating: 1,
  queued: 1,
  processed: 2,
  features: 2,
  anomaly: 3,
  behavior: 3,
  risk: 4,
  ai: 5,
  decision: 6,
  action: 7,
  complete: 7,
};

export default function PipelineTracker({ stage, message }) {
  const active = STAGE_MAP[stage] ?? -1;
  return (
    <div className="card p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-white">Live pipeline</h3>
        <span className="text-xs text-slate-400">{message || "Waiting for events"}</span>
      </div>
      <div className="grid grid-cols-2 gap-2 md:grid-cols-4 xl:grid-cols-8">
        {STAGES.map((label, index) => (
          <div
            key={label}
            className={`rounded-lg border px-2 py-2 text-center text-[11px] font-medium ${
              index <= active
                ? "border-accent/40 bg-accent/10 text-accent"
                : "border-white/10 text-slate-500"
            }`}
          >
            {label}
          </div>
        ))}
      </div>
    </div>
  );
}
