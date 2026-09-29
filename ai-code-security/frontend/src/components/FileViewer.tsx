import { useEffect, useState } from "react";
import { fetchFile } from "../services/api";
import type { Finding } from "../types";
import SeverityBadge from "./SeverityBadge";

interface Props {
  scanId: string;
  path: string | null;
  findings: Finding[];
  onSelectFinding: (finding: Finding) => void;
}

export default function FileViewer({ scanId, path, findings, onSelectFinding }: Props) {
  const [content, setContent] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!path) {
      setContent(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetchFile(scanId, path)
      .then((response) => {
        if (!cancelled) setContent(response.content);
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Load failed");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [scanId, path]);

  const byLine = new Map<number, Finding[]>();
  for (const finding of findings) {
    const list = byLine.get(finding.line) ?? [];
    list.push(finding);
    byLine.set(finding.line, list);
  }

  if (!path) {
    return (
      <div className="flex h-full items-center justify-center rounded-lg border border-[#E2E8F0] bg-white text-sm text-[#64748B]">
        Select a file to view its source.
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col overflow-hidden rounded-lg border border-slate-800 bg-[#0F172A]">
      <div className="flex items-center justify-between border-b border-[#1E293B] px-4 py-3">
        <p className="mono text-sm text-[#E2E8F0]">{path}</p>
        <span className="text-[11px] text-[#94A3B8]">
          {findings.length} finding{findings.length === 1 ? "" : "s"}
        </span>
      </div>

      {loading && (
        <p className="px-4 py-6 text-xs text-[#94A3B8]">Loading file…</p>
      )}
      {error && <p className="px-4 py-6 text-xs text-[#F87171]">{error}</p>}

      {!loading && !error && content !== null && (
        <div className="flex-1 overflow-auto">
          <table className="w-full border-collapse text-xs">
            <tbody>
              {content.split("\n").map((line, index) => {
                const lineNumber = index + 1;
                const lineFindings = byLine.get(lineNumber) ?? [];
                const highlighted = lineFindings.length > 0;
                return (
                  <tr
                    key={lineNumber}
                    className={[
                      highlighted ? "bg-[rgba(220,38,38,0.12)]" : "",
                      "group",
                    ].join(" ")}
                  >
                    <td className="w-12 select-none border-r border-[#1E293B] px-2 py-0.5 text-right align-top tabular-nums text-[#64748B]">
                      {lineNumber}
                    </td>
                    <td className="w-1.5 p-0">
                      {highlighted && (
                        <button
                          type="button"
                          onClick={() => onSelectFinding(lineFindings[0])}
                          className="h-full w-1.5 bg-[#DC2626] transition-opacity duration-150 hover:opacity-70"
                          title={`Open ${lineFindings[0].title}`}
                        />
                      )}
                    </td>
                    <td className="mono whitespace-pre-wrap break-words px-3 py-0.5 text-[#E2E8F0] group-hover:bg-white/5">
                      {line || " "}
                    </td>
                    <td className="w-40 px-2 py-0.5 align-top">
                      {lineFindings.map((finding) => (
                        <button
                          key={finding.id}
                          type="button"
                          onClick={() => onSelectFinding(finding)}
                          className="mr-1 inline-block"
                          title={finding.title}
                        >
                          <SeverityBadge severity={finding.severity} compact />
                        </button>
                      ))}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
