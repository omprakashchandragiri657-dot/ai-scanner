import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { Finding, ScanResult } from "../types";

const STORAGE_KEY = "acs:last-scan";

interface ScanContextValue {
  result: ScanResult | null;
  setResult: (result: ScanResult | null) => void;
  selectedFinding: Finding | null;
  selectFinding: (finding: Finding | null) => void;
  selectedFile: string | null;
  selectFile: (path: string | null) => void;
}

const ScanContext = createContext<ScanContextValue | null>(null);

function loadStoredResult(): ScanResult | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as ScanResult;
  } catch {
    return null;
  }
}

export function ScanProvider({ children }: { children: ReactNode }) {
  const [result, setResultState] = useState<ScanResult | null>(loadStoredResult);
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);

  const setResult = useCallback((next: ScanResult | null) => {
    setResultState(next);
    try {
      if (next) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      } else {
        localStorage.removeItem(STORAGE_KEY);
      }
    } catch {
      // Storage may be full or disabled; the scan still works in memory.
    }
  }, []);

  const selectFinding = useCallback((finding: Finding | null) => {
    setSelectedFinding(finding);
  }, []);

  const selectFile = useCallback((path: string | null) => {
    setSelectedFile(path);
  }, []);

  useEffect(() => {
    if (result && !selectedFile && result.project.tree.length > 0) {
      const first = findFirstFile(result.project.tree);
      if (first) setSelectedFile(first);
    }
  }, [result, selectedFile]);

  const value = useMemo(
    () => ({
      result,
      setResult,
      selectedFinding,
      selectFinding,
      selectedFile,
      selectFile,
    }),
    [result, setResult, selectedFinding, selectFinding, selectedFile, selectFile],
  );

  return <ScanContext.Provider value={value}>{children}</ScanContext.Provider>;
}

function findFirstFile(nodes: { type: string; path?: string; children?: unknown[] }[]): string | null {
  for (const node of nodes) {
    if (node.type === "file" && node.path) return node.path;
    if (node.type === "dir" && node.children) {
      const found = findFirstFile(
        node.children as { type: string; path?: string; children?: unknown[] }[],
      );
      if (found) return found;
    }
  }
  return null;
}

export function useScan(): ScanContextValue {
  const context = useContext(ScanContext);
  if (!context) {
    throw new Error("useScan must be used inside ScanProvider");
  }
  return context;
}
