import { Link } from "react-router-dom";
import FindingsTable from "../components/FindingsTable";
import { useScan } from "../context/ScanContext";

export default function Findings() {
  const { result, selectFinding } = useScan();

  if (!result) {
    return (
      <div className="mx-auto max-w-4xl px-8 py-16 text-center">
        <h1 className="text-xl font-semibold text-[#0F172A]">Findings</h1>
        <p className="mt-3 text-sm text-slate-400">
          Run a project scan first — every finding with file, line and evidence will appear
          here.
        </p>
        <Link
          to="/scanner"
          className="mt-5 inline-block rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500"
        >
          Open Project Scanner
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6 px-8 py-8">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold text-[#0F172A]">Findings</h1>
          <p className="mt-1 text-sm text-slate-400">
            {result.summary.total} vulnerabilities in{" "}
            <span className="mono text-slate-300">{result.project.name}</span> — filter and
            open any row for full evidence and remediation.
          </p>
        </div>
        <div className="flex gap-4 text-xs">
          <span className="text-red-400">{result.summary.critical} critical</span>
          <span className="text-orange-400">{result.summary.high} high</span>
          <span className="text-amber-400">{result.summary.medium} medium</span>
          <span className="text-sky-400">{result.summary.low} low</span>
        </div>
      </header>

      <FindingsTable result={result} onSelect={selectFinding} />
    </div>
  );
}
