import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Finding, Severity } from "../types";
import { SEVERITY_COLOR } from "./SeverityBadge";

interface Row {
  file: string;
  count: number;
  severity: Severity;
}

const ORDER: Record<Severity, number> = {
  CRITICAL: 0,
  HIGH: 1,
  MEDIUM: 2,
  LOW: 3,
};

export default function FileChart({ findings }: { findings: Finding[] }) {
  const byFile = new Map<string, Row>();
  for (const finding of findings) {
    const current = byFile.get(finding.file);
    if (!current) {
      byFile.set(finding.file, {
        file: finding.file,
        count: 1,
        severity: finding.severity,
      });
    } else {
      current.count += 1;
      if (ORDER[finding.severity] < ORDER[current.severity]) {
        current.severity = finding.severity;
      }
    }
  }

  const data = [...byFile.values()]
    .sort((a, b) => b.count - a.count || a.file.localeCompare(b.file))
    .slice(0, 8)
    .map((row) => ({
      ...row,
      short: row.file.length > 26 ? `…${row.file.slice(-25)}` : row.file,
    }));

  if (data.length === 0) {
    return <p className="py-10 text-center text-sm text-slate-500">No findings to chart.</p>;
  }

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 4, right: 16, left: 4, bottom: 4 }}>
          <CartesianGrid horizontal={false} stroke="#E2E8F0" />
          <XAxis
            type="number"
            allowDecimals={false}
            tick={{ fill: "#64748B", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            type="category"
            dataKey="short"
            width={170}
            tick={{ fill: "#64748B", fontSize: 10 }}
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
          <Bar dataKey="count" radius={[0, 4, 4, 0]}>
            {data.map((row) => (
              <Cell key={row.file} fill={SEVERITY_COLOR[row.severity]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
