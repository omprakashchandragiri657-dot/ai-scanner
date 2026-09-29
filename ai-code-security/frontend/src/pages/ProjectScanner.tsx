import { useCallback, useState } from "react";
import FileViewer from "../components/FileViewer";
import ProjectExplorer from "../components/ProjectExplorer";
import ReportSummary from "../components/ReportSummary";
import ScanningScreen, { type ProgressState } from "../components/ScanningScreen";
import UploadPanel from "../components/UploadPanel";
import { useScan } from "../context/ScanContext";
import { fetchDemoProject, scanDemo, scanZip } from "../services/api";
import type { ScanResult, Structure } from "../types";
import { findFirstFile, renderTree } from "../utils/tree";

type Phase = "upload" | "scanning" | "report";

export default function ProjectScanner() {
  const { result, setResult, selectedFile, selectFile, selectFinding } = useScan();
  const [phase, setPhase] = useState<Phase>(result ? "report" : "upload");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [steps, setSteps] = useState<string[]>([]);
  const [progress, setProgress] = useState<ProgressState | null>(null);
  const [structure, setStructure] = useState<Structure | null>(null);
  const [demoPreview, setDemoPreview] = useState<Structure | null>(null);

  const handleResult = useCallback(
    (scanResult: ScanResult) => {
      setResult(scanResult);
      setProgress(null);
      setPhase("report");
      setBusy(false);
      const first = findFirstFile(scanResult.project.tree);
      if (first) selectFile(first);
    },
    [setResult, selectFile],
  );

  const handlers = useCallback(
    () => ({
      onStep: (label: string) => setSteps((previous) => [...previous, label]),
      onStructure: setStructure,
      onProgress: (file: string, index: number, total: number, percent: number) =>
        setProgress({ file, index, total, percent }),
      onResult: handleResult,
      onError: (message: string) => {
        setError(message);
        setPhase("upload");
        setBusy(false);
      },
    }),
    [handleResult],
  );

  function beginScanning() {
    setError(null);
    setSteps([]);
    setProgress(null);
    setStructure(null);
    setDemoPreview(null);
    setPhase("scanning");
    setBusy(true);
  }

  function fail(err: unknown) {
    setError(err instanceof Error ? err.message : "Scan failed");
    setPhase("upload");
    setBusy(false);
  }

  async function startZipScan(file: File) {
    beginScanning();
    try {
      await scanZip(file, handlers());
    } catch (err) {
      fail(err);
    }
  }

  async function loadDemo() {
    setError(null);
    setBusy(true);
    try {
      setDemoPreview(await fetchDemoProject());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load the demo project");
    } finally {
      setBusy(false);
    }
  }

  async function startDemoScan() {
    beginScanning();
    try {
      await scanDemo(handlers());
    } catch (err) {
      fail(err);
    }
  }

  function reset() {
    setPhase("upload");
    setError(null);
    setDemoPreview(null);
    setSteps([]);
    setProgress(null);
    setStructure(null);
  }

  const fileFindings = result
    ? result.findings.filter((finding) => finding.file === selectedFile)
    : [];

  return (
    <div className="mx-auto max-w-7xl space-y-6 px-8 py-8">
      <header>
        <h1 className="text-xl font-semibold text-[#0F172A]">Project Scanner</h1>
        <p className="mt-1 text-sm text-slate-400">
          Upload an entire project ZIP — the analyzer extracts, traverses and scans every
          supported source file.
        </p>
      </header>

      {phase === "upload" && (
        <>
          <UploadPanel
            onFileSelected={startZipScan}
            onDemo={loadDemo}
            error={error}
            busy={busy}
          />
          {demoPreview && (
            <DemoPreview structure={demoPreview} onScan={startDemoScan} busy={busy} />
          )}
        </>
      )}

      {phase === "scanning" && (
        <ScanningScreen steps={steps} progress={progress} structure={structure} />
      )}

      {phase === "report" && result && (
        <>
          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={reset}
              className="rounded-md border border-slate-700 px-3 py-1.5 text-xs text-slate-300 hover:bg-slate-800"
            >
              ← New Scan
            </button>
            <p className="text-xs text-slate-500">
              Scan completed in {result.stats.duration_seconds}s ·{" "}
              {result.project.files_scanned} files analyzed
            </p>
          </div>

          <ReportSummary result={result} />

          <div className="grid gap-4 lg:grid-cols-5">
            <div className="h-[560px] lg:col-span-2">
              <ProjectExplorer
                tree={result.project.tree}
                projectName={result.project.name}
                selectedFile={selectedFile}
                onSelectFile={selectFile}
              />
            </div>
            <div className="h-[560px] lg:col-span-3">
              <FileViewer
                scanId={result.project.scan_id}
                path={selectedFile}
                findings={fileFindings}
                onSelectFinding={selectFinding}
              />
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function DemoPreview({
  structure,
  onScan,
  busy,
}: {
  structure: Structure;
  onScan: () => void;
  busy: boolean;
}) {
  return (
    <div className="animate-fade-in rounded-xl border border-indigo-500/40 bg-indigo-500/5 p-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-sm font-semibold text-slate-100">
            {structure.name}
            <span className="ml-2 text-xs font-normal text-slate-400">
              {structure.source_files} source files · {structure.files_found} total
            </span>
          </h2>
          <p className="mt-1 text-xs text-amber-400/90">{structure.note}</p>
          <p className="mt-2 text-xs text-slate-400">
            {Object.entries(structure.by_language)
              .map(([language, count]) => `${count} ${language}`)
              .join(" · ")}
            {structure.ignored > 0 && ` · ${structure.ignored} ignored`}
          </p>
        </div>
        <button
          type="button"
          onClick={onScan}
          disabled={busy}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
        >
          Scan Demo Project
        </button>
      </div>
      <pre className="mono mt-4 max-h-56 overflow-auto rounded-md border border-slate-800 bg-slate-950 p-3 text-[11px] leading-relaxed text-slate-400">
        {renderTree(structure.tree)}
      </pre>
    </div>
  );
}

