import { useRef, useState, type ChangeEvent } from "react";
import { Link } from "react-router-dom";
import SeverityBadge from "../components/SeverityBadge";
import StatCard from "../components/StatCard";
import { useScan } from "../context/ScanContext";
import { scanZip } from "../services/api";
import { formatSize, MAX_ZIP_BYTES, zipFolderFiles } from "../utils/zipFolder";

interface ProgressState {
  file: string;
  index: number;
  total: number;
  percent: number;
}

export default function Dashboard() {
  const { result, setResult, selectFinding } = useScan();

  // --- Upload flow -------------------------------------------------------
  const fileInputRef = useRef<HTMLInputElement>(null);
  const folderInputRef = useRef<HTMLInputElement>(null);
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [zipping, setZipping] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [progress, setProgress] = useState<ProgressState | null>(null);
  const [scanStep, setScanStep] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  /** Native OS file picker — triggered directly by the Upload Project button. */
  function openFilePicker() {
    if (scanning) return;
    fileInputRef.current?.click();
  }

  function handleFileSelect(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    setError(null);
    setProgress(null);
    setScanStep("");
    if (file && file.size > MAX_ZIP_BYTES) {
      setPendingFile(null);
      setError(
        `${file.name} is ${formatSize(file.size)} — the upload limit is ${formatSize(
          MAX_ZIP_BYTES,
        )}.`,
      );
    } else {
      setPendingFile(file ?? null);
    }
    // Reset so the same file can be re-selected later.
    event.target.value = "";
  }

  /** Folder picker: compress the whole folder to project.zip in the browser. */
  async function handleFolderSelect(event: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files ?? []);
    event.target.value = "";
    if (files.length === 0) return;
    setError(null);
    setProgress(null);
    setScanStep("");
    setZipping(true);
    try {
      setPendingFile(await zipFolderFiles(files));
    } catch (err) {
      setPendingFile(null);
      setError(err instanceof Error ? err.message : "Could not compress the folder.");
    } finally {
      setZipping(false);
    }
  }

  async function startScan() {
    if (!pendingFile || scanning) return;
    setScanning(true);
    setError(null);
    setProgress(null);
    setScanStep("Uploading project…");
    try {
      await scanZip(pendingFile, {
        onStep: (label) => setScanStep(label),
        onProgress: (file, index, total, percent) =>
          setProgress({ file, index, total, percent }),
        onResult: (scanResult) => {
          setResult(scanResult);
          setPendingFile(null);
          setProgress(null);
          setScanStep("");
          requestAnimationFrame(() => {
            document
              .getElementById("latest-scan")
              ?.scrollIntoView({ behavior: "smooth", block: "start" });
          });
        },
        onError: (message) => setError(message),
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setScanning(false);
    }
  }

  return (
    <div className="mx-auto max-w-6xl px-8 py-10 space-y-8">
      <section className="animate-fade-in">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-blue-500">
          Cybersecurity Research
        </p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-[#0F172A]">
          AI Code Security Analyzer
        </h1>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-400">
          Analyze AI-generated software for security vulnerabilities before production.
        </p>
        <div className="mt-5 flex flex-wrap items-center gap-3">
          {/* Hidden file inputs — buttons below open the native pickers */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileSelect}
            hidden
          />
          <input
            ref={folderInputRef}
            type="file"
            multiple
            onChange={handleFolderSelect}
            hidden
            {...({ webkitdirectory: "", directory: "" } as unknown as Record<
              string,
              string
            >)}
          />
          <button
            type="button"
            onClick={openFilePicker}
            disabled={scanning || zipping}
            className="rounded-md bg-blue-600 px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-500 disabled:opacity-50"
          >
            Upload Project
          </button>
          <button
            type="button"
            onClick={() => !scanning && !zipping && folderInputRef.current?.click()}
            disabled={scanning || zipping}
            className="rounded-md border border-slate-700 px-5 py-2.5 text-sm font-medium text-slate-300 transition-colors hover:bg-slate-800 disabled:opacity-50"
          >
            Upload Folder
          </button>
          <Link
            to="/scanner"
            className="rounded-md border border-slate-700 px-5 py-2.5 text-sm font-medium text-slate-300 transition-colors hover:bg-slate-800"
          >
            Try Demo Project
          </Link>
          <span className="text-xs text-slate-500">
            Select a <span className="mono">project.zip</span> (any file type is
            selectable — the backend validates it) or pick a whole folder — max{" "}
            {formatSize(MAX_ZIP_BYTES)}
          </span>
        </div>

        {/* Compressing a folder selection */}
        {zipping && (
          <div className="animate-fade-in mt-4 flex items-center gap-2 rounded-md border border-slate-700 bg-slate-900/80 px-4 py-3 text-xs text-slate-300">
            <span className="scan-pulse h-2 w-2 rounded-full bg-indigo-500" />
            Compressing selected folder to project.zip…
          </div>
        )}

        {/* Selected file summary + scan trigger */}
        {pendingFile && !scanning && (
          <div className="animate-fade-in mt-4 flex flex-wrap items-center gap-4 rounded-lg border border-slate-700 bg-slate-900/80 px-4 py-3">
            <span className="text-lg">📦</span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-slate-200">
                {pendingFile.name}
              </p>
              <p className="text-xs text-slate-500">
                {formatSize(pendingFile.size)} · ready to upload
              </p>
            </div>
            <button
              type="button"
              onClick={startScan}
              className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-emerald-500"
            >
              Scan Project
            </button>
            <button
              type="button"
              onClick={() => setPendingFile(null)}
              className="rounded-md px-3 py-2 text-xs text-slate-400 hover:bg-slate-800"
            >
              Remove
            </button>
          </div>
        )}

        {/* Uploading / processing state */}
        {scanning && (
          <div className="animate-fade-in mt-4 rounded-lg border border-blue-500/40 bg-blue-500/5 px-4 py-3">
            <div className="flex items-center justify-between gap-4 text-xs">
              <span className="flex min-w-0 items-center gap-2 text-slate-300">
                <span className="scan-pulse h-2 w-2 shrink-0 rounded-full bg-blue-500" />
                <span className="truncate">
                  {progress
                    ? `Scanning ${progress.file} (${progress.index}/${progress.total})`
                    : scanStep || "Uploading project…"}
                </span>
              </span>
              <span className="shrink-0 tabular-nums text-slate-500">
                {progress ? `${progress.percent}%` : ""}
              </span>
            </div>
            <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-800">
              <div
                className="h-full rounded-full bg-gradient-to-r from-blue-600 to-indigo-500 transition-[width] duration-200"
                style={{ width: `${progress ? progress.percent : 8}%` }}
              />
            </div>
          </div>
        )}

        {error && (
          <div className="animate-fade-in mt-4 rounded-md border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        )}
      </section>

      {result ? (
        <>
          <section
            id="latest-scan"
            className="grid grid-cols-2 gap-3 md:grid-cols-5"
          >
            <StatCard label="Project" value={result.project.name} />
            <StatCard label="Files Scanned" value={result.project.files_scanned} />
            <StatCard label="Lines Analyzed" value={result.project.lines_analyzed.toLocaleString()} />
            <StatCard label="Rules Executed" value={result.stats.rules_executed} />
            <StatCard
              label="Vulnerabilities"
              value={result.summary.total}
              accent={result.summary.total > 0 ? "text-red-400" : "text-emerald-400"}
            />
          </section>

          <section className="grid grid-cols-4 gap-3">
            <SeverityMini label="Critical" count={result.summary.critical} color="text-red-400" />
            <SeverityMini label="High" count={result.summary.high} color="text-orange-400" />
            <SeverityMini label="Medium" count={result.summary.medium} color="text-amber-400" />
            <SeverityMini label="Low" count={result.summary.low} color="text-sky-400" />
          </section>

          <section className="rounded-lg border border-slate-800 bg-slate-900/70">
            <div className="flex items-center justify-between border-b border-slate-800 px-5 py-3">
              <h2 className="text-sm font-semibold text-slate-200">Latest Scan</h2>
              <Link to="/scanner" className="text-xs text-blue-400 hover:text-blue-300">
                Open in scanner →
              </Link>
            </div>
            <ul className="divide-y divide-slate-800/70">
              {result.findings.slice(0, 6).map((finding) => (
                <li key={finding.id}>
                  <button
                    type="button"
                    onClick={() => selectFinding(finding)}
                    className="flex w-full items-center gap-4 px-5 py-3 text-left transition-colors hover:bg-slate-800/60"
                  >
                    <SeverityBadge severity={finding.severity} compact />
                    <span className="flex-1 text-sm text-slate-200">{finding.title}</span>
                    <span className="mono text-xs text-slate-500">{finding.cwe}</span>
                    <span className="mono max-w-64 truncate text-xs text-slate-500">
                      {finding.file}:{finding.line}
                    </span>
                    <span className="tabular-nums text-xs text-slate-500">
                      {finding.confidence}%
                    </span>
                  </button>
                </li>
              ))}
              {result.findings.length === 0 && (
                <li className="px-5 py-6 text-center text-sm text-slate-500">
                  No vulnerabilities detected in the last scan.
                </li>
              )}
            </ul>
            <div className="border-t border-slate-800 px-5 py-3 text-xs text-slate-500">
              Showing {Math.min(6, result.findings.length)} of {result.findings.length}{" "}
              findings · scanned {new Date(result.generated_at).toLocaleString()}
            </div>
          </section>
        </>
      ) : (
        <section className="rounded-lg border border-dashed border-slate-700 bg-slate-900/40 px-6 py-12 text-center">
          <p className="text-sm text-slate-400">
            No scan yet. Upload a project ZIP or launch the built-in demo project to see the
            dashboard populated with real analysis results.
          </p>
          <Link
            to="/scanner"
            className="mt-4 inline-block rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500"
          >
            Go to Project Scanner
          </Link>
        </section>
      )}
    </div>
  );
}

function SeverityMini({
  label,
  count,
  color,
}: {
  label: string;
  count: number;
  color: string;
}) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/70 px-4 py-3">
      <p className="text-[11px] uppercase tracking-wider text-slate-500">{label}</p>
      <p className={`mt-1 text-xl font-semibold tabular-nums ${color}`}>{count}</p>
    </div>
  );
}
