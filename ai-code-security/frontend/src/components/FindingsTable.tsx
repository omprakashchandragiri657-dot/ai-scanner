import { useMemo, useState } from "react";
import type { Finding, ScanResult } from "../types";
import SeverityBadge from "./SeverityBadge";

interface Props {
  result: ScanResult;
  onSelect: (finding: Finding) => void;
}

export default function FindingsTable({ result, onSelect }: Props) {
  const [query, setQuery] = useState("");
  const [severity, setSeverity] = useState("ALL");
  const [language, setLanguage] = useState("ALL");
  const [cwe, setCwe] = useState("ALL");
  const [file, setFile] = useState("ALL");

  const options = useMemo(() => {
    const cwes = new Set<string>();
    const files = new Set<string>();
    const languages = new Set<string>();
    for (const finding of result.findings) {
      cwes.add(finding.cwe);
      files.add(finding.file);
      languages.add(finding.language);
    }
    return {
      cwes: [...cwes].sort(),
      files: [...files].sort(),
      languages: [...languages].sort(),
    };
  }, [result.findings]);

  const filtered = result.findings.filter((finding) => {
    if (severity !== "ALL" && finding.severity !== severity) return false;
    if (language !== "ALL" && finding.language !== language) return false;
    if (cwe !== "ALL" && finding.cwe !== cwe) return false;
    if (file !== "ALL" && finding.file !== file) return false;
    if (query.trim()) {
      const haystack = [
        finding.title,
        finding.file,
        finding.cwe,
        finding.description,
        finding.id,
      ]
        .join(" ")
        .toLowerCase();
      if (!haystack.includes(query.trim().toLowerCase())) return false;
    }
    return true;
  });

  const selectClass =
    "rounded-md border border-slate-700 bg-slate-900 px-2 py-1.5 text-xs text-slate-300 outline-none focus:border-blue-500";

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <input
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search findings…"
          className="rounded-md border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs text-slate-200 outline-none focus:border-blue-500"
        />
        <select value={severity} onChange={(e) => setSeverity(e.target.value)} className={selectClass}>
          <option value="ALL">Severity: All</option>
          <option value="CRITICAL">Critical</option>
          <option value="HIGH">High</option>
          <option value="MEDIUM">Medium</option>
          <option value="LOW">Low</option>
        </select>
        <select value={language} onChange={(e) => setLanguage(e.target.value)} className={selectClass}>
          <option value="ALL">Language: All</option>
          {options.languages.map((entry) => (
            <option key={entry} value={entry}>
              {entry}
            </option>
          ))}
        </select>
        <select value={cwe} onChange={(e) => setCwe(e.target.value)} className={selectClass}>
          <option value="ALL">CWE: All</option>
          {options.cwes.map((entry) => (
            <option key={entry} value={entry}>
              {entry}
            </option>
          ))}
        </select>
        <select value={file} onChange={(e) => setFile(e.target.value)} className={selectClass}>
          <option value="ALL">File: All</option>
          {options.files.map((entry) => (
            <option key={entry} value={entry}>
              {entry}
            </option>
          ))}
        </select>
        <span className="ml-auto text-xs text-slate-500">
          {filtered.length} of {result.findings.length}
        </span>
      </div>

      <div className="overflow-x-auto rounded-lg border border-slate-800">
        <table className="w-full text-left text-xs">
          <thead className="border-b border-[#E2E8F0] bg-[#F8FAFC] text-[11px] uppercase tracking-wider text-slate-500">
            <tr>
              <th className="px-4 py-3 font-medium">Severity</th>
              <th className="px-4 py-3 font-medium">Vulnerability</th>
              <th className="px-4 py-3 font-medium">CWE</th>
              <th className="px-4 py-3 font-medium">File</th>
              <th className="px-4 py-3 font-medium">Line</th>
              <th className="px-4 py-3 font-medium">Confidence</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/80">
            {filtered.map((finding) => (
              <tr
                key={finding.id}
                onClick={() => onSelect(finding)}
                className="cursor-pointer bg-slate-950/40 transition-colors hover:bg-slate-800/60"
              >
                <td className="px-4 py-2.5">
                  <SeverityBadge severity={finding.severity} compact />
                </td>
                <td className="px-4 py-2.5">
                  <span className="font-medium text-slate-200">{finding.title}</span>
                  <span className="ml-2 text-[10px] text-slate-600">{finding.id}</span>
                </td>
                <td className="mono px-4 py-2.5 text-slate-400">{finding.cwe}</td>
                <td className="mono max-w-56 truncate px-4 py-2.5 text-slate-400" title={finding.file}>
                  {finding.file}
                </td>
                <td className="px-4 py-2.5 tabular-nums text-slate-400">{finding.line}</td>
                <td className="px-4 py-2.5 tabular-nums text-slate-400">
                  {finding.confidence}%
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-slate-500">
                  No findings match the current filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
