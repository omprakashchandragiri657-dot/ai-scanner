import type { RuleInfo, ScanEvent, ScanResult, Structure } from "../types";

// Backend base URL. Defaults to "/api" (Vite dev proxy → http://127.0.0.1:8000);
// override with VITE_API_BASE when the frontend is served separately.
const BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? "/api";

export interface ScanHandlers {
  onStep?: (label: string) => void;
  onStructure?: (structure: Structure) => void;
  onProgress?: (file: string, index: number, total: number, percent: number) => void;
  onResult?: (result: ScanResult) => void;
  onError?: (message: string) => void;
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${BASE}${path}`);
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return (await response.json()) as T;
}

async function readError(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: string };
    return payload.detail || `Request failed (${response.status})`;
  } catch {
    return `Request failed (${response.status})`;
  }
}

export function fetchHealth(): Promise<{ status: string; version: string }> {
  return getJson("/health");
}

export function fetchRules(): Promise<{ count: number; rules: RuleInfo[] }> {
  return getJson("/rules");
}

export function fetchDemoProject(): Promise<Structure> {
  return getJson("/demo/project");
}

export function fetchFile(
  scanId: string,
  path: string,
): Promise<{ path: string; content: string; lines: number }> {
  const params = new URLSearchParams({ path });
  return getJson(`/projects/${scanId}/file?${params.toString()}`);
}

async function runScan(form: FormData, handlers: ScanHandlers): Promise<void> {
  const response = await fetch(`${BASE}/projects/scan?stream=true`, {
    method: "POST",
    body: form,
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  if (!response.body) {
    throw new Error("Streaming is not supported by this browser.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  const dispatch = (line: string) => {
    let event: ScanEvent;
    try {
      event = JSON.parse(line) as ScanEvent;
    } catch {
      return;
    }
    switch (event.type) {
      case "step":
        handlers.onStep?.(event.label);
        break;
      case "structure":
        handlers.onStructure?.(event.structure);
        break;
      case "progress":
        handlers.onProgress?.(event.file, event.index, event.total, event.percent);
        break;
      case "result":
        handlers.onResult?.(event.result);
        break;
      case "error":
        handlers.onError?.(event.message);
        break;
    }
  };

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let newline = buffer.indexOf("\n");
    while (newline >= 0) {
      const line = buffer.slice(0, newline).trim();
      buffer = buffer.slice(newline + 1);
      if (line) dispatch(line);
      newline = buffer.indexOf("\n");
    }
  }
  if (buffer.trim()) dispatch(buffer.trim());
}

export function scanZip(file: File, handlers: ScanHandlers): Promise<void> {
  const form = new FormData();
  form.append("file", file);
  return runScan(form, handlers);
}

export function scanDemo(handlers: ScanHandlers): Promise<void> {
  const form = new FormData();
  form.append("demo", "true");
  return runScan(form, handlers);
}

export async function analyzeCode(
  code: string,
  language: string,
): Promise<{ findings: ScanResult["findings"]; summary: ScanResult["summary"] }> {
  const response = await fetch(`${BASE}/code/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code, language }),
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return response.json();
}

export function exportReport(result: ScanResult): void {
  const blob = new Blob([JSON.stringify(result, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "security-report.json";
  anchor.click();
  URL.revokeObjectURL(url);
}
