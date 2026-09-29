const PIPELINE = [
  "AI-Generated Code",
  "Static Analysis",
  "Security Detection",
  "Vulnerability Classification",
  "Evidence & Explanation",
  "Risk Assessment",
  "Remediation",
];

const PLANNED = [
  "Multi-engine detection",
  "AST analysis",
  "Taint analysis",
  "LLM-assisted analysis",
  "Dynamic testing",
  "Vulnerability correlation",
  "Dataset generation",
  "AI model comparison",
];

export default function Research() {
  return (
    <div className="mx-auto max-w-4xl space-y-8 px-8 py-10">
      <header>
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-blue-500">
          About the project
        </p>
        <h1 className="mt-2 text-2xl font-bold text-[#0F172A]">Research Objective</h1>
        <blockquote className="mt-4 border-l-2 border-blue-500 pl-4 text-sm leading-relaxed text-slate-300">
          To systematically identify, quantify, and explain security vulnerabilities
          introduced by AI-generated software before it reaches production.
        </blockquote>
      </header>

      <section>
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
          Analysis Pipeline
        </h2>
        <ol className="mt-4 space-y-2">
          {PIPELINE.map((step, index) => (
            <li key={step} className="flex items-center gap-3">
              <span className="flex h-7 w-7 items-center justify-center rounded-full bg-slate-800 text-xs font-semibold text-blue-400">
                {index + 1}
              </span>
              <span className="rounded-md border border-slate-800 bg-slate-900/70 px-3 py-1.5 text-sm text-slate-200">
                {step}
              </span>
              {index < PIPELINE.length - 1 && <span className="text-slate-600">→</span>}
            </li>
          ))}
        </ol>
      </section>

      <section className="rounded-lg border border-slate-800 bg-slate-900/60 p-5">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-200">Future Research</h2>
          <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-slate-400">
            Planned Research Extensions
          </span>
        </div>
        <p className="mt-2 text-xs text-slate-500">
          The following capabilities are planned and not yet implemented in this MVP.
        </p>
        <ul className="mt-4 grid gap-2 sm:grid-cols-2">
          {PLANNED.map((item) => (
            <li key={item} className="flex items-center gap-2 text-sm text-slate-400">
              <span className="text-emerald-500">✓</span>
              {item}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
