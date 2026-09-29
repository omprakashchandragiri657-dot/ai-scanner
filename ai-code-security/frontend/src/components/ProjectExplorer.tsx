import { useState } from "react";
import type { Severity, TreeNode } from "../types";

const SEVERITY_TEXT: Record<string, string> = {
  CRITICAL: "text-red-400",
  HIGH: "text-orange-400",
  MEDIUM: "text-amber-400",
  LOW: "text-sky-400",
};

const SEVERITY_BG: Record<string, string> = {
  CRITICAL: "bg-red-500/20 text-red-400",
  HIGH: "bg-orange-500/20 text-orange-400",
  MEDIUM: "bg-amber-500/20 text-amber-400",
  LOW: "bg-sky-500/20 text-sky-400",
};

interface Props {
  tree: TreeNode[];
  projectName: string;
  selectedFile: string | null;
  onSelectFile: (path: string) => void;
}

export default function ProjectExplorer({
  tree,
  projectName,
  selectedFile,
  onSelectFile,
}: Props) {
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());

  function toggle(path: string) {
    setCollapsed((previous) => {
      const next = new Set(previous);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });
  }

  function renderNodes(nodes: TreeNode[], depth: number) {
    return nodes.map((node) => {
      if (node.type === "dir") {
        const isCollapsed = collapsed.has(node.path);
        return (
          <div key={node.path}>
            <button
              type="button"
              onClick={() => toggle(node.path)}
              className="flex w-full items-center gap-1.5 rounded px-2 py-1 text-left text-xs text-slate-400 hover:bg-slate-800/70"
              style={{ paddingLeft: `${depth * 14 + 8}px` }}
            >
              <span className="w-3 text-slate-600">{isCollapsed ? "▸" : "▾"}</span>
              <span className="text-slate-500">📁</span>
              <span className="mono">{node.name}</span>
            </button>
            {!isCollapsed && node.children && renderNodes(node.children, depth + 1)}
          </div>
        );
      }

      const findings = node.findings ?? 0;
      const severity = node.max_severity as Severity | null | undefined;
      const active = selectedFile === node.path;

      return (
        <button
          key={node.path}
          type="button"
          onClick={() => onSelectFile(node.path)}
          title={node.path}
          className={[
            "flex w-full items-center gap-1.5 rounded px-2 py-1 text-left text-xs transition-colors",
            active
              ? "bg-[#EFF6FF] text-[#1D4ED8]"
              : "text-slate-400 hover:bg-slate-800/70",
          ].join(" ")}
          style={{ paddingLeft: `${depth * 14 + 8}px` }}
        >
          <span className="w-3" />
          <span className="text-slate-600">📄</span>
          <span className="mono flex-1 truncate">{node.name}</span>
          {findings > 0 && severity && (
            <span
              className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${
                SEVERITY_BG[severity]
              }`}
            >
              {findings}
            </span>
          )}
        </button>
      );
    });
  }

  const totalFindings = countFindings(tree);

  return (
    <div className="flex h-full flex-col rounded-lg border border-slate-800 bg-slate-900/70">
      <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Project Explorer
          </p>
          <p className="mono mt-0.5 text-sm text-slate-200">{projectName}/</p>
        </div>
        {totalFindings > 0 && (
          <span className="rounded bg-red-500/15 px-2 py-0.5 text-[11px] text-red-400">
            {totalFindings} findings
          </span>
        )}
      </div>
      <div className="flex-1 overflow-y-auto p-2">{renderNodes(tree, 0)}</div>
      <p className="border-t border-slate-800 px-4 py-2 text-[10px] text-slate-600">
        Numbers show findings per file (color = worst severity).
      </p>
    </div>
  );
}

function countFindings(nodes: TreeNode[]): number {
  let total = 0;
  for (const node of nodes) {
    if (node.type === "file") total += node.findings ?? 0;
    else if (node.children) total += countFindings(node.children);
  }
  return total;
}

export { SEVERITY_TEXT };
