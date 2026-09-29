import { useRef, useState, type ChangeEvent, type DragEvent } from "react";
import { zipFolderFiles, formatSize, MAX_ZIP_BYTES } from "../utils/zipFolder";

interface Props {
  onFileSelected: (file: File) => void;
  onDemo: () => void;
  error: string | null;
  busy: boolean;
}

export default function UploadPanel({ onFileSelected, onDemo, error, busy }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [pasteOpen, setPasteOpen] = useState(false);
  const [zipping, setZipping] = useState(false);

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragging(false);
    const file = event.dataTransfer.files?.[0];
    if (file) onFileSelected(file);
  }

  async function handleFolderSelect(event: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files ?? []);
    event.target.value = "";
    if (files.length === 0) return;
    setZipping(true);
    try {
      onFileSelected(await zipFolderFiles(files));
    } catch (err) {
      alert(err instanceof Error ? err.message : "Could not compress the folder.");
    } finally {
      setZipping(false);
    }
  }

  return (
    <div className="space-y-4">
      <div
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => !busy && inputRef.current?.click()}
        className={[
          "cursor-pointer rounded-xl border-2 border-dashed px-6 py-12 text-center transition-colors",
          dragging
            ? "border-blue-500 bg-blue-500/10"
            : "border-slate-700 bg-slate-900/60 hover:border-slate-500 hover:bg-slate-900",
        ].join(" ")}
      >
        <input
          ref={inputRef}
          type="file"
          className="hidden"
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) onFileSelected(file);
            event.target.value = "";
          }}
        />
        <input
          ref={folderInputRef}
          type="file"
          multiple
          className="hidden"
          onChange={handleFolderSelect}
          {...({ webkitdirectory: "", directory: "" } as unknown as Record<
            string,
            string
          >)}
        />
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-slate-800 text-2xl text-slate-400">
          ⬆
        </div>
        <p className="mt-4 text-sm font-medium text-slate-200">Upload Project</p>
        <p className="mt-1 text-xs text-slate-500">
          Drop a <span className="mono text-slate-400">project.zip</span> here, click to
          browse any file, or use Upload Folder (max {formatSize(MAX_ZIP_BYTES)})
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={() => !busy && !zipping && folderInputRef.current?.click()}
          disabled={busy || zipping}
          className="rounded-md border border-slate-700 px-4 py-2 text-sm font-medium text-slate-300 transition-colors hover:bg-slate-800 disabled:opacity-50"
        >
          {zipping ? "Compressing…" : "Upload Folder"}
        </button>
        <button
          type="button"
          onClick={onDemo}
          disabled={busy}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-500 disabled:opacity-50"
        >
          Try Demo Project
        </button>
        <button
          type="button"
          onClick={() => setPasteOpen(true)}
          disabled={busy}
          className="rounded-md border border-slate-700 px-4 py-2 text-sm font-medium text-slate-300 transition-colors hover:bg-slate-800 disabled:opacity-50"
        >
          Paste Code
        </button>
        <p className="text-xs text-slate-500">
          Scans the whole project recursively — not just a single snippet.
        </p>
      </div>

      {error && (
        <div className="animate-fade-in rounded-md border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-300">
          {error}
        </div>
      )}

      {pasteOpen && <PasteCodeModal onClose={() => setPasteOpen(false)} />}
    </div>
  );
}

import { analyzeCode } from "../services/api";
import type { Finding, Summary } from "../types";
import SeverityBadge from "./SeverityBadge";

const LANGUAGES = [
  { value: "python", label: "Python" },
  { value: "javascript", label: "JavaScript" },
  { value: "typescript", label: "TypeScript" },
  { value: "java", label: "Java" },
];

function PasteCodeModal({ onClose }: { onClose: () => void }) {
  const [language, setLanguage] = useState("python");
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [findings, setFindings] = useState<Finding[] | null>(null);
  const [summary, setSummary] = useState<Summary | null>(null);

  async function run() {
    setBusy(true);
    setError(null);
    try {
      const result = await analyzeCode(code, language);
      setFindings(result.findings);
      setSummary(result.summary);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/70 px-4">
      <div className="animate-fade-in w-full max-w-3xl rounded-lg border border-slate-700 bg-slate-900 shadow-2xl">
        <div className="flex items-center justify-between border-b border-slate-800 px-5 py-3">
          <h3 className="text-sm font-semibold text-slate-100">Paste Code</h3>
          <button
            type="button"
            onClick={onClose}
            className="text-slate-500 hover:text-slate-200"
            aria-label="Close"
          >
            ✕
          </button>
        </div>
        <div className="space-y-3 px-5 py-4">
          <div className="flex items-center gap-3">
            <label className="text-xs text-slate-400" htmlFor="paste-language">
              Language
            </label>
            <select
              id="paste-language"
              value={language}
              onChange={(event) => setLanguage(event.target.value)}
              className="rounded border border-slate-700 bg-slate-800 px-2 py-1 text-xs text-slate-200"
            >
              {LANGUAGES.map((entry) => (
                <option key={entry.value} value={entry.value}>
                  {entry.label}
                </option>
              ))}
            </select>
          </div>
          <textarea
            value={code}
            onChange={(event) => setCode(event.target.value)}
            rows={10}
            spellCheck={false}
            placeholder={
              'Paste source code here…\n\nquery = f"SELECT * FROM users WHERE id={uid}"\ncursor.execute(query)'
            }
            className="mono w-full rounded-md border border-slate-700 bg-slate-950 p-3 text-xs text-slate-200 outline-none focus:border-blue-500"
          />
          {error && <p className="text-xs text-red-400">{error}</p>}
          {summary && (
            <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400">
              <span>
                Findings: <strong className="text-slate-200">{summary.total}</strong>
              </span>
              <SeverityBadge severity="CRITICAL" compact />
              <span>{summary.critical}</span>
              <SeverityBadge severity="HIGH" compact />
              <span>{summary.high}</span>
            </div>
          )}
          {findings && findings.length > 0 && (
            <ul className="max-h-40 space-y-1 overflow-y-auto text-xs">
              {findings.map((finding) => (
                <li key={finding.id} className="flex items-center gap-2 text-slate-300">
                  <SeverityBadge severity={finding.severity} compact />
                  <span>{finding.title}</span>
                  <span className="text-slate-500">
                    {finding.file}:{finding.line}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className="flex justify-end gap-2 border-t border-slate-800 px-5 py-3">
          <button
            type="button"
            onClick={onClose}
            className="rounded-md px-3 py-1.5 text-xs text-slate-400 hover:bg-slate-800"
          >
            Close
          </button>
          <button
            type="button"
            onClick={run}
            disabled={busy || !code.trim()}
            className="rounded-md bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-500 disabled:opacity-50"
          >
            {busy ? "Analyzing…" : "Analyze Code"}
          </button>
        </div>
      </div>
    </div>
  );
}

