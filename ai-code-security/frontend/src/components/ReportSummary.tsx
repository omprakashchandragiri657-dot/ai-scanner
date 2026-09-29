import type { ReactNode } from "react";
import { exportReport } from "../services/api";
import type { ScanResult } from "../types";
import CweChart from "./CweChart";
import FileChart from "./FileChart";
import SeverityChart from "./SeverityChart";
import StatCard from "./StatCard";

export default function ReportSummary({ result }: { result: ScanResult }) {
  const { project, summary, stats } = result;

  return (
    <section className="animate-fade-in space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-[#0F172A]">Security Report</h2>
          <p className="text-sm text-slate-400">
            Project: <span className="font-medium text-slate-200">{project.name}</span>
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-500">
            {new Date(result.generated_at).toLocaleString()}
          </span>
          <button
            type="button"
            onClick={() => exportReport(result)}
            className="rounded-md border border-slate-700 px-3 py-1.5 text-xs font-medium text-slate-300 transition-colors hover:bg-slate-800"
          >
            Export Report ↓
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
        <StatCard label="Files Scanned" value={project.files_scanned} hint={`${stats.total_files} files found`} />
        <StatCard label="Lines Analyzed" value={project.lines_analyzed.toLocaleString()} />
        <StatCard label="Rules Executed" value={stats.rules_executed} />
        <StatCard
          label="Vulnerabilities"
          value={summary.total}
          accent={summary.total > 0 ? "text-red-400" : "text-emerald-400"}
          hint={`${stats.duration_seconds}s scan`}
        />
        <StatCard
          label="Severity Peak"
          value={
            summary.critical > 0
              ? "CRITICAL"
              : summary.high > 0
                ? "HIGH"
                : summary.medium > 0
                  ? "MEDIUM"
                  : summary.low > 0
                    ? "LOW"
                    : "CLEAN"
          }
          accent={
            summary.critical > 0
              ? "text-red-400"
              : summary.high > 0
                ? "text-orange-400"
                : summary.medium > 0
                  ? "text-amber-400"
                  : summary.low > 0
                    ? "text-sky-400"
                    : "text-emerald-400"
          }
        />
      </div>

      <div className="grid grid-cols-4 gap-3">
        <SeverityCount label="Critical" count={summary.critical} className="text-red-400" />
        <SeverityCount label="High" count={summary.high} className="text-orange-400" />
        <SeverityCount label="Medium" count={summary.medium} className="text-amber-400" />
        <SeverityCount label="Low" count={summary.low} className="text-sky-400" />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <ChartCard title="Severity Distribution">
          <SeverityChart summary={summary} />
        </ChartCard>
        <ChartCard title="Vulnerabilities by File">
          <FileChart findings={result.findings} />
        </ChartCard>
        <ChartCard title="CWE Distribution">
          <CweChart findings={result.findings} />
        </ChartCard>
      </div>

      {stats.skipped_files.length > 0 && (
        <p className="text-xs text-slate-500">
          Skipped files (over 2 MB): {stats.skipped_files.join(", ")}
        </p>
      )}
    </section>
  );
}

function SeverityCount({
  label,
  count,
  className,
}: {
  label: string;
  count: number;
  className: string;
}) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/70 px-4 py-3">
      <p className="text-[11px] uppercase tracking-wider text-slate-500">{label}</p>
      <p className={`mt-1 text-xl font-semibold tabular-nums ${className}`}>{count}</p>
    </div>
  );
}

function ChartCard({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/70 p-4">
      <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
        {title}
      </p>
      {children}
    </div>
  );
}
