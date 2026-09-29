import type { Structure } from "../types";

export interface ProgressState {
  file: string;
  index: number;
  total: number;
  percent: number;
}

interface Props {
  steps: string[];
  progress: ProgressState | null;
  structure: Structure | null;
}

export default function ScanningScreen({ steps, progress, structure }: Props) {
  const scanning = progress !== null;

  return (
    <div className="animate-fade-in rounded-xl border border-slate-800 bg-slate-900/70 p-6">
      <div className="flex items-center gap-3">
        <span className="scan-pulse h-2.5 w-2.5 rounded-full bg-blue-500" />
        <h2 className="text-sm font-semibold tracking-wide text-slate-100">
          Scanning Project
        </h2>
        {structure && (
          <span className="text-xs text-slate-500">
            {structure.name} · {structure.source_files} source files
          </span>
        )}
      </div>

      <ul className="mt-4 space-y-1.5">
        {steps.map((step, index) => (
          <li
            key={`${step}-${index}`}
            className="animate-fade-in flex items-center gap-2 text-xs text-slate-300"
          >
            <span className="text-emerald-400">✓</span>
            <span>{step}</span>
          </li>
        ))}
        {scanning && (
          <li className="flex items-center gap-2 text-xs text-slate-400">
            <span className="scan-pulse text-blue-400">●</span>
            <span>Scanning files…</span>
          </li>
        )}
      </ul>

      {progress && (
        <div className="mt-5">
          <div className="flex items-baseline justify-between text-xs">
            <span className="mono truncate text-slate-300" title={progress.file}>
              {progress.file}
            </span>
            <span className="tabular-nums text-slate-500">
              {progress.index}/{progress.total} · {progress.percent}%
            </span>
          </div>
          <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-800">
            <div
              className="h-full rounded-full bg-gradient-to-r from-blue-600 to-indigo-500 transition-[width] duration-200"
              style={{ width: `${progress.percent}%` }}
            />
          </div>
        </div>
      )}

      {structure && (
        <div className="mt-5 grid grid-cols-2 gap-3 border-t border-slate-800 pt-4 text-xs sm:grid-cols-4">
          <Meta label="Files Found" value={structure.files_found} />
          <Meta label="Source Files" value={structure.source_files} />
          <Meta label="Ignored" value={structure.ignored} />
          <Meta
            label="Languages"
            value={Object.entries(structure.by_language)
              .map(([lang, count]) => `${count} ${lang}`)
              .join(", ")}
          />
        </div>
      )}
    </div>
  );
}

function Meta({ label, value }: { label: string; value: string | number }) {
  return (
    <div>
      <p className="text-[10px] uppercase tracking-wider text-slate-500">{label}</p>
      <p className="mt-0.5 text-slate-200">{value}</p>
    </div>
  );
}
