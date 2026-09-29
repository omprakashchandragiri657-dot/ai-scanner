import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Finding } from "../types";

export default function CweChart({ findings }: { findings: Finding[] }) {
  const byCwe = new Map<string, number>();
  for (const finding of findings) {
    byCwe.set(finding.cwe, (byCwe.get(finding.cwe) ?? 0) + 1);
  }
  const data = [...byCwe.entries()]
    .map(([cwe, count]) => ({ cwe, count }))
    .sort((a, b) => b.count - a.count || a.cwe.localeCompare(b.cwe));

  if (data.length === 0) {
    return <p className="py-10 text-center text-sm text-slate-500">No findings to chart.</p>;
  }

  return (
    <div className="h-56">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
          <CartesianGrid vertical={false} stroke="#E2E8F0" />
          <XAxis
            dataKey="cwe"
            tick={{ fill: "#64748B", fontSize: 10 }}
            axisLine={{ stroke: "#E2E8F0" }}
            tickLine={false}
            interval={0}
            angle={-24}
            textAnchor="end"
            height={46}
          />
          <YAxis
            allowDecimals={false}
            tick={{ fill: "#64748B", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            cursor={{ fill: "rgba(15, 23, 42, 0.04)" }}
            contentStyle={{
              background: "#FFFFFF",
              border: "1px solid #E2E8F0",
              borderRadius: 8,
              fontSize: 12,
              color: "#334155",
              boxShadow: "0 1px 3px rgba(15,23,42,0.06)",
            }}
          />
          <Bar dataKey="count" fill="#2563EB" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}