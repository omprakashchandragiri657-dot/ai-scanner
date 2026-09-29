import { useEffect, type ReactNode } from "react";
import type { Finding } from "../types";
import SeverityBadge from "./SeverityBadge";

export default function FindingDetail({
  finding,
  onClose,
}: {
  finding: Finding;
  onClose: () => void;
}) {
  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex justify-end bg-black/60"
      onClick={onClose}
      role="presentation"
    >
      <div
        className="animate-fade-in flex h-full w-full max-w-2xl flex-col overflow-y-auto border-l border-slate-700 bg-slate-900 shadow-2xl"
        onClick={(event) => event.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label={finding.title}
      >
        <header className="sticky top-0 z-10 border-b border-slate-800 bg-slate-900 px-6 py-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-3">
                <h2 className="text-lg font-semibold text-[#0F172A]">{finding.title}</h2>
                <SeverityBadge severity={finding.severity} />
              </div>
              <p className="mt-1 flex items-center gap-3 text-xs text-slate-400">
                <span className="mono">{finding.cwe}</span>
                <span>Confidence: {finding.confidence}%</span>
                <span className="mono text-slate-500">{finding.id}</span>
              </p>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="rounded-md px-2 py-1 text-slate-500 transition-colors hover:bg-slate-800 hover:text-slate-200"
              aria-label="Close details"
            >
              ✕
            </button>
          </div>
        </header>

        <div className="space-y-6 px-6 py-5 text-sm">
          <Section title="Location">
            <p className="mono text-slate-300">
              {finding.file}
              <span className="text-slate-500"> : Line {finding.line}</span>
            </p>
            <p className="mt-1 text-xs text-slate-500">
              Language: {finding.language} · Detector: {finding.detector}
            </p>
          </Section>

          <Section title="Vulnerable Code">
            <pre className="mono overflow-x-auto rounded-lg border border-[#1E293B] bg-[#0F172A] p-3 text-xs leading-relaxed">
              {finding.context.map((entry) => (
                <div
                  key={entry.line}
                  className={
                    entry.highlight
                      ? "-mx-3 border-l-2 border-[#DC2626] bg-[rgba(220,38,38,0.12)] px-3 text-[#E2E8F0]"
                      : "text-[#94A3B8]"
                  }
                >
                  <span className="mr-4 inline-block w-8 select-none text-right tabular-nums text-[#64748B]">
                    {entry.line}
                  </span>
                  {entry.text || " "}
                </div>
              ))}
            </pre>
          </Section>

          <Section title="Why Is This Vulnerable?">
            <p className="leading-relaxed text-slate-300">{finding.description}</p>
          </Section>

          <Section title="Detection Evidence">
            <ol className="space-y-1">
              {finding.flow.map((step, index) => (
                <li key={`${step}-${index}`} className="flex items-center gap-2 text-xs">
                  <span className="flex h-5 w-5 items-center justify-center rounded-full bg-indigo-500/20 text-[10px] font-semibold text-indigo-300">
                    {index + 1}
                  </span>
                  <span className="mono text-slate-300">{step}</span>
                  {index < finding.flow.length - 1 && (
                    <span className="ml-3 text-slate-600">↓</span>
                  )}
                </li>
              ))}
            </ol>
            <p className="mt-2 rounded-md border border-slate-800 bg-slate-950/60 px-3 py-2 text-xs leading-relaxed text-slate-400">
              {finding.evidence}
            </p>
          </Section>

          <Section title="Recommended Fix">
            <p className="mb-2 text-xs font-medium text-[#0F766E]">
              Recommended remediation
            </p>
            <div className="grid gap-3 md:grid-cols-2">
              <CodeBlock label="Vulnerable" tone="bad" code={finding.remediation.vulnerable} />
              <CodeBlock label="Recommended" tone="good" code={finding.remediation.secure} />
            </div>
            <p className="mt-2 text-xs leading-relaxed text-slate-400">
              {finding.remediation.explanation}
            </p>
            <p className="mt-2 text-xs text-slate-400">
              <span className="font-medium text-slate-300">Recommendation:</span>{" "}
              {finding.recommendation}
            </p>
          </Section>
        </div>
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section>
      <h3 className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
        {title}
      </h3>
      {children}
    </section>
  );
}

function CodeBlock({
  label,
  tone,
  code,
}: {
  label: string;
  tone: "bad" | "good";
  code: string;
}) {
  if (!code) return null;
  return (
    <div className="rounded-lg border border-[#1E293B] bg-[#0F172A] p-3">
      <p
        className={[
          "mb-1.5 text-[10px] font-semibold uppercase tracking-wider",
          tone === "bad" ? "text-[#F87171]" : "text-[#5EEAD4]",
        ].join(" ")}
      >
        {label}
      </p>
      <pre className="mono whitespace-pre-wrap text-[11px] leading-relaxed text-[#E2E8F0]">
        {code}
      </pre>
    </div>
  );
}
