export type Severity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";

export type Language = "python" | "javascript" | "typescript" | "java";

export interface ContextLine {
  line: number;
  text: string;
  highlight: boolean;
}

export interface Remediation {
  vulnerable: string;
  secure: string;
  explanation: string;
}

export interface Finding {
  id: string;
  title: string;
  severity: Severity;
  cwe: string;
  confidence: number;
  file: string;
  line: number;
  code: string;
  language: Language;
  description: string;
  evidence: string;
  recommendation: string;
  detector: string;
  rule_id?: string;
  flow: string[];
  context: ContextLine[];
  remediation: Remediation;
}

export interface Summary {
  total: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
}

export interface ScanStats {
  files_scanned: number;
  lines_analyzed: number;
  rules_executed: number;
  duration_seconds: number;
  languages: Record<string, number>;
  total_files: number;
  ignored_files: number;
  skipped_files: string[];
}

export interface TreeNode {
  name: string;
  path: string;
  type: "dir" | "file";
  children?: TreeNode[];
  source?: boolean;
  language?: Language | null;
  findings?: number;
  max_severity?: Severity | null;
}

export interface ProjectInfo {
  scan_id: string;
  name: string;
  files_found: number;
  source_files: number;
  files_scanned: number;
  lines_analyzed: number;
  by_language: Record<string, number>;
  ignored: number;
  tree: TreeNode[];
}

export interface ScanResult {
  project: ProjectInfo;
  summary: Summary;
  stats: ScanStats;
  findings: Finding[];
  generated_at: string;
}

export interface Structure {
  name: string;
  files_found: number;
  source_files: number;
  by_language: Record<string, number>;
  ignored: number;
  tree: TreeNode[];
  note?: string;
}

export interface RuleInfo {
  id: string;
  name: string;
  description: string;
  cwe: string;
  severity: Severity;
  confidence: number;
  language: string;
}

export type ScanEvent =
  | { type: "step"; label: string }
  | { type: "structure"; structure: Structure }
  | { type: "progress"; file: string; index: number; total: number; percent: number }
  | { type: "result"; result: ScanResult }
  | { type: "error"; message: string };
