import type { TreeNode } from "../types";

/** Render a file tree as a plain-text structure listing. */
export function renderTree(nodes: TreeNode[], prefix = ""): string {
  const lines: string[] = [];
  nodes.forEach((node, index) => {
    const last = index === nodes.length - 1;
    const branch = last ? "└── " : "├── ";
    lines.push(`${prefix}${branch}${node.name}${node.type === "dir" ? "/" : ""}`);
    if (node.type === "dir" && node.children) {
      lines.push(renderTree(node.children, prefix + (last ? "    " : "│   ")));
    }
  });
  return lines.join("\n");
}

/** First file path in depth-first order. */
export function findFirstFile(nodes: TreeNode[]): string | null {
  for (const node of nodes) {
    if (node.type === "file") return node.path;
    if (node.type === "dir" && node.children) {
      const found = findFirstFile(node.children);
      if (found) return found;
    }
  }
  return null;
}
