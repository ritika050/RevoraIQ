import { useMemo } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const COLORS = ["#2ee6d6", "#818cf8", "#f59e0b", "#f43f5e", "#34d399", "#38bdf8"];

export default function Charts({ charts }) {
  const events = charts?.events_over_time || [];
  const risk = charts?.risk_distribution || [];
  const anomalies = charts?.anomaly_trend || [];
  const amounts = charts?.amount_trend || [];
  const users = charts?.risk_by_user || [];
  const sources = charts?.sources || [];

  const pieData = useMemo(
    () => risk.map((d) => ({ name: d.severity, value: d.count })),
    [risk]
  );

  return (
    <div className="grid gap-4 xl:grid-cols-2">
      <ChartCard title="Events over time">
        <AreaChart data={events}>
          <CartesianGrid stroke="rgba(255,255,255,0.06)" />
          <XAxis dataKey="bucket" hide />
          <YAxis stroke="#94a3b8" />
          <Tooltip contentStyle={tooltip} />
          <Area dataKey="count" stroke="#2ee6d6" fill="rgba(46,230,214,0.2)" />
        </AreaChart>
      </ChartCard>
      <ChartCard title="Risk distribution">
        <PieChart>
          <Pie data={pieData} dataKey="value" nameKey="name" outerRadius={80}>
            {pieData.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip contentStyle={tooltip} />
          <Legend />
        </PieChart>
      </ChartCard>
      <ChartCard title="Anomaly trend">
        <BarChart data={anomalies}>
          <CartesianGrid stroke="rgba(255,255,255,0.06)" />
          <XAxis dataKey="bucket" hide />
          <YAxis stroke="#94a3b8" />
          <Tooltip contentStyle={tooltip} />
          <Bar dataKey="count" fill="#f43f5e" radius={4} />
        </BarChart>
      </ChartCard>
      <ChartCard title="Transaction amount trend">
        <AreaChart data={amounts}>
          <CartesianGrid stroke="rgba(255,255,255,0.06)" />
          <XAxis dataKey="bucket" hide />
          <YAxis stroke="#94a3b8" />
          <Tooltip contentStyle={tooltip} />
          <Area dataKey="amount" stroke="#818cf8" fill="rgba(129,140,248,0.2)" />
        </AreaChart>
      </ChartCard>
      <ChartCard title="Risk by user">
        <BarChart data={users}>
          <CartesianGrid stroke="rgba(255,255,255,0.06)" />
          <XAxis dataKey="user_id" stroke="#94a3b8" />
          <YAxis stroke="#94a3b8" />
          <Tooltip contentStyle={tooltip} />
          <Bar dataKey="avg_risk" fill="#f59e0b" radius={4} />
        </BarChart>
      </ChartCard>
      <ChartCard title="Event source distribution">
        <BarChart data={sources}>
          <CartesianGrid stroke="rgba(255,255,255,0.06)" />
          <XAxis dataKey="source" stroke="#94a3b8" />
          <YAxis stroke="#94a3b8" />
          <Tooltip contentStyle={tooltip} />
          <Bar dataKey="count" fill="#38bdf8" radius={4} />
        </BarChart>
      </ChartCard>
    </div>
  );
}

function ChartCard({ title, children }) {
  return (
    <div className="card p-4">
      <h3 className="mb-3 text-sm font-semibold text-white">{title}</h3>
      <div className="h-56">
        <ResponsiveContainer width="100%" height="100%">
          {children}
        </ResponsiveContainer>
      </div>
    </div>
  );
}

const tooltip = {
  background: "#121a2b",
  border: "1px solid rgba(255,255,255,0.1)",
  borderRadius: 12,
};
