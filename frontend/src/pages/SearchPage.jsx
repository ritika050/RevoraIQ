import { useEffect, useState } from "react";
import EventTable from "../components/EventTable";
import { api } from "../services/api";

export default function SearchPage() {
  const [filters, setFilters] = useState({
    event_id: "",
    user_id: "",
    severity: "",
    event_type: "",
    date: "",
    anomaly: "",
  });
  const [rows, setRows] = useState([]);

  async function search(e) {
    e?.preventDefault();
    setRows(await api.events(filters));
  }

  useEffect(() => {
    search();
  }, []);

  function set(key, value) {
    setFilters((prev) => ({ ...prev, [key]: value }));
  }

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-semibold">Search & Analysis</h1>
      <form className="card grid gap-3 p-4 md:grid-cols-3" onSubmit={search}>
        <input className="rounded-lg border border-white/10 bg-black/20 px-3 py-2" placeholder="Event ID" value={filters.event_id} onChange={(e) => set("event_id", e.target.value)} />
        <input className="rounded-lg border border-white/10 bg-black/20 px-3 py-2" placeholder="User ID" value={filters.user_id} onChange={(e) => set("user_id", e.target.value)} />
        <select className="rounded-lg border border-white/10 bg-black/20 px-3 py-2" value={filters.severity} onChange={(e) => set("severity", e.target.value)}>
          <option value="">Any risk level</option>
          {["LOW", "MEDIUM", "HIGH", "CRITICAL"].map((x) => (
            <option key={x}>{x}</option>
          ))}
        </select>
        <input className="rounded-lg border border-white/10 bg-black/20 px-3 py-2" placeholder="Event type (payment)" value={filters.event_type} onChange={(e) => set("event_type", e.target.value)} />
        <input className="rounded-lg border border-white/10 bg-black/20 px-3 py-2" type="date" value={filters.date} onChange={(e) => set("date", e.target.value)} />
        <select className="rounded-lg border border-white/10 bg-black/20 px-3 py-2" value={filters.anomaly} onChange={(e) => set("anomaly", e.target.value)}>
          <option value="">Any anomaly status</option>
          <option value="true">Anomaly</option>
          <option value="false">Normal</option>
        </select>
        <button className="btn-primary md:col-span-3">Apply filters</button>
      </form>
      <div className="card p-4">
        <EventTable rows={rows} />
      </div>
    </div>
  );
}
