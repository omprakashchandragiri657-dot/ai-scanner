import type { ReactNode } from "react";

export default function About() {
  return (
    <div className="mx-auto max-w-3xl space-y-8 px-8 py-10">
      <header>
        <h1 className="text-2xl font-bold text-[#0F172A]">About</h1>
        <p className="mt-2 text-sm leading-relaxed text-slate-400">
          The AI Code Security Analyzer is a static source-code security analyzer built for
          a cybersecurity research project on AI-generated software. It takes an entire
          project, scans its source files with a modular rule engine, and explains every
          finding with evidence and remediation guidance.
        </p>
      </header>

      <section className="grid gap-3 sm:grid-cols-2">
        <Card title="Static analysis only">
          Uploaded projects are extracted, read and analyzed — never executed on the host
          system.
        </Card>
        <Card title="Supported languages">
          Python (.py), JavaScript (.js/.jsx), TypeScript (.ts/.tsx) and Java (.java).
        </Card>
        <Card title="Detection coverage">
          SQL injection, command injection, code injection, insecure deserialization,
          hardcoded credentials, path traversal, XSS, weak cryptography and more — each
          mapped to a CWE identifier.
        </Card>
        <Card title="Architecture">
          FastAPI backend with a pluggable <span className="mono">SecurityRule</span> engine
          (ready for Semgrep, CodeQL, LLM and taint-analysis extensions); React + TypeScript
          + Tailwind frontend with Recharts visualizations.
        </Card>
      </section>

      <section className="rounded-lg border border-slate-800 bg-slate-900/60 p-5 text-sm text-slate-400">
        <h2 className="text-sm font-semibold text-slate-200">Disclaimer</h2>
        <p className="mt-2 leading-relaxed">
          Detection results are heuristic and intended for research and demonstration.
          Findings should be reviewed by a human before acting. The built-in demo project
          intentionally contains vulnerable code for security testing.
        </p>
      </section>
    </div>
  );
}

function Card({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
      <h2 className="text-sm font-semibold text-slate-200">{title}</h2>
      <p className="mt-1.5 text-xs leading-relaxed text-slate-400">{children}</p>
    </div>
  );
}
